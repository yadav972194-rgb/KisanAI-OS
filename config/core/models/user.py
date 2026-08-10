"""
KisanAI OS
User Model
Version: 1.0.0

Authentication / account model (Phase 3).
"""

from datetime import datetime

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100))
    mobile: Mapped[str] = mapped_column(String(15))
    role: Mapped[str] = mapped_column(String(20), default="farmer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[str] = mapped_column(String(19), default=_now)

    def to_dict(self):
        """Public representation - password hash is never exposed."""
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "mobile": self.mobile,
            "role": self.role,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }
