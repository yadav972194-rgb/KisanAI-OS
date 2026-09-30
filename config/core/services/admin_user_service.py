"""
KisanAI OS
Admin User Service
Version: 1.0.0

Admin Control & Farmer Support module. Account controls: deactivate,
restore, delete (super-admin, confirmation required) and super-admin
privilege assignment. Self-modification is always rejected and the
"at least one active super-admin remains" invariant is enforced.
"""

from config.core.models.user import User
from config.core.repositories.session_repository import SessionRepository
from config.core.repositories.user_repository import UserRepository
from config.core.services.audit_service import AuditService


class AdminUserService:
    """Admin User Service"""

    def __init__(self, session=None):
        self.user_repo = UserRepository(session)
        self.session_repo = SessionRepository(session)
        self.audit = AuditService(session)

    def list_users(self):
        return self.user_repo.get_all_users()

    def set_super_admin(self, actor_user_id, user_id, super_admin):
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            return {
                "success": False,
                "message": "User Not Found",
            }

        if int(user.id) == int(actor_user_id):
            return {
                "success": False,
                "message": "You cannot change your own privileges",
            }

        if bool(user.super_admin) == bool(super_admin):
            return {
                "success": True,
                "message": (
                    "Super-admin privilege already set to "
                    f"{'enabled' if super_admin else 'disabled'}"
                ),
            }

        if not super_admin and user.super_admin:
            active = self.user_repo.count_active_super_admins()
            if active <= 1:
                return {
                    "success": False,
                    "message": (
                        "Cannot demote the last active super-admin"
                    ),
                }

        user.super_admin = bool(super_admin)
        self.user_repo.update(user)

        self.audit.record(
            actor_user_id,
            "user.super_admin",
            "user",
            user.id,
            details={
                "username": user.username,
                "super_admin": bool(super_admin),
            },
        )

        return {
            "success": True,
            "message": (
                "Super-admin privilege "
                f"{'enabled' if super_admin else 'disabled'}"
            ),
        }

    def deactivate_user(self, actor_user_id, user_id):
        user = self._get_for_account_action(actor_user_id, user_id)
        if isinstance(user, dict):
            return user

        if not user.is_active:
            return {
                "success": False,
                "message": "Account already inactive",
            }

        user.is_active = False
        self.user_repo.update(user)
        self.session_repo.revoke_all_for_user(int(user.id))

        self.audit.record(
            actor_user_id,
            "user.deactivate",
            "user",
            user.id,
            details={"username": user.username},
        )

        return {
            "success": True,
            "message": "Account deactivated successfully",
        }

    def restore_user(self, actor_user_id, user_id):
        user = self.user_repo.get_by_id(user_id)
        if user is None:
            return {
                "success": False,
                "message": "User Not Found",
            }

        if user.is_active:
            return {
                "success": True,
                "message": "Account is already active",
            }

        user.is_active = True
        self.user_repo.update(user)

        self.audit.record(
            actor_user_id,
            "user.restore",
            "user",
            user.id,
            details={"username": user.username},
        )

        return {
            "success": True,
            "message": "Account restored successfully",
        }

    def delete_user(self, actor_user_id, user_id, confirm=False):
        """Super-admin account deletion. Requires explicit confirmation."""
        if not confirm:
            return {
                "success": False,
                "message": "Deletion requires confirmation",
            }

        user = self._get_for_account_action(actor_user_id, user_id)
        if isinstance(user, dict):
            return user

        if user.super_admin:
            active = self.user_repo.count_active_super_admins()
            if active <= 1:
                return {
                    "success": False,
                    "message": (
                        "Cannot delete the last active super-admin"
                    ),
                }

        self.session_repo.revoke_all_for_user(int(user.id))
        self.user_repo.delete(int(user.id))

        self.audit.record(
            actor_user_id,
            "user.delete",
            "user",
            user_id,
            details={"username": user.username},
        )

        return {
            "success": True,
            "message": "Account deleted successfully",
        }

    def _get_for_account_action(self, actor_user_id, user_id):
        if int(user_id) == int(actor_user_id):
            return {
                "success": False,
                "message": "You cannot perform this action on yourself",
            }

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            return {
                "success": False,
                "message": "User Not Found",
            }

        return user

    def close(self):
        self.user_repo.close()
        self.session_repo.close()
        self.audit.close()