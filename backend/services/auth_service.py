"""services/auth_service.py — Authentication business logic (stub)

This module will wrap Firebase Admin SDK calls once Firebase is configured.
"""

import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Handles authentication logic.

    TODO: Replace stub methods with Firebase Admin SDK calls.
    """

    @staticmethod
    def register_user(name: str, email: str, password: str) -> dict:
        """Create a new user account.

        Args:
            name: Display name for the user.
            email: User's email address.
            password: Plain-text password (Firebase will hash it).

        Returns:
            dict with user info or error message.
        """
        # TODO: firebase_admin.auth.create_user(...)
        logger.info("register_user stub called for %s", email)
        return {"uid": "stub-uid", "email": email, "name": name}

    @staticmethod
    def login_user(email: str, password: str) -> dict:
        """Verify credentials and return a session token.

        Args:
            email: User's email address.
            password: Plain-text password.

        Returns:
            dict with token or error message.
        """
        # TODO: Verify via Firebase REST API or client SDK token
        logger.info("login_user stub called for %s", email)
        return {"token": "stub-token", "email": email}

    @staticmethod
    def logout_user(uid: str) -> bool:
        """Revoke the user's session.

        Args:
            uid: Firebase user UID.

        Returns:
            True on success.
        """
        # TODO: firebase_admin.auth.revoke_refresh_tokens(uid)
        logger.info("logout_user stub called for uid %s", uid)
        return True
