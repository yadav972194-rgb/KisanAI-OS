"""
KisanAI OS
Soil Schemas
Version: 5.3.0
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


class SoilCreate(BaseModel):
    soil_id: Optional[int] = None
    farmer_id: Optional[int] = None
    soil_type: str
    ph: float = Field(ge=0.0, le=14.0)
    moisture: float = Field(ge=0.0, le=100.0)
    nitrogen: int = Field(ge=0)
    phosphorus: int = Field(ge=0)
    potassium: int = Field(ge=0)

    @field_validator("soil_type", mode="before")
    @classmethod
    def _normalize_soil_type(cls, value):
        return _clean_required(value)


class SoilUpdate(BaseModel):
    farmer_id: Optional[int] = None
    soil_type: str
    ph: float = Field(ge=0.0, le=14.0)
    moisture: float = Field(ge=0.0, le=100.0)
    nitrogen: int = Field(ge=0)
    phosphorus: int = Field(ge=0)
    potassium: int = Field(ge=0)

    @field_validator("soil_type", mode="before")
    @classmethod
    def _normalize_soil_type(cls, value):
        return _clean_required(value)


class SoilOut(BaseModel):
    soil_id: int
    farmer_id: Optional[int] = None
    soil_type: str
    ph: float
    moisture: float
    nitrogen: int
    phosphorus: int
    potassium: int
    created_at: str
