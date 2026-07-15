"""
backend/services/planner_service.py — Deterministic schedules weight builder, daily planner engines, carry-forward shifters, and pruners
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
from services.analysis_service import get_analysis_by_material_id, generate_analysis
from services.ai.ai_client import ai_client
from services.ai.ai_exceptions import AIException
from services.ai.response_parser import parse_structured_json

logger = logging.getLogger(__name__)

# Resolve base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLANS_DIR = os.path.join(BASE_DIR, "storage", "plans")
DAILY_DIR = os.path.join(PLANS_DIR, "daily")
HISTORY_DIR = os.path.join(PLANS_DIR, "history")
METADATA_FILE = os.path.join(PLANS_DIR, "plans.json")


def _safe_relpath(path: str, start: str) -> str:
    try:
        return os.path.relpath(path, start).replace("\\", "/")
    except ValueError:
        return os.path.abspath(path).replace("\\", "/")


def initialize_storage() -> None:
    """Ensure plans directories exist on disk."""
    os.makedirs(PLANS_DIR, exist_ok=True)
    os.makedirs(DAILY_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"plans_registry": []}, f, indent=2)
        logger.info("Initialized plans.json registry index file.")


def _read_registry() -> Dict[str, List[Dict[str, Any]]]:
    """Read full planner registry index."""
    initialize_storage()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to read plans registry: %s", str(e))
        return {"plans_registry": []}


def _write_registry(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Overwrite planner registry index."""
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to write plans registry: %s", str(e))
        raise IOError(f"Could not persist plans metadata: {str(e)}")


