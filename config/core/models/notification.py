"""
KisanAI OS
Admin Notification Record Model
Version: 1.0.0

Admin Control & Farmer Support module. Notifications / AI-report / alert
records created by an admin for a farmer or user account. ``status``
tracks delivery state (new -> delivered; a record can be dismissed).
Delivery is a recorded flag - no fake SMS/push transport is simulated.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Notification(Base):
    """Admin-created notification / AI-report record."""

    __tablename__ = "notifications"

    notification_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
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
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(150), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new")
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[str] = mapped_column(String(19), default=_now)
    delivered_at: Mapped[str | None] = mapped_column(String(19), nullable=True)

    def to_dict(self):
        return {
            "notification_id": self.notification_id,
            "user_id": self.user_id,
            "farmer_id": self.farmer_id,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
        }