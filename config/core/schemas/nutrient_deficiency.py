"""
KisanAI OS
Nutrient Deficiency Detection Schemas
Version: 1.0.0

Future-compatible prediction result. A real model will populate
``deficiency_name``, ``confidence`` and ``model``; until then these
stay ``None`` with ``status = MODEL_NOT_CONFIGURED`` so "no model" is
never confused with "no deficiency" or "deficiency detected". No local
filesystem paths are ever exposed.
"""

from typing import Optional

from pydantic import BaseModel


class NutrientDeficiencyOut(BaseModel):
    """Structured nutrient-deficiency detection response."""

    success: bool = True
    status: str
    crop: Optional[str] = None
    deficiency_name: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    message: Optional[str] = ""
