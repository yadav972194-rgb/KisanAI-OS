"""
KisanAI OS
Weed Detection Schemas
Version: 1.0.0

Future-compatible prediction result. A real model will populate
``weed_name``, ``confidence`` and ``model``; until then these stay
``None`` with ``status = MODEL_NOT_CONFIGURED`` so "no model" is never
confused with "no weed" or "weed detected". No local filesystem paths
are ever exposed.
"""

from typing import Optional

from pydantic import BaseModel


class WeedDetectionOut(BaseModel):
    """Structured weed-detection response."""

    success: bool = True
    status: str
    crop: Optional[str] = None
    weed_name: Optional[str] = None
    confidence: Optional[float] = None
    model: Optional[str] = None
    message: Optional[str] = ""
