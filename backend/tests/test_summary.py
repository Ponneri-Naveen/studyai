"""
backend/tests/test_summary.py — Pytest suite verifying summary chunking loops, version retention caps, and cache registers
"""

import os
import json
import pytest
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from services.summary_service import (
    generate_summary, get_summary_by_material_id, delete_summary, get_summary_history,
    SUMMARIES_DIR, METADATA_FILE
)
from services.storage_service import add_material, delete_material
from services.ai.ai_exceptions import AIException


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_storage():
    """Ensure dynamic indexes are purged before and after test executions."""
    # Clean summaries.json
    if os.path.exists(METADATA_FILE):
        try:
            os.remove(METADATA_FILE)
        except Exception:
            pass
    # Clean text versions files
    text_dir = os.path.join(SUMMARIES_DIR, "texts")
    if os.path.exists(text_dir):
        for f in os.listdir(text_dir):
            try:
                os.remove(os.path.join(text_dir, f))
            except Exception:
                pass


@patch("services.ai.ai_client.AIClient.run_completion")
def test_generate_summary_workflow(mock_completion, client):
    """
    Test generating summary from start to finish, confirming caching and version indices.
    """
    # Create study material
    mat = add_material(
        filename="notes.txt",
        title="History Notes",
        subject="History",
        file_type="txt",
        size_bytes=50,
        md5_checksum="md5_abc123",
        page_count=1,
        word_count=5,
        character_count=20,
        extracted_text="American civil war history notes text."
    )
    mat_id = mat["id"]
    
    # Mock AI response
    mock_completion.return_value = {
        "text": "# Summary\n- Deep Civil War Outlines",
        "tokens_used": 100,
        "latency_ms": 500
    }
    
    # POST Generate
    response = client.post(
        "/api/v1/summary/generate",
        data=json.dumps({"material_id": mat_id}),
        content_type="application/json"
    )
    
    assert response.status_code == 201
    data = response.get_json()
    assert data["material_id"] == mat_id
    assert data["summary_version"] == 1
    assert "Deep Civil War Outlines" in data["summary_markdown"]
    assert data["cached"] is False
    
    # Test cache logic
    response_cached = client.post(
        "/api/v1/summary/generate",
        data=json.dumps({"material_id": mat_id}),
        content_type="application/json"
    )
    assert response_cached.status_code == 200
    assert response_cached.get_json()["cached"] is True

    # Clean up material
    delete_material(mat_id)


@patch("services.ai.ai_client.AIClient.run_completion")
def test_generate_summary_version_increment_limit(mock_completion, client):
    """
    Test that regeneration increments versions correctly and cleans up version 1 if history exceeds 5 versions.
    """
    mat = add_material(
        filename="biology.txt",
        title="Cell Structure",
        subject="Biology",
        file_type="txt",
        size_bytes=30,
        md5_checksum="md5_bio1",
        page_count=1,
        word_count=3,
        character_count=15,
        extracted_text="Extracted biology cell study text data."
    )
    mat_id = mat["id"]
    
    mock_completion.return_value = {
        "text": "Biology summary markdown content",
        "tokens_used": 50,
        "latency_ms": 300
    }
    
    # Generate versions 1 through 6
    for i in range(1, 7):
        response = client.post(
            "/api/v1/summary/generate",
            data=json.dumps({"material_id": mat_id, "regenerate": True}),
            content_type="application/json"
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["summary_version"] == i
        
    # Check history history mapping endpoint
    response_history = client.get(f"/api/v1/summary/{mat_id}/history")
    assert response_history.status_code == 200
    history_data = response_history.get_json()
    assert history_data["active_version"] == 6
    # Should only retain exactly 5 versions (versions 2, 3, 4, 5, 6)
    versions = history_data["versions"]
    assert len(versions) == 5
    # Version 1 is deleted, lowest retained is version 2
    assert versions[0]["version"] == 2
    assert versions[-1]["version"] == 6

    # Verify version 1 file is missing, while version 6 exists
    text_dir = os.path.join(SUMMARIES_DIR, "texts")
    assert not os.path.exists(os.path.join(text_dir, f"sum_{mat_id}_v1.md"))
    assert os.path.exists(os.path.join(text_dir, f"sum_{mat_id}_v6.md"))

    # Cleanup
    delete_material(mat_id)
    delete_summary(mat_id)


@patch("services.ai.ai_client.AIClient.run_completion")
def test_document_chunking_summarization(mock_completion, client):
    """
    Test chunking splits and consolidation passes for massive text payloads.
    """
    mat = add_material(
        filename="long.txt",
        title="Huge Notes",
        subject="Chemistry",
        file_type="txt",
        size_bytes=10,
        md5_checksum="md5_chem1",
        page_count=1,
        word_count=2,
        character_count=5,
        extracted_text="Chemistry text"
    )
    mat_id = mat["id"]
    
    mock_completion.return_value = {
        "text": "Chemistry study notes markdown content",
        "tokens_used": 60,
        "latency_ms": 200
    }
    
    # Overwrite configuration thresholds inside test logic
    with patch("services.summary_service.get_config") as mock_config:
        mock_cfg_inst = MagicMock()
        mock_cfg_inst.MAX_SUMMARY_INPUT_CHARS = 10
        mock_cfg_inst.MAX_SUMMARY_OVERLAP_CHARS = 2
        mock_cfg_inst.MAX_SUMMARY_TOTAL_LIMIT = 500000
        mock_cfg_inst.MAX_SUMMARY_VERSIONS_RETAINED = 5
        mock_cfg_inst.MODELS = {"default": "llama-3.3-70b-versatile"}
        mock_config.return_value = mock_cfg_inst
        
        # Ingest text larger than MAX_SUMMARY_INPUT_CHARS (10)
        # Using a patch to run completion multiple times (for chunks and consolidation)
        # Mock text has length 35 (so it will break into chunks)
        large_text = "Hydrogen Oxygen Nitrogen Carbon Helium"
        with patch("services.summary_service.get_material_by_id") as mock_get_mat:
            mock_get_mat.return_value = {
                "id": mat_id,
                "title": "Huge Notes",
                "extracted_text": large_text,
                "subject": "Chemistry"
            }
            
            response = client.post(
                "/api/v1/summary/generate",
                data=json.dumps({"material_id": mat_id}),
                content_type="application/json"
            )
            
            assert response.status_code == 201
            # Ensure AI was called multiple times (for chunks + final consolidation)
            assert mock_completion.call_count >= 2
            data = response.get_json()
            assert data["summary_version"] == 1
            
    delete_material(mat_id)
