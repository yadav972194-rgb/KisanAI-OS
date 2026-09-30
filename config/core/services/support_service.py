"""
KisanAI OS
Support Service
Version: 1.0.0

Admin Control & Farmer Support module. Farmer problems/feedback lifecycle
and admin contact records (phone/email). Status transitions are validated
against a fixed workflow; every mutation is audited.
"""

from datetime import datetime

from config.core.models.contact_record import ContactRecord
from config.core.models.feedback import Feedback
from config.core.repositories.contact_repository import ContactRepository
from config.core.repositories.farmer_repository import FarmerRepository
from config.core.repositories.feedback_repository import FeedbackRepository
from config.core.services.audit_service import AuditService

FEEDBACK_STATUSES = {
    "new",
    "investigating",
    "contacted",
    "in_progress",
    "resolved",
    "closed",
}

FEEDBACK_PRIORITIES = {"low", "medium", "high"}

CONTACT_CHANNELS = {"phone", "email"}

# Allowed status transitions (closed can reopen to new).
FEEDBACK_TRANSITIONS = {
    "new": {"investigating", "contacted"},
    "investigating": {"contacted", "in_progress", "resolved"},
    "contacted": {"in_progress", "resolved"},
    "in_progress": {"resolved"},
    "resolved": {"closed"},
    "closed": {"new"},
}


def _clean_text(value):
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


