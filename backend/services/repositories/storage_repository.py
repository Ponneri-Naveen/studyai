"""
backend/services/repositories/storage_repository.py — Abstract Base Storage Repository Interface representing database actions
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class StorageRepository(ABC):
    """
    Interface definition for all study data operations.
    Supports swapping implementations at runtime.
    """

    # ── Study Materials ──────────────────────────────────────────────────────
    @abstractmethod
    def get_all_materials(self, user_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_material_by_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_material(self, user_id: str, material: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def delete_material(self, user_id: str, mat_id: str) -> None:
        pass

    # ── AI Study Summaries ──────────────────────────────────────────────────
    @abstractmethod
    def get_summary_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_summary(self, user_id: str, summary: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def delete_summary(self, user_id: str, mat_id: str) -> None:
        pass

    # ── AI Flashcards ────────────────────────────────────────────────────────
    @abstractmethod
    def get_flashcards_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_flashcards(self, user_id: str, flashcards: Dict[str, Any]) -> None:
        pass

    # ── AI Quizzes ──────────────────────────────────────────────────────────
    @abstractmethod
    def get_quizzes_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_quizzes(self, user_id: str, quizzes: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def get_quiz_attempts(self, user_id: str, mat_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_quiz_attempt(self, user_id: str, mat_id: str, attempt: Dict[str, Any]) -> None:
        pass

    # ── Weak Topic Analysis ──────────────────────────────────────────────────
    @abstractmethod
    def get_analysis_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_analysis(self, user_id: str, analysis: Dict[str, Any]) -> None:
        pass

    # ── Personalized Study Planner ──────────────────────────────────────────
    @abstractmethod
    def get_active_plan(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_active_plan(self, user_id: str, plan: Dict[str, Any]) -> None:
        pass

    # ── Learning Analytics ───────────────────────────────────────────────────
    @abstractmethod
    def get_analytics_snapshot(self, user_id: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def save_analytics_snapshot(self, user_id: str, snapshot: Dict[str, Any]) -> None:
        pass