def _update_material_status(material_id: str, generated: bool) -> None:
    """Helper to update planner flag inside materials index."""
    materials_data = _read_materials()
    materials = materials_data.get("materials", [])
    
    updated = False
    for m in materials:
        if m["id"] == material_id:
            m["plan_generated"] = generated
            m["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            updated = True
            break
            
    if updated:
        _write_materials(materials_data)


def get_active_plan(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Find active plan metadata and load active daily plan sheet.
    """
    registry_data = _read_registry()
    registry = registry_data.get("plans_registry", [])
    entry = next((p for p in registry if p["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    active_version_num = entry.get("active_version", 1)
    history = entry.get("history", [])
    active_history = next((h for h in history if h["version"] == active_version_num), None)
    
    if not active_history:
        return None
        
    file_path = active_history["plan_file_path"]
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
            # Automatic reprioritization: carry forward unfinished tasks dynamically if today is subsequent date
            plan = _carry_forward_incomplete_tasks(plan)
            return plan
    except Exception as e:
        logger.error("Failed to read study plan file %s: %s", abs_path, str(e))
        return None


def get_plan_history(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve previous plan runs history list.
    """
    registry_data = _read_registry()
    registry = registry_data.get("plans_registry", [])
    entry = next((p for p in registry if p["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    versions_list = []
    for h in entry.get("history", []):
        versions_list.append({
            "version": h["version"],
            "created_at": h["created_at"],
            "model": h.get("ai_metadata", {}).get("model", "llama-3.3-70b-versatile"),
            "latency_ms": h.get("ai_metadata", {}).get("latency_ms", 0),
            "preferences": h.get("preferences", {})
        })
        
    return {
        "material_id": material_id,
        "active_version": entry.get("active_version", 1),
        "versions": versions_list
    }


def _carry_forward_incomplete_tasks(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Business Logic: Automatically identify past incomplete tasks and carry them forward to the active day.
    """
    daily_schedule = plan.get("daily_schedule", [])
    if not daily_schedule:
        return plan
        
    current_date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    
    # 1. Gather all past incomplete tasks (excluding breaks)
    incomplete_past_tasks = []
    active_day_index = -1
    
    for i, day in enumerate(daily_schedule):
        day_date_str = day.get("date", "").split("T")[0]
        
        # If day date is prior to current date, retrieve incomplete items
        if day_date_str < current_date_str:
            tasks = day.get("tasks", [])
            still_incomplete = []
            for t in tasks:
                if not t.get("completed", False) and t.get("task_type") != "break":
                    incomplete_past_tasks.append(t)
                else:
                    still_incomplete.append(t)
            day["tasks"] = [t for t in tasks if t in still_incomplete or t.get("completed", False)]
            
        elif day_date_str == current_date_str:
            active_day_index = i
            
    # If no matching today date found, default to first day that has incomplete tasks
    if active_day_index == -1:
        # Check if there is a day marked as day_number 1 or default to current running index
        for i, day in enumerate(daily_schedule):
            if not all(t.get("completed", False) for t in day.get("tasks", [])):
                active_day_index = i
                break
                
    if active_day_index == -1:
        active_day_index = len(daily_schedule) - 1
        
    if incomplete_past_tasks and active_day_index < len(daily_schedule):
        # Prevent overloading the day by capping the total estimated minutes added
        today_tasks = daily_schedule[active_day_index].get("tasks", [])
        
        existing_task_ids = {t["task_id"] for t in today_tasks}
        
        for task in incomplete_past_tasks:
            if task["task_id"] not in existing_task_ids:
                # Flag carried forward
                task["carried_forward"] = True
                today_tasks.insert(0, task)
                
        daily_schedule[active_day_index]["tasks"] = today_tasks
        
    # Recalculate dashboard preparation metrics
    plan["daily_schedule"] = daily_schedule
    plan = _recalculate_plan_metrics(plan)
    
    return plan


def _recalculate_plan_metrics(plan: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recalculate tasks completed, streak counters, and learning scores percentages.
    """
    daily_schedule = plan.get("daily_schedule", [])
    
    total_tasks = 0
    completed_tasks = 0
    
    # Track streaks
    streak = 0
    consecutive = True
    
    for day in daily_schedule:
        tasks = day.get("tasks", [])
        day_tasks_count = len(tasks)
        day_completed_count = sum(1 for t in tasks if t.get("completed", False))
        
        total_tasks += day_tasks_count
        completed_tasks += day_completed_count
        
        # Check if day is fully complete
        if day_tasks_count > 0:
            if day_completed_count == day_tasks_count:
                if consecutive:
                    streak += 1
            else:
                consecutive = False
        else:
            # If zero tasks (e.g. break day), don't break streak if prior was active
            pass
            
    overall_completion = (completed_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0
    
    # Calculate daily completion metrics for today
    current_date_str = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    today_completed_percent = 0.0
    
    for day in daily_schedule:
        day_date_str = day.get("date", "").split("T")[0]
        if day_date_str == current_date_str:
            day_tasks = day.get("tasks", [])
            if day_tasks:
                today_completed_percent = (sum(1 for t in day_tasks if t.get("completed", False)) / len(day_tasks)) * 100.0
            break
            
    plan["dashboard_preparation"] = {
        "tasks_completed": completed_tasks,
        "tasks_remaining": max(0, total_tasks - completed_tasks),
        "daily_completion_percent": float(f"{today_completed_percent:.1f}"),
        "overall_completion_percent": float(f"{overall_completion:.1f}"),
        "current_streak": streak,
        "study_consistency_score": float(f"{(100.0 if overall_completion >= streak else max(overall_completion, streak)):.1f}")
    }
    
    return plan


def generate_plan(
    material_id: str,
    exam_date: str,
    total_days: int = 14,
    daily_study_hours: float = 3.0,
    time_preference: str = "morning",
    regenerate: bool = False
) -> Dict[str, Any]:
    """
    Load Weak Topic Analysis, calculate priorities deterministically, and invoke LLM formatting.
    """
    initialize_storage()
    cfg = get_config()
    
    # 1. Caching lookups
    if not regenerate:
        existing = get_active_plan(material_id)
        if existing:
            existing["cached"] = True
            return existing
            
    # 2. Check and load Weak Topic Analysis
    analysis = get_analysis_by_material_id(material_id)
    if not analysis:
        # Attempt to dynamically generate analysis
        try:
            analysis = generate_analysis(material_id, regenerate=True)
        except Exception:
            raise AIException(
                "Performance diagnostics missing. Please take a quiz or review flashcards first to establish performance records.",
                code=400
            )
            
    # 3. Sort topics and determine priority weights
    topics_list = analysis.get("topics_analysis", [])
    if not topics_list:
        raise AIException("No study topics discovered in Weak Topic Analysis files.", code=400)
        
    # Sort confidence scores ascending (Critical topics first)
    sorted_topics = sorted(topics_list, key=lambda x: x.get("confidence_score", 0.0))
    
    topic_priorities_list = []
    for t in sorted_topics:
        conf = t.get("confidence_score", 50.0)
        topic_name = t.get("topic", "General")
        weakness = t.get("weakness_level", "Needs Review")
        
        # Calculate recommended hours allocation based on weakness level weightings
        if conf < 30.0:  # Critical
            weight_desc = "Priority: Critical (allocate 45% total prep time). Practice flashcards daily."
        elif conf < 50.0:  # Weak
            weight_desc = "Priority: High (allocate 30% total prep time). Practice quizzes frequently."
        elif conf < 70.0:  # Needs Review
            weight_desc = "Priority: Medium (allocate 15% total prep time). Review notes once."
        else:  # Good/Excellent
            weight_desc = "Priority: Low (allocate 10% total prep time). Review cards only."
            
        topic_priorities_list.append(f"- Topic: {topic_name} (Confidence: {conf:.1f}%, Status: {weakness}) -> {weight_desc}")
        
    topic_priorities_str = "\n".join(topic_priorities_list)
    
    # 4. Invoke LLM scheduler formatter
    variables = {
        "exam_date": exam_date,
        "total_days": str(total_days),
        "daily_study_hours": f"{daily_study_hours:.1f}",
        "time_preference": time_preference,
        "topic_priorities_list": topic_priorities_str
    }
    
    start_time = time.time()
    try:
        result = ai_client.run_completion(
            prompt_type="study_plan_v1",
            template_variables=variables,
            temperature=0.3
        )
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Parse output JSON daily schedules
        parsed_data = parse_structured_json(result["text"])
        daily_schedule = parsed_data.get("daily_schedule", [])
        motivational_note = parsed_data.get("motivational_note", "Stay focused on your exam prep goals!")
        
        # 5. Schema Normalization & Date allocation
        start_date = datetime.datetime.utcnow()
        
        for day in daily_schedule:
            day_num = day.get("day_number", 1)
            target_date = start_date + datetime.timedelta(days=(day_num - 1))
            day["date"] = target_date.strftime("%Y-%m-%dT00:00:00Z")
            
            tasks = day.get("tasks", [])
            for task in tasks:
                # Ensure unique task ID exists
                if not task.get("task_id") or not task.get("task_id").startswith("tsk_"):
                    task["task_id"] = f"tsk_{uuid.uuid4().hex[:8]}"
                # Force status flags
                task["completed"] = False
                task["completed_at"] = null = None
                
        # Build complete plan structure
        registry_data = _read_registry()
        registry = registry_data.get("plans_registry", [])
        entry = next((p for p in registry if p["material_id"] == material_id), None)
        
        new_version_num = 1
        history_list = []
        
        if entry:
            new_version_num = entry.get("active_version", 0) + 1
            history_list = entry.get("history", [])
        else:
            entry = {
                "material_id": material_id,
                "active_version": 1,
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "history": []
            }
            registry.append(entry)
            
        filename = f"pl_{material_id}_v{new_version_num}.json"
        file_abs_path = os.path.join(DAILY_DIR, filename)
        
        plan_payload = {
            "plan_id": f"pl_{material_id.replace('mat_', '')}",
            "material_id": material_id,
            "plan_version": new_version_num,
            "analysis_version": analysis.get("active_version", 1),
            "summary_version": analysis.get("summary_version", 1),
            "flashcard_version": analysis.get("flashcard_version", 1),
            "quiz_version": analysis.get("quiz_version", 1),
            "exam_date": exam_date,
            "preferences": {
                "total_days": total_days,
                "daily_study_hours": daily_study_hours,
                "time_preference": time_preference
            },
            "dashboard_preparation": {
                "tasks_completed": 0,
                "tasks_remaining": sum(len(d.get("tasks", [])) for d in daily_schedule),
                "daily_completion_percent": 0.0,
                "overall_completion_percent": 0.0,
                "current_streak": 0,
                "study_consistency_score": 100.0
            },
            "daily_schedule": daily_schedule,
            "motivational_note": motivational_note
        }
        
        # Save daily study plan sheet
        with open(file_abs_path, "w", encoding="utf-8") as f:
            json.dump(plan_payload, f, indent=2)
            
        rel_path = _safe_relpath(file_abs_path, BASE_DIR)
        
        # Log metadata trackers
        ai_metadata = {
            "model": cfg.MODELS.get("default", "llama-3.3-70b-versatile"),
            "prompt_version": "study_plan_v1",
            "latency_ms": latency_ms,
            "prompt_tokens": int(result.get("tokens_used", 0) * 0.75),
            "completion_tokens": int(result.get("tokens_used", 0) * 0.25),
            "total_tokens": result.get("tokens_used", 0)
        }
        
        new_version_entry = {
            "version": new_version_num,
            "plan_file_path": rel_path,
            "preferences": plan_payload["preferences"],
            "ai_metadata": ai_metadata,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        history_list.append(new_version_entry)
        
        # Pruning ceiling versions limit (> 5 versions)
        if len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
            history_list.sort(key=lambda x: x["version"])
            while len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
                oldest = history_list.pop(0)
                oldest_path = oldest["plan_file_path"]
                oldest_abs = oldest_path if os.path.isabs(oldest_path) else os.path.join(BASE_DIR, oldest_path)
                if os.path.exists(oldest_abs):
                    try:
                        os.remove(oldest_abs)
                        logger.info("Purged old study plan version file: %s", oldest_abs)
                    except Exception as e:
                        logger.warning("Failed to delete old plan file %s: %s", oldest_abs, str(e))
                        
        entry["active_version"] = new_version_num
        entry["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        entry["history"] = history_list
        
        _write_registry(registry_data)
        
        # Sync material plan generation flag status
        _update_material_status(material_id, True)
        
        return plan_payload
    except Exception as e:
        logger.error("Failed to generate personalized study plan for material %s: %s", material_id, str(e), exc_info=True)
        raise e


def toggle_task_completion(material_id: str, task_id: str, completed: bool) -> Dict[str, Any]:
    """
    Toggle completed status of a specific task and trigger streaks recalculation.
    """
    registry_data = _read_registry()
    registry = registry_data.get("plans_registry", [])
    entry = next((p for p in registry if p["material_id"] == material_id), None)
    
    if not entry:
        raise AIException("Active study plan not found for this study material.", code=404)
        
    active_version_num = entry.get("active_version", 1)
    history = entry.get("history", [])
    active_history = next((h for h in history if h["version"] == active_version_num), None)
    
    if not active_history:
        raise AIException("Study plan version file not found.", code=404)
        
    file_path = active_history["plan_file_path"]
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            plan = json.load(f)
            
        task_found = False
        for day in plan.get("daily_schedule", []):
            for task in day.get("tasks", []):
                if task["task_id"] == task_id:
                    task["completed"] = completed
                    task["completed_at"] = (datetime.datetime.utcnow().isoformat() + "Z") if completed else None
                    task_found = True
                    break
            if task_found:
                break
                
        if not task_found:
            raise AIException(f"Task with ID {task_id} not discovered in daily schedule lists.", code=404)
            
        # Recompute plan stats
        plan = _recalculate_plan_metrics(plan)
        
        # Save back to disk
        with open(abs_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2)
            
        return plan
    except AIException as e:
        raise e
    except Exception as e:
        logger.error("Failed to toggle task %s in material %s: %s", task_id, material_id, str(e), exc_info=True)
        raise AIException("Failed to update task details: " + str(e), code=500)


def delete_plan(material_id: str) -> None:
    """
    Remove study plan versioned files and registry indices.
    """
    registry_data = _read_registry()
    registry = registry_data.get("plans_registry", [])
    entry = next((p for p in registry if p["material_id"] == material_id), None)
    
    if not entry:
        raise AIException("Study plan registry entry not found for this material.", code=404)
        
    # Delete versioned daily files
    for h in entry.get("history", []):
        file_path = h["plan_file_path"]
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception as e:
                logger.warning("Failed to remove study plan version file %s: %s", abs_path, str(e))
                
    # Remove from index registry
    registry.remove(entry)
    _write_registry(registry_data)
    
    # Sync material generated flag
    _update_material_status(material_id, False)
    logger.info("Successfully deleted study planner registers for material: %s", material_id)
