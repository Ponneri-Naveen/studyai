"""
StudyAI Backend — Configuration
Reads settings from environment variables (via .env).
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration."""
    # Flask
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    DEBUG: bool = False
    TESTING: bool = False

    # CORS
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Groq AI Configurations
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_TIMEOUT_SECONDS: float = float(os.getenv("GROQ_TIMEOUT_SECONDS", "30.0"))
    GROQ_MAX_RETRIES: int = int(os.getenv("GROQ_MAX_RETRIES", "3"))

    # Centralized Model Registry
    MODELS: dict = {
        "default": "llama-3.3-70b-versatile",
        "fast": "llama-3.1-8b-instant"
    }

    # Centralized Usage Limits
    MAX_PROMPT_LENGTH: int = 50000
    MAX_OUTPUT_TOKENS: int = 4096
    MAX_REQUESTS_PER_MINUTE: int = 20

    # Summary Ingestion Parameters
    MAX_SUMMARY_INPUT_CHARS: int = int(os.getenv("MAX_SUMMARY_INPUT_CHARS", "30000"))
    MAX_SUMMARY_OVERLAP_CHARS: int = int(os.getenv("MAX_SUMMARY_OVERLAP_CHARS", "2000"))
    MAX_SUMMARY_TOTAL_LIMIT: int = 500000
    MAX_SUMMARY_VERSIONS_RETAINED: int = 5

    # Firebase (populated later)
    FIREBASE_PROJECT_ID: str = os.getenv("FIREBASE_PROJECT_ID", "")
    FIREBASE_CREDENTIALS_PATH: str = os.getenv("FIREBASE_CREDENTIALS_PATH", "")

    # Upload settings
    UPLOAD_FOLDER: str = os.path.join(os.path.dirname(__file__), "uploads")
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16 MB

    # Logging
    LOG_FOLDER: str = os.path.join(os.path.dirname(__file__), "logs")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG: bool = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG: bool = False


class TestingConfig(Config):
    """Testing configuration."""
    TESTING: bool = True
    DEBUG: bool = True


# Map FLASK_ENV → config class
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config() -> Config:
    env = os.getenv("FLASK_ENV", "development")
    return config_map.get(env, DevelopmentConfig)()
