"""
backend/routes/quizzes.py — REST API blueprints for quizzes generation, query lists, submits and attempts histories
"""

import logging
from flask import Blueprint, request, jsonify

from services.quiz_service import (
    generate_quiz, get_quiz_by_material_id, get_quizzes_history, submit_quiz_answers, delete_quiz
)
from services.ai.ai_exceptions import AIException

logger = logging.getLogger(__name__)

quizzes_bp = Blueprint("quizzes", __name__)


@quizzes_bp.route("/generate", methods=["POST"])
def post_generate_quiz():
    """
    POST /api/v1/quizzes/generate
    Body: { "material_id": "mat_xxxx", "regenerate": false }
    """
    data = request.get_json() or {}
    material_id = data.get("material_id", "").strip()
    regenerate = bool(data.get("regenerate", False))
    
    if not material_id:
        return jsonify({"error": "material_id parameter is required."}), 400
        
    try:
        result = generate_quiz(material_id, regenerate=regenerate)
        status_code = 200 if result.get("cached", False) else 201
        return jsonify(result), status_code
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to generate quiz for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500


@quizzes_bp.route("/<material_id>", methods=["GET"])
def get_quiz_questions(material_id):
    """
    GET /api/v1/quizzes/{material_id}
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        quiz = get_quiz_by_material_id(material_id)
        if not quiz:
            return jsonify({"error": "No quiz generated for this study material yet."}), 404
        return jsonify(quiz), 200
    except Exception as e:
        logger.error("Failed to fetch quiz for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal lookup error occurred."}), 500


@quizzes_bp.route("/<material_id>/history", methods=["GET"])
def get_quiz_attempts_history(material_id):
    """
    GET /api/v1/quizzes/{material_id}/history
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        history = get_quizzes_history(material_id)
        if not history:
            return jsonify({"error": "No history attempts records found for this material."}), 404
        return jsonify(history), 200
    except Exception as e:
        logger.error("Failed to fetch attempts history for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal server history query failed."}), 500


@quizzes_bp.route("/<quiz_id>/submit", methods=["POST"])
def post_submit_quiz_answers(quiz_id):
    """
    POST /api/v1/quizzes/{quiz_id}/submit
    Body: {
      "material_id": "mat_xxxx",
      "quiz_version": 1,
      "mode": "exam",
      "time_taken_seconds": 120,
      "question_order": ["q_1", "q_2"],
      "answers": {
        "q_1": "student answer text"
      }
    }
    """
    data = request.get_json() or {}
    material_id = data.get("material_id", "").strip()
    quiz_version = int(data.get("quiz_version", 1))
    mode = data.get("mode", "exam").strip()
    time_taken_seconds = int(data.get("time_taken_seconds", 0))
    question_order = data.get("question_order", [])
    answers = data.get("answers", {})
    
    if not material_id:
        return jsonify({"error": "material_id parameter is required inside submit payload."}), 400
        
    try:
        attempt = submit_quiz_answers(
            quiz_id=quiz_id,
            answers=answers,
            mode=mode,
            time_taken_seconds=time_taken_seconds,
            question_order=question_order,
            material_id=material_id,
            quiz_version=quiz_version
        )
        return jsonify(attempt), 201
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to evaluate and save quiz submission: %s", str(e), exc_info=True)
        return jsonify({"error": "Internal scoring engine evaluation failed."}), 500


@quizzes_bp.route("/<material_id>", methods=["DELETE"])
def delete_material_quiz(material_id):
    """
    DELETE /api/v1/quizzes/{material_id}
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        delete_quiz(material_id)
        return jsonify({
            "message": "Quiz questions sheets and version files deleted successfully.",
            "material_id": material_id
        }), 200
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to delete quiz for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal error deleting quiz."}), 500
