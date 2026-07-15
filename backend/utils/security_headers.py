"""
backend/utils/security_headers.py — Secure HTTP headers Talisman config rules for production deployment
"""

import logging
from flask import Flask
from flask_talisman import Talisman

logger = logging.getLogger(__name__)


def apply_security_headers(app: Flask) -> None:
    """
    Applies security headers to the Flask application using Flask-Talisman.
    Skips headers enforcement in testing or development configs.
    """
    if app.config.get("TESTING") or app.config.get("DEBUG"):
        logger.info("Skipping Talisman secure headers enforcement in development/testing mode.")
        return
        
    csp = {
        'default-src': '\'self\'',
        'script-src': '\'self\'',
        'style-src': '\'self\' \'unsafe-inline\'',
        'img-src': '\'self\' data:',
        'connect-src': '\'self\' https://api.groq.com'
    }
    
    Talisman(
        app,
        content_security_policy=csp,
        force_https=True,
        frame_options='DENY',
        x_content_type_options=True,
        referrer_policy='strict-origin-when-cross-origin'
    )
    
    logger.info("Strict Talisman secure headers applied successfully.")
