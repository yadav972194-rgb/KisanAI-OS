"""
KisanAI OS
OTP Model
Version: 1.0.0

One-time password requests (Phase 3 OTP authentication). Codes are
stored as bcrypt hashes, never plain text, and expire after a short
window. ``attempts`` bounds brute-force trials and ``verified`` marks a
used code so it cannot be replayed.
"""

from datetime import datetime

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from config.core.database import Base


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class OtpCode(Base):
    """OTP request model."""

    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    mobile: Mapped[str] = mapped_column(String(15), index=True, nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[str] = mapped_column(String(19), nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String(19), default=_now)
