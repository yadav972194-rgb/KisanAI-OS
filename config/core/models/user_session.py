"""
KisanAI OS
User Session Model
Version: 1.0.0

Server-side session ledger (Phase 3). Every issued JWT carries a unique
``jti`` recorded here. Logout and revocation flip ``revoked`` so a stolen
or logged-out token stops working before its natural expiry, giving real
server-side session control on top of the stateless JWT.
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class UserSession(Base):
    """Active login session ledger."""

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[str] = mapped_column(String(19), default=_now)
    expires_at: Mapped[str] = mapped_column(String(19), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    revoked_at: Mapped[str] = mapped_column(String(19), nullable=True)

    user: Mapped["User"] = relationship(back_populates="sessions")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "jti": self.jti,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "revoked_at": self.revoked_at,
        }
