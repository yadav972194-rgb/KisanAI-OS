"""
KisanAI OS
User Auth Schemas
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from config.constants import ROLE_EXPERT, ROLE_FARMER

INDIAN_MOBILE_PATTERN = r"^[6-9]\d{9}$"

ADMIN_MANAGED_ROLES = {ROLE_FARMER, ROLE_EXPERT}

OTP_PURPOSES = {
    "register",
    "forgot_username",
    "forgot_password",
}


def _clean_mobile(value):
    return str(value or "").strip()


class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    mobile: Optional[str] = Field(default=None, pattern=INDIAN_MOBILE_PATTERN)
    role: str = ROLE_FARMER

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        if value is None:
            return None
        return _clean_mobile(value)


class OtpRequest(BaseModel):
    """Request an OTP for a mobile number and purpose."""

    mobile: str = Field(pattern=INDIAN_MOBILE_PATTERN)
    purpose: str

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        return _clean_mobile(value)

    @field_validator("purpose")
    @classmethod
    def _check_purpose(cls, value):
        text = str(value or "").strip().lower()
        if text not in OTP_PURPOSES:
            raise ValueError("purpose must be register, forgot_username or forgot_password")
        return text


class OtpVerify(BaseModel):
    """Verify an OTP for a mobile number and purpose."""

    mobile: str = Field(pattern=INDIAN_MOBILE_PATTERN)
    purpose: str
    code: str = Field(min_length=4, max_length=10)

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        return _clean_mobile(value)

    @field_validator("purpose")
    @classmethod
    def _check_purpose(cls, value):
        text = str(value or "").strip().lower()
        if text not in OTP_PURPOSES:
            raise ValueError("purpose must be register, forgot_username or forgot_password")
        return text

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value):
        return str(value or "").strip()


class OtpRegister(BaseModel):
    """Register a new account using a verified mobile OTP."""

    mobile: str = Field(pattern=INDIAN_MOBILE_PATTERN)
    code: str = Field(min_length=4, max_length=10)
    username: str
    password: str = Field(min_length=6)
    full_name: Optional[str] = None

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        return _clean_mobile(value)

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value):
        return str(value or "").strip()


class ForgotUsernameRequest(BaseModel):
    """Recover the username for a verified mobile number."""

    mobile: str = Field(pattern=INDIAN_MOBILE_PATTERN)
    code: str = Field(min_length=4, max_length=10)

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        return _clean_mobile(value)

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value):
        return str(value or "").strip()


class ResetPasswordRequest(BaseModel):
    """Reset the password using a verified mobile OTP."""

    mobile: str = Field(pattern=INDIAN_MOBILE_PATTERN)
    code: str = Field(min_length=4, max_length=10)
    new_password: str = Field(min_length=6)

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        return _clean_mobile(value)

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value):
        return str(value or "").strip()


class OtpRequestOut(BaseModel):
    """OTP request response. ``dev_otp`` is only populated in mock mode."""

    success: bool
    message: str
    ttl_seconds: Optional[int] = None
    dev_otp: Optional[str] = None


class UsernameOut(BaseModel):
    """Forgot-username response (mobile OTP verified)."""

    success: bool
    message: str
    username: Optional[str] = None


class UserOut(BaseModel):
    """User response - never contains the password hash."""

    id: int
    username: str
    full_name: Optional[str] = None
    mobile: Optional[str] = None
    mobile_verified: bool = False
    role: str
    is_active: bool
    created_at: str


class UserRoleUpdate(BaseModel):
    """Admin-managed role assignment (Phase 5.9 Expert Role Activation).

    Only farmer and expert are assignable via the API; the admin role
    remains bootstrap-only so an API compromise cannot escalate to admin.
    """

    role: str

    @field_validator("role", mode="before")
    @classmethod
    def _check_role(cls, value):
        text = str(value).strip().lower()
        if text not in ADMIN_MANAGED_ROLES:
            raise ValueError("role must be farmer or expert")
        return text


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
