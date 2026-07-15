"""
backend/services/summary_service.py — Ingestion, chunking, caching, and versioning for AI summaries
"""

import os
import json
import time
import datetime
import logging
from typing import List, Dict, Any, Optional

from config import get_config
from services.storage_service import get_material_by_id, _read_metadata as _read_materials, _write_metadata as _write_materials
from services.ai.ai_client import ai_client
from services.ai.ai_exceptions import AIException

logger = logging.getLogger(__name__)

# Resolve base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SUMMARIES_DIR = os.path.join(BASE_DIR, "storage", "summaries")
TEXTS_DIR = os.path.join(SUMMARIES_DIR, "texts")
METADATA_FILE = os.path.join(SUMMARIES_DIR, "summaries.json")


def _safe_relpath(path: str, start: str) -> str:
    try:
        return os.path.relpath(path, start).replace("\\", "/")
    except ValueError:
        return os.path.abspath(path).replace("\\", "/")


def initialize_storage() -> None:
    """Ensure summary database and raw markdown directories exist on disk."""
    os.makedirs(SUMMARIES_DIR, exist_ok=True)
    os.makedirs(TEXTS_DIR, exist_ok=True)
    
    if not os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"summaries": []}, f, indent=2)
        logger.info("Initialized summaries.json database file.")


def _read_summaries() -> Dict[str, List[Dict[str, Any]]]:
    """Read full summaries registry index."""
    initialize_storage()
    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("Failed to read summaries registry: %s", str(e))
        return {"summaries": []}


