"""
KisanAI OS
Notification Service
Version: 1.0.0

Admin Control & Farmer Support module. Manages admin-created notification
/ AI-report / alert records. Delivery is a recorded status flag (new ->
delivered) on the stored record - no fake SMS/push transport is used.
"""

from datetime import datetime

from config.core.models.notification import Notification
from config.core.repositories.farmer_repository import FarmerRepository
from config.core.repositories.notification_repository import (
    NotificationRepository,
)
from config.core.repositories.user_repository import UserRepository
from config.core.services.audit_service import AuditService

NOTIFICATION_CATEGORIES = {
    "AI_REPORT",
    "ALERT",
    "ADVISORY",
    "SYSTEM",
}

NOTIFICATION_STATUSES = {"new", "delivered", "dismissed"}


def _clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


class NotificationService:
    """Notification Service"""

    def __init__(self, session=None):
        self.notice_repo = NotificationRepository(session)
        self.user_repo = UserRepository(session)
        self.farmer_repo = FarmerRepository(session)
        self.audit = AuditService(session)

    def list(self, category=None, status=None, user_id=None, page=1, size=20):
        if category:
            category = category.strip().upper()
            if category not in NOTIFICATION_CATEGORIES:
                return {
                    "success": False,
                    "message": f"Invalid category: {category}",
                }
        if status:
            status = status.strip().lower()
            if status not in NOTIFICATION_STATUSES:
                return {
                    "success": False,
                    "message": f"Invalid status: {status}",
                }

        rows = self.notice_repo.list_all(
            category=category or None,
            status=status or None,
            user_id=user_id,
            page=page,
            size=size,
        )
        total = self.notice_repo.count(
            category=category or None,
            status=status or None,
            user_id=user_id,
        )
        return {
            "success": True,
            "items": [row.to_dict() for row in rows],
            "total": total,
            "page": page,
            "size": size,
        }

    def create(self, actor_user_id, data):
        category = (data.get("category") or "").strip().upper()
        if category not in NOTIFICATION_CATEGORIES:
            return {
                "success": False,
                "message": (
                    "Category must be one of "
                    + ", ".join(sorted(NOTIFICATION_CATEGORIES))
                ),
            }

        title = _clean_text(data.get("title"))
        message = _clean_text(data.get("message"))
        if not title or not message:
            return {
                "success": False,
                "message": "Title and message are required",
            }

        user_id = data.get("user_id")
        if user_id is not None and self.user_repo.get_by_id(user_id) is None:
            return {
                "success": False,
                "message": "User Not Found",
            }

        farmer_id = data.get("farmer_id")
        if farmer_id is not None and self.farmer_repo.get_farmer_by_id(
            farmer_id
        ) is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        notification = Notification(
            user_id=user_id,
            farmer_id=farmer_id,
            category=category,
            title=title,
            message=message,
            status="new",
            created_by=actor_user_id,
        )
        self.notice_repo.add(notification)

        self.audit.record(
            actor_user_id,
            "notification.create",
            "notification",
            notification.notification_id,
            details={
                "category": category,
                "title": title,
                "user_id": user_id,
                "farmer_id": farmer_id,
            },
        )

        return {"success": True, "data": notification.to_dict()}

    def mark_delivered(self, actor_user_id, notification_id):
        row = self.notice_repo.get_by_id(notification_id)
        if row is None:
            return {
                "success": False,
                "message": "Notification Not Found",
            }

        if row.status != "delivered":
            row.status = "delivered"
            row.delivered_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.notice_repo.update(row)
            self.audit.record(
                actor_user_id,
                "notification.deliver",
                "notification",
                row.notification_id,
                details={"title": row.title},
            )

        return {"success": True, "data": row.to_dict()}

    def close(self):
        self.notice_repo.close()
        self.user_repo.close()
        self.farmer_repo.close()
        self.audit.close()