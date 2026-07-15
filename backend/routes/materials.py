"""
backend/routes/materials.py — REST controllers for material upload and manual text submissions
"""

import os
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from utils.validators import validate_uploaded_file, validate_text_input, compute_md5, get_file_extension
from services.extractor import extract_metadata_and_text, TextExtractionError
import services.storage_service as storage_service

logger = logging.getLogger(__name__)

materials_bp = Blueprint("materials", __name__)


@materials_bp.route("/upload", methods=["POST"])
def upload_material():
    """
    POST /api/v1/materials/upload
    multipart/form-data
    Parameters:
        file: binary
        subject: string (optional)
        force: query parameter string 'true'/'false' (optional)
    """
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    filename = file.filename

    if not filename or filename == "":
        return jsonify({"error": "No selected file"}), 400

    # 1. Basic validation (extension, size, empty file checks)
    is_valid, err_msg = validate_uploaded_file(file, filename)
    if not is_valid:
        return jsonify({"error": err_msg}), 400

    subject = request.form.get("subject", "General").strip() or "General"
    force_upload = request.args.get("force", "false").lower() == "true"

    # 2. Check for duplicate upload via MD5 checksum
    try:
        checksum = compute_md5(file)
    except Exception as e:
        logger.error("Failed to compute MD5: %s", str(e))
        return jsonify({"error": "Failed to analyze file integrity."}), 500

    if not force_upload:
        duplicate_id = storage_service.check_duplicate_checksum(checksum)
        if duplicate_id:
            return jsonify({
                "warning": "duplicate_detected",
                "message": "This file appears to have been uploaded before.",
                "existing_material_id": duplicate_id
            }), 200

    # 3. Save raw file securely to isolated directory
    try:
        # Generate clean name keeping extension but overriding filename
        ext = get_file_extension(filename)
        # Allocate temp UUID filename to avoid filesystem traversal and shell execution risks
        import uuid
        safe_id = f"mat_{uuid.uuid4().hex[:8]}"
        safe_filename = f"{safe_id}.{ext}"
        
        # Resolve target directory
        upload_folder = current_app.config["UPLOAD_FOLDER"]
        raw_file_path = os.path.join(upload_folder, safe_filename)
        
        # Save raw upload binary
        file.save(raw_file_path)
    except Exception as e:
        logger.error("Failed to save uploaded file: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to save file on server."}), 500

    # 4. Extract Text & Statistics
    try:
        # Re-open stream or open the saved file path
        with open(raw_file_path, "rb") as f:
            extraction_results = extract_metadata_and_text(f, filename)
    except TextExtractionError as e:
        # Clean up saved raw file if extraction fails
        if os.path.exists(raw_file_path):
            os.remove(raw_file_path)
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        logger.error("Unexpected extraction crash: %s", str(e), exc_info=True)
        if os.path.exists(raw_file_path):
            os.remove(raw_file_path)
        return jsonify({"error": "Failed to process text extraction from document."}), 500

    # 5. Persist to storage
    try:
        title = filename.rsplit(".", 1)[0]
        material_record = storage_service.add_material(
            filename=filename,
            title=title,
            subject=subject,
            file_type=ext,
            size_bytes=os.path.getsize(raw_file_path),
            md5_checksum=checksum,
            page_count=extraction_results["page_count"],
            word_count=extraction_results["word_count"],
            character_count=extraction_results["character_count"],
            extracted_text=extraction_results["text"],
            raw_file_path=raw_file_path
        )
        return jsonify(material_record), 201
    except Exception as e:
        logger.error("Failed to record material to storage: %s", str(e), exc_info=True)
        # Clean up files
        if os.path.exists(raw_file_path):
            os.remove(raw_file_path)
        return jsonify({"error": "Failed to store material on server."}), 500


@materials_bp.route("/text", methods=["POST"])
def create_text_material():
    """
    POST /api/v1/materials/text
    JSON payload
    Body: { "title": string, "subject": string (optional), "text": string }
    """
    data = request.get_json() or {}
    title = data.get("title", "").strip()
    subject = data.get("subject", "General").strip() or "General"
    text = data.get("text", "")

    # 1. Validation
    is_valid, err_msg = validate_text_input(title, text)
    if not is_valid:
        return jsonify({"error": err_msg}), 400

    # 2. Extract Statistics
    word_count = len(text.split())
    character_count = len(text)
    size_bytes = len(text.encode("utf-8"))
    
    # Calculate md5 checksum of raw pasted text
    import hashlib
    hasher = hashlib.md5()
    hasher.update(text.encode("utf-8"))
    checksum = hasher.hexdigest()

    # 3. Persist to storage (No raw file needed for copy-pasted text)
    try:
        material_record = storage_service.add_material(
            filename="text_paste.txt",
            title=title,
            subject=subject,
            file_type="text_paste",
            size_bytes=size_bytes,
            md5_checksum=checksum,
            page_count=1,
            word_count=word_count,
            character_count=character_count,
            extracted_text=text,
            raw_file_path=None
        )
        return jsonify(material_record), 201
    except Exception as e:
        logger.error("Failed to store text material: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to store text material on server."}), 500


@materials_bp.route("", methods=["GET"])
def list_materials():
    """
    GET /api/v1/materials
    """
    try:
        materials = storage_service.get_all_materials()
        return jsonify(materials), 200
    except Exception as e:
        logger.error("Failed to list materials: %s", str(e))
        return jsonify({"error": "Failed to fetch study materials."}), 500


@materials_bp.route("/<string:mat_id>", methods=["GET"])
def get_material(mat_id: str):
    """
    GET /api/v1/materials/{id}
    """
    try:
        material = storage_service.get_material_by_id(mat_id)
        if not material:
            return jsonify({"error": "Material resource not found"}), 404
        return jsonify(material), 200
    except Exception as e:
        logger.error("Failed to retrieve material %s: %s", mat_id, str(e))
        return jsonify({"error": "Failed to load material details."}), 500


@materials_bp.route("/<string:mat_id>", methods=["DELETE"])
def delete_material(mat_id: str):
    """
    DELETE /api/v1/materials/{id}
    """
    try:
        deleted = storage_service.delete_material(mat_id)
        if not deleted:
            return jsonify({"error": "Material resource not found"}), 404
        return jsonify({"message": "Material deleted successfully", "id": mat_id}), 200
    except Exception as e:
        logger.error("Failed to delete material %s: %s", mat_id, str(e))
        return jsonify({"error": "Failed to delete study material."}), 500
