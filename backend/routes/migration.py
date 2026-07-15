"""
backend/routes/migration.py — JSON-to-Firestore database registry migration controllers endpoints
"""

import logging
from flask import Blueprint, jsonify

from services.repositories.repository_factory import RepositoryFactory
from services.repositories.json_repository import JSONRepository

logger = logging.getLogger(__name__)

migration_bp = Blueprint("migration", __name__)


@migration_bp.route("/start", methods=["POST"])
def start_db_migration():
    """
    POST /api/v1/migration/start
    Migrate local registry documents to Firestore collections checks.
    """
    try:
        RepositoryFactory.initialize()
        if not RepositoryFactory._use_firebase:
            return jsonify({"error": "Migration skipped. Firebase backend config profiles are disabled."}), 400
            
        json_repo = JSONRepository()
        firestore_repo = RepositoryFactory.get_repository()
        
        # We use a mock user ID for migration transfers
        migration_user_id = "migration_sync_user"
        
        local_materials = json_repo.get_all_materials(migration_user_id)
        migrated = 0
        skipped = 0
        
        for mat in local_materials:
            mat_id = mat.get("id")
            checksum = mat.get("md5_checksum")
            
            # Check if exists in firestore
            exists = False
            try:
                # Direct check by document ID
                existing = firestore_repo.get_material_by_id(migration_user_id, mat_id)
                if existing:
                    exists = True
            except Exception:
                pass
                
            if exists:
                skipped += 1
            else:
                firestore_repo.save_material(migration_user_id, mat)
                migrated += 1
                
        return jsonify({
            "status": "success",
            "migrated_materials_count": migrated,
            "skipped_materials_count": skipped
        }), 200
    except Exception as e:
        logger.error("Migration task crashed: %s", str(e), exc_info=True)
        return jsonify({"error": "Migration failed: " + str(e)}), 500
