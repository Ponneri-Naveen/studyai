"""
backend/tests/test_materials.py — Pytest suite for material uploads and text extraction pipeline
"""

import os
import io
import json
import shutil
import pytest
import sys

# Ensure backend root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
import services.storage_service as storage_service


@pytest.fixture
def client(tmp_path):
    """
    Configure testing app client and patch storage_service to use tmp_path
    to ensure database clean isolation during runs.
    """
    app = create_app()
    app.config["TESTING"] = True
    
    # Configure testing specific upload folder
    test_upload_dir = tmp_path / "uploads"
    test_upload_dir.mkdir()
    app.config["UPLOAD_FOLDER"] = str(test_upload_dir)
    
    # Configure testing specific storage folders
    test_storage_dir = tmp_path / "storage"
    test_texts_dir = test_storage_dir / "texts"
    test_storage_dir.mkdir()
    test_texts_dir.mkdir()
    
    test_metadata_file = test_storage_dir / "materials.json"
    
    # Monkey-patch paths in storage_service
    orig_storage_dir = storage_service.STORAGE_DIR
    orig_texts_dir = storage_service.TEXTS_DIR
    orig_metadata_file = storage_service.METADATA_FILE
    
    storage_service.STORAGE_DIR = str(test_storage_dir)
    storage_service.TEXTS_DIR = str(test_texts_dir)
    storage_service.METADATA_FILE = str(test_metadata_file)
    
    # Initialise testing metadata file
    with open(test_metadata_file, "w", encoding="utf-8") as f:
        json.dump({"materials": []}, f)
        
    with app.test_client() as client:
        yield client
        
    # Restore original paths
    storage_service.STORAGE_DIR = orig_storage_dir
    storage_service.TEXTS_DIR = orig_texts_dir
    storage_service.METADATA_FILE = orig_metadata_file


def test_list_materials_initially_empty(client):
    response = client.get("/api/v1/materials")
    assert response.status_code == 200
    assert response.get_json() == []


def test_create_text_material(client):
    payload = {
        "title": "Introduction to Biology",
        "subject": "Biology",
        "text": "Cell theory states that all living organisms are made of cells."
    }
    response = client.post(
        "/api/v1/materials/text",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 201
    data = response.get_json()
    assert "id" in data
    assert data["title"] == "Introduction to Biology"
    assert data["subject"] == "Biology"
    assert data["file_type"] == "text_paste"
    assert data["page_count"] == 1
    assert data["word_count"] == 11
    assert data["character_count"] == len(payload["text"])


def test_create_text_material_invalid_empty(client):
    payload = {
        "title": "",
        "text": ""
    }
    response = client.post(
        "/api/v1/materials/text",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_upload_txt_file(client):
    file_content = b"This is a sample plain text note."
    data = {
        "file": (io.BytesIO(file_content), "notes.txt"),
        "subject": "Physics"
    }
    response = client.post(
        "/api/v1/materials/upload",
        data=data,
        content_type="multipart/form-data"
    )
    assert response.status_code == 201
    res_data = response.get_json()
    assert res_data["filename"] == "notes.txt"
    assert res_data["subject"] == "Physics"
    assert res_data["file_type"] == "txt"
    assert res_data["character_count"] == len(file_content)


def test_upload_invalid_type(client):
    file_content = b"<html>Test</html>"
    data = {
        "file": (io.BytesIO(file_content), "index.html"),
        "subject": "WebDev"
    }
    response = client.post(
        "/api/v1/materials/upload",
        data=data,
        content_type="multipart/form-data"
    )
    assert response.status_code == 400
    assert "error" in response.get_json()


def test_duplicate_file_upload(client):
    file_content = b"Identical file upload content duplicate testing."
    data1 = {
        "file": (io.BytesIO(file_content), "test_doc.txt"),
        "subject": "Chem"
    }
    response1 = client.post(
        "/api/v1/materials/upload",
        data=data1,
        content_type="multipart/form-data"
    )
    assert response1.status_code == 201
    
    # Re-upload same file content without force parameter
    data2 = {
        "file": (io.BytesIO(file_content), "test_doc.txt"),
        "subject": "Chem"
    }
    response2 = client.post(
        "/api/v1/materials/upload",
        data=data2,
        content_type="multipart/form-data"
    )
    assert response2.status_code == 200
    res_json = response2.get_json()
    assert res_json.get("warning") == "duplicate_detected"
    assert "existing_material_id" in res_json

    # Re-upload with force parameter set to true
    data3 = {
        "file": (io.BytesIO(file_content), "test_doc.txt"),
        "subject": "Chem"
    }
    response3 = client.post(
        "/api/v1/materials/upload?force=true",
        data=data3,
        content_type="multipart/form-data"
    )
    assert response3.status_code == 201


def test_delete_material(client):
    # Setup test entry
    payload = {
        "title": "Delete Target",
        "subject": "Bio",
        "text": "Extracted text content target"
    }
    response_create = client.post(
        "/api/v1/materials/text",
        data=json.dumps(payload),
        content_type="application/json"
    )
    created_id = response_create.get_json()["id"]
    
    # Verify it exists in list
    list_res1 = client.get("/api/v1/materials")
    assert len(list_res1.get_json()) == 1

    # Delete the material
    response_delete = client.delete(f"/api/v1/materials/{created_id}")
    assert response_delete.status_code == 200
    
    # Verify it was removed
    list_res2 = client.get("/api/v1/materials")
    assert len(list_res2.get_json()) == 0
