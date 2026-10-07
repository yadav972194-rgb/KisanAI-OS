"""
KisanAI OS
Contact Record Model
Version: 1.0.0

Admin Control & Farmer Support module. Immutable-style record of every
outbound admin contact with a farmer (phone or email), including the
reason for the contact and the admin who performed it.
"""

from datetime import datetime

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ContactRecord(Base):
    """Outbound admin contact log for a farmer."""

    __tablename__ = "contact_records"

    contact_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    farmer_id: Mapped[int] = mapped_column(
        ForeignKey("farmers.farmer_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(10), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(150), nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[str] = mapped_column(String(19), default=_now)

    def to_dict(self):
        return {
            "contact_id": self.contact_id,
            "farmer_id": self.farmer_id,
            "channel": self.channel,
            "reason": self.reason,
            "note": self.note,
            "created_by": self.created_by,
            "created_at": self.created_at,
        }