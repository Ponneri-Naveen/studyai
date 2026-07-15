"""
backend/tests/test_analytics.py — Pytest suite verifying trend regression slopes, achievement unlocks, and cached snapshots
"""

import os
import json
import pytest
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from services.analytics_service import (
    calculate_dashboard_metrics, force_refresh_dashboard,
    ANALYTICS_DIR, CACHE_FILE
)


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_analytics_cache():
    """Purge analytics snapshot file before and after test runs."""
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
        except Exception:
            pass


@patch("services.analytics_service._read_materials")
@patch("services.analytics_service._safe_read_json")
def test_empty_databases_fallback(mock_safe_read, mock_read_mats, client):
    """
    Test analytics metrics return zeroed/default indicators for empty databases.
    """
    mock_read_mats.return_value = {"materials": []}
    mock_safe_read.return_value = {}
    
    # Force a refresh to bypass any pre-existing cache
    metrics = force_refresh_dashboard()

    assert metrics is not None
    overview = metrics["overview"]
    assert overview["materials_uploaded"] == 0
    assert overview["summaries_generated"] == 0
    assert overview["flashcards_generated"] == 0
    assert overview["quiz_attempts"] == 0
    assert overview["avg_quiz_score"] == 0.0
    assert overview["current_streak"] == 0
    assert overview["consistency_score"] == 100.0


def test_trend_regression_slope_calculation():
    """
    Verify regression slope equations classify upward/downward scores correctly.
    """
    # Upward score trend slope: 50 -> 60 -> 70 -> 80 -> 90
    # Let's mock quiz_scores
    with patch("services.analytics_service._safe_read_json") as mock_read:
        # Mock quiz quizzes.json
        mock_read.side_effect = lambda path, default: (
            {"quizzes_registry": [{"material_id": "m1"}]}
            if "quizzes.json" in path
            else default
        )
        
        # Mock get_quizzes_history
        with patch("services.analytics_service.get_quizzes_history") as mock_hist:
            mock_hist.return_value = {
                "attempts": [
                    {"metrics": {"score_percentage": 50.0}},
                    {"metrics": {"score_percentage": 60.0}},
                    {"metrics": {"score_percentage": 70.0}},
                    {"metrics": {"score_percentage": 85.0}},
                    {"metrics": {"score_percentage": 95.0}}
                ]
            }
            
            result = calculate_dashboard_metrics(force=True)
            assert result["trends"]["quiz_score_trend"] == "upward"


def test_achievements_unlock_conditions():
    """
    Verify badge unlocks match calculated milestones.
    """
    # Mock uploads = 1, perfect quiz = 100
    with patch("services.analytics_service._safe_read_json") as mock_read:
        mock_read.side_effect = lambda path, default: (
            {"quizzes_registry": [{"material_id": "m1"}]}
            if "quizzes.json" in path
            else default
        )
        
        with patch("services.analytics_service._read_materials") as mock_materials:
            mock_materials.return_value = {"materials": [{"id": "m1"}]}
            
            with patch("services.analytics_service.get_quizzes_history") as mock_hist:
                mock_hist.return_value = {
                    "attempts": [
                        {"metrics": {"score_percentage": 100.0}}
                    ]
                }
                
                result = calculate_dashboard_metrics(force=True)
                achievements = result["achievements"]
                
                # First Upload should be unlocked
                first_upload = next(a for a in achievements if a["id"] == "ach_first_upload")
                assert first_upload["unlocked"] is True
                
                # Perfect Score should be unlocked since highest score == 100.0
                perfect_quiz = next(a for a in achievements if a["id"] == "ach_perfect_quiz")
                assert perfect_quiz["unlocked"] is True
                
                # 7-Day Streak should be locked (streak is 0)
                streak_7 = next(a for a in achievements if a["id"] == "ach_streak_7")
                assert streak_7["unlocked"] is False
                assert streak_7["progress"] == 0.0
