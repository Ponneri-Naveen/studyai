"""
backend/utils/error_handlers.py — Production error handlers, JSON standardization filters, and stack trace filters
"""

import logging
from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException
from utils.logger_factory import get_request_id

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    """
    Hook application error handlers mapping JSON outputs.
    """
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # 1. Log errors internally
        request_id = get_request_id()
        
        # If it is a standard Werkzeug HTTP Exception, retain status codes
        if isinstance(e, HTTPException):
            status_code = e.code
            error_code = e.name.upper().replace(" ", "_")
            message = e.description
            # Log warnings for 4xx, errors for 5xx
            if status_code >= 500:
                logger.error("HTTP Internal Server Error occurred [ID: %s]: %s", request_id, str(e), exc_info=True)
            else:
                logger.warning("HTTP Client Exception [ID: %s]: %s", request_id, str(e))
        else:
            status_code = 500
            error_code = "INTERNAL_SERVER_ERROR"
            # Strip stack traces, return user-safe messages in Production
            if app.config.get("DEBUG") or app.config.get("TESTING"):
                message = str(e)
            else:
                message = "An unexpected error occurred. Please contact customer support with your Request ID."
            logger.error("Unhandled exceptions crashed request execution [ID: %s]: %s", request_id, str(e), exc_info=True)
            
        # 2. Format JSON payload response
        payload = {
            "error": {
                "code": error_code,
                "message": message,
                "request_id": request_id
            }
        }
        
        return jsonify(payload), status_code
