"""
routes/__init__.py — Blueprint registry
"""

from flask import Flask


def register_blueprints(app: Flask) -> None:
    from routes.health import health_bp
    from routes.auth import auth_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
