"""
backend/services/ai/ai_exceptions.py — Custom exceptions for the AI integration subsystem
"""

class AIException(Exception):
    """Base exception for all AI/Groq related errors."""
    def __init__(self, message: str, code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code


class AIConfigurationException(AIException):
    """Raised when the AI key or environment setup is missing or invalid."""
    def __init__(self, message: str = "AI API key or client is unconfigured."):
        super().__init__(message, 401)


class AITimeoutException(AIException):
    """Raised when an API request to the AI model times out."""
    def __init__(self, message: str = "The AI service request timed out."):
        super().__init__(message, 504)


class AIRateLimitException(AIException):
    """Raised when AI rate limits are exceeded (429)."""
    def __init__(self, message: str = "AI service rate limits exceeded. Please retry later.", retry_after: int = 60):
        super().__init__(message, 429)
        self.retry_after = retry_after


class AIResponseParseException(AIException):
    """Raised when AI model returns unparsable responses or invalid format structures."""
    def __init__(self, message: str = "Failed to parse structured JSON response from AI model."):
        super().__init__(message, 422)
