"""
backend/routes/planner.py — REST API blueprints routes for personalized study planners, status checks, and deletions
"""

import logging
from flask import Blueprint, request, jsonify

from services.planner_service import (
    generate_plan, get_active_plan, get_plan_history, toggle_task_completion, delete_plan
)
from services.ai.ai_exceptions import AIException

logger = logging.getLogger(__name__)

planner_bp = Blueprint("planner", __name__)


@planner_bp.route("/generate", methods=["POST"])
def post_generate_study_plan():
    """
    POST /api/v1/plans/generate
    Body: { "material_id": "mat_xxxx", "exam_date": "ISO", "total_days": 14, "daily_study_hours": 3.0, "time_preference": "morning", "regenerate": false }
    """
    data = request.get_json() or {}
    material_id = data.get("material_id", "").strip()
    exam_date = data.get("exam_date", "").strip()
    total_days = int(data.get("total_days", 14))
    daily_study_hours = float(data.get("daily_study_hours", 3.0))
    time_preference = data.get("time_preference", "morning").strip()
    regenerate = bool(data.get("regenerate", False))
    
    if not material_id:
        return jsonify({"error": "material_id parameter is required."}), 400
    if not exam_date:
        return jsonify({"error": "exam_date parameter is required."}), 400
        
    try:
        result = generate_plan(
            material_id=material_id,
            exam_date=exam_date,
            total_days=total_days,
            daily_study_hours=daily_study_hours,
            time_preference=time_preference,
            regenerate=regenerate
        )
        status_code = 200 if result.get("cached", False) else 201
        return jsonify(result), status_code
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to generate study plan for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "An unexpected error occurred: " + str(e)}), 500


@planner_bp.route("/<material_id>", methods=["GET"])
def get_active_study_plan(material_id):
    """
    GET /api/v1/plans/{material_id}
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        plan = get_active_plan(material_id)
        if not plan:
            return jsonify({"error": "No study plan generated for this study material yet."}), 404
        return jsonify(plan), 200
    except Exception as e:
        logger.error("Failed to fetch active plan for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal lookup error occurred."}), 500


@planner_bp.route("/<material_id>/task/<task_id>", methods=["PATCH"])
def patch_toggle_task_status(material_id, task_id):
    """
    PATCH /api/v1/plans/{material_id}/task/{task_id}
    Body: { "completed": true }
    """
    material_id = material_id.strip()
    task_id = task_id.strip()
    data = request.get_json() or {}
    
    if "completed" not in data:
        return jsonify({"error": "completed boolean status is required."}), 400
        
    completed = bool(data["completed"])
    
    try:
        updated_plan = toggle_task_completion(material_id, task_id, completed)
        return jsonify(updated_plan), 200
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to update task completion status: %s", str(e), exc_info=True)
        return jsonify({"error": "Internal task status update failed."}), 500


@planner_bp.route("/<material_id>/history", methods=["GET"])
def get_study_plan_runs_history(material_id):
    """
    GET /api/v1/plans/{material_id}/history
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        history = get_plan_history(material_id)
        if not history:
            return jsonify({"error": "No history runs records found for this plan."}), 404
        return jsonify(history), 200
    except Exception as e:
        logger.error("Failed to fetch plan history for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal server history query failed."}), 500


@planner_bp.route("/<material_id>", methods=["DELETE"])
def delete_study_plan(material_id):
    """
    DELETE /api/v1/plans/{material_id}
    """
    material_id = material_id.strip()
    if not material_id:
        return jsonify({"error": "material_id is required."}), 400
        
    try:
        delete_plan(material_id)
        return jsonify({
            "message": "Study plan sheets and version registers deleted successfully.",
            "material_id": material_id
        }), 200
    except AIException as e:
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Failed to delete study plan for material %s: %s", material_id, str(e), exc_info=True)
        return jsonify({"error": "Internal error deleting study plan."}), 500
