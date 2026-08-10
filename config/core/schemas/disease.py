"""
KisanAI OS
Disease Schemas
Version: 5.4.0
"""

from typing import Optional

from pydantic import BaseModel, field_validator

SEVERITY_VALUES = {"Low", "Medium", "High"}


def _validate_severity(v):
    if v is None or not str(v).strip():
        raise ValueError("severity is required")

    title = str(v).strip().title()

    if title not in SEVERITY_VALUES:
        raise ValueError("severity must be Low, Medium or High")

    return title


def _clean_required(value):
    """Strip + collapse whitespace; reject blank input."""
    if value is None:
        raise ValueError("value is required")

    text = " ".join(str(value).strip().split())

    if not text:
        raise ValueError("value cannot be blank")

    return text


class DiseaseCreate(BaseModel):
    disease_id: Optional[int] = None
    crop_id: Optional[int] = None
    crop_name: str
    disease_name: str
    symptoms: str
    solution: str
    severity: str

    @field_validator("severity")
    @classmethod
    def _check_severity(cls, v):
        return _validate_severity(v)

    @field_validator("crop_name", "disease_name", "symptoms", "solution", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)


class DiseaseUpdate(BaseModel):
    crop_id: Optional[int] = None
    crop_name: str
    disease_name: str
    symptoms: str
    solution: str
    severity: str

    @field_validator("severity")
    @classmethod
    def _check_severity(cls, v):
        return _validate_severity(v)

    @field_validator("crop_name", "disease_name", "symptoms", "solution", mode="before")
    @classmethod
    def _normalize_text(cls, value):
        return _clean_required(value)


class DiseaseOut(BaseModel):
    disease_id: int
    crop_id: Optional[int] = None
    crop_name: str
    disease_name: str
    symptoms: str
    solution: str
    severity: str
    created_at: str
