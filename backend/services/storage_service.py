"""
backend/services/storage_service.py — Local JSON storage engine for materials metadata and extracted texts
"""

import os
import json
import uuid
import datetime
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Resolve base directories relative to this file (backend/services/storage_service.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORAGE_DIR = os.path.join(BASE_DIR, "storage", "materials")
TEXTS_DIR = os.path.join(STORAGE_DIR, "texts")
METADATA_FILE = os.path.join(STORAGE_DIR, "materials.json")


def _safe_relpath(path: str, start: str) -> str:
    try:
        return os.path.relpath(path, start).replace("\\", "/")
    except ValueError:
        # Cross-drive path resolution (e.g. D: start vs C: path in temp tests)
        return os.path.abspath(path).replace("\\", "/")


def initialize_storage() -> None:
    """Ensure all database and text directories exist on disk."""
    os.makedirs(STORAGE_DIR, exist_ok=True)
    os.makedirs(TEXTS_DIR, exist_ok=True)
    
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"materials": []}, f, indent=2)
        logger.info("Initialized materials.json database file.")


def _read_metadata() -> Dict[str, List[Dict[str, Any]]]:
    """Read full metadata index."""
    initialize_storage()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to read metadata file: %s", str(e))
        return {"materials": []}


def _write_metadata(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Overwrite metadata index."""
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to write metadata file: %s", str(e))
        raise IOError(f"Could not persist metadata: {str(e)}")


def get_all_materials() -> List[Dict[str, Any]]:
    """Return lists of all materials metadata entries (excluding full text to keep listing fast)."""
    data = _read_metadata()
    return data.get("materials", [])


def get_material_by_id(mat_id: str) -> Optional[Dict[str, Any]]:
    """
    Get material metadata by ID and attach the full extracted text block.
    """
    materials = get_all_materials()
    material = next((m for m in materials if m["id"] == mat_id), None)
    
    if not material:
        return None
        
    # Read the extracted text from its separate file
    path_val = material["text_file_path"]
    text_path = path_val if os.path.isabs(path_val) else os.path.join(BASE_DIR, path_val)
    try:
        with open(text_path, "r", encoding="utf-8") as f:
            full_text = f.read()
        
        # Return a copy with text injected
        result = dict(material)
        result["extracted_text"] = full_text
        return result
    except Exception as e:
        logger.error("Failed to load text for material %s: %s", mat_id, str(e))
        result = dict(material)
        result["extracted_text"] = "[Error: Text file missing or unreadable]"
        return result


def check_duplicate_checksum(md5_checksum: str) -> Optional[str]:
    """
    Check if a file with the given MD5 checksum already exists.
    Returns the duplicate material's ID if found, else None.
    """
    if not md5_checksum:
        return None
    materials = get_all_materials()
    for m in materials:
        if m.get("md5_checksum") == md5_checksum:
            return m["id"]
    return None


def add_material(
    filename: str,
    title: str,
    subject: str,
    file_type: str,
    size_bytes: int,
    md5_checksum: str,
    page_count: int,
    word_count: int,
    character_count: int,
    extracted_text: str,
    raw_file_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Add a new material entry to database and save extracted text to disk.
    """
    initialize_storage()
    
    # Generate unique ID
    mat_id = f"mat_{uuid.uuid4().hex[:8]}"
    
    # Save the text block to a separate txt file
    text_filename = f"{mat_id}.txt"
    text_file_abs_path = os.path.join(TEXTS_DIR, text_filename)
    
    with open(text_file_abs_path, "w", encoding="utf-8") as f:
        f.write(extracted_text)
        
    # Build relative paths to store in json
    rel_text_path = _safe_relpath(text_file_abs_path, BASE_DIR)
    rel_raw_path = _safe_relpath(raw_file_path, BASE_DIR) if raw_file_path else None
    
    timestamp = datetime.datetime.utcnow().isoformat() + "Z"
    
    new_material = {
        "id": mat_id,
        "title": title,
        "subject": subject or "General",
        "filename": filename,
        "file_type": file_type,
        "size_bytes": size_bytes,
        "md5_checksum": md5_checksum,
        "page_count": page_count,
        "word_count": word_count,
        "character_count": character_count,
        "summary_generated": False,
        "summary_status": "not_generated",
        "flashcards_generated": False,
        "quiz_generated": False,
        "created_at": timestamp,
        "updated_at": timestamp,
        "text_file_path": rel_text_path,
        "raw_file_path": rel_raw_path
    }
    
    data = _read_metadata()
    data["materials"].append(new_material)
    _write_metadata(data)
    
    logger.info("Saved new material: %s (id: %s)", title, mat_id)
    return new_material


def delete_material(mat_id: str) -> bool:
    """
    Delete a study material entry, its raw file, and its extracted text file.
    """
    data = _read_metadata()
    materials = data.get("materials", [])
    
    material = next((m for m in materials if m["id"] == mat_id), None)
    if not material:
        return False
        
    # Remove from list
    data["materials"] = [m for m in materials if m["id"] != mat_id]
    _write_metadata(data)
    
    # 1. Delete extracted text file
    path_val = material["text_file_path"]
    text_path = path_val if os.path.isabs(path_val) else os.path.join(BASE_DIR, path_val)
    if os.path.exists(text_path):
        try:
            os.remove(text_path)
        except Exception as e:
            logger.warning("Could not delete text file %s: %s", text_path, str(e))
            
    # 2. Delete raw file (if any)
    if material.get("raw_file_path"):
        raw_val = material["raw_file_path"]
        raw_path = raw_val if os.path.isabs(raw_val) else os.path.join(BASE_DIR, raw_val)
        if os.path.exists(raw_path):
            try:
                os.remove(raw_path)
            except Exception as e:
                logger.warning("Could not delete raw file %s: %s", raw_path, str(e))
                
    logger.info("Successfully deleted material id: %s", mat_id)
    return True
