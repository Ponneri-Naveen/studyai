"""
backend/services/repositories/repository_factory.py — Centralized repository driver initializer and switcher selector
"""

import os
import logging
import firebase_admin
from firebase_admin import credentials

from config import get_config
from services.repositories.json_repository import JSONRepository

logger = logging.getLogger(__name__)


class RepositoryFactory:
    """
    Manages initialization and selection of database driver implementations.
    Falls back to JSON file drivers on validation checks exceptions.
    """
    
    _instance = None
    _use_firebase = False
    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        """Loads SDK settings and determines active database engine driver."""
        if cls._initialized:
            return
            
        cfg = get_config()
        project_id = getattr(cfg, "FIREBASE_PROJECT_ID", None)
        cred_path = getattr(cfg, "FIREBASE_CREDENTIALS_PATH", None)
        
        # Check environment configurations parameters
        if project_id and cred_path and os.path.exists(cred_path):
            try:
                # Avoid multi-apps initialization crashes
                if not firebase_admin._apps:
                    cred_cert = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred_cert, {
                        'projectId': project_id
                    })
                cls._use_firebase = True
                logger.info("Firebase production environment Admin SDK initialized successfully.")
            except Exception as e:
                cls._use_firebase = False
                logger.warning("Firebase app initialization failed: %s. Falling back to JSON DB.", str(e))
        else:
            cls._use_firebase = False
            logger.info("Local development profile active. Swapping database engine to local JSON DB driver.")
            
        cls._initialized = True

    @classmethod
    def get_repository(cls):
        """Returns the appropriate StorageRepository instance."""
        cls.initialize()
        if cls._use_firebase:
            try:
                from services.repositories.firestore_repository import FirestoreRepository
                if cls._instance is None or not isinstance(cls._instance, FirestoreRepository):
                    cls._instance = FirestoreRepository()
                return cls._instance
            except Exception as e:
                logger.error("Failed to construct FirestoreRepository: %s. Swapping to JSON driver.", str(e))
                return JSONRepository()
        else:
            if cls._instance is None or not isinstance(cls._instance, JSONRepository):
                cls._instance = JSONRepository()
            return cls._instance
