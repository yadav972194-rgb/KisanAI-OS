"""
KisanAI OS
Upload Schemas
"""

from typing import Optional

from pydantic import BaseModel


class UploadOut(BaseModel):
    """Safe image upload response - never exposes local filesystem paths."""

    success: bool = True
    message: str = ""
    filename: Optional[str] = None
