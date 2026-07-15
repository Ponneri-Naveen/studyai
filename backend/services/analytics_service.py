"""
backend/services/analytics_service.py — Read-only performance database metrics aggregator, trend calculator, and badging unlock rules
"""

import os
import json
import time
import datetime
import logging
from typing import List, Dict, Any, Optional

from config import get_config
from services.storage_service import _read_metadata as _read_materials
from services.summary_service import METADATA_FILE as SUMMARY_METADATA
from services.flashcard_service import FLASHCARDS_DIR, get_flashcards_by_material_id
from services.quiz_service import QUIZZES_DIR, get_quizzes_history
from services.analysis_service import ANALYSIS_DIR, get_analysis_by_material_id
from services.planner_service import PLANS_DIR, get_active_plan
from services.ai.ai_client import ai_client
from services.ai.ai_exceptions import AIException
from services.ai.response_parser import parse_structured_json

logger = logging.getLogger(__name__)

# Resolve base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYTICS_DIR = os.path.join(BASE_DIR, "storage", "analytics")
CACHE_FILE = os.path.join(ANALYTICS_DIR, "snapshot.json")


def initialize_storage() -> None:
    """Ensure analytics directory exists on disk."""
    os.makedirs(ANALYTICS_DIR, exist_ok=True)


def get_cached_dashboard() -> Optional[Dict[str, Any]]:
    """
    Load cached analytics snapshot if it is fresh (< 5 minutes old).
    """
    initialize_storage()
    if not os.path.exists(CACHE_FILE):
        return None
        
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            snapshot = json.load(f)
            
        last_updated = snapshot.get("last_updated", "")
        if last_updated:
            dt = datetime.datetime.fromisoformat(last_updated.replace("Z", ""))
            age = (datetime.datetime.utcnow() - dt).total_seconds()
            if age < 300:  # 5 minutes cache threshold
                logger.info("Serving analytics from cached snapshot (Age: %d seconds)", age)
                return snapshot
    except Exception as e:
        logger.warning("Failed to load cached analytics dashboard: %s", str(e))
        
    return None


def force_refresh_dashboard() -> Dict[str, Any]:
    """
    Invalidate cache and calculate fresh metrics.
    """
    return calculate_dashboard_metrics(force=True)


def _safe_read_json(file_path: str, default_val: Any = None) -> Any:
    if not os.path.exists(file_path):
        return default_val
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_val


