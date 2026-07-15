"""
backend/tests/test_analysis.py — Pytest suite verifying mathematical scoring classifications and attempts fallbacks
"""

import os
import json
import pytest
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from services.storage_service import add_material, delete_material
from services.analysis_service import (
    generate_analysis, get_analysis_by_material_id, get_analysis_history,
    delete_analysis, ANALYSIS_DIR, METADATA_FILE, BASE_DIR
)
from services.ai.ai_exceptions import AIException


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_analysis_storage():
    """Ensure dynamic indexes and cards collections are purged before and after test runs."""
    if os.path.exists(METADATA_FILE):
        try:
            os.remove(METADATA_FILE)
        except Exception:
            pass
    history_dir = os.path.join(ANALYSIS_DIR, "history")
    if os.path.exists(history_dir):
        for f in os.listdir(history_dir):
            try:
                os.remove(os.path.join(history_dir, f))
            except Exception:
                pass


def test_missing_performance_data_fallback(client):
    """
    Test that running generate_analysis with zero quiz attempts or flashcard reviews raises a user-friendly 400 bad request.
    """
    mat = add_material(
        filename="empty.txt",
        title="Empty Material",
        subject="Chemistry",
        file_type="txt",
        size_bytes=10,
        md5_checksum="md5_an_empty",
        page_count=1,
        word_count=2,
        character_count=5,
        extracted_text="Chemistry contents"
    )
    mat_id = mat["id"]

    # Generate Analysis API call should fail with a 400 Bad Request since attempts and reviews are missing
    response = client.post(
        "/api/v1/analysis/generate",
        data=json.dumps({"material_id": mat_id}),
        content_type="application/json"
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "Please complete at least one quiz attempt" in data["error"]

    # Cleanup
    delete_material(mat_id)


@patch("services.ai.ai_client.AIClient.run_completion")
def test_deterministic_scoring_math(mock_completion, client):
    """
    Test deterministic weighted classifications accuracy calculations.
    """
    mat_id = "mat_mock_an"
    
    # 1. Setup mock quiz attempts
    with open(os.path.join(BASE_DIR, "storage", "quizzes", "quizzes.json"), "w", encoding="utf-8") as f:
        json.dump({
            "quizzes_registry": [
                {
                    "material_id": mat_id,
                    "quiz_id": "qz_mock",
                    "active_version": 1,
                    "history": [
                        {
                            "version": 1,
                            "questions_file_path": f"storage/quizzes/questions/qz_{mat_id}_v1.json",
                            "created_at": "2026-07-15T16:00:00Z"
                        }
                    ]
                }
            ]
        }, f, indent=2)

    attempts_path = os.path.join(BASE_DIR, "storage", "quizzes", "attempts", f"att_{mat_id}.json")
    os.makedirs(os.path.dirname(attempts_path), exist_ok=True)
    
    # Topic A: 3 attempts, 3 correct answers -> 100% accuracy, difficulty medium
    # Topic B: 2 attempts, 0 correct answers -> 0% accuracy, difficulty hard
    attempts = [
        {
            "attempt_id": "att_1",
            "quiz_id": "qz_mock",
            "quiz_version": 1,
            "mode": "exam",
            "time_taken_seconds": 100,
            "completed_at": "2026-07-15T15:00:00Z",
            "metrics": {
                "score_percentage": 50.0
            },
            "responses": [
                {
                    "question_id": "q1",
                    "question_type": "mcq",
                    "topic": "Topic A",
                    "difficulty": "medium",
                    "student_answer": "Correct",
                    "correct_answer": "Correct",
                    "is_correct": True
                },
                {
                    "question_id": "q2",
                    "question_type": "mcq",
                    "topic": "Topic B",
                    "difficulty": "hard",
                    "student_answer": "Wrong",
                    "correct_answer": "Correct",
                    "is_correct": False
                }
            ]
        },
        {
            "attempt_id": "att_2",
            "quiz_id": "qz_mock",
            "quiz_version": 1,
            "mode": "exam",
            "time_taken_seconds": 120,
            "completed_at": "2026-07-15T16:00:00Z",
            "metrics": {
                "score_percentage": 50.0
            },
            "responses": [
                {
                    "question_id": "q1",
                    "question_type": "mcq",
                    "topic": "Topic A",
                    "difficulty": "medium",
                    "student_answer": "Correct",
                    "correct_answer": "Correct",
                    "is_correct": True
                },
                {
                    "question_id": "q2",
                    "question_type": "mcq",
                    "topic": "Topic B",
                    "difficulty": "hard",
                    "student_answer": "Wrong",
                    "correct_answer": "Correct",
                    "is_correct": False
                }
            ]
        }
    ]
    with open(attempts_path, "w", encoding="utf-8") as f:
        json.dump(attempts, f, indent=2)

    # 2. Setup mock flashcards review logs (Topic A cards mastered, Topic B unmastered)
    cards_path = os.path.join(BASE_DIR, "storage", "flashcards", "cards", f"fc_{mat_id}_v1.json")
    os.makedirs(os.path.dirname(cards_path), exist_ok=True)
    cards = [
        {
            "flashcard_id": "fc1",
            "question": "Card A?",
            "answer": "Answer",
            "topic": "Topic A",
            "difficulty": "medium",
            "mastered": True,
            "review_count": 5
        },
        {
            "flashcard_id": "fc2",
            "question": "Card B?",
            "answer": "Answer",
            "topic": "Topic B",
            "difficulty": "hard",
            "mastered": False,
            "review_count": 0
        }
    ]
    with open(cards_path, "w", encoding="utf-8") as f:
        json.dump(cards, f, indent=2)

    # Mock flashcards.json registry mapping
    with open(os.path.join(BASE_DIR, "storage", "flashcards", "flashcards.json"), "w", encoding="utf-8") as f:
        json.dump({
            "flashcards_registry": [
                {
                    "material_id": mat_id,
                    "active_version": 1,
                    "history": [
                        {
                            "version": 1,
                            "cards_file_path": f"storage/flashcards/cards/fc_{mat_id}_v1.json",
                            "created_at": "2026-07-15T16:00:00Z"
                        }
                    ]
                }
            ]
        }, f, indent=2)

    # Mock AI response
    mock_completion.return_value = {
        "text": json.dumps({
            "personalized_advice": "Focus on Topic B DNA concepts.",
            "revision_priorities": ["Topic B basic details"],
            "learning_strategy": "Review Topic B outlines."
        }),
        "tokens_used": 150,
        "latency_ms": 300
    }

    # Execute deterministic diagnostic calculations
    result = generate_analysis(mat_id, regenerate=True)

    assert result["material_id"] == mat_id
    assert result["active_version"] == 1
    
    # Topic A stats verification
    # Accuracy = 100%, Mastery = 100%, Reviews = 5 (gives 100% review score)
    # Math: (0.5 * 100) + (0.3 * 100) + (0.2 * 100) = 100.0 confidence score -> Excellent
    topic_a = next(t for t in result["topics_analysis"] if t["topic"] == "Topic A")
    assert topic_a["accuracy"] == 100.0
    assert topic_a["mastery_score"] == 100.0
    assert topic_a["confidence_score"] == 100.0
    assert topic_a["weakness_level"] == "Excellent"

    # Topic B stats verification
    # Accuracy = 0%, Mastery = 0%, Reviews = 0 (gives 0% review score)
    # Math: (0.5 * 0) + (0.3 * 0) + (0.2 * 0) = 0.0 + 5.0 (difficulty hard adjustment) = 5.0 confidence score -> Critical
    topic_b = next(t for t in result["topics_analysis"] if t["topic"] == "Topic B")
    assert topic_b["accuracy"] == 0.0
    assert topic_b["mastery_score"] == 0.0
    assert topic_b["confidence_score"] == 5.0
    assert topic_b["weakness_level"] == "Critical"

    # Clean up mock files
    try:
        os.remove(attempts_path)
        os.remove(cards_path)
        os.remove(os.path.join(HISTORY_DIR, f"an_{mat_id}_v1.json"))
        os.remove(os.path.join(BASE_DIR, "storage", "quizzes", "quizzes.json"))
        os.remove(os.path.join(BASE_DIR, "storage", "flashcards", "flashcards.json"))
    except Exception:
        pass
