"""
KisanAI OS
OTP Service
Version: 1.0.0

One-time-password issuance and verification (Phase 3 OTP auth).

Security posture:
  - Codes are random 6-digit values, hashed with bcrypt before storage.
  - Codes expire after OTP_TTL_SECONDS; each code allows a bounded
    number of verify attempts before it is invalidated.
  - Request rate limits are enforced both in-memory (sliding window per
    mobile) and via the database (requests within the window), so
    restarting the server cannot bypass throttling entirely.
  - OTP_MOCK=true (development only) returns ``dev_otp`` in the response
    so local flows and tests can complete. Production never echoes the
    code; it is delivered by the configured SMS provider only.
"""

import secrets
from datetime import datetime, timedelta

from config.core.api.auth import hash_password, verify_password
from config.core.logger import logger
from config.core.models.otp import OtpCode
from config.core.providers import get_otp_provider
from config.core.repositories.otp_repository import OtpRepository
from config.core.security import RateLimiter
from config.settings import settings

PURPOSE_REGISTER = "register"
PURPOSE_FORGOT_USERNAME = "forgot_username"
PURPOSE_FORGOT_PASSWORD = "forgot_password"

VALID_PURPOSES = {
    PURPOSE_REGISTER,
    PURPOSE_FORGOT_USERNAME,
    PURPOSE_FORGOT_PASSWORD,
}

# Shared limiter for OTP requests keyed by mobile number.
_otp_limiter = RateLimiter(
    settings.OTP_REQUEST_LIMIT,
    settings.OTP_REQUEST_WINDOW_SECONDS,
)


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _is_expired(expires_at: str) -> bool:
    try:
        parsed = datetime.strptime(expires_at, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return True
    return datetime.now() > parsed


class OtpService:
    """OTP Service"""

    def __init__(self, session=None, repo=None, provider=None):
        self.repo = repo or OtpRepository(session)
        self.provider = provider or get_otp_provider()

    # ==========================================================
    # Request
    # ==========================================================

    def request_otp(self, mobile, purpose):
        mobile = (mobile or "").strip()
        purpose = (purpose or "").strip().lower()

        if purpose not in VALID_PURPOSES:
            return {
                "success": False,
                "message": "Invalid OTP purpose",
            }

        # Rate limit: sliding window per mobile.
        if not _otp_limiter.allow("otp", mobile):
            return {
                "success": False,
                "message": "Too many OTP requests. Please try again later.",
            }

        # Rate limit: database-backed window (survives restarts).
        if self.repo.count_recent(mobile) >= settings.OTP_REQUEST_LIMIT:
            return {
                "success": False,
                "message": "Too many OTP requests. Please try again later.",
            }

        # Cooldown: a still-valid unverified code blocks re-requests.
        existing = self.repo.get_latest_for(mobile, purpose)
        if existing is not None and not existing.verified:
            if not _is_expired(existing.expires_at):
                return {
                    "success": False,
                    "message": (
                        "An OTP was already sent. Please wait before "
                        "requesting another."
                    ),
                }

        code = self._generate_code()
        expires_at = (
            datetime.now()
            + timedelta(seconds=settings.OTP_TTL_SECONDS)
        ).strftime("%Y-%m-%d %H:%M:%S")

        otp = OtpCode(
            mobile=mobile,
            purpose=purpose,
            code_hash=hash_password(code),
            expires_at=expires_at,
            attempts=0,
            verified=False,
            created_at=_now(),
        )

        try:
            self.provider.send(mobile, code, purpose)
        except Exception as error:  # provider gateway failure
            logger.warning(
                "OTP delivery failed for mobile=%s purpose=%s: %s",
                mobile,
                purpose,
                error,
            )
            return {
                "success": False,
                "message": "Unable to send OTP. Please try again later.",
            }

        self.repo.add(otp)

        response = {
            "success": True,
            "message": "OTP sent successfully",
            "ttl_seconds": settings.OTP_TTL_SECONDS,
        }

        # Development convenience only - production never echoes the code.
        if settings.OTP_MOCK:
            response["dev_otp"] = code
            response["message"] = (
                "OTP sent successfully (development mock)"
            )

        return response

    # ==========================================================
    # Verify
    # ==========================================================

    def verify_otp(self, mobile, purpose, code):
        mobile = (mobile or "").strip()
        purpose = (purpose or "").strip().lower()
        code = (code or "").strip()

        if not code:
            return {
                "success": False,
                "message": "OTP is required",
            }

        otp = self.repo.get_latest_for(mobile, purpose)

        if otp is None or otp.verified:
            return {
                "success": False,
                "message": "Invalid or expired OTP",
            }

        if _is_expired(otp.expires_at):
            return {
                "success": False,
                "message": "OTP has expired. Please request a new one.",
            }

        if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
            return {
                "success": False,
                "message": "Too many incorrect attempts. Please request a new OTP.",
            }

        self.repo.mark_attempt(otp)

        if not verify_password(code, otp.code_hash):
            return {
                "success": False,
                "message": "Invalid OTP",
            }

        self.repo.mark_verified(otp)

        return {
            "success": True,
            "message": "OTP verified successfully",
        }

    def _generate_code(self):
        """Generate a numeric OTP of the configured length."""
        length = max(4, settings.OTP_LENGTH)
        digits = "0123456789"
        return "".join(secrets.choice(digits) for _ in range(length))

    def close(self):
        self.repo.close()