def calculate_dashboard_metrics(force: bool = False) -> Dict[str, Any]:
    """
    Core engine aggregating performance datasets across all stored data.
    """
    if not force:
        cached = get_cached_dashboard()
        if cached:
            return cached
            
    initialize_storage()
    
    # 1. Ingest Materials Count
    materials_data = _read_materials()
    materials = materials_data.get("materials", [])
    materials_uploaded = len(materials)
    
    # 2. Ingest Summaries count
    summary_registry = _safe_read_json(SUMMARY_METADATA, {"summaries_registry": []})
    summaries_count = len(summary_registry.get("summaries_registry", []))
    
    # 3. Ingest Flashcard mastery status
    flashcard_registry = _safe_read_json(
        os.path.join(FLASHCARDS_DIR, "flashcards.json"),
        {"flashcards_registry": []}
    )
    fc_registry = flashcard_registry.get("flashcards_registry", [])
    
    total_flashcards = 0
    total_mastered = 0
    decks_count = len(fc_registry)
    
    for entry in fc_registry:
        mat_id = entry.get("material_id", "")
        fc_data = get_flashcards_by_material_id(mat_id) or {}
        cards = fc_data.get("flashcards", [])
        total_flashcards += len(cards)
        total_mastered += sum(1 for c in cards if c.get("mastered", False))
        
    # 4. Ingest Quiz scores metrics
    quiz_registry = _safe_read_json(
        os.path.join(QUIZZES_DIR, "quizzes.json"),
        {"quizzes_registry": []}
    )
    qz_registry = quiz_registry.get("quizzes_registry", [])
    
    quiz_attempts_total = 0
    quiz_scores = []
    
    for entry in qz_registry:
        mat_id = entry.get("material_id", "")
        hist = get_quizzes_history(mat_id) or {}
        attempts = hist.get("attempts", [])
        quiz_attempts_total += len(attempts)
        for a in attempts:
            score = a.get("metrics", {}).get("score_percentage", 0.0)
            quiz_scores.append(score)
            
    avg_quiz_score = sum(quiz_scores) / len(quiz_scores) if quiz_scores else 0.0
    highest_score = max(quiz_scores) if quiz_scores else 0.0
    lowest_score = min(quiz_scores) if quiz_scores else 0.0
    
    # 5. Ingest Weak Topics classifications
    analysis_registry = _safe_read_json(
        os.path.join(ANALYSIS_DIR, "analysis.json"),
        {"analysis_registry": []}
    )
    an_registry = analysis_registry.get("analysis_registry", [])
    
    weak_topic_count = 0
    strong_topic_count = 0
    weak_topics_list = []
    
    for entry in an_registry:
        mat_id = entry.get("material_id", "")
        an_data = get_analysis_by_material_id(mat_id) or {}
        for topic in an_data.get("topics_analysis", []):
            level = topic.get("weakness_level", "Needs Review")
            if level in ["Critical", "Weak", "Needs Review"]:
                weak_topic_count += 1
                weak_topics_list.append(topic.get("topic", "General"))
            else:
                strong_topic_count += 1
                
    # 6. Ingest Study Planner statistics
    planner_registry = _safe_read_json(
        os.path.join(PLANS_DIR, "plans.json"),
        {"plans_registry": []}
    )
    pl_registry = planner_registry.get("plans_registry", [])
    plans_generated = len(pl_registry)
    
    tasks_completed = 0
    tasks_remaining = 0
    current_streak = 0
    longest_streak = 0
    consistency_sum = 0.0
    
    for entry in pl_registry:
        mat_id = entry.get("material_id", "")
        plan = get_active_plan(mat_id) or {}
        prep = plan.get("dashboard_preparation", {})
        tasks_completed += prep.get("tasks_completed", 0)
        tasks_remaining += prep.get("tasks_remaining", 0)
        
        streak = prep.get("current_streak", 0)
        current_streak = max(current_streak, streak)
        longest_streak = max(longest_streak, streak)
        consistency_sum += prep.get("study_consistency_score", 100.0)
        
    avg_consistency = (consistency_sum / plans_generated) if plans_generated > 0 else 100.0
    
    # 7. Calculate Quiz score slope trends
    quiz_trend_status = "stable"
    if len(quiz_scores) >= 2:
        # Evaluate slope of the last 10 scores
        recent_scores = quiz_scores[-10:]
        x = list(range(len(recent_scores)))
        y = recent_scores
        
        # Simple linear regression slope calculation
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xx = sum(val * val for val in x)
        sum_xy = sum(val_x * val_y for val_x, val_y in zip(x, y))
        
        denominator = (n * sum_xx - sum_x * sum_x)
        if denominator != 0:
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            if slope > 0.1:
                quiz_trend_status = "upward"
            elif slope < -0.1:
                quiz_trend_status = "downward"
                
    # 8. Unlocks achievements badging rules
    achievements = _evaluate_achievements_rules(
        materials_uploaded=materials_uploaded,
        summaries_count=summaries_count,
        decks_count=decks_count,
        quiz_attempts=quiz_attempts_total,
        highest_score=highest_score,
        current_streak=current_streak,
        total_mastered=total_mastered,
        tasks_completed=tasks_completed,
        tasks_remaining=tasks_remaining
    )
    
    # Compile results
    payload = {
      "overview": {
        "materials_uploaded": materials_uploaded,
        "summaries_generated": summaries_count,
        "flashcards_generated": total_flashcards,
        "flashcards_mastered": total_mastered,
        "quiz_attempts": quiz_attempts_total,
        "avg_quiz_score": float(f"{avg_quiz_score:.1f}"),
        "highest_score": float(f"{highest_score:.1f}"),
        "lowest_score": float(f"{lowest_score:.1f}"),
        "weak_topic_count": weak_topic_count,
        "strong_topic_count": strong_topic_count,
        "plans_generated": plans_generated,
        "tasks_completed": tasks_completed,
        "tasks_remaining": tasks_remaining,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "consistency_score": float(f"{avg_consistency:.1f}")
      },
      "trends": {
        "quiz_score_trend": quiz_trend_status,
        "flashcards_mastery_rate": float(f"{(total_mastered / total_flashcards * 100.0):.1f}") if total_flashcards > 0 else 0.0,
        "learning_velocity": float(f"{(total_flashcards + quiz_attempts_total) / max(materials_uploaded, 1):.1f}")
      },
      "weak_topics_list": list(set(weak_topics_list)),
      "achievements": achievements,
      "last_updated": datetime.datetime.utcnow().isoformat() + "Z"
    }
    
    # Cache snapshot file on disk
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except Exception as e:
        logger.warning("Failed to cache analytics snapshot: %s", str(e))
        
    return payload


