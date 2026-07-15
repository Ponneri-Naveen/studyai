"""
backend/services/quiz_service.py — AI generation, parsing, validation, submissions grading, and attempts logs for study quizzes
"""

import os
import json
import uuid
import datetime
import time
import logging
from typing import List, Dict, Any, Optional

from config import get_config
from services.storage_service import _read_metadata as _read_materials, _write_metadata as _write_materials
from services.summary_service import get_summary_by_material_id, generate_summary
from services.flashcard_service import get_flashcards_by_material_id, generate_flashcards
from services.ai.ai_client import ai_client
from services.ai.ai_exceptions import AIException
from services.ai.response_parser import parse_structured_json

logger = logging.getLogger(__name__)

# Resolve base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUIZZES_DIR = os.path.join(BASE_DIR, "storage", "quizzes")
QUESTIONS_DIR = os.path.join(QUIZZES_DIR, "questions")
ATTEMPTS_DIR = os.path.join(QUIZZES_DIR, "attempts")
METADATA_FILE = os.path.join(QUIZZES_DIR, "quizzes.json")


def _safe_relpath(path: str, start: str) -> str:
    try:
        return os.path.relpath(path, start).replace("\\", "/")
    except ValueError:
        return os.path.abspath(path).replace("\\", "/")


def initialize_storage() -> None:
    """Ensure quizzes directories exist on disk."""
    os.makedirs(QUIZZES_DIR, exist_ok=True)
    os.makedirs(QUESTIONS_DIR, exist_ok=True)
    os.makedirs(ATTEMPTS_DIR, exist_ok=True)
    
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"quizzes_registry": []}, f, indent=2)
        logger.info("Initialized quizzes.json registry file.")


def _read_registry() -> Dict[str, List[Dict[str, Any]]]:
    """Read full quizzes registry index."""
    initialize_storage()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to read quizzes registry: %s", str(e))
        return {"quizzes_registry": []}


