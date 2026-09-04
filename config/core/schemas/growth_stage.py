"""
KisanAI OS
Crop Growth Stage Detection Schemas
Version: 1.0.0

Future-compatible prediction result. A real model will populate
``growth_stage``, ``confidence`` and ``model``; until then these stay
``None`` with ``status = MODEL_NOT_CONFIGURED`` so "no model" is never
confused with "no stage" or "stage detected". No local filesystem paths
are ever exposed.
"""

from typing import Optional

from pydantic import BaseModel


class GrowthStageOut(BaseModel):
    """Structured crop-growth-stage detection response."""

    success: bool = True
    status: str
    crop: Optional[str] = None
    growth_stage: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    message: Optional[str] = ""
