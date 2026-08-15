"""
KisanAI OS
OTP Repository
Version: 1.0.0
"""

from datetime import datetime, timedelta

from sqlalchemy import select, update

from config.core.database import SessionLocal
from config.core.models.otp import OtpCode
from config.settings import settings


class OtpRepository:
    """OTP Repository"""

    def __init__(self, session=None):
        self.session = session or SessionLocal()

    def _commit(self):
        try:
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def add(self, otp: OtpCode):
        self.session.add(otp)
        self._commit()

    def get_latest_for(self, mobile, purpose):
        return self.session.scalar(
            select(OtpCode)
            .where(
                OtpCode.mobile == mobile,
                OtpCode.purpose == purpose,
            )
            .order_by(OtpCode.id.desc())
            .limit(1)
        )

    def count_recent(self, mobile, purpose=None):
        """Count OTP requests for the mobile within the request window."""
        window_start = (
            datetime.now()
            - timedelta(seconds=settings.OTP_REQUEST_WINDOW_SECONDS)
        ).strftime("%Y-%m-%d %H:%M:%S")

        statement = select(OtpCode).where(
            OtpCode.mobile == mobile,
            OtpCode.created_at >= window_start,
        )
        if purpose is not None:
            statement = statement.where(OtpCode.purpose == purpose)

        return len(list(self.session.scalars(statement)))

    def mark_attempt(self, otp: OtpCode):
        otp.attempts += 1
        self._commit()

    def mark_verified(self, otp: OtpCode):
        otp.verified = True
        self._commit()

    def close(self):
        self.session.close()
