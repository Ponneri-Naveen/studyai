"""
backend/routes/analysis.py — REST API blueprints for weak topic analysis, queries, history comparisons and deletions
"""

import logging
from flask import Blueprint, request, jsonify

from services.analysis_service import (
    generate_analysis, get_analysis_by_material_id, get_analysis_history, delete_analysis
)
from services.ai.ai_exceptions import AIException

logger = logging.getLogger(__name__)

analysis_bp = Blueprint("analysis", __name__)


@analysis_bp.route("/generate", methods=["POST"])
def post_generate_analysis():
    """
    POST /api/v1/analysis/generate
    Body: { "material_id": "mat_xxxx", "regenerate": false }
    """
    data = request.get_json() or {}
    material_id = data.get("material_id", "").strip()
    regenerate = bool(data.get("regenerate", False))
    
    if not material_id:
        return jsonify({"error": "material_id parameter is required."}), 400
        
    try:
        result = generate_analysis(material_id, regenerate=regenerate)
        status_code = 200 if result.get("cached", False) else 201
        return jsonify(result), status_code
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to generate analysis for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500


@analysis_bp.route("/<material_id>", methods=["GET"])
def get_analysis_diagnostics(material_id):
    """
    GET /api/v1/analysis/{material_id}
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        analysis = get_analysis_by_material_id(material_id)
        if not analysis:
            return jsonify({"error": "No weak topic analysis generated for this study material yet."}), 404
        return jsonify(analysis), 200
    except Exception as e:
        logger.error("Failed to fetch analysis for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal lookup error occurred."}), 500


@analysis_bp.route("/<material_id>/history", methods=["GET"])
def get_analysis_runs_history(material_id):
    """
    GET /api/v1/analysis/{material_id}/history
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        history = get_analysis_history(material_id)
        if not history:
            return jsonify({"error": "No history runs records found for this material."}), 404
        return jsonify(history), 200
    except Exception as e:
        logger.error("Failed to fetch analysis history for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal server history query failed."}), 500


@analysis_bp.route("/<material_id>", methods=["DELETE"])
def delete_material_analysis(material_id):
    """
    DELETE /api/v1/analysis/{material_id}
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        delete_analysis(material_id)
        return jsonify({
            "message": "Weak topic analysis diagnostic file and version registers deleted successfully.",
            "material_id": material_id
        }), 200
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to delete analysis for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal error deleting analysis."}), 500
