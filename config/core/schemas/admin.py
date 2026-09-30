"""
KisanAI OS
Admin Schemas (Admin Control & Farmer Support module)
"""

from typing import Optional

from pydantic import BaseModel, Field

from config.core.schemas.crop import CropOut
from config.core.schemas.farmer import FarmerOut
from config.core.schemas.soil import SoilOut
from config.core.schemas.support import ContactOut, FeedbackOut


class AdminMeOut(BaseModel):
    """Current admin identity (role + super-admin flag)."""

    id: int
    username: str
    role: str
    super_admin: bool


class FarmerSearchParams(BaseModel):
    """Filters accepted by the admin farmer directory.

    ``q`` searches name / mobile / village; location filters are exact
    matches on the farmer's stored location fields.
    """

    state: Optional[str] = None
    district: Optional[str] = None
    block: Optional[str] = None
    q: Optional[str] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class FarmerListOut(BaseModel):
    items: list[FarmerOut]
    total: int
    page: int
    size: int


class FarmerProfileOut(BaseModel):
    farmer: FarmerOut
    soils: list[SoilOut]
    contacts: list[ContactOut]
    feedback: list[FeedbackOut]


class DeletePreviewOut(BaseModel):
    """Affected-record summary shown before a confirmed farmer deletion."""

    farmer_id: int
    name: str
    crops: int
    soils: int
    feedback: int
    contacts: int
    notifications: int


class SuperAdminRoleUpdate(BaseModel):
    """Toggle the super-admin escalation flag on a user account."""

    super_admin: bool = True


class AuditOut(BaseModel):
    audit_id: int
    actor_user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[dict] = None
    created_at: str


class AuditListOut(BaseModel):
    items: list[AuditOut]
    total: int
    page: int
    size: int


class NotificationCreate(BaseModel):
    """Create an admin notification / AI-report / alert record."""

    category: str
    title: str
    message: str
    user_id: Optional[int] = None
    farmer_id: Optional[int] = None


class NotificationOut(BaseModel):
    notification_id: int
    user_id: Optional[int] = None
    farmer_id: Optional[int] = None
    category: str
    title: str
    message: str
    status: str
    created_by: Optional[int] = None
    created_at: str
    delivered_at: Optional[str] = None


class NotificationListOut(BaseModel):
    items: list[NotificationOut]
    total: int
    page: int
    size: int