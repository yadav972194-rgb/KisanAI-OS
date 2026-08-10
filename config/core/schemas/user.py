"""
KisanAI OS
User Auth Schemas
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from config.constants import ROLE_EXPERT, ROLE_FARMER

INDIAN_MOBILE_PATTERN = r"^[6-9]\d{9}$"

ADMIN_MANAGED_ROLES = {ROLE_FARMER, ROLE_EXPERT}


class UserCreate(BaseModel):
    username: str
    password: str = Field(min_length=6)
    full_name: Optional[str] = None
    mobile: Optional[str] = Field(default=None, pattern=INDIAN_MOBILE_PATTERN)
    role: str = ROLE_FARMER


class UserOut(BaseModel):
    """User response - never contains the password hash."""

    id: int
    username: str
    full_name: Optional[str] = None
    mobile: Optional[str] = None
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
