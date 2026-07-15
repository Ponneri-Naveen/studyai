"""
backend/tests/test_quizzes.py — Pytest suite verifying AI quiz JSON parsing, attempts grading scorers, float partial credits, and history prunings
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
from services.flashcard_service import delete_flashcards
from services.quiz_service import (
    generate_quiz, get_quiz_by_material_id, get_quizzes_history,
    delete_quiz, QUIZZES_DIR, METADATA_FILE
)
from services.ai.ai_exceptions import AIException


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_quiz_storage():
    """Ensure dynamic indexes and cards collections are purged before and after test runs."""
    if os.path.exists(METADATA_FILE):
        try:
            os.remove(METADATA_FILE)
        except Exception:
            pass
    questions_dir = os.path.join(QUIZZES_DIR, "questions")
    if os.path.exists(questions_dir):
        for f in os.listdir(questions_dir):
            try:
                os.remove(os.path.join(questions_dir, f))
            except Exception:
                pass
    attempts_dir = os.path.join(QUIZZES_DIR, "attempts")
    if os.path.exists(attempts_dir):
        for f in os.listdir(attempts_dir):
            try:
                os.remove(os.path.join(attempts_dir, f))
            except Exception:
                pass


@patch("services.ai.ai_client.AIClient.run_completion")
def test_generate_quiz_workflow(mock_completion, client):
    """
    Test generating quiz questions sheet from active contexts.
    """
    mat = add_material(
        filename="dna.txt",
        title="Genetics Introduction",
        subject="Biology",
        file_type="txt",
        size_bytes=40,
        md5_checksum="md5_qz_1",
        page_count=1,
        word_count=5,
        character_count=20,
        extracted_text="Deoxyribonucleic acid nucleotides genes chromosomes double helix."
    )
    mat_id = mat["id"]

    # Mock responses:
    # 1. Summary Generation
    # 2. Flashcard Generation
    # 3. Quiz Generation
    mock_completion.side_effect = [
        # Call 1: Summary Ingestion
        {
            "text": "# DNA Summary\nDouble helix outlines.",
            "tokens_used": 100,
            "latency_ms": 300
        },
        # Call 2: Flashcards Ingestion
        {
            "text": json.dumps({
                "flashcards": [
                    {
                        "question": "What shape is DNA?",
                        "answer": "Double helix.",
                        "topic": "DNA Structure",
                        "difficulty": "easy",
                        "tags": ["dna"]
                    }
                ]
            }),
            "tokens_used": 150,
            "latency_ms": 400
        },
        # Call 3: Quiz Ingestion
        {
            "text": json.dumps({
                "questions": [
                    {
                        "question_type": "mcq",
                        "question": "Which nucleotides pair in DNA?",
                        "topic": "DNA Structure",
                        "difficulty": "medium",
                        "choices": ["Adenine-Thymine", "Adenine-Uracil", "Guanine-Adenine", "Cytosine-Thymine"],
                        "correct_answer": "Adenine-Thymine",
                        "explanation": "Adenine base pairs with thymine, cytosine pairs with guanine."
                    },
                    {
                        "question_type": "true_false",
                        "question": "DNA is single stranded.",
                        "topic": "DNA Structure",
                        "difficulty": "easy",
                        "choices": ["True", "False"],
                        "correct_answer": "False",
                        "explanation": "DNA is structured as a double stranded helix."
                    },
                    {
                        "question_type": "short_answer",
                        "question": "What is the full name of DNA?",
                        "topic": "Terminology",
                        "difficulty": "hard",
                        "choices": [],
                        "correct_answer": "Deoxyribonucleic Acid",
                        "explanation": "Deoxyribonucleic acid is full biochemical spelling."
                    }
                ]
            }),
            "tokens_used": 350,
            "latency_ms": 700
        }
    ]

    # Generate Quiz API POST
    response = client.post(
        "/api/v1/quizzes/generate",
        data=json.dumps({"material_id": mat_id}),
        content_type="application/json"
    )

    assert response.status_code == 201
    data = response.get_json()
    assert data["material_id"] == mat_id
    assert data["active_version"] == 1
    assert len(data["questions"]) == 3
    assert data["questions"][0]["question_type"] == "mcq"
    assert data["questions"][0]["marks"] == 1.0

    # Clean up
    delete_material(mat_id)
    delete_summary(mat_id)
    delete_flashcards(mat_id)


def test_submit_quiz_grading_scorer(client):
    """
    Test quiz submissions grading engine evaluating MCQs, True/False, and Short Answers (with float partial credits).
    """
    # Write a temporary mock questions sheet file
    mat_id = "mat_mock_qz"
    questions = [
        {
            "question_id": "q_mcq_1",
            "question_type": "mcq",
            "question": "Question A?",
            "choices": ["A", "B", "C"],
            "correct_answer": "A",
            "explanation": "Exp MCQ",
            "marks": 2.0
        },
        {
            "question_id": "q_tf_1",
            "question_type": "true_false",
            "question": "Question B?",
            "choices": ["True", "False"],
            "correct_answer": "True",
            "explanation": "Exp TF",
            "marks": 1.0
        },
        {
            "question_id": "q_sa_1",
            "question_type": "short_answer",
            "question": "Question C?",
            "choices": [],
            "correct_answer": "Mitochondria",
            "explanation": "Exp SA",
            "marks": 2.0
        }
    ]
    
    os.makedirs(os.path.join(QUIZZES_DIR, "questions"), exist_ok=True)
    with open(os.path.join(QUIZZES_DIR, "questions", f"qz_{mat_id}_v1.json"), "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=2)

    # Mock metadata entry in quizzes.json
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "quizzes_registry": [
                {
                    "material_id": mat_id,
                    "quiz_id": "qz_mock_qz",
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

    # Student submission sheet answers
    # Answer MCQ correctly, TF incorrectly, and Short Answer with partial correct match check
    student_answers = {
        "q_mcq_1": "A",
        "q_tf_1": "False",
        "q_sa_1": "mitochondria organelle cell power"  # Contains 'mitochondria' term inside -> partial credit
    }

    response = client.post(
        "/api/v1/quizzes/qz_mock_qz/submit",
        data=json.dumps({
            "material_id": mat_id,
            "quiz_version": 1,
            "mode": "exam",
            "time_taken_seconds": 150,
            "question_order": ["q_mcq_1", "q_tf_1", "q_sa_1"],
            "answers": student_answers
        }),
        content_type="application/json"
    )

    assert response.status_code == 201
    res = response.get_json()
    assert res["metrics"]["total_questions"] == 3
    assert res["metrics"]["obtained_marks"] == 3.0  # 2.0 for MCQ + 0.0 for TF + 1.0 (50% of 2.0) for partial SA match
    assert res["metrics"]["total_marks"] == 5.0
    assert res["metrics"]["score_percentage"] == 60.0
    assert res["question_order"] == ["q_mcq_1", "q_tf_1", "q_sa_1"]

    # Verify response schema entries
    assert res["responses"][0]["is_correct"] is True
    assert res["responses"][1]["is_correct"] is False
    assert res["responses"][2]["is_correct"] is True
    assert res["responses"][2]["obtained_marks"] == 1.0

    # Assert attempts list logs files exist
    response_history = client.get(f"/api/v1/quizzes/{mat_id}/history")
    assert response_history.status_code == 200
    hist = response_history.get_json()
    assert len(hist["attempts"]) == 1
    assert hist["attempts"][0]["metrics"]["score_percentage"] == 60.0

    # Cleanup mock files manually
    try:
        os.remove(os.path.join(QUIZZES_DIR, "questions", f"qz_{mat_id}_v1.json"))
        os.remove(os.path.join(QUIZZES_DIR, "attempts", f"att_{mat_id}.json"))
    except Exception:
        pass
