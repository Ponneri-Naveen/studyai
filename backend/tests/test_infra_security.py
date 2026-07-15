"""
backend/tests/test_infra_security.py — Pytest suite verifying class configuration checks, startup validation pings, and security correlation headers
"""

import os
import json
import pytest
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from config import get_config
from utils.startup_validator import validate_production_readiness, ConfigurationError


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_missing_secret_key_fails_fast():
    """
    Verify that startup validator raises ConfigurationError if Flask secret key is missing.
    """
    mock_config = MagicMock()
    mock_config.SECRET_KEY = None
    mock_config.GROQ_API_KEY = "mock_key"
    
    with pytest.raises(ConfigurationError) as excinfo:
        validate_production_readiness(mock_config)
        
    assert "SECRET_KEY is missing or insecure" in str(excinfo.value)


def test_missing_groq_key_fails_fast():
    """
    Verify that startup validator raises ConfigurationError if Groq API key is missing.
    """
    mock_config = MagicMock()
    mock_config.SECRET_KEY = "mock_secret"
    mock_config.GROQ_API_KEY = None
    
    with pytest.raises(ConfigurationError) as excinfo:
        validate_production_readiness(mock_config)
        
    assert "GROQ_API_KEY environment variable is required" in str(excinfo.value)


def test_request_correlation_headers_tracing(client):
    """
    Test that every request is assigned X-Request-ID and X-Correlation-ID headers.
    """
    response = client.get("/api/health")
    
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")
    assert response.headers["X-Correlation-ID"].startswith("corr_")


def test_custom_correlation_headers_propagation(client):
    """
    Test that incoming X-Request-ID values propagate into headers.
    """
    response = client.get(
        "/api/health",
        headers={
            "X-Request-ID": "custom_req_token_123",
            "X-Correlation-ID": "custom_corr_token_567"
        }
    )
    
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "custom_req_token_123"
    assert response.headers["X-Correlation-ID"] == "custom_corr_token_567"


def test_standardized_json_errors_handling(client):
    """
    Test that application intercepts routes exceptions and returns structured JSON messages.
    """
    # Trigger 404 Not Found error
    response = client.get("/api/v1/invalid_route_path_nonexistent")
    
    assert response.status_code == 404
    data = response.get_json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "request_id" in data["error"]
