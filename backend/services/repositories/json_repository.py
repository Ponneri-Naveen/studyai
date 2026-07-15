"""
backend/services/repositories/json_repository.py — Local JSON file database drivers repository implementation
"""

import os
import json
from typing import List, Dict, Any, Optional

from services.repositories.storage_repository import StorageRepository
import services.storage_service as legacy_storage
import services.summary_service as legacy_summary
import services.flashcard_service as legacy_flashcard
import services.quiz_service as legacy_quiz
import services.analysis_service as legacy_analysis
import services.planner_service as legacy_planner
import services.analytics_service as legacy_analytics


class JSONRepository(StorageRepository):
    """
    JSON local database file driver implementation routing to legacy storage routines.
    """

    # ── Study Materials ──────────────────────────────────────────────────────
    def get_all_materials(self, user_id: str) -> List[Dict[str, Any]]:
        return legacy_storage.get_all_materials()

    def get_material_by_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        return legacy_storage.get_material_by_id(mat_id)

    def save_material(self, user_id: str, material: Dict[str, Any]) -> None:
        # Map parameters from add_material signature if dict properties are present
        legacy_storage.add_material(
            filename=material.get("filename"),
            title=material.get("title"),
            subject=material.get("subject"),
            file_type=material.get("file_type"),
            size_bytes=material.get("size_bytes"),
            md5_checksum=material.get("md5_checksum"),
            page_count=material.get("page_count", 0),
            word_count=material.get("word_count", 0),
            character_count=material.get("character_count", 0),
            extracted_text=material.get("extracted_text", ""),
            raw_file_path=material.get("raw_file_path")
        )

    def delete_material(self, user_id: str, mat_id: str) -> None:
        legacy_storage.delete_material(mat_id)

    # ── AI Study Summaries ──────────────────────────────────────────────────
    def get_summary_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        return legacy_summary.get_summary_by_material_id(mat_id)

    def save_summary(self, user_id: str, summary: Dict[str, Any]) -> None:
        # summary schema keys updates mapping
        legacy_summary.save_summary(
            material_id=summary.get("material_id"),
            summary_content=summary.get("summary_content"),
            model=summary.get("model", "llama-3.3-70b-versatile"),
            prompt_version=summary.get("prompt_version", "summary_v1"),
            cached=summary.get("cached", False),
            latency_ms=summary.get("latency_ms", 0),
            prompt_tokens=summary.get("prompt_tokens", 0),
            completion_tokens=summary.get("completion_tokens", 0),
            total_tokens=summary.get("total_tokens", 0)
        )

    def delete_summary(self, user_id: str, mat_id: str) -> None:
        legacy_summary.delete_summary(mat_id)

    # ── AI Flashcards ────────────────────────────────────────────────────────
    def get_flashcards_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        return legacy_flashcard.get_flashcards_by_material_id(mat_id)

    def save_flashcards(self, user_id: str, flashcards: Dict[str, Any]) -> None:
        legacy_flashcard.save_flashcards(
            material_id=flashcards.get("material_id"),
            cards_list=flashcards.get("flashcards", [])
        )

    # ── AI Quizzes ──────────────────────────────────────────────────────────
    def get_quizzes_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        return legacy_quiz.get_quizzes_by_material_id(mat_id)

    def save_quizzes(self, user_id: str, quizzes: Dict[str, Any]) -> None:
        legacy_quiz.save_quizzes(
            material_id=quizzes.get("material_id"),
            questions=quizzes.get("quizzes", [])
        )

    def get_quiz_attempts(self, user_id: str, mat_id: str) -> List[Dict[str, Any]]:
        history = legacy_quiz.get_quizzes_history(mat_id) or {}
        return history.get("attempts", [])

    def save_quiz_attempt(self, user_id: str, mat_id: str, attempt: Dict[str, Any]) -> None:
        legacy_quiz.save_quiz_attempt(
            material_id=mat_id,
            attempt_data=attempt
        )

    # ── Weak Topic Analysis ──────────────────────────────────────────────────
    def get_analysis_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        return legacy_analysis.get_analysis_by_material_id(mat_id)

    def save_analysis(self, user_id: str, analysis: Dict[str, Any]) -> None:
        legacy_analysis.save_analysis(
            material_id=analysis.get("material_id"),
            topics_list=analysis.get("topics_analysis", [])
        )

    # ── Personalized Study Planner ──────────────────────────────────────────
    def get_active_plan(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        return legacy_planner.get_active_plan(mat_id)

    def save_active_plan(self, user_id: str, plan: Dict[str, Any]) -> None:
        legacy_planner.save_plan(
            material_id=plan.get("material_id"),
            planner_data=plan
        )

    # ── Learning Analytics ───────────────────────────────────────────────────
    def get_analytics_snapshot(self, user_id: str) -> Optional[Dict[str, Any]]:
        return legacy_analytics.get_cached_dashboard()

    def save_analytics_snapshot(self, user_id: str, snapshot: Dict[str, Any]) -> None:
        # Saves to snapshot local snapshot files caches
        pass