class SupportService:
    """Support Service"""

    def __init__(self, session=None):
        self.feedback_repo = FeedbackRepository(session)
        self.contact_repo = ContactRepository(session)
        self.farmer_repo = FarmerRepository(session)
        self.audit = AuditService(session)

    # ==========================================================
    # Feedback / problems
    # ==========================================================

    @staticmethod
    def _validate_status(value):
        text = (value or "").strip().lower()
        if text not in FEEDBACK_STATUSES:
            return None, f"Invalid status: {value or ''}"
        return text, None

    @staticmethod
    def _validate_priority(value):
        text = (value or "").strip().lower()
        if text not in FEEDBACK_PRIORITIES:
            return None, f"Invalid priority: {value or ''}"
        return text, None

    def create_feedback(self, actor_user_id, data):
        farmer_id = data.get("farmer_id")
        if farmer_id is not None and self.farmer_repo.get_farmer_by_id(
            farmer_id
        ) is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        subject = _clean_text(data.get("subject"))
        description = _clean_text(data.get("description"))
        if not subject or not description:
            return {
                "success": False,
                "message": "Subject and description are required",
            }

        priority, error = self._validate_priority(data.get("priority"))
        if error is not None:
            return {"success": False, "message": error}

        feedback = Feedback(
            user_id=actor_user_id,
            farmer_id=farmer_id,
            subject=subject,
            description=description,
            status="new",
            priority=priority or "medium",
        )
        self.feedback_repo.add(feedback)

        self.audit.record(
            actor_user_id,
            "feedback.create",
            "feedback",
            feedback.feedback_id,
            details={"subject": subject, "farmer_id": farmer_id},
        )

        return {
            "success": True,
            "message": "Problem recorded successfully",
            "data": feedback.to_dict(),
        }

    def list_feedback(self, status=None, priority=None, page=1, size=20):
        if status:
            status, error = self._validate_status(status)
            if error is not None:
                return {"success": False, "message": error}
        if priority:
            priority, error = self._validate_priority(priority)
            if error is not None:
                return {"success": False, "message": error}

        rows = self.feedback_repo.list_all(
            status=status or None,
            priority=priority or None,
            page=page,
            size=size,
        )
        total = self.feedback_repo.count(
            status=status or None,
            priority=priority or None,
        )
        return {
            "success": True,
            "items": [row.to_dict() for row in rows],
            "total": total,
            "page": page,
            "size": size,
        }

    def get_feedback(self, feedback_id):
        row = self.feedback_repo.get_by_id(feedback_id)
        if row is None:
            return {
                "success": False,
                "message": "Problem Not Found",
            }
        return {"success": True, "data": row.to_dict()}

    def list_by_farmer(self, farmer_id):
        if self.farmer_repo.get_farmer_by_id(farmer_id) is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }
        rows = self.feedback_repo.list_by_farmer(farmer_id)
        return {
            "success": True,
            "items": [row.to_dict() for row in rows],
            "total": len(rows),
        }

    def update_feedback(self, actor_user_id, feedback_id, data):
        row = self.feedback_repo.get_by_id(feedback_id)
        if row is None:
            return {
                "success": False,
                "message": "Problem Not Found",
            }

        changes = {}
        if "subject" in data:
            subject = _clean_text(data.get("subject"))
            if not subject:
                return {
                    "success": False,
                    "message": "Subject cannot be blank",
                }
            if subject != row.subject:
                changes["subject"] = [row.subject, subject]
                row.subject = subject

        if "description" in data and isinstance(data.get("description"), str):
            description = _clean_text(data["description"])
            if description != row.description:
                changes["description"] = [row.description, description]
                row.description = description

        if "priority" in data:
            priority, error = self._validate_priority(data.get("priority"))
            if error is not None:
                return {"success": False, "message": error}
            if priority != row.priority:
                changes["priority"] = [row.priority, priority]
                row.priority = priority

        if changes:
            row.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.feedback_repo.update(row)
            self.audit.record(
                actor_user_id,
                "feedback.update",
                "feedback",
                row.feedback_id,
                details={"changes": changes},
            )

        return {"success": True, "data": row.to_dict()}

    def transition_feedback(self, actor_user_id, feedback_id, new_status):
        row = self.feedback_repo.get_by_id(feedback_id)
        if row is None:
            return {
                "success": False,
                "message": "Problem Not Found",
            }

        target, error = self._validate_status(new_status)
        if error is not None:
            return {"success": False, "message": error}

        allowed = FEEDBACK_TRANSITIONS.get(row.status, set())
        if target not in allowed:
            return {
                "success": False,
                "message": (
                    f"Cannot move status from '{row.status}' to '{target}'"
                ),
            }

        old_status = row.status
        row.status = target
        row.updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.feedback_repo.update(row)

        self.audit.record(
            actor_user_id,
            "feedback.status",
            "feedback",
            row.feedback_id,
            details={"from": old_status, "to": target},
        )

        return {"success": True, "data": row.to_dict()}

    # ==========================================================
    # Contact records
    # ==========================================================

    def record_contact(self, actor_user_id, data):
        farmer_id = data.get("farmer_id")
        if self.farmer_repo.get_farmer_by_id(farmer_id) is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }

        channel = (data.get("channel") or "").strip().lower()
        if channel not in CONTACT_CHANNELS:
            return {
                "success": False,
                "message": "Channel must be phone or email",
            }

        reason = _clean_text(data.get("reason"))
        note = data.get("note")
        note = _clean_text(note) if isinstance(note, str) and note else None

        contact = ContactRecord(
            farmer_id=farmer_id,
            channel=channel,
            reason=reason or None,
            note=note,
            created_by=actor_user_id,
        )
        self.contact_repo.add(contact)

        self.audit.record(
            actor_user_id,
            "contact.create",
            "contact",
            contact.contact_id,
            details={
                "farmer_id": farmer_id,
                "channel": channel,
                "reason": contact.reason,
            },
        )

        return {"success": True, "data": contact.to_dict()}

    def list_contacts(self, farmer_id):
        if self.farmer_repo.get_farmer_by_id(farmer_id) is None:
            return {
                "success": False,
                "message": "Farmer Not Found",
            }
        rows = self.contact_repo.list_by_farmer(farmer_id)
        total = self.contact_repo.count_by_farmer(farmer_id)
        return {
            "success": True,
            "items": [row.to_dict() for row in rows],
            "total": total,
        }

    def close(self):
        self.feedback_repo.close()
        self.contact_repo.close()
        self.farmer_repo.close()
        self.audit.close()