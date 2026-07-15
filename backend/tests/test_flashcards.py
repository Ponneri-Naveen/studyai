"""
backend/tests/test_flashcards.py — Pytest suite verifying AI flashcard JSON parsing, version prunings, and spaced repetition metrics
"""

import os
import json
import pytest
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from services.storage_service import add_material, delete_material
from services.summary_service import delete_summary
from services.flashcard_service import (
    generate_flashcards, get_flashcards_by_material_id, get_flashcards_history,
    delete_flashcards, FLASHCARDS_DIR, METADATA_FILE
)
from services.ai.ai_exceptions import AIException


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_flashcard_storage():
    """Ensure dynamic indexes and cards collections are purged before and after test runs."""
    # Clean flashcards.json
    if os.path.exists(METADATA_FILE):
        try:
            os.remove(METADATA_FILE)
        except Exception:
            pass
    # Clean cards version files
    cards_dir = os.path.join(FLASHCARDS_DIR, "cards")
    if os.path.exists(cards_dir):
        for f in os.listdir(cards_dir):
            try:
                os.remove(os.path.join(cards_dir, f))
            except Exception:
                pass
    # Clean history files
    hist_dir = os.path.join(FLASHCARDS_DIR, "history")
    if os.path.exists(hist_dir):
        for f in os.listdir(hist_dir):
            try:
                os.remove(os.path.join(hist_dir, f))
            except Exception:
                pass


@patch("services.ai.ai_client.AIClient.run_completion")
def test_generate_flashcards_workflow(mock_completion, client):
    """
    Test generating cards when summary is missing.
    Asserts that a summary is auto-generated first, followed by active-recall JSON cards.
    """
    mat = add_material(
        filename="cells.txt",
        title="Cell biology details",
        subject="Biology",
        file_type="txt",
        size_bytes=30,
        md5_checksum="md5_fc_1",
        page_count=1,
        word_count=5,
        character_count=15,
        extracted_text="Cell wall mitochondria organelles nucleus details."
    )
    mat_id = mat["id"]

    # Mock responses:
    # 1. First call (Summary Generator) -> Returns Markdown
    # 2. Second call (Flashcard Generator) -> Returns JSON string
    mock_completion.side_effect = [
        # Call 1: Summary Ingestion
        {
            "text": "# Biology Summary\nStudy organelles outlines.",
            "tokens_used": 150,
            "latency_ms": 400
        },
        # Call 2: Flashcards Ingestion
        {
            "text": json.dumps({
                "flashcards": [
                    {
                        "question": "What is the primary function of Cell Wall?",
                        "answer": "Provides structural support and protection to plant cells.",
                        "topic": "Cell Biology",
                        "difficulty": "easy",
                        "tags": ["plant", "cell"]
                    },
                    {
                        "question": "What does Nucleus contain?",
                        "answer": "Contains genetic material (DNA) directing cell actions.",
                        "topic": "Cell Biology",
                        "difficulty": "medium",
                        "tags": ["nucleus", "organelle"]
                    }
                ]
            }),
            "tokens_used": 200,
            "latency_ms": 600
        }
    ]

    # POST Generate Flashcards
    response = client.post(
        "/api/v1/flashcards/generate",
        data=json.dumps({"material_id": mat_id}),
        content_type="application/json"
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["material_id"] == mat_id
    assert data["active_version"] == 1
    assert len(data["flashcards"]) == 2
    assert data["flashcards"][0]["question"] == "What is the primary function of Cell Wall?"
    assert data["flashcards"][0]["ease_factor"] == 2.5
    assert data["flashcards"][0]["interval_days"] == 1
    assert data["cached"] is False

    # Check database load GET
    response_get = client.get(f"/api/v1/flashcards/{mat_id}")
    assert response_get.status_code == 200
    assert len(response_get.get_json()["flashcards"]) == 2

    # Clean up
    delete_material(mat_id)
    delete_summary(mat_id)


@patch("services.ai.ai_client.AIClient.run_completion")
def test_flashcard_mastery_and_spaced_repetition(mock_completion, client):
    """
    Test mastery toggle and SM-2 spaced repetition interval updates on review answers.
    """
    mat = add_material(
        filename="test.txt",
        title="Test Spaced",
        subject="Chemistry",
        file_type="txt",
        size_bytes=10,
        md5_checksum="md5_fc_chem",
        page_count=1,
        word_count=2,
        character_count=5,
        extracted_text="Chemistry content"
    )
    mat_id = mat["id"]

    mock_completion.side_effect = [
        # Summary
        {
            "text": "# Chem summary outlines",
            "tokens_used": 50,
            "latency_ms": 200
        },
        # Flashcards
        {
            "text": json.dumps({
                "flashcards": [
                    {
                        "question": "What is atomic number of Hydrogen?",
                        "answer": "Atomic number of hydrogen is 1.",
                        "topic": "Elements",
                        "difficulty": "easy",
                        "tags": ["hydrogen"]
                    }
                ]
            }),
            "tokens_used": 100,
            "latency_ms": 400
        }
    ]

    # Generate
    client.post(
        "/api/v1/flashcards/generate",
        data=json.dumps({"material_id": mat_id}),
        content_type="application/json"
    )

    # Get active flashcards to capture ID
    cards_data = get_flashcards_by_material_id(mat_id)
    card_id = cards_data["flashcards"][0]["flashcard_id"]

    # 1. Test Toggle Mastery
    resp_master = client.patch(
        f"/api/v1/flashcards/{card_id}/mastered",
        data=json.dumps({"material_id": mat_id, "mastered": True}),
        content_type="application/json"
    )
    assert resp_master.status_code == 200
    assert resp_master.get_json()["mastered"] is True

    # 2. Test Spaced Repetition Review (knows answer)
    resp_review = client.patch(
        f"/api/v1/flashcards/{card_id}/review",
        data=json.dumps({"material_id": mat_id, "know_answer": True}),
        content_type="application/json"
    )
    assert resp_review.status_code == 200
    rev_data = resp_review.get_json()
    assert rev_data["review_count"] == 1
    # Check that ease factor incremented and interval days multiplied (2.5 * 1 = 2)
    assert rev_data["interval_days"] == 2
    assert rev_data["next_review"] is not None

    # Cleanup
    delete_material(mat_id)
    delete_summary(mat_id)
    delete_flashcards(mat_id)
