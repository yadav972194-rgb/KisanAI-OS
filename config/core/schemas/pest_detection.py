"""
KisanAI OS
Pest Detection Schemas
Version: 1.0.0

Future-compatible prediction result. A real model will populate
``pest_name``, ``confidence`` and ``model``; until then these stay
``None`` with ``status = MODEL_NOT_CONFIGURED`` so "no model" is never
confused with "no pest" or "pest detected". No local filesystem paths
are ever exposed.
"""

from typing import Optional

from pydantic import BaseModel


class PestDetectionOut(BaseModel):
    """Structured pest-detection response."""

    success: bool = True
    status: str
    crop: Optional[str] = None
    pest_name: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    message: Optional[str] = ""
