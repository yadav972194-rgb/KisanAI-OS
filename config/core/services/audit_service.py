"""
KisanAI OS
Audit Service
Version: 1.0.0

Admin Control & Farmer Support module. Appends immutable audit records
for significant admin mutations. Written inside the caller's database
session so the audit row commits atomically with the mutation it
describes.
"""

from datetime import datetime
import json

from config.core.models.admin_audit_log import AdminAuditLog
from config.core.repositories.audit_repository import AuditRepository


class AuditService:
    """Audit Service (append-only)."""

    def __init__(self, session=None):
        self.repo = AuditRepository(session)

    def record(self, actor_user_id, action, entity_type, entity_id=None,
               details=None):
        """Persist one audit row. ``details`` is a JSON-serialisable dict."""
        details_json = None
        if details is not None:
            details_json = json.dumps(details, ensure_ascii=False)

        audit = AdminAuditLog(
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details_json,
        )
        self.repo.add(audit)

        return {
            "success": True,
            "message": "Audit logged",
            "audit": audit.to_dict(),
        }

    def list(self, entity_type=None, entity_id=None, actor_user_id=None,
             page=1, size=20):
        """Read the audit trail. Only filters/reads - never writes."""
        rows = self.repo.list(
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            page=page,
            size=size,
        )
        total = self.repo.count(
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
        )
        return {
            "items": [self._out(row) for row in rows],
            "total": total,
            "page": page,
            "size": size,
        }

    def _out(self, row):
        item = row.to_dict()
        details = row.details
        if details:
            try:
                item["details"] = json.loads(details)
            except (TypeError, ValueError):
                item["details"] = details
        return item

    def close(self):
        self.repo.close()