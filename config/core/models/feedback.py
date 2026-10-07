"""
KisanAI OS
Farmer Problem / Feedback Model
Version: 1.0.0

Admin Control & Farmer Support module. Farmer problems and feedback are
tracked through a status lifecycle (new -> investigating -> contacted ->
in_progress -> resolved -> closed; closed can reopen to new). The row is
linked to an optional farmer record and to the user account that created
it or raised it.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Feedback(Base):
    """Farmer problem / feedback record."""

    __tablename__ = "feedback"

    feedback_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    farmer_id: Mapped[int | None] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    subject: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new")
    priority: Mapped[str] = mapped_column(String(10), default="medium")
    created_at: Mapped[str] = mapped_column(String(19), default=_now)
    updated_at: Mapped[str] = mapped_column(String(19), default=_now)

    def to_dict(self):
        return {
            "feedback_id": self.feedback_id,
            "user_id": self.user_id,
            "farmer_id": self.farmer_id,
            "subject": self.subject,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }