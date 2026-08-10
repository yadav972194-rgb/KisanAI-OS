"""
KisanAI OS
User Service
Version: 1.1.0

Registration, authentication and admin bootstrap.
"""

from config.constants import (
    ROLE_ADMIN,
    ROLE_EXPERT,
    ROLE_FARMER,
)
from config.core.api.auth import hash_password, verify_password
from config.core.logger import logger
from config.core.models.user import User
from config.core.repositories.user_repository import UserRepository
from config.settings import settings

VALID_ROLES = {ROLE_ADMIN, ROLE_FARMER, ROLE_EXPERT}


class UserService:
    """User Service"""

    def __init__(self, session=None):
        self.repo = UserRepository(session)

    def register_user(self, user_data):
        username = user_data.get("username", "").strip()

        if not username:
            return {
                "success": False,
                "message": "Username is required",
            }

        if self.repo.get_by_username(username) is not None:
            return {
                "success": False,
                "message": "Username already exists",
            }

        role = user_data.get("role") or ROLE_FARMER

        if role == ROLE_ADMIN:
            return {
                "success": False,
                "message": "Invalid role",
            }

        if role not in VALID_ROLES:
            return {
                "success": False,
                "message": "Invalid role",
            }

        user = User(
            username=username,
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data.get("full_name"),
            mobile=user_data.get("mobile"),
            role=role,
            is_active=True,
        )

        self.repo.add(user)

        logger.info("User registered: %s (role=%s)", username, role)

        return {
            "success": True,
            "message": "User Registered Successfully",
            "data": user.to_dict(),
        }

    def authenticate_user(self, username, password):
        """Verify credentials. Never exposes the stored hash."""

        user = self.repo.get_by_username(username)

        if user is None or not verify_password(
            password, user.hashed_password
        ):
            return {
                "success": False,
                "message": "Invalid username or password",
            }

        if not user.is_active:
            return {
                "success": False,
                "message": "Inactive user",
            }

        return {
            "success": True,
            "message": "Login Successful",
            "data": user,
        }

    def bootstrap_admin(self):
        """Idempotently create the admin account from settings."""

        username = (settings.ADMIN_USERNAME or "").strip()
        password = settings.ADMIN_PASSWORD or ""

        if not username or not password:
            logger.warning(
                "ADMIN_USERNAME/ADMIN_PASSWORD not configured; "
                "skipping admin bootstrap"
            )
            return

        if self.repo.get_by_username(username) is not None:
            logger.info("Admin account already exists: %s", username)
            return

        user = User(
            username=username,
            hashed_password=hash_password(password),
            full_name="System Administrator",
            role=ROLE_ADMIN,
            is_active=True,
        )

        self.repo.add(user)

        logger.info("Admin bootstrap created: %s", username)

    def set_user_role(self, user_id, role):
        """Assign an admin-managed role (farmer/expert) to an existing user.

        Used by the Phase 5.9 Expert Role Activation endpoint. The caller
        (schema layer) already restricts ``role`` to farmer/expert; admin
        accounts are bootstrap-only.
        """
        user = self.repo.get_by_id(user_id)

        if user is None:
            return {
                "success": False,
                "message": "User Not Found",
            }

        if role not in (ROLE_FARMER, ROLE_EXPERT):
            return {
                "success": False,
                "message": "Invalid role",
            }

        user.role = role
        self.repo.update(user)

        logger.info("Admin assigned role=%s to user id=%s", role, user_id)

        return {
            "success": True,
            "message": f"User role updated to {role}",
        }

    def get_all_users(self):
        return [
            user.to_dict()
            for user in self.repo.get_all_users()
        ]

    def count_users(self):
        return self.repo.count_users()

    def close(self):
        self.repo.close()
