"""
backend/services/ai/ai_client.py — Primary orchestrator client for AI prompt loading, parameter binding, and logging
"""

import os
import time
import uuid
import json
import logging
from typing import Dict, Any

from config import get_config
from services.ai.groq_service import GroqService
from services.ai.prompt_manager import render_prompt
from services.ai.ai_exceptions import AIConfigurationException, AIException

logger = logging.getLogger(__name__)

# Base directory relative to backend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AI_LOG_FILE = os.path.join(BASE_DIR, "logs", "ai_completions.log")


class AIClient:
    """
    Main orchestration class wrapper for the StudyAI AI interface.
    """
    def __init__(self):
        cfg = get_config()
        self.api_key = cfg.GROQ_API_KEY
        self.models_registry = cfg.MODELS
        
        # Usage limits configurations
        self.max_prompt_length = cfg.MAX_PROMPT_LENGTH
        self.max_output_tokens = cfg.MAX_OUTPUT_TOKENS
        
        # Ensure log directories exist
        os.makedirs(os.path.dirname(AI_LOG_FILE), exist_ok=True)
        
        # Initialize service driver
        self.service = GroqService(
            api_key=self.api_key,
            timeout=cfg.GROQ_TIMEOUT_SECONDS,
            max_retries=cfg.GROQ_MAX_RETRIES
        )

    def health_check(self) -> Dict[str, Any]:
        """
        Verify API configuration presence and SDK driver status without query execution.
        """
        key_exists = bool(self.api_key and self.api_key.strip() != "")
        client_init = self.service.verify_initialization()
        
        status = "healthy" if (key_exists and client_init) else "unhealthy"
        
        return {
            "status": status,
            "api_key_configured": key_exists,
            "client_initialized": client_init,
            "default_model": self.models_registry.get("default", "llama-3.3-70b-versatile")
        }

    def run_completion(
        self,
        prompt_type: str,
        template_variables: Dict[str, Any],
        model_key: str = "default",
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """
        Orchestrate prompt loading, parameter rendering, SDK execution, and token logging.
        """
        request_id = f"ai_req_{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        
        # Resolve target model
        model = self.models_registry.get(model_key, self.models_registry["default"])
        
        # 1. Load System Prompt template
        try:
            system_prompt = render_prompt("base_system")
        except Exception as e:
            logger.error("Failed to load base system template: %s", str(e))
            raise AIException("Failed to load prompt scaffolding.")
            
        # 2. Render User Prompt template
        try:
            user_prompt = render_prompt(prompt_type, **template_variables)
        except Exception as e:
            logger.error("Failed to render prompt template '%s': %s", prompt_type, str(e))
            raise AIException(f"Failed to compile prompt template details: {str(e)}")

        # 3. Enforce usage prompt length limits
        if len(user_prompt) > self.max_prompt_length:
            raise AIException(
                f"Ingested prompt length exceeds the maximum limit of {self.max_prompt_length} characters "
                f"(found {len(user_prompt)} characters).",
                code=400
            )

        logger.info("Executing completion request %s (type: %s, model: %s)", request_id, prompt_type, model)

        # 4. Execute completion call
        result = self.service.execute_completion(
            model=model,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=temperature,
            max_tokens=self.max_output_tokens
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 5. Token usage pricing calculation estimations (generic Llama 70B rates: Input $0.59/1M, Output $0.79/1M)
        prompt_tokens = result.get("prompt_tokens", 0)
        completion_tokens = result.get("completion_tokens", 0)
        total_tokens = result.get("total_tokens", 0)
        
        cost_usd = ((prompt_tokens * 0.59) + (completion_tokens * 0.79)) / 1000000.0

        # 6. Log metrics structured as JSON Lines
        log_entry = {
            "request_id": request_id,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S") + "Z",
            "model": model,
            "prompt_type": prompt_type,
            "latency_ms": latency_ms,
            "tokens": {
                "prompt": prompt_tokens,
                "completion": completion_tokens,
                "total": total_tokens
            },
            "cost_usd": float(f"{cost_usd:.7f}")
        }
        
        try:
            with open(AI_LOG_FILE, "a", encoding="utf-8") as log_f:
                log_f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            logger.warning("Failed to record completion usage logs: %s", str(e))

        return {
            "text": result["content"],
            "request_id": request_id,
            "tokens_used": total_tokens,
            "latency_ms": latency_ms
        }


# Singleton Client instance
ai_client = AIClient()