def _write_summaries(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Overwrite summaries registry index."""
    try:
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error("Failed to write summaries registry: %s", str(e))
        raise IOError(f"Could not persist summaries metadata: {str(e)}")


def _update_material_status(material_id: str, status: str, generated: bool) -> None:
    """Helper to update summary parameters inside materials database index."""
    materials_data = _read_materials()
    materials = materials_data.get("materials", [])
    
    updated = False
    for m in materials:
        if m["id"] == material_id:
            m["summary_status"] = status
            m["summary_generated"] = generated
            m["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            updated = True
            break
            
    if updated:
        _write_materials(materials_data)


def get_summary_by_material_id(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Find summary entry for material, loading active markdown file content if found.
    """
    data = _read_summaries()
    summaries = data.get("summaries", [])
    entry = next((s for s in summaries if s["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    active_version_num = entry.get("active_version", 1)
    history = entry.get("history", [])
    active_history = next((h for h in history if h["version"] == active_version_num), None)
    
    if not active_history:
        return None
        
    # Read the markdown text file
    file_path = active_history["markdown_file_path"]
    abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
    
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            markdown_content = f.read()
            
        result = {
            "material_id": material_id,
            "summary_id": entry["summary_id"],
            "summary_version": active_version_num,
            "title": entry["title"],
            "subject": entry["subject"],
            "summary_markdown": markdown_content,
            "summary_status": entry["summary_status"],
            "ai_metadata": active_history.get("ai_metadata", {}),
            "created_at": active_history["created_at"]
        }
        return result
    except Exception as e:
        logger.error("Failed to read markdown file for summary %s: %s", material_id, str(e))
        return None


def get_summary_history(material_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve version history listing for material.
    """
    data = _read_summaries()
    summaries = data.get("summaries", [])
    entry = next((s for s in summaries if s["material_id"] == material_id), None)
    
    if not entry:
        return None
        
    versions_list = []
    for h in entry.get("history", []):
        versions_list.append({
            "version": h["version"],
            "created_at": h["created_at"],
            "model": h.get("model", "llama-3.3-70b-versatile"),
            "word_count": h.get("word_count", 0),
            "latency_ms": h.get("ai_metadata", {}).get("latency_ms", 0)
        })
        
    return {
        "material_id": material_id,
        "active_version": entry.get("active_version", 1),
        "versions": versions_list
    }


def chunk_document_text(text: str, chunk_size: int, overlap: int) -> List[str]:
    """
    Split long document string into overlapping segments.
    """
    if not text:
        return []
        
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunks.append(text[start:end])
        # Increment by chunk_size minus overlap
        start += (chunk_size - overlap)
        if start >= text_length or chunk_size >= text_length:
            break
            
    return chunks


def generate_summary(material_id: str, regenerate: bool = False) -> Dict[str, Any]:
    """
    Generate summary, executing chunked LLM calls if needed, and saving versioned files.
    """
    initialize_storage()
    cfg = get_config()
    
    # 1. Check Cache index
    if not regenerate:
        existing = get_summary_by_material_id(material_id)
        if existing:
            existing["cached"] = True
            return existing
            
    # Load raw text from material
    material = get_material_by_id(material_id)
    if not material:
        raise AIException("Study material not found.", code=404)
        
    raw_text = material.get("extracted_text", "").strip()
    if not raw_text or raw_text == "[Error: Text file missing or unreadable]":
        raise AIException("Extracted raw text block is empty or missing content.", code=422)
        
    # Enforce global input limits
    if len(raw_text) > cfg.MAX_SUMMARY_TOTAL_LIMIT:
        raise AIException(
            f"Ingested document length ({len(raw_text)} chars) exceeds maximum supported limit of "
            f"{cfg.MAX_SUMMARY_TOTAL_LIMIT} characters.",
            code=400
        )

    # Set status to generating
    _update_material_status(material_id, "generating", False)
    
    latency_accum = 0
    prompt_tokens_accum = 0
    completion_tokens_accum = 0
    total_tokens_accum = 0
    
    try:
        # Determine if chunking is required
        if len(raw_text) > cfg.MAX_SUMMARY_INPUT_CHARS:
            logger.info("Material length %s exceeds limit %s, entering chunking logic...", len(raw_text), cfg.MAX_SUMMARY_INPUT_CHARS)
            
            chunks = chunk_document_text(raw_text, cfg.MAX_SUMMARY_INPUT_CHARS, cfg.MAX_SUMMARY_OVERLAP_CHARS)
            sub_summaries = []
            
            # Phase 1: Summarize Chunks individually
            for idx, chunk in enumerate(chunks):
                chunk_variables = {"material_text": chunk}
                result = ai_client.run_completion(
                    prompt_type="summary_v1",
                    template_variables=chunk_variables,
                    temperature=0.2
                )
                sub_summaries.append(result["text"])
                latency_accum += result["latency_ms"]
                total_tokens_accum += result["tokens_used"]
                # In mock tests or small setups, tokens are simple totals, simulate prompt/completion splits
                prompt_tokens_accum += int(result["tokens_used"] * 0.7)
                completion_tokens_accum += int(result["tokens_used"] * 0.3)
                
            # Phase 2: Consolidate summaries
            merged_context = "\n\n".join(sub_summaries)
            consolidation_variables = {"material_text": merged_context}
            final_result = ai_client.run_completion(
                prompt_type="summary_v1",
                template_variables=consolidation_variables,
                temperature=0.2
            )
            
            summary_markdown = final_result["text"]
            latency_accum += final_result["latency_ms"]
            total_tokens_accum += final_result["tokens_used"]
            prompt_tokens_accum += int(final_result["tokens_used"] * 0.7)
            completion_tokens_accum += int(final_result["tokens_used"] * 0.3)
        else:
            # Under limits, direct prompt run
            variables = {"material_text": raw_text}
            result = ai_client.run_completion(
                prompt_type="summary_v1",
                template_variables=variables,
                temperature=0.2
            )
            summary_markdown = result["text"]
            latency_accum = result["latency_ms"]
            total_tokens_accum = result["tokens_used"]
            prompt_tokens_accum = int(result["tokens_used"] * 0.7)
            completion_tokens_accum = int(result["tokens_used"] * 0.3)

        # 2. Build history logs and version parameters
        registry_data = _read_summaries()
        summaries = registry_data.get("summaries", [])
        
        entry = next((s for s in summaries if s["material_id"] == material_id), None)
        
        new_version_num = 1
        history_list = []
        
        if entry:
            new_version_num = entry.get("active_version", 0) + 1
            history_list = entry.get("history", [])
        else:
            entry = {
                "material_id": material_id,
                "summary_id": f"sum_{material_id.replace('mat_', '')}",
                "title": f"{material['title']} Summary",
                "subject": material.get("subject", "General"),
                "active_version": 1,
                "summary_status": "generated",
                "created_at": datetime.datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "history": []
            }
            summaries.append(entry)
            
        # Target write path
        filename = f"sum_{material_id}_v{new_version_num}.md"
        file_abs_path = os.path.join(TEXTS_DIR, filename)
        
        with open(file_abs_path, "w", encoding="utf-8") as f:
            f.write(summary_markdown)
            
        rel_markdown_path = _safe_relpath(file_abs_path, BASE_DIR)
        
        # Word and character counts
        word_count = len(summary_markdown.split())
        char_count = len(summary_markdown)
        
        ai_metadata = {
            "model": cfg.MODELS.get("default", "llama-3.3-70b-versatile"),
            "prompt_version": "summary_v1",
            "latency_ms": latency_accum,
            "prompt_tokens": prompt_tokens_accum,
            "completion_tokens": completion_tokens_accum,
            "total_tokens": total_tokens_accum
        }
        
        # Add new version entry
        new_version_entry = {
            "version": new_version_num,
            "model": cfg.MODELS.get("default", "llama-3.3-70b-versatile"),
            "prompt_version": "summary_v1",
            "word_count": word_count,
            "char_count": char_count,
            "markdown_file_path": rel_markdown_path,
            "ai_metadata": ai_metadata,
            "created_at": datetime.datetime.utcnow().isoformat() + "Z"
        }
        
        history_list.append(new_version_entry)
        
        # Enforce history limit ceiling (MAX_SUMMARY_VERSIONS_RETAINED)
        if len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
            # Sort history and clean up oldest file
            history_list.sort(key=lambda x: x["version"])
            while len(history_list) > cfg.MAX_SUMMARY_VERSIONS_RETAINED:
                oldest = history_list.pop(0)
                oldest_path = oldest["markdown_file_path"]
                oldest_abs = oldest_path if os.path.isabs(oldest_path) else os.path.join(BASE_DIR, oldest_path)
                if os.path.exists(oldest_abs):
                    try:
                        os.remove(oldest_abs)
                        logger.info("Cleaned up old summary version file: %s", oldest_abs)
                    except Exception as e:
                        logger.warning("Failed to delete old version file %s: %s", oldest_abs, str(e))
        
        # Update entry properties
        entry["active_version"] = new_version_num
        entry["summary_status"] = "generated"
        entry["updated_at"] = datetime.datetime.utcnow().isoformat() + "Z"
        entry["history"] = history_list
        
        # Write indexes back
        _write_summaries(registry_data)
        
        # Update material status indicators
        _update_material_status(material_id, "generated", True)
        
        return {
            "material_id": material_id,
            "summary_id": entry["summary_id"],
            "summary_version": new_version_num,
            "title": entry["title"],
            "subject": entry["subject"],
            "summary_markdown": summary_markdown,
            "summary_status": "generated",
            "ai_metadata": ai_metadata,
            "cached": False,
            "created_at": new_version_entry["created_at"]
        }
    except Exception as e:
        logger.error("Summary generation crashed for material %s: %s", material_id, str(e), exc_info=True)
        # Update status to failed on crash
        _update_material_status(material_id, "failed", False)
        raise e


def delete_summary(material_id: str) -> None:
    """
    Remove all generated version files and registry mappings for material.
    """
    data = _read_summaries()
    summaries = data.get("summaries", [])
    entry = next((s for s in summaries if s["material_id"] == material_id), None)
    
    if not entry:
        raise AIException("Summary registry not found for this study material.", code=404)
        
    # Delete all physical markdown files
    for h in entry.get("history", []):
        file_path = h["markdown_file_path"]
        abs_path = file_path if os.path.isabs(file_path) else os.path.join(BASE_DIR, file_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
            except Exception as e:
                logger.warning("Failed to remove summary markdown file %s: %s", abs_path, str(e))
                
    # Remove index entry
    summaries.remove(entry)
    _write_summaries(data)
    
    # Update materials status fields
    _update_material_status(material_id, "not_generated", False)
    logger.info("Successfully deleted all summary histories for material: %s", material_id)
