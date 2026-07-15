"""
StudyAI Backend — Flask Application Factory
"""

import os
import logging
from flask import Flask
from flask_cors import CORS

from utils.orjson_compat import patch_json_globally
patch_json_globally()

from config import get_config
from utils.error_handlers import register_error_handlers
from utils.logger_factory import configure_logging, get_request_id, get_correlation_id
from utils.startup_validator import validate_production_readiness
from utils.security_headers import apply_security_headers
from routes import register_blueprints

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create, validate, and configure the Flask application."""
    # ── 1. Load configuration ────────────────────────────────────────────────────
    cfg = get_config()
    
    # ── 2. Configure logging ──────────────────────────────────────────────────────
    log_level_val = getattr(logging, cfg.LOG_LEVEL, logging.INFO)
    configure_logging(log_level_val)
    
    # ── 3. Run production environment validations ───────────────────────────────
    validate_production_readiness(cfg)
    
    # ── 4. Initialize Flask ───────────────────────────────────────────────────────
    app = Flask(__name__)
    app.config.from_object(cfg)

    # ── 5. Ensure upload folders exist ────────────────────────────────────────────
    os.makedirs(cfg.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(cfg.LOG_FOLDER, exist_ok=True)

    # Initialize local storage databases
    from services.storage_service import initialize_storage
    initialize_storage()
    
    # Initialize repositories selection factory drivers
    from services.repositories.repository_factory import RepositoryFactory
    RepositoryFactory.initialize()

    # ── 6. Request Correlation Identifiers ───────────────────────────────────────
    @app.before_request
    def assign_trace_ids():
        import uuid
        from flask import g, request
        g.request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex[:12]}"
        g.correlation_id = request.headers.get("X-Correlation-ID") or f"corr_{uuid.uuid4().hex[:12]}"

    @app.after_request
    def append_trace_headers(response):
        from flask import g
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id
        if hasattr(g, "correlation_id"):
            response.headers["X-Correlation-ID"] = g.correlation_id
        return response

    # ── 7. CORS Origin Whitelisting ──────────────────────────────────────────────
    CORS(
        app,
        resources={r"/api/*": {"origins": cfg.FRONTEND_URL}},
        supports_credentials=True,
    )

    # ── 8. Secure Headers (Talisman) ─────────────────────────────────────────────
    apply_security_headers(app)

    # ── 9. Blueprints ────────────────────────────────────────────────────────────
    register_blueprints(app)

    # ── 10. Global Error Handlers ─────────────────────────────────────────────────
    register_error_handlers(app)

    logger.info("StudyAI backend successfully initialized in '%s' mode.", os.getenv("FLASK_ENV", "development"))
    return app


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    application = create_app()
    port = int(os.getenv("PORT", 5000))
    application.run(host="0.0.0.0", port=port, debug=application.config["DEBUG"])
