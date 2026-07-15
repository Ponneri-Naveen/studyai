"""
routes/__init__.py — Blueprint registry
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    from routes.health import health_bp
    from routes.auth import auth_bp
    from routes.materials import materials_bp
    from routes.ai import ai_bp
    from routes.summary import summary_bp
    from routes.flashcards import flashcards_bp
    from routes.quizzes import quizzes_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(materials_bp, url_prefix="/api/v1/materials")
    app.register_blueprint(ai_bp, url_prefix="/api/v1/ai")
    app.register_blueprint(summary_bp, url_prefix="/api/v1/summary")
    app.register_blueprint(flashcards_bp, url_prefix="/api/v1/flashcards")
    app.register_blueprint(quizzes_bp, url_prefix="/api/v1/quizzes")
