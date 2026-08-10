"""
KisanAI OS
Prediction Schemas
Version: 1.0.0

Future-compatible structured input and result for the AI Prediction
Engine. A real model will populate ``result``, ``confidence`` and
``model``; until then these stay ``None`` with
``status = MODEL_NOT_CONFIGURED`` so "no model" is never confused with
any real prediction. No local filesystem paths are ever exposed.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator

# Supported prediction types, matching data the system can actually
# provide today. Unknown types are rejected as invalid input.
PREDICTION_TYPES = ("crop_yield", "soil_analysis")


def _clean_optional(value):
    """Strip + collapse whitespace for an optional string field."""
    if value is None:
        return None
    text = " ".join(str(value).strip().split())
    return text or None


class SoilContext(BaseModel):
    """Optional soil information for a prediction request."""

    soil_type: Optional[str] = None
    ph: Optional[float] = Field(default=None, ge=0.0, le=14.0)
    moisture: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    nitrogen: Optional[int] = Field(default=None, ge=0)
    phosphorus: Optional[int] = Field(default=None, ge=0)
    potassium: Optional[int] = Field(default=None, ge=0)

    @field_validator("soil_type", mode="before")
    @classmethod
    def _clean_soil_type(cls, value):
        return _clean_optional(value)


class WeatherContext(BaseModel):
    """Optional weather information for a prediction request."""

    temperature: Optional[float] = None
    humidity: Optional[int] = Field(default=None, ge=0, le=100)
    condition: Optional[str] = None
    wind_speed: Optional[float] = Field(default=None, ge=0.0)

    @field_validator("condition", mode="before")
    @classmethod
    def _clean_condition(cls, value):
        return _clean_optional(value)


class PredictionRequest(BaseModel):
    """Structured agricultural context for a prediction."""

    prediction_type: str
    farmer_id: Optional[int] = Field(default=None, ge=0)
    crop_id: Optional[int] = Field(default=None, ge=0)
    crop_name: Optional[str] = None
    soil: Optional[SoilContext] = None
    weather: Optional[WeatherContext] = None

    @field_validator("prediction_type")
    @classmethod
    def _check_prediction_type(cls, value):
        if value is None or not str(value).strip():
            raise ValueError("prediction_type is required")

        prediction_type = " ".join(str(value).strip().split())

        if prediction_type not in PREDICTION_TYPES:
            raise ValueError(
                "prediction_type must be one of: "
                + ", ".join(PREDICTION_TYPES)
            )

        return prediction_type

    @field_validator("crop_name", mode="before")
    @classmethod
    def _clean_crop_name(cls, value):
        return _clean_optional(value)


class PredictionOut(BaseModel):
    """Structured prediction-engine response."""

    success: bool = True
    status: str
    prediction_type: str
    result: Optional[dict] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    metadata: Optional[dict] = None
    message: Optional[str] = ""
