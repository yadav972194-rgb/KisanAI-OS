"""
KisanAI OS
Farmer Schemas
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

from config.core.schemas.crop import CropOut

INDIAN_MOBILE_PATTERN = r"^[6-9]\d{9}$"

DEFAULT_COUNTRY = "India"


def _clean_required(value):
    """Strip + collapse whitespace; reject blank input."""
    if value is None:
        raise ValueError("value is required")

    text = " ".join(str(value).strip().split())

    if not text:
        raise ValueError("value cannot be blank")

    return text


def _clean_optional(value):
    """Strip + collapse whitespace; None stays None."""
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return text or None


class FarmerCreate(BaseModel):
    farmer_id: Optional[int] = None
    name: str
    mobile: str = Field(pattern=INDIAN_MOBILE_PATTERN)
    village: str
    block: Optional[str] = None
    district: str
    state: str
    country: str = DEFAULT_COUNTRY
    farm_size: Optional[float] = Field(default=None, ge=0)

    @field_validator("name", "village", "district", "state", "country", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)

    @field_validator("block", mode="before")
    @classmethod
    def _normalize_block(cls, value):
        return _clean_optional(value)

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        return str(value).strip()


class FarmerUpdate(BaseModel):
    name: str
    mobile: str = Field(pattern=INDIAN_MOBILE_PATTERN)
    village: str
    block: Optional[str] = None
    district: str
    state: str
    country: str = DEFAULT_COUNTRY
    farm_size: Optional[float] = Field(default=None, ge=0)

    @field_validator("name", "village", "district", "state", "country", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)

    @field_validator("block", mode="before")
    @classmethod
    def _normalize_block(cls, value):
        return _clean_optional(value)

    @field_validator("mobile", mode="before")
    @classmethod
    def _normalize_mobile(cls, value):
        return str(value).strip()


class FarmerOut(BaseModel):
    farmer_id: int
    user_id: Optional[int] = None
    name: str
    mobile: str
    village: str
    block: Optional[str] = None
    district: str
    state: str
    country: str = DEFAULT_COUNTRY
    farm_size: Optional[float] = None
    created_at: str
    crops: list[CropOut] = []


class MyFarmCreate(BaseModel):
    """Create the authenticated user's own farm record.

    Name and mobile are taken from the linked user account; the farmer
    supplies location and farm size.
    """

    farm_size: Optional[float] = Field(default=None, ge=0)
    village: str
    block: Optional[str] = None
    district: str
    state: str
    country: str = DEFAULT_COUNTRY

    @field_validator("village", "district", "state", "country", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)

    @field_validator("block", mode="before")
    @classmethod
    def _normalize_block(cls, value):
        return _clean_optional(value)


class MyFarmUpdate(BaseModel):
    """Update the authenticated user's own farm. All fields optional."""

    farm_size: Optional[float] = Field(default=None, ge=0)
    village: Optional[str] = None
    block: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

    @field_validator("village", "district", "state", "country", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        if value is None:
            return None
        return _clean_required(value)

    @field_validator("block", mode="before")
    @classmethod
    def _normalize_block(cls, value):
        return _clean_optional(value)