def _write_registry(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Overwrite quizzes registry index."""
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to write quizzes registry: %s", str(e))
        raise IOError(f"Could not persist quizzes metadata: {str(e)}")


def _update_material_status(material_id: str, generated: bool) -> None:
    """Helper to update quiz flag inside materials index."""
    materials_data = _read_materials()
    materials = materials_data.get("materials", [])
    
    updated = False
    for m in materials:
        if m["id"] == material_id:
            m["quiz_generated"] = generated
            m["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            updated = True
            break
            
    if updated:
        _write_materials(materials_data)


def validate_questions_list(raw_questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Validate and structure AI-generated quiz questions, filtering duplicates or bad options.
    """
    validated = []
    seen_questions = set()
    
    for q in raw_questions:
        q_type = q.get("question_type", "mcq").strip().lower()
        question = q.get("question", "").strip()
        topic = q.get("topic", "General").strip()
        difficulty = q.get("difficulty", "medium").strip()
        choices = q.get("choices", [])
        correct_answer = q.get("correct_answer", "").strip()
        explanation = q.get("explanation", "").strip()
        
        if not question or not correct_answer:
            continue
        if len(question) < 10:
            continue
            
        norm_q = question.lower()
        if norm_q in seen_questions:
            continue
        seen_questions.add(norm_q)
        
        # Enforce difficulty mappings
        if difficulty.lower() not in ["easy", "medium", "hard"]:
            difficulty = "medium"
            
        # Normalize types
        if q_type not in ["mcq", "true_false", "short_answer"]:
            q_type = "mcq"
            
        if q_type == "true_false":
            choices = ["True", "False"]
            if correct_answer.lower() in ["true", "t", "yes", "1"]:
                correct_answer = "True"
            else:
                correct_answer = "False"
        elif q_type == "short_answer":
            choices = []
        else:  # mcq
            if not isinstance(choices, list) or len(choices) < 2:
                continue
            # Ensure correct answer is one of the choices
            if correct_answer not in choices:
                # Fallback: append it
                choices.append(correct_answer)
                
        validated.append({
            "question_id": f"q_{uuid.uuid4().hex[:8]}",
            "question_type": q_type,
            "question": question,
            "topic": topic or "General",
            "difficulty": difficulty.lower(),
            "choices": choices,
            "correct_answer": correct_answer,
            "explanation": explanation or "No explanation provided.",
            "marks": 1.0
        })
        
    return validated


def get_quiz_by_material_id(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Find active quiz metadata and load versioned questions sheet.
    """
    registry_data = _read_registry()
    registry = registry_data.get("quizzes_registry", [])
    entry = next((q for q in registry if q["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    active_version_num = entry.get("active_version", 1)
    history = entry.get("history", [])
    active_history = next((h for h in history if h["version"] == active_version_num), None)
    
    if not active_history:
        return None
        
    file_path = active_history["questions_file_path"]
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
            
        return {
            "material_id": material_id,
            "quiz_id": entry["quiz_id"],
            "active_version": active_version_num,
            "questions": questions,
            "ai_metadata": active_history.get("ai_metadata", {})
        }
    except Exception as e:
        logger.error("Failed to read quiz questions file %s: %s", abs_path, str(e))
        return None


def get_quizzes_history(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Load previous attempts log list and active version index details.
    """
    registry_data = _read_registry()
    registry = registry_data.get("quizzes_registry", [])
    entry = next((q for q in registry if q["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    # Read attempts list from separate attempts JSON file
    attempts = []
    hist_filename = f"att_{material_id}.json"
    hist_abs_path = os.path.join(ATTEMPTS_DIR, hist_filename)
    
    if os.path.exists(hist_abs_path):
        try:
            with open(hist_abs_path, "r", encoding="utf-8") as f:
                attempts = json.load(f)
        except Exception as e:
            logger.warning("Failed to load attempts history logs for %s: %s", material_id, str(e))
            attempts = []
            
    return {
        "material_id": material_id,
        "quiz_id": entry["quiz_id"],
        "active_version": entry.get("active_version", 1),
        "attempts_count": len(attempts),
        "attempts": attempts
    }


def generate_quiz(material_id: str, regenerate: bool = False) -> Dict[str, Any]:
    """
    Assemble context from Summary/Flashcards and generate versioned quiz questions list.
    """
    initialize_storage()
    cfg = get_config()
    
    # 1. Caching check
    if not regenerate:
        existing = get_quiz_by_material_id(material_id)
        if existing:
            existing["cached"] = True
            return existing
            
    # 2. Context assemblies loading
    summary = get_summary_by_material_id(material_id)
    if not summary:
        logger.info("Summary missing for material %s, auto-generating summary context first...", material_id)
        summary = generate_summary(material_id, regenerate=False)
        
    flashcards_data = get_flashcards_by_material_id(material_id)
    if not flashcards_data:
        logger.info("Flashcards missing for material %s, auto-generating cards context first...", material_id)
        flashcards_data = generate_flashcards(material_id, regenerate=False)
        
    summary_text = summary["summary_markdown"]
    
    # Minimize flashcard list format to save prompt tokens
    fc_list = flashcards_data.get("flashcards", [])
    minified_fc = [{"q": c["question"], "a": c["answer"], "topic": c["topic"]} for c in fc_list]
    flashcards_str = json.dumps(minified_fc)
    
    variables = {
        "summary_markdown": summary_text,
        "flashcards_json": flashcards_str
    }
    
    start_time = time.time()
    
    try:
        result = ai_client.run_completion(
            prompt_type="quiz_v1",
            template_variables=variables,
            temperature=0.2
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Parse output JSON
        parsed_data = parse_structured_json(result["text"])
        raw_questions = parsed_data.get("questions", [])
        
        if not isinstance(raw_questions, list):
            raise AIException("AI output format invalid: expected questions array list.", code=422)
            
        validated_questions = validate_questions_list(raw_questions)
        if not validated_questions:
            raise AIException("AI generated zero valid questions sheets. Parse validation failure.", code=422)
            
        # 3. Save questions list to questions folder
        registry_data = _read_registry()
        registry = registry_data.get("quizzes_registry", [])
        entry = next((q for q in registry if q["material_id"] == material_id), None)
        
        new_version_num = 1
        history_list = []
        
        if entry:
            new_version_num = entry.get("active_version", 0) + 1
            history_list = entry.get("history", [])
        else:
            entry = {
                "material_id": material_id,
                "quiz_id": f"qz_{material_id.replace('mat_', '')}",
                "summary_version": summary["summary_version"],
                "flashcard_version": flashcards_data["active_version"],
                "active_version": 1,
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "history": []
            }
            registry.append(entry)
            
        # Target write file
        filename = f"qz_{material_id}_v{new_version_num}.json"
        file_abs_path = os.path.join(QUESTIONS_DIR, filename)
        
        with open(file_abs_path, "w", encoding="utf-8") as f:
            json.dump(validated_questions, f, indent=2)
            
        rel_path = _safe_relpath(file_abs_path, BASE_DIR)
        
        # AI metadata trackers
        total_tokens = result.get("tokens_used", 0)
        prompt_tokens = int(total_tokens * 0.7)
        completion_tokens = int(total_tokens * 0.3)
        
        ai_metadata = {
            "model": cfg.MODELS.get("default", "llama-3.3-70b-versatile"),
            "prompt_version": "quiz_v1",
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
        
        # Append version history registry
        new_version_entry = {
            "version": new_version_num,
            "questions_file_path": rel_path,
            "ai_metadata": ai_metadata,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        history_list.append(new_version_entry)
        
        # History version cleaning ceiling limits (Keep latest 5 versions)
        if len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
            history_list.sort(key=lambda x: x["version"])
            while len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
                oldest = history_list.pop(0)
                oldest_path = oldest["questions_file_path"]
                oldest_abs = oldest_path if os.path.isabs(oldest_path) else os.path.join(BASE_DIR, oldest_path)
                if os.path.exists(oldest_abs):
                    try:
                        os.remove(oldest_abs)
                        logger.info("Purged old questions list sheet: %s", oldest_abs)
                    except Exception as e:
                        logger.warning("Failed to delete old questions file %s: %s", oldest_abs, str(e))
                        
        entry["active_version"] = new_version_num
        entry["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        entry["history"] = history_list
        
        _write_registry(registry_data)
        
        # Sync material status flags
        _update_material_status(material_id, True)
        
        return {
            "material_id": material_id,
            "quiz_id": entry["quiz_id"],
            "active_version": new_version_num,
            "questions": validated_questions,
            "ai_metadata": ai_metadata,
            "cached": False
        }
    except Exception as e:
        logger.error("Failed to generate quiz for material %s: %s", material_id, str(e), exc_info=True)
        raise e


def submit_quiz_answers(
    quiz_id: str,
    answers: Dict[str, str],
    mode: str,
    time_taken_seconds: int,
    question_order: List[str],
    material_id: str,
    quiz_version: int
) -> Dict[str, Any]:
    """
    Evaluate student answers sheet against correct keys and append a permanent attempt record.
    """
    initialize_storage()
    
    # Load versioned questions sheet
    filename = f"qz_{material_id}_v{quiz_version}.json"
    file_abs_path = os.path.join(QUESTIONS_DIR, filename)
    
    if not os.path.exists(file_abs_path):
        raise AIException("Target quiz questions file not found on disk.", code=404)
        
    try:
        with open(file_abs_path, "r", encoding="utf-8") as f:
            questions = json.load(f)
    except Exception as e:
        logger.error("Failed to read quiz questions JSON file: %s", str(e))
        raise AIException("Internal error loading questions.", code=500)
        
    # Evaluate answers
    responses = []
    correct_count = 0
    wrong_count = 0
    skipped_count = 0
    obtained_marks_accum = 0.0
    total_marks_accum = 0.0
    
    # Resolve difficulty and topic stats mapping
    difficulties = []
    
    for q in questions:
        q_id = q["question_id"]
        correct = q["correct_answer"]
        marks = float(q.get("marks", 1.0))
        total_marks_accum += marks
        difficulties.append(q.get("difficulty", "medium"))
        
        student_ans = answers.get(q_id, "").strip()
        
        # Grading evaluation logic
        is_correct = False
        obtained_marks = 0.0
        
        if not student_ans:
            skipped_count += 1
        else:
            q_type = q.get("question_type", "mcq")
            if q_type in ["mcq", "true_false"]:
                if student_ans.lower() == correct.lower():
                    is_correct = True
                    obtained_marks = marks
                    correct_count += 1
                else:
                    wrong_count += 1
            else:  # short_answer: whitespace trimmed, case insensitive matching
                if student_ans.lower() == correct.lower():
                    is_correct = True
                    obtained_marks = marks
                    correct_count += 1
                else:
                    # Basic loose partial matches checks if student text contains correct terms
                    if correct.lower() in student_ans.lower() and len(student_ans) < len(correct) * 4.0:
                        is_correct = True
                        obtained_marks = marks * 0.5  # Give 50% partial credit marks
                        correct_count += 1
                    else:
                        wrong_count += 1
                        
        obtained_marks_accum += obtained_marks
        
        responses.append({
            "question_id": q_id,
            "question_type": q["question_type"],
            "topic": q.get("topic", "General"),
            "difficulty": q.get("difficulty", "medium"),
            "student_answer": student_ans,
            "correct_answer": correct,
            "is_correct": is_correct,
            "marks": marks,
            "obtained_marks": obtained_marks,
            "explanation": q.get("explanation", "")
        })
        
    # Calculate score percentage
    score_percentage = (obtained_marks_accum / total_marks_accum * 100.0) if total_marks_accum > 0 else 0.0
    
    # Calculate average difficulty
    avg_difficulty = "medium"
    if difficulties:
        diff_vals = {"easy": 1, "medium": 2, "hard": 3}
        mean_diff = sum(diff_vals.get(d, 2) for d in difficulties) / len(difficulties)
        if mean_diff < 1.6:
            avg_difficulty = "easy"
        elif mean_diff > 2.4:
            avg_difficulty = "hard"
            
    attempt_id = f"att_{uuid.uuid4().hex[:8]}"
    attempt_record = {
        "attempt_id": attempt_id,
        "quiz_id": quiz_id,
        "quiz_version": quiz_version,
        "mode": mode,
        "time_taken_seconds": time_taken_seconds,
        "completed_at": datetime.datetime.utcnow().isoformat() + "Z",
        "question_order": question_order or [q["question_id"] for q in questions],
        "metrics": {
            "total_questions": len(questions),
            "answered_count": len(answers),
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "skipped_count": skipped_count,
            "obtained_marks": float(f"{obtained_marks_accum:.2f}"),
            "total_marks": total_marks_accum,
            "score_percentage": float(f"{score_percentage:.2f}"),
            "average_difficulty": avg_difficulty
        },
        "responses": responses
    }
    
    # Load and save to attempts JSON
    hist_filename = f"att_{material_id}.json"
    hist_abs_path = os.path.join(ATTEMPTS_DIR, hist_filename)
    
    hist_list = []
    if os.path.exists(hist_abs_path):
        try:
            with open(hist_abs_path, "r", encoding="utf-8") as f:
                hist_list = json.load(f)
        except Exception:
            hist_list = []
            
    hist_list.append(attempt_record)
    
    try:
        with open(hist_abs_path, "w", encoding="utf-8") as f:
            json.dump(hist_list, f, indent=2)
    except Exception as e:
        logger.error("Failed to save attempt results to disk: %s", str(e))
        raise AIException("Internal save error saving attempt records.", code=500)
        
    return attempt_record


def delete_quiz(material_id: str) -> None:
    """
    Remove versioned question sheets and registry indexes. Attempts history is retained under attempts/ folder.
    """
    registry_data = _read_registry()
    registry = registry_data.get("quizzes_registry", [])
    entry = next((q for q in registry if q["material_id"] == material_id), None)
    
    if not entry:
        raise AIException("Quiz registry entry not found for this study material.", code=404)
        
    # Delete versioned files
    for h in entry.get("history", []):
        file_path = h["questions_file_path"]
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception as e:
                logger.warning("Failed to remove quiz question file %s: %s", abs_path, str(e))
                
    # Remove index entry
    registry.remove(entry)
    _write_registry(registry_data)
    
    # Sync material generated flag
    _update_material_status(material_id, False)
    logger.info("Successfully deleted quiz questions sheet for material: %s", material_id)
