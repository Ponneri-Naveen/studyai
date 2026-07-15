"""
backend/tests/test_firebase_fallback.py — Pytest suite verifying RepositoryFactory driver selection logic and local JSON fallbacks
"""

import os
import pytest
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.repositories.repository_factory import RepositoryFactory
from services.repositories.json_repository import JSONRepository


def test_repository_factory_defaults_to_json():
    """
    Assert that RepositoryFactory correctly switches to local JSON Repository fallback when Firebase configurations are missing.
    """
    # Reset factory states
    RepositoryFactory._initialized = False
    RepositoryFactory._use_firebase = False
    RepositoryFactory._instance = None
    
    with patch("services.repositories.repository_factory.get_config") as mock_cfg:
        mock_val = MagicMock()
        mock_val.FIREBASE_PROJECT_ID = None
        mock_val.FIREBASE_CREDENTIALS_PATH = None
        mock_cfg.return_value = mock_val
        
        RepositoryFactory.initialize()
        
        assert RepositoryFactory._use_firebase is False
        repo = RepositoryFactory.get_repository()
        assert isinstance(repo, JSONRepository)


def test_repository_factory_firestore_initialization():
    """
    Verify that factory selects FirestoreRepository when credentials attributes are active.
    """
    RepositoryFactory._initialized = False
    RepositoryFactory._use_firebase = False
    RepositoryFactory._instance = None
    
    with patch("services.repositories.repository_factory.get_config") as mock_cfg:
        mock_val = MagicMock()
        mock_val.FIREBASE_PROJECT_ID = "mock_project_id"
        mock_val.FIREBASE_CREDENTIALS_PATH = "mock_credentials.json"
        mock_cfg.return_value = mock_val
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            
            with patch("firebase_admin.initialize_app") as mock_init:
                with patch("firebase_admin.credentials.Certificate") as mock_cert:
                    with patch("services.repositories.firestore_repository.FirestoreRepository") as mock_firestore_repo:
                        RepositoryFactory.initialize()
                        assert RepositoryFactory._use_firebase is True
