"""
backend/routes/analytics.py — REST API blueprints routes for learning analytics queries, dashboard updates, and AI insights
"""

import logging
from flask import Blueprint, jsonify

from services.analytics_service import (
    calculate_dashboard_metrics, force_refresh_dashboard, generate_ai_insights
)

logger = logging.getLogger(__name__)

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/dashboard", methods=["GET"])
def get_dashboard_analytics_profile():
    """
    GET /api/v1/analytics/dashboard
    """
    try:
        metrics = calculate_dashboard_metrics(force=False)
        return jsonify(metrics), 200
    except Exception as e:
        logger.error("Failed to load dashboard metrics: %s", str(e), exc_info=True)
        return jsonify({"error": "Failed to aggregate performance data: " + str(e)}), 500


@analytics_bp.route("/performance", methods=["GET"])
def get_performance_charts_data():
    """
    GET /api/v1/analytics/performance
    Returns mock/formatted timelines history mapping for charts.
    """
    try:
        metrics = calculate_dashboard_metrics(force=False)
        # Yield weekly breakdown lists compatible with Recharts rendering.
        # We synthesize a weekly timeline from attempts count.
        performance_data = [
            {"week": "Week 1", "quizzes": 1, "accuracy": 70, "cards_mastered": 5},
            {"week": "Week 2", "quizzes": min(metrics["overview"]["quiz_attempts"], 3), "accuracy": int(metrics["overview"]["avg_quiz_score"] * 0.9), "cards_mastered": min(metrics["overview"]["flashcards_mastered"], 20)},
            {"week": "Week 3", "quizzes": metrics["overview"]["quiz_attempts"], "accuracy": int(metrics["overview"]["avg_quiz_score"]), "cards_mastered": metrics["overview"]["flashcards_mastered"]}
        ]
        return jsonify({"performance_timeline": performance_data}), 200
    except Exception as e:
        logger.error("Failed to load performance timeline: %s", str(e))
        return jsonify({"error": "Failed to calculate performance trends."}), 500


@analytics_bp.route("/trends", methods=["GET"])
def get_velocity_trends():
    """
    GET /api/v1/analytics/trends
    """
    try:
        metrics = calculate_dashboard_metrics(force=False)
        return jsonify(metrics.get("trends", {})), 200
    except Exception as e:
        logger.error("Failed to fetch trends: %s", str(e))
        return jsonify({"error": "Failed to compute analytics trends."}), 500


@analytics_bp.route("/activity", methods=["GET"])
def get_recent_activity_log():
    """
    GET /api/v1/analytics/activity
    Returns synthesized recent logs.
    """
    try:
        metrics = calculate_dashboard_metrics(force=False)
        overview = metrics["overview"]
        activity_logs = [
            {"event": "Study Material Uploaded", "detail": f"{overview['materials_uploaded']} total notes", "timestamp": metrics["last_updated"]},
            {"event": "Practice Test Completed", "detail": f"Avg score {overview['avg_quiz_score']}%", "timestamp": metrics["last_updated"]},
            {"event": "Card Deck Mastered", "detail": f"{overview['flashcards_mastered']} review sessions complete", "timestamp": metrics["last_updated"]}
        ]
        return jsonify({"activities": activity_logs}), 200
    except Exception as e:
        logger.error("Failed to load activity log: %s", str(e))
        return jsonify({"error": "Failed to query recent activities timeline."}), 500


@analytics_bp.route("/refresh", methods=["POST"])
def post_force_refresh_cache():
    """
    POST /api/v1/analytics/refresh
    """
    try:
        refreshed_metrics = force_refresh_dashboard()
        return jsonify(refreshed_metrics), 200
    except Exception as e:
        logger.error("Failed to force recalculations: %s", str(e), exc_info=True)
        return jsonify({"error": "Recalculation error: " + str(e)}), 500


@analytics_bp.route("/insights", methods=["GET"])
def get_ai_insights_encouragement():
    """
    GET /api/v1/analytics/insights
    """
    try:
        insights = generate_ai_insights()
        return jsonify(insights), 200
    except Exception as e:
        logger.error("Failed to fetch AI insights: %s", str(e), exc_info=True)
        return jsonify({"error": "Insights gen failed."}), 500
