"""
backend/routes/ai.py — REST endpoints for AI status configurations and connection ping diagnostic runs
"""

import logging
from flask import Blueprint, request, jsonify

from services.ai.ai_client import ai_client
from services.ai.ai_exceptions import AIException

logger = logging.getLogger(__name__)

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/health", methods=["GET"])
def get_ai_health():
    """
    GET /api/v1/ai/health
    Return config-based health checks of API configuration. Does not query LLM.
    """
    try:
        health_data = ai_client.health_check()
        return jsonify(health_data), 200
    except Exception as e:
        logger.error("AI health check crashed: %s", str(e), exc_info=True)
        return jsonify({
            "status": "unhealthy",
            "error": "Internal checks failed to query configurations."
        }), 500


@ai_bp.route("/test", methods=["POST"])
def run_ai_test():
    """
    POST /api/v1/ai/test
    Body: { "test_text": "text content" }
    Runs a live connectivity completion check using test_ping prompt template.
    """
    data = request.get_json() or {}
    test_text = data.get("test_text", "").strip()

    if not test_text:
        return jsonify({"error": "test_text content is required and cannot be empty."}), 400

    try:
        # Execute query via Llama model using test_ping template
        result = ai_client.run_completion(
            prompt_type="test_ping",
            template_variables={"test_text": test_text}
        )
        
        return jsonify({
            "success": True,
            "raw_response": result["text"],
            "tokens_used": result["tokens_used"],
            "latency_ms": result["latency_ms"]
        }), 200
        
    except AIException as e:
        logger.warning("AI execution failed on test ping: %s (code: %s)", e.message, e.code)
        return jsonify({"error": e.message}), e.code
    except Exception as e:
        logger.error("Unexpected crash running AI test ping: %s", str(e), exc_info=True)
        return jsonify({"error": "An unexpected error occurred during the AI connection test."}), 500
