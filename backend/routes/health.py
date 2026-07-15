"""
routes/health.py — Health check endpoint
GET /api/health
"""

from flask import Blueprint, jsonify

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Returns the current health status of the API.
    ---
    Response:
        200: { "status": "running", "version": "1.0.0" }
    """
    return jsonify({
        "status": "running",
        "version": "1.0.0",
        "service": "StudyAI API",
    }), 200
