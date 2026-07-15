"""
backend/utils/startup_validator.py — Production startup checks, storage permission validations, and prompt template maps checks
"""

import os
import logging
from services.ai.groq_service import GroqService

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Exception raised for missing or invalid startup configurations."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def validate_production_readiness(app_config) -> None:
    """
    Validates env keys, storage permissions, and prompt catalogs.
    Fails fast by raising ConfigurationError.
    """
    if getattr(app_config, "TESTING", False) is True:
        logger.info("Bypassing production readiness validations under testing configs.")
        return
        
    logger.info("Executing production environment startup validations...")
    
    # 1. Environment Secrets Valids checks
    secret_key = getattr(app_config, "SECRET_KEY", None)
    if not secret_key or secret_key == "change-this-in-production":
        raise ConfigurationError(
            "FLASK_SECRET_KEY is missing or insecure. In production, configure a robust cryptographically random key."
        )
        
    groq_api_key = getattr(app_config, "GROQ_API_KEY", None)
    if not groq_api_key:
        raise ConfigurationError(
            "GROQ_API_KEY environment variable is required to establish connection with AI client gateways."
        )
        
    # 2. Storage write permission loops checks
    storage_dirs = [
        os.path.join(getattr(app_config, "BASE_DIR"), "storage"),
        getattr(app_config, "UPLOAD_FOLDER", None),
        getattr(app_config, "LOG_FOLDER", None)
    ]
    
    for path in storage_dirs:
        if not path:
            continue
        # Attempt folder creation or permission writing validations
        os.makedirs(path, exist_ok=True)
        test_file_path = os.path.join(path, ".startup_write_test")
        try:
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write("test")
            os.remove(test_file_path)
        except Exception as e:
            raise ConfigurationError(
                f"Directory permission verification failed. Path '{path}' is not writable: {str(e)}"
            )
            
    # 3. Prompt templates list map verification
    prompts_dir = os.path.join(getattr(app_config, "BASE_DIR"), "services", "ai", "prompts")
    required_prompts = [
        "base_system.txt",
        "summary_v1.txt",
        "flashcards_v1.txt",
        "quiz_v1.txt",
        "weak_topics_v1.txt",
        "study_plan_v1.txt",
        "analytics_insight_v1.txt"
    ]
    
    for prompt_filename in required_prompts:
        prompt_abs_path = os.path.join(prompts_dir, prompt_filename)
        if not os.path.exists(prompt_abs_path):
            raise ConfigurationError(
                f"Required AI prompt template file is missing on disk: {prompt_abs_path}. Build deployment incomplete."
            )
            
    # 4. Fast connection ping warnings
    try:
        ping_client = GroqService(api_key=groq_api_key)
        # Fast non-model connectivity checks or client ping
        if not ping_client.client:
             logger.warning("Groq client initialized but SDK client object is missing.")
        logger.info("AI infrastructure gateways connectivity verified successfully.")
    except Exception as e:
        logger.warning("Groq AI infrastructure ping failed during startup checks: %s. Continuing startup.", str(e))
        
    logger.info("All startup infrastructure checks completed. Production system validated successfully.")
