"""
backend/tests/test_planner.py — Pytest suite verifying scheduling algorithms and carry-forward allocations
"""

import os
import json
import pytest
import sys
import datetime
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from services.storage_service import add_material, delete_material
from services.planner_service import (
    generate_plan, get_active_plan, toggle_task_completion, delete_plan,
    PLANS_DIR, METADATA_FILE, DAILY_DIR, BASE_DIR
)
from services.ai.ai_exceptions import AIException


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_planner_storage():
    """Ensure dynamic indexes are clean before and after test runs."""
    if os.path.exists(METADATA_FILE):
        try:
            os.remove(METADATA_FILE)
        except Exception:
            pass
    daily_dir = os.path.join(PLANS_DIR, "daily")
    if os.path.exists(daily_dir):
        for f in os.listdir(daily_dir):
            try:
                os.remove(os.path.join(daily_dir, f))
            except Exception:
                pass


def test_missing_diagnostics_fallback(client):
    """
    Test fallback to trigger analysis or raise 400 Bad Request error if Weak Topic Analysis is missing and can't be created.
    """
    mat_id = "mat_empty_pl"

    # Plan Generation API call should fail with a 400 Bad Request since performance analytics are missing
    response = client.post(
        "/api/v1/plans/generate",
        data=json.dumps({
            "material_id": mat_id,
            "exam_date": "2026-08-15T00:00:00Z",
            "total_days": 7
        }),
        content_type="application/json"
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert "Performance diagnostics missing" in data["error"]


@patch("services.ai.ai_client.AIClient.run_completion")
def test_carry_forward_logic(mock_completion, client):
    """
    Test that past incomplete tasks are automatically carried forward when active plan is queried.
    """
    mat_id = "mat_mock_pl"
    
    # 1. Setup mock active plan file on disk
    os.makedirs(DAILY_DIR, exist_ok=True)
    plan_path = os.path.join(DAILY_DIR, f"pl_{mat_id}_v1.json")
    
    # Yesterday's date
    yesterday = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime("%Y-%m-%dT00:00:00Z")
    # Today's date
    today = datetime.datetime.utcnow().strftime("%Y-%m-%dT00:00:00Z")
    
    plan_payload = {
        "plan_id": "pl_mock",
        "material_id": mat_id,
        "plan_version": 1,
        "analysis_version": 1,
        "summary_version": 1,
        "flashcard_version": 1,
        "quiz_version": 1,
        "exam_date": "2026-08-15T00:00:00Z",
        "preferences": {
            "total_days": 2,
            "daily_study_hours": 3.0,
            "time_preference": "morning"
        },
        "dashboard_preparation": {
            "tasks_completed": 0,
            "tasks_remaining": 3,
            "daily_completion_percent": 0.0,
            "overall_completion_percent": 0.0,
            "current_streak": 0,
            "study_consistency_score": 100.0
        },
        "daily_schedule": [
            {
                "day_number": 1,
                "date": yesterday,
                "tasks": [
                    {
                        "task_id": "tsk_yesterday_incomplete",
                        "task_type": "reading",
                        "revision_topic": "DNA Structure",
                        "task": "Study pairing rules.",
                        "priority": "critical",
                        "estimated_minutes": 30,
                        "completed": False,
                        "completed_at": None
                    },
                    {
                        "task_id": "tsk_yesterday_complete",
                        "task_type": "flashcard_review",
                        "revision_topic": "DNA Structure",
                        "task": "Review cards.",
                        "priority": "high",
                        "estimated_minutes": 15,
                        "completed": True,
                        "completed_at": yesterday
                    }
                ]
            },
            {
                "day_number": 2,
                "date": today,
                "tasks": [
                    {
                        "task_id": "tsk_today_normal",
                        "task_type": "quiz_practice",
                        "revision_topic": "Replication",
                        "task": "Practice quiz.",
                        "priority": "medium",
                        "estimated_minutes": 20,
                        "completed": False,
                        "completed_at": None
                    }
                ]
            }
        ],
        "motivational_note": "Keep going!"
    }
    
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(plan_payload, f, indent=2)
        
    # Write metadata index
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "plans_registry": [
                {
                    "material_id": mat_id,
                    "active_version": 1,
                    "created_at": "2026-07-15T16:00:00Z",
                    "updated_at": "2026-07-15T16:00:00Z",
                    "history": [
                        {
                            "version": 1,
                            "plan_file_path": f"storage/plans/daily/pl_{mat_id}_v1.json",
                            "created_at": "2026-07-15T16:00:00Z"
                        }
                    ]
                }
            ]
        }, f, indent=2)

    # 2. Get active plan (triggers carry forward)
    plan = get_active_plan(mat_id)
    
    assert plan is not None
    
    # Verify tsk_yesterday_incomplete is carried forward to Day 2 (today)
    day1 = next(d for d in plan["daily_schedule"] if d["day_number"] == 1)
    day2 = next(d for d in plan["daily_schedule"] if d["day_number"] == 2)
    
    # Day 1 should now only contain completed or non-carried-forward tasks
    assert len(day1["tasks"]) == 1
    assert day1["tasks"][0]["task_id"] == "tsk_yesterday_complete"
    
    # Day 2 should now contain both today's task and the carried forward task
    assert len(day2["tasks"]) == 2
    carried_task = next(t for t in day2["tasks"] if t["task_id"] == "tsk_yesterday_incomplete")
    assert carried_task["carried_forward"] is True

    # 3. Toggle task completion
    updated = toggle_task_completion(mat_id, "tsk_yesterday_incomplete", True)
    assert updated["dashboard_preparation"]["tasks_completed"] == 2
    assert updated["dashboard_preparation"]["tasks_remaining"] == 1

    # Clean up mock files
    try:
        os.remove(plan_path)
    except Exception:
        pass
