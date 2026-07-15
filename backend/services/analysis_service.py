"""
backend/services/analysis_service.py — Deterministic performance diagnostics, weighted scoring algorithm, version pruners, and AI suggestions compiler
"""

import os
import json
import uuid
import time
import datetime
import logging
from typing import List, Dict, Any, Optional

from config import get_config
from services.storage_service import _read_metadata as _read_materials, _write_metadata as _write_materials
from services.summary_service import get_summary_by_material_id
from services.flashcard_service import get_flashcards_by_material_id, FLASHCARDS_DIR
from services.quiz_service import get_quizzes_history, QUIZZES_DIR
from services.ai.ai_client import ai_client
from services.ai.ai_exceptions import AIException
from services.ai.response_parser import parse_structured_json

logger = logging.getLogger(__name__)

# Resolve base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ANALYSIS_DIR = os.path.join(BASE_DIR, "storage", "analysis")
HISTORY_DIR = os.path.join(ANALYSIS_DIR, "history")
METADATA_FILE = os.path.join(ANALYSIS_DIR, "analysis.json")


def _safe_relpath(path: str, start: str) -> str:
    try:
        return os.path.relpath(path, start).replace("\\", "/")
    except ValueError:
        return os.path.abspath(path).replace("\\", "/")


def initialize_storage() -> None:
    """Ensure analysis directories exist on disk."""
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"analysis_registry": []}, f, indent=2)
        logger.info("Initialized analysis.json registry file.")


def _read_registry() -> Dict[str, List[Dict[str, Any]]]:
    """Read full analysis registry index."""
    initialize_storage()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to read analysis registry: %s", str(e))
        return {"analysis_registry": []}


