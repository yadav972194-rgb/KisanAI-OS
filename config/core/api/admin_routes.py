"""
KisanAI OS
Admin API Routes
Version: 1.0.0

Admin Control & Farmer Support module.

Every route lives under ``/api/admin`` and requires an authenticated
admin bearer token. Shared capabilities require the admin role; delete
and member-management (super-admin) actions additionally require the
``users.super_admin`` flag. All sensitive mutations append an audit
record through AuditService.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from config.constants import ROLE_ADMIN
from config.core.api.auth import get_current_user, require_role
from config.core.database import get_db
from config.core.models.user import User
from config.core.schemas import (
    AdminMeOut,
    AuditListOut,
    ContactCreate,
    ContactListOut,
    ContactOut,
    CropUpdate,
    DeletePreviewOut,
    FarmerListOut,
    FarmerProfileOut,
    FarmerUpdate,
    FeedbackCreate,
    FeedbackListOut,
    FeedbackOut,
    FeedbackStatusUpdate,
    FeedbackUpdate,
    MessageOut,
    NotificationCreate,
    NotificationListOut,
    NotificationOut,
    SoilUpdate,
    SuperAdminRoleUpdate,
)
from config.core.services.admin_farmer_service import AdminFarmerService
from config.core.services.admin_user_service import AdminUserService
from config.core.services.audit_service import AuditService
from config.core.services.notification_service import NotificationService
from config.core.services.support_service import SupportService


router = APIRouter(prefix="/api/admin", tags=["admin"])

# Shared admin capability: role admin (super-admin accounts keep role admin).
admin_required = require_role(ROLE_ADMIN)


def require_super_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency: admin role PLUS the super-admin escalation flag."""
    if current_user.role != ROLE_ADMIN or not current_user.super_admin:
        raise HTTPException(
            status_code=403,
            detail={
                "success": False,
                "message": "Insufficient permissions",
            },
        )
    return current_user


def _to_http(result):
    """Translate a failed service dict into a proper HTTP exception."""
    message = result.get("message", "Request failed")
    lowered = message.lower()

    if "not found" in lowered:
        status_code, code = 404, "NOT_FOUND"
    elif "already" in lowered:
        status_code, code = 409, "CONFLICT"
    elif any(
        token in lowered
        for token in ("yourself", "own privileges", "last active super")
    ):
        status_code, code = 403, "FORBIDDEN"
    elif "cannot" in lowered or "invalid" in lowered:
        status_code, code = 422, "VALIDATION_ERROR"
    else:
        status_code, code = 400, "VALIDATION_ERROR"

    raise HTTPException(
        status_code=status_code,
        detail={"success": False, "message": message, "code": code},
    )


def _ok(result):
    """Unwrap a service dict: raise on failure, return payload on success."""
    if isinstance(result, dict) and result.get("success") is False:
        _to_http(result)
    return result.get("data", result)


def _linked_user_id(db, farmer_id):
    """Return the user_id linked to a farmer account, or a failure dict."""
    profile = AdminFarmerService(db).get_farmer_profile(farmer_id)
    if profile["success"] is False:
        return None, profile
    return profile["farmer"]["user_id"], None


# ==========================================================
# Admin identity
# ==========================================================

@router.get("/me", response_model=AdminMeOut)
def admin_me(
    current_user: User = Depends(admin_required),
):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "super_admin": bool(current_user.super_admin),
    }


# ==========================================================
# Farmer directory & profile corrections
# ==========================================================

@router.get("/farmers", response_model=FarmerListOut)
def search_farmers(
    state: str | None = Query(default=None),
    district: str | None = Query(default=None),
    block: str | None = Query(default=None),
    q: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_required),
):
    return AdminFarmerService(db).search_farmers(
        {
            "state": state,
            "district": district,
            "block": block,
            "q": q,
            "page": page,
            "size": size,
        }
    )


@router.get("/farmers/{farmer_id}", response_model=FarmerProfileOut)
def get_farmer_profile(
    farmer_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_required),
):
    return _ok(AdminFarmerService(db).get_farmer_profile(farmer_id))


