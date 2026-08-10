"""
KisanAI OS
Recommendation Schemas
Version: 1.0.0

Structured, future-compatible input and result for the Recommendation
Engine. All context fields are optional at the schema level so that
missing context reaches the engine, which returns a controlled
``INSUFFICIENT_DATA`` status identifying exactly what is missing -
missing data is never guessed. No local filesystem paths are exposed.
"""

from typing import Optional

from pydantic import BaseModel, field_validator

from config.core.schemas.prediction import SoilContext, WeatherContext

SEVERITY_VALUES = {"Low", "Medium", "High"}


def _clean_optional(value):
    """Strip + collapse whitespace for an optional string field."""
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return text or None


class DiseaseContext(BaseModel):
    """Optional disease context. If provided, severity must be valid.

    Absence of disease context is never interpreted as "healthy" or
    "no disease" - disease guidance is simply omitted.
    """

    name: Optional[str] = None
    severity: Optional[str] = None

    @field_validator("name", mode="before")
    @classmethod
    def _clean_name(cls, value):
        return _clean_optional(value)

    @field_validator("severity", mode="before")
    @classmethod
    def _check_severity(cls, value):
        if value is None:
            return None

        text = " ".join(str(value).strip().split())

        if text.title() not in SEVERITY_VALUES:
            raise ValueError("severity must be Low, Medium or High")

        return text.title()


class RecommendationRequest(BaseModel):
    """Verified agricultural context for a recommendation."""

    crop_name: Optional[str] = None
    soil: Optional[SoilContext] = None
    weather: Optional[WeatherContext] = None
    disease: Optional[DiseaseContext] = None

    @field_validator("crop_name", mode="before")
    @classmethod
    def _clean_crop_name(cls, value):
        return _clean_optional(value)


class RecommendationItem(BaseModel):
    """A single traceable recommendation."""

    category: str
    text: str
    reason: Optional[str] = None
    source: Optional[str] = None


class RecommendationOut(BaseModel):
    """Structured recommendation-engine response."""

    success: bool = True
    status: str
    recommendation_type: str
    recommendations: list[RecommendationItem] = []
    warnings: list[str] = []
    required_context: list[str]
    missing: list[str] = []
    reason: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    provider: Optional[str] = None
    message: Optional[str] = ""
