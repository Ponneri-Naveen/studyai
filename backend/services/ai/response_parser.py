"""
backend/services/ai/response_parser.py — Normalization and parsing of model responses (such as JSON parsing)
"""

import json
import logging
import re
from typing import Dict, Any

from services.ai.ai_exceptions import AIResponseParseException

logger = logging.getLogger(__name__)


def clean_markdown_json(raw_text: str) -> str:
    """
    Remove markdown code block delimiters (e.g. ```json ... ```) from a text response.
    """
    if not raw_text:
        return ""
        
    cleaned = raw_text.strip()
    
    # Strip opening backticks blocks
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    # Strip closing backticks
    cleaned = re.sub(r"\s*```$", "", cleaned)
    
    return cleaned.strip()


def parse_structured_json(raw_text: str) -> Dict[str, Any]:
    """
    Clean and parse an LLM text block into a Python dictionary.
    Raises AIResponseParseException if the text is not valid JSON.
    """
    cleaned_text = clean_markdown_json(raw_text)
    
    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON content from text. Error: %s. Cleaned text: %s", str(e), cleaned_text)
        raise AIResponseParseException(f"AI response is not valid JSON format: {str(e)}")
