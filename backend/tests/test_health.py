"""tests/test_health.py — Health endpoint unit tests"""

import pytest
import sys
import os

# Make sure the backend root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health_returns_200(client):
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_returns_running_status(client):
    response = client.get("/api/health")
    data = response.get_json()
    assert data["status"] == "running"


def test_health_returns_version(client):
    response = client.get("/api/health")
    data = response.get_json()
    assert "version" in data


def test_health_returns_service_name(client):
    response = client.get("/api/health")
    data = response.get_json()
    assert data["service"] == "StudyAI API"
