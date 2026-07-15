"""
utils/error_handler.py — Global Flask error handlers

All error responses follow the shape:
    { "error": "<message>", "code": <http_status_code> }
"""

import logging
from flask import Flask, jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """Register application-wide error handlers."""

    @app.errorhandler(400)
    def bad_request(error):
        logger.warning("400 Bad Request: %s", str(error))
        return jsonify({"error": "Bad request — check your input data.", "code": 400}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        logger.warning("401 Unauthorized: %s", str(error))
        return jsonify({"error": "Authentication required.", "code": 401}), 401

    @app.errorhandler(403)
    def forbidden(error):
        logger.warning("403 Forbidden: %s", str(error))
        return jsonify({"error": "You do not have permission to access this resource.", "code": 403}), 403

    @app.errorhandler(404)
    def not_found(error):
        logger.warning("404 Not Found: %s", str(error))
        return jsonify({"error": "The requested resource was not found.", "code": 404}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        logger.warning("405 Method Not Allowed: %s", str(error))
        return jsonify({"error": "HTTP method not allowed for this endpoint.", "code": 405}), 405

    @app.errorhandler(422)
    def unprocessable_entity(error):
        logger.warning("422 Unprocessable Entity: %s", str(error))
        return jsonify({"error": "Validation failed — check your request body.", "code": 422}), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        logger.error("500 Internal Server Error: %s", str(error), exc_info=True)
        return jsonify({"error": "An unexpected error occurred. Please try again later.", "code": 500}), 500
