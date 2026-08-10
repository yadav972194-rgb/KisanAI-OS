"""
KisanAI OS
Common Response Schemas
"""

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class MessageOut(BaseModel):
    """Generic success message response."""

    success: bool = True
    message: str = ""


class ErrorOut(BaseModel):
    """Generic error response body."""

    success: bool = False
    message: str = ""


class ApiResponse(BaseModel, Generic[T]):
    """Standard envelope response wrapper."""

    success: bool = True
    message: str = ""
    data: Optional[T] = None
