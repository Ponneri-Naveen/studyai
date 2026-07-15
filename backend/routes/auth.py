"""
routes/auth.py — Authentication endpoints (stubs)

These endpoints will be connected to Firebase Auth in a later phase.
Currently they return placeholder responses so the frontend routing works.
"""

from flask import Blueprint, jsonify, request

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    POST /api/auth/register
    Body: { "name": str, "email": str, "password": str }
    ---
    TODO: Implement Firebase Auth registration.
    """
    return jsonify({
        "message": "register endpoint ready",
        "note": "Firebase Auth integration pending",
    }), 200


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    POST /api/auth/login
    Body: { "email": str, "password": str }
    ---
    TODO: Implement Firebase Auth login / token verification.
    """
    return jsonify({
        "message": "login endpoint ready",
        "note": "Firebase Auth integration pending",
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    POST /api/auth/logout
    ---
    TODO: Revoke Firebase session / token.
    """
    return jsonify({
        "message": "logout endpoint ready",
        "note": "Firebase Auth integration pending",
    }), 200
