"""
KisanAI OS
Admin Audit Log Model
Version: 1.0.0

Append-only ledger of every significant admin mutation. Rows are never
updated or deleted by the application; the repository only exposes ``add``
and query methods. ``details`` stores a JSON snapshot (e.g. changed fields
or affected-record counts) for forensic inspection.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class AdminAuditLog(Base):
    """Immutable admin action audit record."""

    __tablename__ = "admin_audit_log"

    audit_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String(19), default=_now)

    def to_dict(self):
        return {
            "audit_id": self.audit_id,
            "actor_user_id": self.actor_user_id,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "details": self.details,
            "created_at": self.created_at,
        }