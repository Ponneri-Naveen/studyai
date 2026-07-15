"""
backend/tests/test_ai.py — Pytest suite with mock Groq clients verifying AI exception captures and configurations
"""

import os
import json
import pytest
import sys
from unittest.mock import patch, MagicMock

# Make sure the backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from services.ai.ai_client import AIClient
import services.ai.ai_client as ai_client_module
from services.ai.ai_exceptions import AITimeoutException, AIRateLimitException, AIConfigurationException


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_ai_health_check_endpoint(client):
    """
    Test that the health endpoint returns config indicators without calling the model.
    """
    response = client.get("/api/v1/ai/health")
    assert response.status_code == 200
    data = response.get_json()
    assert "status" in data
    assert "api_key_configured" in data
    assert "client_initialized" in data
    assert "default_model" in data


@patch("services.ai.groq_service.GroqService.execute_completion")
def test_ai_test_completion_success(mock_execute, client):
    """
    Test that the POST test route calls completions successfully and registers metadata metrics.
    """
    mock_execute.return_value = {
        "content": "Ping Response: Hello World",
        "prompt_tokens": 10,
        "completion_tokens": 5,
        "total_tokens": 15
    }
    
    payload = {"test_text": "Hello World"}
    response = client.post(
        "/api/v1/ai/test",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["raw_response"] == "Ping Response: Hello World"
    assert data["tokens_used"] == 15
    assert "latency_ms" in data


@patch("services.ai.groq_service.GroqService.execute_completion")
def test_ai_test_timeout_handling(mock_execute, client):
    """
    Test that timed-out connections throw custom AITimeoutException mapped to correct codes.
    """
    mock_execute.side_effect = AITimeoutException("Request timed out.")
    
    payload = {"test_text": "Timeout Test"}
    response = client.post(
        "/api/v1/ai/test",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 504
    assert response.get_json()["error"] == "Request timed out."


@patch("services.ai.groq_service.GroqService.execute_completion")
def test_ai_test_rate_limit_handling(mock_execute, client):
    """
    Test that rate limits 429 errors from Groq return clean JSON warnings.
    """
    mock_execute.side_effect = AIRateLimitException("AI Rate Limits Exceeded", retry_after=30)
    
    payload = {"test_text": "Rate Limit Test"}
    response = client.post(
        "/api/v1/ai/test",
        data=json.dumps(payload),
        content_type="application/json"
    )
    
    assert response.status_code == 429
    assert response.get_json()["error"] == "AI Rate Limits Exceeded"


def test_ai_prompt_rendering():
    """
    Test prompt manager interpolation rules.
    """
    from services.ai.prompt_manager import render_prompt
    # Render test_ping prompt
    result = render_prompt("test_ping", test_text="Hello System")
    assert "Incoming ping payload: Hello System" in result
    assert "Ping Response: Hello System" in result
