"""
KisanAI OS
Farmer Schemas
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from config.core.schemas.crop import CropOut

INDIAN_MOBILE_PATTERN = r"^[6-9]\d{9}$"


def _clean_required(value):
    """Strip + collapse whitespace; reject blank input."""
    if value is None:
        raise ValueError("value is required")

    text = " ".join(str(value).strip().split())

    if not text:
        raise ValueError("value cannot be blank")

    return text


class FarmerCreate(BaseModel):
    farmer_id: Optional[int] = None
    name: str
    mobile: str = Field(pattern=INDIAN_MOBILE_PATTERN)
    village: str
    district: str
    state: str

    @field_validator("name", "village", "district", "state", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        return str(value).strip()


class FarmerUpdate(BaseModel):
    name: str
    mobile: str = Field(pattern=INDIAN_MOBILE_PATTERN)
    village: str
    district: str
    state: str

    @field_validator("name", "village", "district", "state", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        return str(value).strip()


class FarmerOut(BaseModel):
    farmer_id: int
    name: str
    mobile: str
    village: str
    district: str
    state: str
    created_at: str
    crops: list[CropOut] = []
