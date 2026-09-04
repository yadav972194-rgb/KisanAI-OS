"""
KisanAI OS
Crop Water Stress Detection Schemas
Version: 1.0.0

Future-compatible prediction result. A real model will populate
``stress_level``, ``confidence`` and ``model``; until then these stay
``None`` with ``status = MODEL_NOT_CONFIGURED`` so "no model" is never
confused with "no stress" or "stress detected". No local filesystem
paths are ever exposed.
"""

from typing import Optional

from pydantic import BaseModel


class WaterStressOut(BaseModel):
    """Structured crop-water-stress detection response."""

    success: bool = True
    status: str
    crop: Optional[str] = None
    stress_level: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    message: Optional[str] = ""