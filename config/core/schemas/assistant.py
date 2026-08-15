"""
KisanAI OS
Assistant / Intent Router Schemas
"""

from typing import Optional

from pydantic import BaseModel, Field


class AssistantRequest(BaseModel):
    """A free-text farmer query routed to a stable intent.

    ``text`` is the farmer's question (Hindi / Hinglish / English).
    ``soil`` and ``disease`` are optional verified context that the
    client may attach so CROP_STATUS / advice can use real data when
    it is available on the device.
    """

    text: str = Field(..., min_length=1)
    soil: Optional[dict] = None
    disease: Optional[dict] = None


class AssistantOut(BaseModel):
    """Honest, structured assistant response.

    ``intent`` is the routed intent code. ``status`` is one of
    ``OK``, ``INSUFFICIENT_DATA`` or ``UNAVAILABLE``. ``message`` is
    the Hindi answer built only from verified data or honest pointers;
    ``data`` carries the structured sections (farm, crops, weather,
    soil, disease, advice) when available.
    """

    intent: str
    status: str = "OK"
    message: str = ""
    data: Optional[dict] = None
