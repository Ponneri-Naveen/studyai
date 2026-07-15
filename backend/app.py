"""
StudyAI Backend — Flask Application Factory
"""

import os
import logging
from flask import Flask
from flask_cors import CORS

from config import get_config
from utils.error_handler import register_error_handlers
from routes import register_blueprints


def create_app() -> Flask:
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # ── Load configuration ────────────────────────────────────────────────────
    cfg = get_config()
    app.config.from_object(cfg)

    # ── Ensure runtime directories exist ─────────────────────────────────────
    os.makedirs(cfg.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(cfg.LOG_FOLDER, exist_ok=True)

    # ── Logging ───────────────────────────────────────────────────────────────
    log_file = os.path.join(cfg.LOG_FOLDER, "app.log")
    logging.basicConfig(
        level=getattr(logging, cfg.LOG_LEVEL, logging.INFO),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting StudyAI backend in '%s' mode", os.getenv("FLASK_ENV", "development"))

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS(
        app,
        resources={r"/api/*": {"origins": cfg.FRONTEND_URL}},
        supports_credentials=True,
    )

    # ── Blueprints ────────────────────────────────────────────────────────────
    register_blueprints(app)

    # ── Global error handlers ─────────────────────────────────────────────────
    register_error_handlers(app)

    return app


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    application = create_app()
    port = int(os.getenv("PORT", 5000))
    application.run(host="0.0.0.0", port=port, debug=application.config["DEBUG"])
