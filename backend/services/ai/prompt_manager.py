"""
backend/services/ai/prompt_manager.py — Manager for loading, caching, and interpolating prompt templates
"""

import os
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Resolve absolute path to backend/services/ai/prompts/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROMPTS_DIR = os.path.join(BASE_DIR, "prompts")

# In-memory template cache
_templates_cache: Dict[str, str] = {}


def load_template(template_name: str) -> str:
    """
    Load a raw prompt template from disk, caching the result in-memory.
    """
    if template_name in _templates_cache:
        return _templates_cache[template_name]
        
    filename = f"{template_name}.txt"
    file_path = os.path.join(PROMPTS_DIR, filename)
    
    if not os.path.exists(file_path):
        logger.error("Prompt template file missing: %s", file_path)
        raise FileNotFoundError(f"AI Prompt Template '{template_name}' not found on disk.")
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        _templates_cache[template_name] = content
        return content
    except Exception as e:
        logger.error("Failed to read prompt template %s: %s", template_name, str(e))
        raise IOError(f"Could not load template file: {str(e)}")


def render_prompt(template_name: str, **kwargs) -> str:
    """
    Load a template and replace double-brace variables (e.g. {{ key }}) with keyword values.
    """
    raw_template = load_template(template_name)
    rendered = raw_template
    
    for key, val in kwargs.items():
        placeholder = f"{{{{ {key} }}}}"
        rendered = rendered.replace(placeholder, str(val))
        
        # Support fallback without spaces: {{key}}
        placeholder_no_spaces = f"{{{{{key}}}}}"
        rendered = rendered.replace(placeholder_no_spaces, str(val))
        
    return rendered
