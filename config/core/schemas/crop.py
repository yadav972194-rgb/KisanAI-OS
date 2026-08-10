"""
KisanAI OS
Crop Schemas
Version: 5.2.0
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


def _clean_required(value):
    """Strip + collapse whitespace; reject blank input."""
    if value is None:
        raise ValueError("value is required")

    text = " ".join(str(value).strip().split())

    if not text:
        raise ValueError("value cannot be blank")

    return text


class CropCreate(BaseModel):
    crop_id: Optional[int] = None
    farmer_id: Optional[int] = None
    crop_name: str
    season: str
    duration_days: int = Field(gt=0)
    water_requirement: str

    @field_validator("crop_name", "season", "water_requirement", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)


class CropUpdate(BaseModel):
    farmer_id: Optional[int] = None
    crop_name: str
    season: str
    duration_days: int = Field(gt=0)
    water_requirement: str

    @field_validator("crop_name", "season", "water_requirement", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)


class CropOut(BaseModel):
    crop_id: int
    farmer_id: Optional[int] = None
    crop_name: str
    season: str
    duration_days: int
    water_requirement: str
    created_at: str