@router.put("/farmers/{farmer_id}", response_model=MessageOut)
def update_farmer_profile(
    farmer_id: int,
    data: FarmerUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    return _ok(
        AdminFarmerService(db).update_farmer(
            admin.id,
            farmer_id,
            data.model_dump(),
        )
    )


@router.put("/farmers/{farmer_id}/crops/{crop_id}", response_model=MessageOut)
def update_farmer_crop(
    farmer_id: int,
    crop_id: int,
    data: CropUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    return _ok(
        AdminFarmerService(db).update_crop(
            admin.id,
            farmer_id,
            crop_id,
            data.model_dump(),
        )
    )


@router.put("/farmers/{farmer_id}/soils/{soil_id}", response_model=MessageOut)
def update_farmer_soil(
    farmer_id: int,
    soil_id: int,
    data: SoilUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    return _ok(
        AdminFarmerService(db).update_soil(
            admin.id,
            farmer_id,
            soil_id,
            data.model_dump(),
        )
    )


# ==========================================================
# Farmer problems & contacts
# ==========================================================

@router.get("/farmers/{farmer_id}/problems", response_model=FeedbackListOut)
def list_farmer_problems(
    farmer_id: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_required),
):
    result = SupportService(db).list_by_farmer(farmer_id)
    if result["success"] is False:
        _to_http(result)
    result.setdefault("page", page)
    result.setdefault("size", size)
    return result


@router.post("/farmers/{farmer_id}/problems", response_model=FeedbackOut)
def create_farmer_problem(
    farmer_id: int,
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    payload = data.model_dump()
    payload["farmer_id"] = farmer_id
    return _ok(SupportService(db).create_feedback(admin.id, payload))


@router.get("/farmers/{farmer_id}/contacts", response_model=ContactListOut)
def list_farmer_contacts(
    farmer_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_required),
):
    result = SupportService(db).list_contacts(farmer_id)
    if result["success"] is False:
        _to_http(result)
    result.setdefault("page", 1)
    result.setdefault("size", len(result.get("items", [])) or 1)
    return result


@router.post("/farmers/{farmer_id}/contacts", response_model=ContactOut)
def record_farmer_contact(
    farmer_id: int,
    data: ContactCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    payload = data.model_dump()
    payload["farmer_id"] = farmer_id
    return _ok(SupportService(db).record_contact(admin.id, payload))


# ==========================================================
# Account deactivate / restore / delete (farmer scoped)
# ==========================================================

@router.post("/farmers/{farmer_id}/deactivate", response_model=MessageOut)
def deactivate_farmer_account(
    farmer_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    user_id, error = _linked_user_id(db, farmer_id)
    if error is not None:
        _to_http(error)
    if user_id is None:
        _to_http(
            {
                "success": False,
                "message": "Farmer has no linked user account",
            }
        )
    return _ok(AdminUserService(db).deactivate_user(admin.id, user_id))


@router.post("/farmers/{farmer_id}/restore", response_model=MessageOut)
def restore_farmer_account(
    farmer_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    user_id, error = _linked_user_id(db, farmer_id)
    if error is not None:
        _to_http(error)
    if user_id is None:
        _to_http(
            {
                "success": False,
                "message": "Farmer has no linked user account",
            }
        )
    return _ok(AdminUserService(db).restore_user(admin.id, user_id))


@router.post("/farmers/{farmer_id}/delete/preview", response_model=DeletePreviewOut)
def farmer_delete_preview(
    farmer_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_super_admin),
):
    return _ok(AdminFarmerService(db).delete_preview(farmer_id))


@router.delete("/farmers/{farmer_id}", response_model=MessageOut)
def delete_farmer(
    farmer_id: int,
    confirm: bool = Query(default=False),
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    return _ok(
        AdminFarmerService(db).delete_farmer(admin.id, farmer_id, confirm)
    )


# ==========================================================
# Problems / feedback (global workflow)
# ==========================================================

@router.get("/problems", response_model=FeedbackListOut)
def list_feedback(
    status: str | None = Query(default=None),
    priority: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_required),
):
    return _ok(
        SupportService(db).list_feedback(
            status=status,
            priority=priority,
            page=page,
            size=size,
        )
    )


@router.get("/problems/{feedback_id}", response_model=FeedbackOut)
def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_required),
):
    return _ok(SupportService(db).get_feedback(feedback_id))


@router.post("/problems", response_model=FeedbackOut)
def create_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    return _ok(SupportService(db).create_feedback(admin.id, data.model_dump()))


@router.put("/problems/{feedback_id}", response_model=FeedbackOut)
def update_feedback(
    feedback_id: int,
    data: FeedbackUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    return _ok(
        SupportService(db).update_feedback(
            admin.id,
            feedback_id,
            data.model_dump(exclude_unset=True),
        )
    )


@router.patch("/problems/{feedback_id}/status", response_model=FeedbackOut)
def transition_feedback_status(
    feedback_id: int,
    data: FeedbackStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    return _ok(
        SupportService(db).transition_feedback(
            admin.id,
            feedback_id,
            data.status,
        )
    )


# ==========================================================
# Notifications / AI reports / alerts
# ==========================================================

@router.get("/notifications", response_model=NotificationListOut)
def list_notifications(
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    user_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_required),
):
    return _ok(
        NotificationService(db).list(
            category=category,
            status=status,
            user_id=user_id,
            page=page,
            size=size,
        )
    )


@router.post("/notifications", response_model=NotificationOut)
def create_notification(
    data: NotificationCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    return _ok(
        NotificationService(db).create(admin.id, data.model_dump())
    )


@router.post("/notifications/{notification_id}/deliver", response_model=MessageOut)
def deliver_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    result = NotificationService(db).mark_delivered(admin.id, notification_id)
    if isinstance(result, dict) and result.get("success") is False:
        _to_http(result)
    return {
        "success": True,
        "message": "Notification marked as delivered",
    }


# ==========================================================
# Audit trail (read-only)
# ==========================================================

@router.get("/audit", response_model=AuditListOut)
def list_audit(
    entity_type: str | None = Query(default=None),
    entity_id: int | None = Query(default=None),
    actor_user_id: int | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _admin: User = Depends(admin_required),
):
    return AuditService(db).list(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor_user_id,
        page=page,
        size=size,
    )


# ==========================================================
# User account controls (admin + super-admin)
# ==========================================================

@router.post("/users/{user_id}/super-admin", response_model=MessageOut)
def set_super_admin(
    user_id: int,
    data: SuperAdminRoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    return _ok(
        AdminUserService(db).set_super_admin(
            admin.id,
            user_id,
            data.super_admin,
        )
    )


@router.post("/users/{user_id}/deactivate", response_model=MessageOut)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    return _ok(AdminUserService(db).deactivate_user(admin.id, user_id))


@router.post("/users/{user_id}/restore", response_model=MessageOut)
def restore_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_required),
):
    return _ok(AdminUserService(db).restore_user(admin.id, user_id))


@router.delete("/users/{user_id}", response_model=MessageOut)
def delete_user(
    user_id: int,
    confirm: bool = Query(default=False),
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    return _ok(
        AdminUserService(db).delete_user(
            admin.id,
            user_id,
            confirm=confirm,
        )
    )