def _evaluate_achievements_rules(
    materials_uploaded: int,
    summaries_count: int,
    decks_count: int,
    quiz_attempts: int,
    highest_score: float,
    current_streak: int,
    total_mastered: int,
    tasks_completed: int,
    tasks_remaining: int
) -> List[Dict[str, Any]]:
    """
    Evaluates achievement unlocked conditions.
    """
    now_str = datetime.datetime.utcnow().isoformat() + "Z"
    
    ach_list = [
        {
            "id": "ach_first_upload",
            "name": "First Upload",
            "description": "Upload a textbook or lecture notes file.",
            "unlocked": materials_uploaded >= 1,
            "progress": 100.0 if materials_uploaded >= 1 else 0.0,
            "unlock_date": now_str if materials_uploaded >= 1 else None
        },
        {
            "id": "ach_first_summary",
            "name": "First Summary",
            "description": "Generate key study summaries.",
            "unlocked": summaries_count >= 1,
            "progress": 100.0 if summaries_count >= 1 else 0.0,
            "unlock_date": now_str if summaries_count >= 1 else None
        },
        {
            "id": "ach_first_cards",
            "name": "Card Deck Builder",
            "description": "Create a flashcard active-recall deck.",
            "unlocked": decks_count >= 1,
            "progress": 100.0 if decks_count >= 1 else 0.0,
            "unlock_date": now_str if decks_count >= 1 else None
        },
        {
            "id": "ach_first_quiz",
            "name": "First Quiz Attempt",
            "description": "Attempt practice recall quizzes.",
            "unlocked": quiz_attempts >= 1,
            "progress": 100.0 if quiz_attempts >= 1 else 0.0,
            "unlock_date": now_str if quiz_attempts >= 1 else None
        },
        {
            "id": "ach_perfect_quiz",
            "name": "Perfect Score",
            "description": "Unlock a 100% quiz evaluation score.",
            "unlocked": highest_score == 100.0,
            "progress": 100.0 if highest_score == 100.0 else 0.0,
            "unlock_date": now_str if highest_score == 100.0 else None
        },
        {
            "id": "ach_streak_7",
            "name": "7-Day Streak",
            "description": "Study consecutive 7 days.",
            "unlocked": current_streak >= 7,
            "progress": min(100.0, (current_streak / 7.0) * 100.0),
            "unlock_date": now_str if current_streak >= 7 else None
        },
        {
            "id": "ach_cards_100",
            "name": "Master Card Strategist",
            "description": "Master 100 active-recall flashcards.",
            "unlocked": total_mastered >= 100,
            "progress": min(100.0, (total_mastered / 100.0) * 100.0),
            "unlock_date": now_str if total_mastered >= 100 else None
        },
        {
            "id": "ach_plan_complete",
            "name": "Planner Completed",
            "description": "Finish all checklist tasks in a study plan.",
            "unlocked": tasks_completed > 0 and tasks_remaining == 0,
            "progress": 100.0 if (tasks_completed > 0 and tasks_remaining == 0) else 0.0,
            "unlock_date": now_str if (tasks_completed > 0 and tasks_remaining == 0) else None
        }
    ]
    
    return ach_list


def generate_ai_insights() -> Dict[str, Any]:
    """
    Submit aggregated statistics to AI client and fetch motivational revision encouragement advice.
    """
    stats = force_refresh_dashboard()
    cfg = get_config()
    
    overview = stats["overview"]
    weak_topics_str = "\n".join(f"- {t}" for t in stats["weak_topics_list"]) if stats["weak_topics_list"] else "No weak topics detected! Performance is strong."
    
    variables = {
        "uploads": str(overview["materials_uploaded"]),
        "fc_mastered": f"{overview['flashcards_mastered']}/{overview['flashcards_generated']}",
        "quiz_avg": f"{overview['avg_quiz_score']:.1f}",
        "streak": str(overview["current_streak"]),
        "weak_topics_str": weak_topics_str
    }
    
    try:
        result = ai_client.run_completion(
            prompt_type="analytics_insight_v1",
            template_variables=variables,
            temperature=0.4
        )
        
        parsed_data = parse_structured_json(result["text"])
        return {
            "insight_paragraph": parsed_data.get("insight_paragraph", "Keep working on your active-recall cards and revision guides!"),
            "suggested_actions": parsed_data.get("suggested_actions", ["Review flashcard decks daily."]),
            "ai_metadata": {
                "model": cfg.MODELS.get("default", "llama-3.3-70b-versatile"),
                "prompt_version": "analytics_insight_v1"
            }
        }
    except Exception as e:
        logger.error("Failed to generate AI analytics insights: %s", str(e), exc_info=True)
        return {
            "insight_paragraph": "Aggregated metrics profile suggests focus on card reviews.",
            "suggested_actions": ["Practice incorrect quiz answers."],
            "ai_metadata": {
                "model": "local",
                "prompt_version": "analytics_insight_v1"
            }
        }
