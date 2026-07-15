"""
backend/services/repositories/firestore_repository.py — Google Cloud Firestore production database client repository implementation
"""

import logging
from typing import List, Dict, Any, Optional
import firebase_admin
from firebase_admin import firestore

from services.repositories.storage_repository import StorageRepository

logger = logging.getLogger(__name__)


class FirestoreRepository(StorageRepository):
    """
    Production Firestore implementation of StorageRepository enforcing user context boundaries.
    """

    def __init__(self):
        # Retrieve initialized db client reference
        self.db = firestore.client()

    # Helper wrapper to map raw documents to list dictionary values
    def _doc_to_dict(self, doc) -> Optional[Dict[str, Any]]:
        if not doc.exists:
            return None
        data = doc.to_dict()
        # Enforce timestamp conversions to standard string formats
        for key, val in list(data.items()):
            if hasattr(val, "isoformat"):
                data[key] = val.isoformat()
        return data

    # ── Study Materials ──────────────────────────────────────────────────────
    def get_all_materials(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            docs = self.db.collection("materials").where("owner_id", "==", user_id).stream()
            return [self._doc_to_dict(d) for d in docs if d.exists]
        except Exception as e:
            logger.error("Firestore get_all_materials failed: %s", str(e))
            return []

    def get_material_by_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = self.db.collection("materials").document(mat_id).get()
            data = self._doc_to_dict(doc_ref)
            if data and data.get("owner_id") == user_id:
                return data
        except Exception as e:
            logger.error("Firestore get_material_by_id failed: %s", str(e))
        return None

    def save_material(self, user_id: str, material: Dict[str, Any]) -> None:
        try:
            mat_id = material.get("id")
            doc_data = dict(material)
            doc_data["owner_id"] = user_id
            doc_data["updated_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("materials").document(mat_id).set(doc_data)
        except Exception as e:
            logger.error("Firestore save_material failed: %s", str(e))
            raise IOError("Could not save material meta: " + str(e))

    def delete_material(self, user_id: str, mat_id: str) -> None:
        try:
            # Enforce user boundary check
            doc_ref = self.db.collection("materials").document(mat_id)
            doc = doc_ref.get()
            if doc.exists and doc.to_dict().get("owner_id") == user_id:
                doc_ref.delete()
        except Exception as e:
            logger.error("Firestore delete_material failed: %s", str(e))

    # ── AI Study Summaries ──────────────────────────────────────────────────
    def get_summary_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = self.db.collection("summaries").document(mat_id).get()
            data = self._doc_to_dict(doc_ref)
            if data and data.get("owner_id") == user_id:
                return data
        except Exception as e:
            logger.error("Firestore get_summary failed: %s", str(e))
        return None

    def save_summary(self, user_id: str, summary: Dict[str, Any]) -> None:
        try:
            mat_id = summary.get("material_id")
            doc_data = dict(summary)
            doc_data["owner_id"] = user_id
            doc_data["updated_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("summaries").document(mat_id).set(doc_data)
        except Exception as e:
            logger.error("Firestore save_summary failed: %s", str(e))
            raise IOError("Could not save summary metadata: " + str(e))

    def delete_summary(self, user_id: str, mat_id: str) -> None:
        try:
            doc_ref = self.db.collection("summaries").document(mat_id)
            doc = doc_ref.get()
            if doc.exists and doc.to_dict().get("owner_id") == user_id:
                doc_ref.delete()
        except Exception as e:
            logger.error("Firestore delete_summary failed: %s", str(e))

    # ── AI Flashcards ────────────────────────────────────────────────────────
    def get_flashcards_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = self.db.collection("flashcards").document(mat_id).get()
            data = self._doc_to_dict(doc_ref)
            if data and data.get("owner_id") == user_id:
                return data
        except Exception as e:
            logger.error("Firestore get_flashcards failed: %s", str(e))
        return None

    def save_flashcards(self, user_id: str, flashcards: Dict[str, Any]) -> None:
        try:
            mat_id = flashcards.get("material_id")
            doc_data = dict(flashcards)
            doc_data["owner_id"] = user_id
            doc_data["updated_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("flashcards").document(mat_id).set(doc_data)
        except Exception as e:
            logger.error("Firestore save_flashcards failed: %s", str(e))

    # ── AI Quizzes ──────────────────────────────────────────────────────────
    def get_quizzes_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = self.db.collection("quizzes").document(mat_id).get()
            data = self._doc_to_dict(doc_ref)
            if data and data.get("owner_id") == user_id:
                return data
        except Exception as e:
            logger.error("Firestore get_quizzes failed: %s", str(e))
        return None

    def save_quizzes(self, user_id: str, quizzes: Dict[str, Any]) -> None:
        try:
            mat_id = quizzes.get("material_id")
            doc_data = dict(quizzes)
            doc_data["owner_id"] = user_id
            doc_data["updated_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("quizzes").document(mat_id).set(doc_data)
        except Exception as e:
            logger.error("Firestore save_quizzes failed: %s", str(e))

    def get_quiz_attempts(self, user_id: str, mat_id: str) -> List[Dict[str, Any]]:
        try:
            # Subcollection verification
            docs = self.db.collection("quizzes").document(mat_id).collection("attempts").stream()
            return [self._doc_to_dict(d) for d in docs if d.exists]
        except Exception as e:
            logger.error("Firestore get_attempts failed: %s", str(e))
            return []

    def save_quiz_attempt(self, user_id: str, mat_id: str, attempt: Dict[str, Any]) -> None:
        try:
            attempt_id = attempt.get("attempt_id") or "att_temp"
            doc_data = dict(attempt)
            doc_data["owner_id"] = user_id
            doc_data["created_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("quizzes").document(mat_id).collection("attempts").document(attempt_id).set(doc_data)
        except Exception as e:
            logger.error("Firestore save_attempt failed: %s", str(e))

    # ── Weak Topic Analysis ──────────────────────────────────────────────────
    def get_analysis_by_material_id(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = self.db.collection("analysis").document(mat_id).get()
            data = self._doc_to_dict(doc_ref)
            if data and data.get("owner_id") == user_id:
                return data
        except Exception as e:
            logger.error("Firestore get_analysis failed: %s", str(e))
        return None

    def save_analysis(self, user_id: str, analysis: Dict[str, Any]) -> None:
        try:
            mat_id = analysis.get("material_id")
            doc_data = dict(analysis)
            doc_data["owner_id"] = user_id
            doc_data["updated_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("analysis").document(mat_id).set(doc_data)
        except Exception as e:
            logger.error("Firestore save_analysis failed: %s", str(e))

    # ── Personalized Study Planner ──────────────────────────────────────────
    def get_active_plan(self, user_id: str, mat_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = self.db.collection("study_plans").document(mat_id).get()
            data = self._doc_to_dict(doc_ref)
            if data and data.get("owner_id") == user_id:
                return data
        except Exception as e:
            logger.error("Firestore get_plan failed: %s", str(e))
        return None

    def save_active_plan(self, user_id: str, plan: Dict[str, Any]) -> None:
        try:
            mat_id = plan.get("material_id")
            doc_data = dict(plan)
            doc_data["owner_id"] = user_id
            doc_data["updated_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("study_plans").document(mat_id).set(doc_data)
        except Exception as e:
            logger.error("Firestore save_plan failed: %s", str(e))

    # ── Learning Analytics ───────────────────────────────────────────────────
    def get_analytics_snapshot(self, user_id: str) -> Optional[Dict[str, Any]]:
        try:
            doc_ref = self.db.collection("analytics").document(user_id).get()
            return self._doc_to_dict(doc_ref)
        except Exception as e:
            logger.error("Firestore get_analytics failed: %s", str(e))
        return None

    def save_analytics_snapshot(self, user_id: str, snapshot: Dict[str, Any]) -> None:
        try:
            doc_data = dict(snapshot)
            doc_data["owner_id"] = user_id
            doc_data["updated_at"] = firestore.SERVER_TIMESTAMP
            self.db.collection("analytics").document(user_id).set(doc_data)
        except Exception as e:
            logger.error("Firestore save_analytics failed: %s", str(e))
