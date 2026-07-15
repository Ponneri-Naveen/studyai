"""
backend/routes/flashcards.py — REST API blueprints for flashcards generation, query lists, toggle mastery and logging reviews
"""

import logging
from flask import Blueprint, request, jsonify

from services.flashcard_service import (
    generate_flashcards, get_flashcards_by_material_id, get_flashcards_history,
    update_flashcard_mastered, update_flashcard_review, delete_flashcards
)
from services.ai.ai_exceptions import AIException

logger = logging.getLogger(__name__)

flashcards_bp = Blueprint("flashcards", __name__)


@flashcards_bp.route("/generate", methods=["POST"])
def post_generate_flashcards():
    """
    POST /api/v1/flashcards/generate
    Body: { "material_id": "mat_xxxx", "regenerate": false }
    """
    data = request.get_json() or {}
    material_id = data.get("material_id", "").strip()
    regenerate = bool(data.get("regenerate", False))
    
    if not material_id:
        return jsonify({"error": "material_id parameter is required."}), 400
        
    try:
        result = generate_flashcards(material_id, regenerate=regenerate)
        status_code = 200 if result.get("cached", False) else 201
        return jsonify(result), status_code
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to generate flashcards for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500


@flashcards_bp.route("/<material_id>", methods=["GET"])
def get_flashcards(material_id):
    """
    GET /api/v1/flashcards/{material_id}
    Get active cards list for material.
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        cards = get_flashcards_by_material_id(material_id)
        if not cards:
            return jsonify({"error": "No flashcards generated for this material yet."}), 404
        return jsonify(cards), 200
    except Exception as e:
        logger.error("Failed to fetch flashcards for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal server lookup error occurred."}), 500


@flashcards_bp.route("/<material_id>/history", methods=["GET"])
def get_flashcards_versions_history(material_id):
    """
    GET /api/v1/flashcards/{material_id}/history
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        history = get_flashcards_history(material_id)
        if not history:
            return jsonify({"error": "No history records found for this material."}), 404
        return jsonify(history), 200
    except Exception as e:
        logger.error("Failed to fetch flashcard history for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal server history query failed."}), 500


@flashcards_bp.route("/<flashcard_id>/mastered", methods=["PATCH"])
def patch_flashcard_mastered(flashcard_id):
    """
    PATCH /api/v1/flashcards/{flashcard_id}/mastered
    Body: { "material_id": "mat_xxxx", "mastered": true }
    """
    data = request.get_json() or {}
    material_id = data.get("material_id", "").strip()
    mastered = bool(data.get("mastered", False))
    
    if not material_id:
        return jsonify({"error": "material_id is required inside request payload."}), 400
        
    try:
        result = update_flashcard_mastered(flashcard_id, mastered, material_id)
        return jsonify(result), 200
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to update mastered state: %s", str(e), exc_info=True)
        return jsonify({"error": "Internal error occurred."}), 500


@flashcards_bp.route("/<flashcard_id>/review", methods=["PATCH"])
def patch_flashcard_review(flashcard_id):
    """
    PATCH /api/v1/flashcards/{flashcard_id}/review
    Body: { "material_id": "mat_xxxx", "know_answer": true }
    """
    data = request.get_json() or {}
    material_id = data.get("material_id", "").strip()
    know_answer = bool(data.get("know_answer", False))
    
    if not material_id:
        return jsonify({"error": "material_id is required inside request payload."}), 400
        
    try:
        result = update_flashcard_review(flashcard_id, know_answer, material_id)
        return jsonify(result), 200
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to log review: %s", str(e), exc_info=True)
        return jsonify({"error": "Internal error occurred."}), 500


@flashcards_bp.route("/<material_id>", methods=["DELETE"])
def delete_material_flashcards(material_id):
    """
    DELETE /api/v1/flashcards/{material_id}
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        delete_flashcards(material_id)
        return jsonify({
            "message": "Flashcard decks and version files deleted successfully.",
            "material_id": material_id
        }), 200
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to delete flashcards for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal error deleting flashcards."}), 500
