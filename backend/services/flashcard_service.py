"""
backend/services/flashcard_service.py — AI generation, validation, persistence, and session reviews for study flashcards
"""

import os
import json
import time
import uuid
import datetime
import logging
from typing import List, Dict, Any, Optional

from config import get_config
from services.storage_service import _read_metadata as _read_materials, _write_metadata as _write_materials
from services.summary_service import get_summary_by_material_id, generate_summary
from services.ai.ai_client import ai_client
from services.ai.ai_exceptions import AIException
from services.ai.response_parser import parse_structured_json

logger = logging.getLogger(__name__)

# Resolve base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLASHCARDS_DIR = os.path.join(BASE_DIR, "storage", "flashcards")
CARDS_DIR = os.path.join(FLASHCARDS_DIR, "cards")
HISTORY_DIR = os.path.join(FLASHCARDS_DIR, "history")
METADATA_FILE = os.path.join(FLASHCARDS_DIR, "flashcards.json")


def _safe_relpath(path: str, start: str) -> str:
    try:
        return os.path.relpath(path, start).replace("\\", "/")
    except ValueError:
        return os.path.abspath(path).replace("\\", "/")


def initialize_storage() -> None:
    """Ensure flashcard directories exist on disk."""
    os.makedirs(FLASHCARDS_DIR, exist_ok=True)
    os.makedirs(CARDS_DIR, exist_ok=True)
    os.makedirs(HISTORY_DIR, exist_ok=True)
    
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"flashcards_registry": []}, f, indent=2)
        logger.info("Initialized flashcards.json registry file.")


def _read_registry() -> Dict[str, List[Dict[str, Any]]]:
    """Read full flashcards registry index."""
    initialize_storage()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to read flashcards registry: %s", str(e))
        return {"flashcards_registry": []}


