"""
backend/utils/logger_factory.py — Production logging subsystem, auto log rotation, and JSON layout formatters
"""

import os
import json
import logging
from logging.handlers import RotatingFileHandler
import uuid
import datetime
from flask import request, has_request_context, g

# Resolve base logs directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGS_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

# Define request ID utility
def get_request_id() -> str:
    """Retrieve Request-ID from active flask g context or generate a fresh trace token."""
    if has_request_context():
        if not hasattr(g, "request_id"):
            g.request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        return g.request_id
    return "N/A"


def get_correlation_id() -> str:
    """Retrieve Correlation-ID from headers or g context."""
    if has_request_context():
        if not hasattr(g, "correlation_id"):
            g.correlation_id = request.headers.get("X-Correlation-ID") or f"corr_{uuid.uuid4().hex[:12]}"
        return g.correlation_id
    return "N/A"


class JSONFormatter(logging.Formatter):
    """Custom log formatter generating clean, production-ready JSON layouts."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_payload = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "log_level": record.levelname,
            "request_id": get_request_id(),
            "correlation_id": get_correlation_id(),
            "module": record.name,
            "message": record.getMessage(),
            "logger": record.name,
            "thread": record.threadName
        }
        
        # Capture error stack trace details if log record has exception info
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
            
        # Extract custom properties if passed using extra dict
        if hasattr(record, "custom_props"):
            log_payload.update(record.custom_props)
            
        return json.dumps(log_payload)


def configure_logging(log_level: int = logging.INFO) -> None:
    """
    Configures automatic file rotation handlers and logs channels routing.
    """
    # 1. Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove any existing handlers
    root_logger.handlers = []
    
    # JSON log formatter
    json_formatter = JSONFormatter()
    
    # 2. Console stream handler (standard stdout format for container/dev environments)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(json_formatter)
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # 3. Access/Root Rotating File Handler
    root_file_handler = RotatingFileHandler(
        filename=os.path.join(LOGS_DIR, "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB per file
        backupCount=14,
        encoding="utf-8"
    )
    root_file_handler.setFormatter(json_formatter)
    root_file_handler.setLevel(log_level)
    root_logger.addHandler(root_file_handler)
    
    # 4. Error Handler filter routing errors to logs/error.log
    error_file_handler = RotatingFileHandler(
        filename=os.path.join(LOGS_DIR, "error.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=14,
        encoding="utf-8"
    )
    error_file_handler.setFormatter(json_formatter)
    error_file_handler.setLevel(logging.ERROR)
    root_logger.addHandler(error_file_handler)
    
    # 5. Route custom loggers to separate rotation handles (Security Logs)
    sec_logger = logging.getLogger("security")
    sec_logger.setLevel(logging.INFO)
    sec_logger.propagate = False
    
    sec_file_handler = RotatingFileHandler(
        filename=os.path.join(LOGS_DIR, "security.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB limit
        backupCount=7,
        encoding="utf-8"
    )
    sec_file_handler.setFormatter(json_formatter)
    sec_logger.addHandler(sec_file_handler)
    
    # 6. Route custom loggers to separate rotation handles (AI Transaction logs)
    ai_logger = logging.getLogger("ai_requests")
    ai_logger.setLevel(logging.INFO)
    ai_logger.propagate = False
    
    ai_file_handler = RotatingFileHandler(
        filename=os.path.join(LOGS_DIR, "ai_request.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=14,
        encoding="utf-8"
    )
    ai_file_handler.setFormatter(json_formatter)
    ai_logger.addHandler(ai_file_handler)
    
    logging.info("Production rotating logging framework initialized.")
