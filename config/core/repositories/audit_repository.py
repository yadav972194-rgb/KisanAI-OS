"""
KisanAI OS
Admin Audit Log Repository
Version: 1.0.0

Append-only repository: only ``add`` and query methods are exposed.
There is deliberately no update/delete path - audit rows are immutable
evidence of admin mutations.
"""

from sqlalchemy import func, select

from config.core.database import SessionLocal
from config.core.models.admin_audit_log import AdminAuditLog


class AuditRepository:
    """Admin Audit Log Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def add(self, audit: AdminAuditLog):
        self.session.add(audit)
        self._commit()
        return audit

    def list(self, entity_type=None, entity_id=None, actor_user_id=None,
             page=1, size=20):
        statement = select(AdminAuditLog)
        if entity_type:
            statement = statement.where(AdminAuditLog.entity_type == entity_type)
        if entity_id is not None:
            statement = statement.where(AdminAuditLog.entity_id == entity_id)
        if actor_user_id is not None:
            statement = statement.where(
                AdminAuditLog.actor_user_id == actor_user_id
            )
        statement = (
            statement.order_by(AdminAuditLog.audit_id.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        return list(self.session.scalars(statement))

    def count(self, entity_type=None, entity_id=None, actor_user_id=None):
        statement = select(func.count(AdminAuditLog.audit_id))
        if entity_type:
            statement = statement.where(AdminAuditLog.entity_type == entity_type)
        if entity_id is not None:
            statement = statement.where(AdminAuditLog.entity_id == entity_id)
        if actor_user_id is not None:
            statement = statement.where(
                AdminAuditLog.actor_user_id == actor_user_id
            )
        return self.session.scalar(statement) or 0

    def close(self):
        self.session.close()