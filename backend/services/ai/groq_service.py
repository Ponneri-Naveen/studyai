"""
backend/services/ai/groq_service.py — Direct connection driver wrapper for Groq Cloud API SDK
"""

import logging
from typing import Dict, Any, Optional
from groq import Groq, APIConnectionError, APITimeoutError, APIStatusError, RateLimitError

from services.ai.ai_exceptions import (
    AIConfigurationException,
    AITimeoutException,
    AIRateLimitException,
    AIException
)

logger = logging.getLogger(__name__)


class GroqService:
    """
    Manages low-level connection parameters and chat completion executions using Groq SDK.
    """
    def __init__(self, api_key: str, timeout: float = 30.0, max_retries: int = 3):
        self.api_key = api_key
        self.timeout = timeout
        self.max_retries = max_retries
        self.client: Optional[Groq] = None
        
        self.initialize_client()

    def initialize_client(self) -> None:
        """Initialize the Groq client object. Verifies API key presence."""
        if not self.api_key or self.api_key.strip() == "":
            logger.warning("Groq API Key is missing or unconfigured.")
            self.client = None
            return

        try:
            self.client = Groq(
                api_key=self.api_key,
                timeout=self.timeout,
                max_retries=self.max_retries
            )
            logger.info("Groq SDK Client successfully initialized.")
        except Exception as e:
            logger.error("Failed to initialize Groq client: %s", str(e))
            self.client = None

    def verify_initialization(self) -> bool:
        """Check if client initialization succeeded."""
        return self.client is not None

    def execute_completion(
        self,
        model: str,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.2,
        max_tokens: int = 4096,
        top_p: float = 0.9
    ) -> Dict[str, Any]:
        """
        Execute chat completions query via the SDK wrapper, catching HTTP/timeout errors.
        """
        if not self.client:
            raise AIConfigurationException("Groq API client is unconfigured. Verify your GROQ_API_KEY environment variable.")

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            
            # Map usage stats
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            completion_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0
            
            content = response.choices[0].message.content
            
            return {
                "content": content,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            }
            
        except APITimeoutError as e:
            logger.error("Groq connection timeout exception: %s", str(e))
            raise AITimeoutException("The AI model request timed out. Please try again.")
            
        except RateLimitError as e:
            logger.error("Groq Rate Limit Error (429): %s", str(e))
            # Try to parse retry-after value, default is 60 seconds
            retry_after = 60
            if hasattr(e, "response") and e.response:
                retry_after = int(e.response.headers.get("retry-after", "60"))
            raise AIRateLimitException("The study assistant is currently busy. Please wait.", retry_after=retry_after)
            
        except APIStatusError as e:
            logger.error("Groq API Status Error: %s", str(e))
            status_code = e.status_code
            if status_code == 401:
                raise AIConfigurationException("Your Groq API key is invalid or unauthorized.")
            raise AIException(f"AI Service error returned status code {status_code}: {e.message}", code=status_code)
            
        except APIConnectionError as e:
            logger.error("Groq Connection Error: %s", str(e))
            raise AIException("Failed to establish connection to the AI service.", code=503)
            
        except Exception as e:
            logger.error("Unexpected error in Groq Service completion: %s", str(e), exc_info=True)
            raise AIException(f"An unexpected AI error occurred: {str(e)}")