def _write_registry(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Overwrite analysis registry index."""
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to write analysis registry: %s", str(e))
        raise IOError(f"Could not persist analysis metadata: {str(e)}")


def _update_material_status(material_id: str, generated: bool) -> None:
    """Helper to update analysis flag inside materials index."""
    materials_data = _read_materials()
    materials = materials_data.get("materials", [])
    
    updated = False
    for m in materials:
        if m["id"] == material_id:
            m["analysis_generated"] = generated
            m["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            updated = True
            break
            
    if updated:
        _write_materials(materials_data)


def get_analysis_by_material_id(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Find active analysis metadata and load versioned analysis sheet.
    """
    registry_data = _read_registry()
    registry = registry_data.get("analysis_registry", [])
    entry = next((a for a in registry if a["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    active_version_num = entry.get("active_version", 1)
    history = entry.get("history", [])
    active_history = next((h for h in history if h["version"] == active_version_num), None)
    
    if not active_history:
        return None
        
    file_path = active_history["analysis_file_path"]
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to read analysis file %s: %s", abs_path, str(e))
        return None


def get_analysis_history(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve previous analysis logs history lists mappings.
    """
    registry_data = _read_registry()
    registry = registry_data.get("analysis_registry", [])
    entry = next((a for a in registry if a["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    versions_list = []
    for h in entry.get("history", []):
        versions_list.append({
            "version": h["version"],
            "created_at": h["created_at"],
            "model": h.get("ai_metadata", {}).get("model", "llama-3.3-70b-versatile"),
            "latency_ms": h.get("ai_metadata", {}).get("latency_ms", 0),
            "dashboard_preparation": h.get("dashboard_preparation", {})
        })
        
    return {
        "material_id": material_id,
        "active_version": entry.get("active_version", 1),
        "versions": versions_list
    }


def aggregate_performance_data(material_id: str) -> Dict[str, Any]:
    """
    Gather diagnostic datasets mapping topics from Quizzes attempts and Flashcard reviews.
    """
    # 1. Gather Quiz attempts list
    quizzes_hist = get_quizzes_history(material_id) or {}
    attempts_list = quizzes_hist.get("attempts", [])
    
    # 2. Gather Flashcards cards list and review sessions log
    flashcards_data = get_flashcards_by_material_id(material_id) or {}
    cards_list = flashcards_data.get("flashcards", [])
    
    # Map review logs if file exists
    review_history = []
    hist_filename = f"hist_{material_id}.json"
    hist_abs_path = os.path.join(FLASHCARDS_DIR, "history", hist_filename)
    if os.path.exists(hist_abs_path):
        try:
            with open(hist_abs_path, "r", encoding="utf-8") as f:
                review_history = json.load(f)
        except Exception:
            review_history = []
            
    # Check if student has taken a test or completed card reviews
    if not attempts_list and not review_history:
        raise AIException("Please complete at least one quiz attempt or review flashcards first to generate performance data.", code=400)
        
    # Group results by topic names
    topics_map = {}
    
    # Process Quiz attempts data
    for att in attempts_list:
        for resp in att.get("responses", []):
            topic = resp.get("topic", "General").strip()
            if not topic:
                topic = "General"
                
            if topic not in topics_map:
                topics_map[topic] = {
                    "quiz_attempts": 0,
                    "quiz_correct": 0,
                    "quiz_wrong": 0,
                    "flashcards_total": 0,
                    "flashcards_mastered": 0,
                    "review_count": 0,
                    "difficulties": []
                }
                
            topics_map[topic]["quiz_attempts"] += 1
            if resp.get("is_correct", False):
                topics_map[topic]["quiz_correct"] += 1
            else:
                topics_map[topic]["quiz_wrong"] += 1
            topics_map[topic]["difficulties"].append(resp.get("difficulty", "medium"))
            
    # Process Flashcard cards data
    for card in cards_list:
        topic = card.get("topic", "General").strip()
        if not topic:
            topic = "General"
            
        if topic not in topics_map:
            topics_map[topic] = {
                "quiz_attempts": 0,
                "quiz_correct": 0,
                "quiz_wrong": 0,
                "flashcards_total": 0,
                "flashcards_mastered": 0,
                "review_count": 0,
                "difficulties": []
            }
            
        topics_map[topic]["flashcards_total"] += 1
        if card.get("mastered", False):
            topics_map[topic]["flashcards_mastered"] += 1
        topics_map[topic]["review_count"] += card.get("review_count", 0)
        
    return {
        "topics_map": topics_map,
        "attempts_list": attempts_list,
        "review_history": review_history
    }


def calculate_learning_trend(attempts_list: List[Dict[str, Any]]) -> str:
    """
    Calculate learning trend (improving | stable | regression) based on recent score comparisons.
    """
    if len(attempts_list) < 2:
        return "stable"
        
    # Sort attempts by completion date (descending)
    sorted_atts = sorted(attempts_list, key=lambda x: x.get("completed_at", ""), reverse=True)
    
    latest_score = sorted_atts[0]["metrics"]["score_percentage"]
    
    # Calculate average score of previous attempts
    prev_atts = sorted_atts[1:]
    prev_avg = sum(a["metrics"]["score_percentage"] for a in prev_atts) / len(prev_atts)
    
    if latest_score > prev_avg + 3.0:  # 3% threshold
        return "improving"
    elif latest_score < prev_avg - 3.0:
        return "regression"
    else:
        return "stable"


def generate_analysis(material_id: str, regenerate: bool = False) -> Dict[str, Any]:
    """
    Perform local mathematical aggregation over student history logs and fetch AI revision strategies.
    """
    initialize_storage()
    cfg = get_config()
    
    # 1. Caching check
    if not regenerate:
        existing = get_analysis_by_material_id(material_id)
        if existing:
            existing["cached"] = True
            return existing
            
    # 2. Aggregations from attempts and review histories
    agg_data = aggregate_performance_data(material_id)
    topics_map = agg_data["topics_map"]
    attempts_list = agg_data["attempts_list"]
    
    # Validate context versions
    summary = get_summary_by_material_id(material_id)
    summary_ver = summary["summary_version"] if summary else 1
    
    flashcards_data = get_flashcards_by_material_id(material_id) or {}
    flashcards_ver = flashcards_data.get("active_version", 1)
    
    quizzes_hist = get_quizzes_history(material_id) or {}
    quiz_ver = quizzes_hist.get("active_version", 1)
    
    # 3. Deterministic score logic math calculations
    topics_analysis = []
    weak_topics_list = []
    
    total_acc_sum = 0.0
    topics_count = 0
    weak_topic_count = 0
    strong_topic_count = 0
    
    for topic, stats in topics_map.items():
        # Quiz Accuracy
        quiz_attempts = stats["quiz_attempts"]
        quiz_accuracy = 100.0
        if quiz_attempts > 0:
            quiz_accuracy = (stats["quiz_correct"] / quiz_attempts) * 100.0
            
        # Mastery Percentage
        total_fc = stats["flashcards_total"]
        mastery_score = 100.0
        if total_fc > 0:
            mastery_score = (stats["flashcards_mastered"] / total_fc) * 100.0
            
        # Average Difficulty
        difficulties = stats["difficulties"]
        topic_diff = "medium"
        if difficulties:
            diff_vals = {"easy": 1, "medium": 2, "hard": 3}
            mean_diff = sum(diff_vals.get(d, 2) for d in difficulties) / len(difficulties)
            if mean_diff < 1.6:
                topic_diff = "easy"
            elif mean_diff > 2.4:
                topic_diff = "hard"
                
        # Deterministic Confidence Score calculations
        # Formula: 0.5 * Accuracy + 0.3 * Mastery + 0.2 * Reviews
        reviews = min(stats["review_count"], 5)  # cap review bonus counts at 5 reviews
        reviews_score = (reviews / 5.0) * 100.0
        
        confidence_score = (0.50 * quiz_accuracy) + (0.30 * mastery_score) + (0.20 * reviews_score)
        
        # Difficulty bonus adjustment (+5% leniency if hard)
        if topic_diff == "hard":
            confidence_score = min(100.0, confidence_score + 5.0)
        elif topic_diff == "easy":
            confidence_score = max(0.0, confidence_score - 5.0)
            
        # Classify weakness level boundaries
        if confidence_score >= 85.0:
            weakness_level = "Excellent"
            recommended_action = "Maintain current revision intervals. Keep doing active recall."
            strong_topic_count += 1
        elif confidence_score >= 70.0:
            weakness_level = "Good"
            recommended_action = "Review flashcards occasionally to prevent memory decay."
            strong_topic_count += 1
        elif confidence_score >= 50.0:
            weakness_level = "Needs Review"
            recommended_action = "Take practice quizzes focused on this specific topic outlines."
            weak_topic_count += 1
        elif confidence_score >= 30.0:
            weakness_level = "Weak"
            recommended_action = "Re-study summaries, complete cards, and review incorrect questions."
            weak_topic_count += 1
        else:
            weakness_level = "Critical"
            recommended_action = "Urgent: reread textbook segments and rewrite manual study summaries."
            weak_topic_count += 1
            
        total_acc_sum += quiz_accuracy
        topics_count += 1
        
        topic_analysis_entry = {
            "topic": topic,
            "difficulty": topic_diff,
            "attempts": quiz_attempts,
            "correct_answers": stats["quiz_correct"],
            "wrong_answers": stats["quiz_wrong"],
            "accuracy": float(f"{quiz_accuracy:.1f}"),
            "mastery_score": float(f"{mastery_score:.1f}"),
            "confidence_score": float(f"{confidence_score:.1f}"),
            "weakness_level": weakness_level,
            "recommended_action": recommended_action
        }
        
        topics_analysis.append(topic_analysis_entry)
        
        # Filter weak topics list for AI prompt ingestion
        if weakness_level in ["Critical", "Weak", "Needs Review"]:
            weak_topics_list.append(f"- {topic} (Weakness: {weakness_level}, Confidence: {confidence_score:.1f}%, Accuracy: {quiz_accuracy:.1f}%)")
            
    # Calculate averages
    avg_accuracy = (total_acc_sum / topics_count) if topics_count > 0 else 100.0
    learning_trend = calculate_learning_trend(attempts_list)
    
    dashboard_preparation = {
        "average_accuracy": float(f"{avg_accuracy:.1f}"),
        "weak_topic_count": weak_topic_count,
        "strong_topic_count": strong_topic_count,
        "learning_trend": learning_trend
    }
    
    # 4. Generate AI Suggestions using deterministic rankings
    weak_topics_str = "\n".join(weak_topics_list) if weak_topics_list else "No weak topics detected! Excellent performance."
    
    variables = {
        "average_accuracy": f"{avg_accuracy:.1f}",
        "weak_topics_list": weak_topics_str
    }
    
    start_time = time.time()
    
    try:
        result = ai_client.run_completion(
            prompt_type="weak_topics_v1",
            template_variables=variables,
            temperature=0.3
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Parse suggestions JSON
        parsed_data = parse_structured_json(result["text"])
        
        ai_recommendations = {
            "personalized_advice": parsed_data.get("personalized_advice", "Review detected weak subjects outline."),
            "revision_priorities": parsed_data.get("revision_priorities", []),
            "learning_strategy": parsed_data.get("learning_strategy", "Focus on active-recall questions.")
        }
        
        # 5. Registry Versioning Persistence
        registry_data = _read_registry()
        registry = registry_data.get("analysis_registry", [])
        entry = next((a for a in registry if a["material_id"] == material_id), None)
        
        new_version_num = 1
        history_list = []
        
        if entry:
            new_version_num = entry.get("active_version", 0) + 1
            history_list = entry.get("history", [])
        else:
            entry = {
                "material_id": material_id,
                "analysis_id": f"an_{material_id.replace('mat_', '')}",
                "active_version": 1,
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "history": []
            }
            registry.append(entry)
            
        filename = f"an_{material_id}_v{new_version_num}.json"
        file_abs_path = os.path.join(HISTORY_DIR, filename)
        
        # Build complete output model
        analysis_payload = {
            "analysis_id": entry["analysis_id"],
            "material_id": material_id,
            "active_version": new_version_num,
            "summary_version": summary_ver,
            "flashcard_version": flashcards_ver,
            "quiz_version": quiz_ver,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "dashboard_preparation": dashboard_preparation,
            "topics_analysis": topics_analysis,
            "ai_recommendations": ai_recommendations,
            "ai_metadata": {
                "model": cfg.MODELS.get("default", "llama-3.3-70b-versatile"),
                "prompt_version": "weak_topics_v1",
                "latency_ms": latency_ms,
                "prompt_tokens": int(result.get("tokens_used", 0) * 0.7),
                "completion_tokens": int(result.get("tokens_used", 0) * 0.3),
                "total_tokens": result.get("tokens_used", 0)
            }
        }
        
        with open(file_abs_path, "w", encoding="utf-8") as f:
            json.dump(analysis_payload, f, indent=2)
            
        rel_path = _safe_relpath(file_abs_path, BASE_DIR)
        
        # Append version history index
        new_version_entry = {
            "version": new_version_num,
            "analysis_file_path": rel_path,
            "dashboard_preparation": dashboard_preparation,
            "ai_metadata": analysis_payload["ai_metadata"],
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        history_list.append(new_version_entry)
        
        # History version cleaning ceiling limits (Keep latest 5 versions)
        if len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
            history_list.sort(key=lambda x: x["version"])
            while len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
                oldest = history_list.pop(0)
                oldest_path = oldest["analysis_file_path"]
                oldest_abs = oldest_path if os.path.isabs(oldest_path) else os.path.join(BASE_DIR, oldest_path)
                if os.path.exists(oldest_abs):
                    try:
                        os.remove(oldest_abs)
                        logger.info("Purged old analysis diagnostics file: %s", oldest_abs)
                    except Exception as e:
                        logger.warning("Failed to delete old analysis file %s: %s", oldest_abs, str(e))
                        
        entry["active_version"] = new_version_num
        entry["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        entry["history"] = history_list
        
        _write_registry(registry_data)
        
        # Sync material status flags
        _update_material_status(material_id, True)
        
        return analysis_payload
    except Exception as e:
        logger.error("Failed to generate weak topics analysis for material %s: %s", material_id, str(e), exc_info=True)
        raise e


def delete_analysis(material_id: str) -> None:
    """
    Remove analysis versioned JSON files and registry entries.
    """
    registry_data = _read_registry()
    registry = registry_data.get("analysis_registry", [])
    entry = next((a for a in registry if a["material_id"] == material_id), None)
    
    if not entry:
        raise AIException("Analysis registry entry not found for this study material.", code=404)
        
    # Delete versioned files
    for h in entry.get("history", []):
        file_path = h["analysis_file_path"]
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception as e:
                logger.warning("Failed to remove analysis file %s: %s", abs_path, str(e))
                
    # Remove index entry
    registry.remove(entry)
    _write_registry(registry_data)
    
    # Sync material generated flag
    _update_material_status(material_id, False)
    logger.info("Successfully deleted weak topic analysis diagnostics for material: %s", material_id)
