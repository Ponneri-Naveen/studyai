"""
routes/health.py — Production health check diagnostics, storage checks, and AI connectivity latency pings
"""

import os
import time
from flask import Blueprint, jsonify, current_app
from config import get_config
from services.ai.groq_service import GroqService

health_bp = Blueprint("health", __name__)

START_TIME = time.time()


@health_bp.route("/health", methods=["GET"])
def health_check():
    """
    Returns the expanded health status of the API, including storage and AI connectivity metrics.
    """
    cfg = get_config()
    
    # 1. Calculate Uptime
    uptime = int(time.time() - START_TIME)
    
    # 2. Check Storage Path Write Capability
    storage_writable = False
    test_file_path = os.path.join(cfg.UPLOAD_FOLDER, ".health_write_test")
    try:
        os.makedirs(cfg.UPLOAD_FOLDER, exist_ok=True)
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("write_ok")
        os.remove(test_file_path)
        storage_writable = True
    except Exception:
        storage_writable = False
        
    # 3. Check Groq AI Connectivity Latency Ping
    groq_status = "disconnected"
    groq_latency = 0
    try:
        ping_start = time.time()
        ping_client = GroqService(api_key=cfg.GROQ_API_KEY)
        if ping_client.client:
            groq_status = "connected"
            groq_latency = int((time.time() - ping_start) * 1000)
    except Exception:
        groq_status = "failed"
        
    return jsonify({
        "status": "healthy" if (storage_writable and groq_status == "connected") else "degraded",
        "version": "1.0.0",
        "service": "StudyAI API",
        "environment": os.getenv("FLASK_ENV", "development"),
        "uptime_seconds": uptime,
        "storage": {
            "writable": storage_writable,
            "upload_folder": _safe_basename(cfg.UPLOAD_FOLDER)
        },
        "groq": {
            "status": groq_status,
            "latency_ms": groq_latency
        },
        "build_version": "production-ready-v1.0"
    }), 200


def _safe_basename(path: str) -> str:
    try:
        return os.path.basename(path)
    except Exception:
        return "uploads"
