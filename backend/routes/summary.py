"""
backend/routes/summary.py — REST API controllers for generating, loading, deleting, and tracking version histories of summaries
"""

import logging
from flask import Blueprint, request, jsonify

from services.summary_service import generate_summary, get_summary_by_material_id, get_summary_history, delete_summary
from services.ai.ai_exceptions import AIException

logger = logging.getLogger(__name__)

summary_bp = Blueprint("summary", __name__)


@summary_bp.route("/generate", methods=["POST"])
def post_generate_summary():
    """
    POST /api/v1/summary/generate
    Body: { "material_id": "mat_xxxx", "regenerate": false }
    Triggers summary generation pipeline (with caching lookup unless override requested).
    """
    data = request.get_json() or {}
    material_id = data.get("material_id", "").strip()
    regenerate = bool(data.get("regenerate", False))
    
    if not material_id:
        return jsonify({"error": "material_id query parameter is required."}), 400
        
    try:
        result = generate_summary(material_id, regenerate=regenerate)
        status_code = 200 if result.get("cached", False) else 201
        return jsonify(result), status_code
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to generate summary for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "An unexpected error occurred during summarization: " + str(e)}), 500


@summary_bp.route("/<material_id>", methods=["GET"])
def get_summary(material_id):
    """
    GET /api/v1/summary/{material_id}
    Retrieve the active generated summary for study material.
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        summary = get_summary_by_material_id(material_id)
        if not summary:
            return jsonify({"error": "No summary generated for this study material yet."}), 404
        return jsonify(summary), 200
    except Exception as e:
        logger.error("Failed to fetch summary for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal server lookup error occurred."}), 500


@summary_bp.route("/<material_id>/history", methods=["GET"])
def get_summary_versions_history(material_id):
    """
    GET /api/v1/summary/{material_id}/history
    Retrieve the historical versions registry checklist for study material.
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        history = get_summary_history(material_id)
        if not history:
            return jsonify({"error": "No history records found for this material."}), 404
        return jsonify(history), 200
    except Exception as e:
        logger.error("Failed to fetch summary history for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal server history query failed."}), 500


@summary_bp.route("/<material_id>", methods=["DELETE"])
def delete_material_summary(material_id):
    """
    DELETE /api/v1/summary/{material_id}
    Delete all summary versions and reset status mappings in database registries.
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        delete_summary(material_id)
        return jsonify({
            "message": "Summary and version files deleted successfully.",
            "material_id": material_id
        }), 200
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to delete summary for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal error deleting summary."}), 500