def _write_registry(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Overwrite flashcards registry index."""
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to write flashcards registry: %s", str(e))
        raise IOError(f"Could not persist flashcards metadata: {str(e)}")


def _update_material_status(material_id: str, generated: bool) -> None:
    """Helper to update flashcards flag inside materials index."""
    materials_data = _read_materials()
    materials = materials_data.get("materials", [])
    
    updated = False
    for m in materials:
        if m["id"] == material_id:
            m["flashcards_generated"] = generated
            m["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            updated = True
            break
            
    if updated:
        _write_materials(materials_data)


def validate_flashcards_list(raw_cards: List[Dict[str, Any]], material_id: str, summary_ver: int) -> List[Dict[str, Any]]:
    """
    Validate and structure AI-generated cards, pruning duplicates and injecting IDs and metrics.
    """
    validated = []
    seen_questions = set()
    
    for c in raw_cards:
        question = c.get("question", "").strip()
        answer = c.get("answer", "").strip()
        topic = c.get("topic", "General").strip()
        difficulty = c.get("difficulty", "medium").strip()
        tags = c.get("tags", [])
        
        # Enforce validation bounds rules (length constraints)
        if not question or not answer:
            continue
        if len(question) < 10 or len(answer) < 5:
            continue
            
        # De-duplicate questions
        norm_q = question.lower()
        if norm_q in seen_questions:
            continue
        seen_questions.add(norm_q)
        
        # Normalize tags
        norm_tags = [t.strip().lower() for t in tags if isinstance(t, str) and t.strip()]
        
        # Normalize difficulty
        if difficulty.lower() not in ["easy", "medium", "hard"]:
            difficulty = "medium"
            
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"
        
        validated.append({
            "flashcard_id": f"fc_{uuid.uuid4().hex[:8]}",
            "material_id": material_id,
            "summary_version": summary_ver,
            "question": question,
            "answer": answer,
            "topic": topic or "General",
            "difficulty": difficulty.lower(),
            "tags": norm_tags,
            "created_at": timestamp,
            "updated_at": timestamp,
            "mastered": False,
            "review_count": 0,
            "last_reviewed": None,
            "next_review": None,
            "ease_factor": 2.5,
            "interval_days": 1
        })
        
    return validated


def get_flashcards_by_material_id(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Find active version of flashcards for material, loading cards list from disk.
    """
    registry_data = _read_registry()
    registry = registry_data.get("flashcards_registry", [])
    entry = next((f for f in registry if f["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    active_version_num = entry.get("active_version", 1)
    history = entry.get("history", [])
    active_history = next((h for h in history if h["version"] == active_version_num), None)
    
    if not active_history:
        return None
        
    file_path = active_history["cards_file_path"]
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            cards_list = json.load(f)
            
        return {
            "material_id": material_id,
            "active_version": active_version_num,
            "flashcards": cards_list,
            "ai_metadata": active_history.get("ai_metadata", {})
        }
    except Exception as e:
        logger.error("Failed to read flashcard JSON file %s: %s", abs_path, str(e))
        return None


def get_flashcards_history(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve list of historical versions for study material.
    """
    registry_data = _read_registry()
    registry = registry_data.get("flashcards_registry", [])
    entry = next((f for f in registry if f["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    versions_list = []
    for h in entry.get("history", []):
        versions_list.append({
            "version": h["version"],
            "created_at": h["created_at"],
            "model": h.get("ai_metadata", {}).get("model", "llama-3.3-70b-versatile"),
            "latency_ms": h.get("ai_metadata", {}).get("latency_ms", 0)
        })
        
    return {
        "material_id": material_id,
        "active_version": entry.get("active_version", 1),
        "versions": versions_list
    }


def generate_flashcards(material_id: str, regenerate: bool = False) -> Dict[str, Any]:
    """
    Orchestrate flashcard generation, pulling from active summaries or auto-summarizing first if missing.
    """
    initialize_storage()
    cfg = get_config()
    
    # 1. Cache lookup
    if not regenerate:
        existing = get_flashcards_by_material_id(material_id)
        if existing:
            existing["cached"] = True
            return existing
            
    # 2. Check summary status
    summary = get_summary_by_material_id(material_id)
    if not summary:
        logger.info("Summary missing for material %s, auto-generating summary context first...", material_id)
        summary = generate_summary(material_id, regenerate=False)
        
    summary_text = summary["summary_markdown"]
    summary_ver = summary["summary_version"]
    
    # 3. Call AI completions with summary context
    variables = {"summary_markdown": summary_text}
    start_time = time.time()
    
    try:
        result = ai_client.run_completion(
            prompt_type="flashcards_v1",
            template_variables=variables,
            temperature=0.3
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Parse output JSON payload
        parsed_data = parse_structured_json(result["text"])
        raw_cards = parsed_data.get("flashcards", [])
        
        if not isinstance(raw_cards, list):
            raise AIException("AI output format invalid: expected flashcards list array.", code=422)
            
        # Validate schema structures
        validated_cards = validate_flashcards_list(raw_cards, material_id, summary_ver)
        if not validated_cards:
            raise AIException("AI validation parsed zero valid flashcards. Malformed completions payload.", code=422)
            
        # 4. Save versioned cards lists
        registry_data = _read_registry()
        registry = registry_data.get("flashcards_registry", [])
        entry = next((f for f in registry if f["material_id"] == material_id), None)
        
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
            
        # Target write file
        filename = f"fc_{material_id}_v{new_version_num}.json"
        file_abs_path = os.path.join(CARDS_DIR, filename)
        
        with open(file_abs_path, "w", encoding="utf-8") as f:
            json.dump(validated_cards, f, indent=2)
            
        rel_path = _safe_relpath(file_abs_path, BASE_DIR)
        
        # AI metadata trackers
        total_tokens = result.get("tokens_used", 0)
        prompt_tokens = int(total_tokens * 0.7)
        completion_tokens = int(total_tokens * 0.3)
        
        ai_metadata = {
            "model": cfg.MODELS.get("default", "llama-3.3-70b-versatile"),
            "prompt_version": "flashcards_v1",
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }
        
        # Append version entry
        new_version_entry = {
            "version": new_version_num,
            "cards_file_path": rel_path,
            "ai_metadata": ai_metadata,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        history_list.append(new_version_entry)
        
        # Pruning retention ceiling (Keep latest 5 versions)
        if len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
            history_list.sort(key=lambda x: x["version"])
            while len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
                oldest = history_list.pop(0)
                oldest_path = oldest["cards_file_path"]
                oldest_abs = oldest_path if os.path.isabs(oldest_path) else os.path.join(BASE_DIR, oldest_path)
                if os.path.exists(oldest_abs):
                    try:
                        os.remove(oldest_abs)
                        logger.info("Purged old flashcards versions: %s", oldest_abs)
                    except Exception as e:
                        logger.warning("Failed to remove old cards file %s: %s", oldest_abs, str(e))
                        
        entry["active_version"] = new_version_num
        entry["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        entry["history"] = history_list
        
        # Overwrite registry index files
        _write_registry(registry_data)
        
        # Sync material generated flag
        _update_material_status(material_id, True)
        
        return {
            "material_id": material_id,
            "active_version": new_version_num,
            "flashcards": validated_cards,
            "ai_metadata": ai_metadata,
            "cached": False
        }
    except Exception as e:
        logger.error("Flashcards generation crashed for material %s: %s", material_id, str(e), exc_info=True)
        raise e


def update_flashcard_mastered(flashcard_id: str, mastered: bool, material_id: str) -> Dict[str, Any]:
    """
    Toggle mastered parameter on specific flashcard inside the active cards JSON file.
    """
    registry_data = _read_registry()
    registry = registry_data.get("flashcards_registry", [])
    entry = next((f for f in registry if f["material_id"] == material_id), None)
    
    if not entry:
        raise AIException("Flashcards registry not found for material.", code=404)
        
    active_version_num = entry.get("active_version", 1)
    history = entry.get("history", [])
    active_history = next((h for h in history if h["version"] == active_version_num), None)
    
    if not active_history:
        raise AIException("Active cards list not found on storage.", code=404)
        
    file_path = active_history["cards_file_path"]
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            cards = json.load(f)
            
        card_updated = False
        target_card = None
        for c in cards:
            if c["flashcard_id"] == flashcard_id:
                c["mastered"] = mastered
                c["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
                card_updated = True
                target_card = c
                break
                
        if not card_updated or not target_card:
            raise AIException("Flashcard not found inside this material deck.", code=404)
            
        with open(abs_path, "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2)
            
        return {
            "flashcard_id": flashcard_id,
            "mastered": mastered,
            "updated_at": target_card["updated_at"]
        }
    except AIException as ae:
        raise ae
    except Exception as e:
        logger.error("Failed to update mastery parameters for card %s: %s", flashcard_id, str(e))
        raise AIException("Internal file save error updating flashcard.", code=500)


def update_flashcard_review(flashcard_id: str, know_answer: bool, material_id: str) -> Dict[str, Any]:
    """
    Update review counts and log sessions outcomes for spaced repetition.
    """
    registry_data = _read_registry()
    registry = registry_data.get("flashcards_registry", [])
    entry = next((f for f in registry if f["material_id"] == material_id), None)
    
    if not entry:
        raise AIException("Flashcards registry not found for material.", code=404)
        
    active_version_num = entry.get("active_version", 1)
    history = entry.get("history", [])
    active_history = next((h for h in history if h["version"] == active_version_num), None)
    
    if not active_history:
        raise AIException("Active cards list not found on storage.", code=404)
        
    file_path = active_history["cards_file_path"]
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            cards = json.load(f)
            
        card_updated = False
        target_card = None
        for c in cards:
            if c["flashcard_id"] == flashcard_id:
                # Basic SuperMemo-2 / Spaced Repetition simulated updates
                c["review_count"] = c.get("review_count", 0) + 1
                c["last_reviewed"] = datetime.datetime.utcnow().isoformat() + "Z"
                
                # Update ease factor & intervals
                if know_answer:
                    c["ease_factor"] = max(1.3, c.get("ease_factor", 2.5) + 0.1)
                    c["interval_days"] = int(c.get("interval_days", 1) * c["ease_factor"])
                else:
                    c["ease_factor"] = max(1.3, c.get("ease_factor", 2.5) - 0.2)
                    c["interval_days"] = 1
                    
                # Calculate next review date
                next_dt = datetime.datetime.utcnow() + datetime.timedelta(days=c["interval_days"])
                c["next_review"] = next_dt.isoformat() + "Z"
                c["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
                
                card_updated = True
                target_card = c
                break
                
        if not card_updated or not target_card:
            raise AIException("Flashcard not found inside this material deck.", code=404)
            
        with open(abs_path, "w", encoding="utf-8") as f:
            json.dump(cards, f, indent=2)
            
        # Log session reviews history
        hist_filename = f"hist_{material_id}.json"
        hist_abs_path = os.path.join(HISTORY_DIR, hist_filename)
        
        hist_list = []
        if os.path.exists(hist_abs_path):
            try:
                with open(hist_abs_path, "r", encoding="utf-8") as hf:
                    hist_list = json.load(hf)
            except Exception:
                hist_list = []
                
        hist_list.append({
            "flashcard_id": flashcard_id,
            "know_answer": know_answer,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "interval_days": target_card["interval_days"]
        })
        
        with open(hist_abs_path, "w", encoding="utf-8") as hf:
            json.dump(hist_list, hf, indent=2)
            
        return {
            "flashcard_id": flashcard_id,
            "review_count": target_card["review_count"],
            "last_reviewed": target_card["last_reviewed"],
            "next_review": target_card["next_review"],
            "interval_days": target_card["interval_days"]
        }
    except AIException as ae:
        raise ae
    except Exception as e:
        logger.error("Failed to update reviews parameters for card %s: %s", flashcard_id, str(e))
        raise AIException("Internal file save error updating flashcard.", code=500)


def delete_flashcards(material_id: str) -> None:
    """
    Remove all generated version files, histories, and registry indexes for study material.
    """
    registry_data = _read_registry()
    registry = registry_data.get("flashcards_registry", [])
    entry = next((f for f in registry if f["material_id"] == material_id), None)
    
    if not entry:
        raise AIException("Flashcard registry entry not found for this study material.", code=404)
        
    # Delete cards version lists
    for h in entry.get("history", []):
        file_path = h["cards_file_path"]
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception as e:
                logger.warning("Failed to delete card file %s: %s", abs_path, str(e))
                
    # Delete review sessions histories log files
    hist_filename = f"hist_{material_id}.json"
    hist_abs_path = os.path.join(HISTORY_DIR, hist_filename)
    if os.path.exists(hist_abs_path):
        try:
            os.remove(hist_abs_path)
        except Exception as e:
            logger.warning("Failed to delete reviews history %s: %s", hist_abs_path, str(e))
            
    # Clean registry entries
    registry.remove(entry)
    _write_registry(registry_data)
    
    # Sync material flag
    _update_material_status(material_id, False)
    logger.info("Successfully deleted all flashcard decks and logs for material: %s", material_id)
