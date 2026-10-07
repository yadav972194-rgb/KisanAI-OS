"""
KisanAI OS
Support Schemas (Admin Control & Farmer Support module)
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

FEEDBACK_STATUSES = {
    "new",
    "investigating",
    "contacted",
    "in_progress",
    "resolved",
    "closed",
}

FEEDBACK_PRIORITIES = {"low", "medium", "high"}

CONTACT_CHANNELS = {"phone", "email"}


def _clean_required(value):
    if value is None:
        raise ValueError("value is required")
    text = " ".join(str(value).strip().split())
    if not text:
        raise ValueError("value cannot be blank")
    return text


def _clean_optional(value):
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return text or None


class FeedbackCreate(BaseModel):
    """Create a farmer problem / feedback record (admin or farmer raised)."""

    farmer_id: Optional[int] = None
    subject: str
    description: str
    priority: str = "medium"

    @field_validator("subject", "description", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)

    @field_validator("priority", mode="before")
    @classmethod
    def _normalize_priority(cls, value):
        text = str(value or "").strip().lower()
        if text not in FEEDBACK_PRIORITIES:
            raise ValueError("priority must be low, medium or high")
        return text


class FeedbackUpdate(BaseModel):
    """Admin update of a feedback record (subject/description/priority)."""

    subject: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None

    @field_validator("subject", "description", mode="before")
    @classmethod
    def _normalize_optional_text(cls, value):
        if value is None:
            return None
        return _clean_required(value)

    @field_validator("priority", mode="before")
    @classmethod
    def _normalize_priority(cls, value):
        if value is None:
            return None
        text = str(value).strip().lower()
        if text not in FEEDBACK_PRIORITIES:
            raise ValueError("priority must be low, medium or high")
        return text


class FeedbackStatusUpdate(BaseModel):
    """Desired next workflow status for a feedback record."""

    status: str

    @field_validator("status", mode="before")
    @classmethod
    def _normalize_status(cls, value):
        text = str(value or "").strip().lower()
        if text not in FEEDBACK_STATUSES:
            raise ValueError("invalid feedback status")
        return text


class FeedbackOut(BaseModel):
    feedback_id: int
    user_id: Optional[int] = None
    farmer_id: Optional[int] = None
    subject: str
    description: str
    status: str
    priority: str
    created_at: str
    updated_at: Optional[str] = None


class FeedbackListOut(BaseModel):
    items: list[FeedbackOut]
    total: int
    page: int
    size: int


class ContactCreate(BaseModel):
    """Record an outbound admin contact (phone/email) with a farmer.

    ``farmer_id`` is optional in the body: path-scoped routes inject it
    from the URL (``/api/admin/farmers/{farmer_id}/contacts``).
    """

    farmer_id: Optional[int] = None
    channel: str
    reason: Optional[str] = None
    note: Optional[str] = None

    @field_validator("channel", mode="before")
    @classmethod
    def _normalize_channel(cls, value):
        text = str(value or "").strip().lower()
        if text not in CONTACT_CHANNELS:
            raise ValueError("channel must be phone or email")
        return text

    @field_validator("reason", "note", mode="before")
    @classmethod
    def _normalize_optional(cls, value):
        return _clean_optional(value)


class ContactOut(BaseModel):
    contact_id: int
    farmer_id: int
    channel: str
    reason: Optional[str] = None
    note: Optional[str] = None
    created_by: Optional[int] = None
    created_at: str


class ContactListOut(BaseModel):
    items: list[ContactOut]
    total: int
    page: int
    size: int