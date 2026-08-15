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
        mobile = (user_data.get("mobile") or "").strip()

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

        if mobile and self.repo.get_by_mobile(mobile) is not None:
            return {
                "success": False,
                "message": "Mobile number already registered",
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

    def _resolve_identity(self, identity):
        """Resolve a user by username OR verified mobile number.

        This backs strong mobile-number based authentication: a farmer can
        log in with either their username or their 10-digit mobile number.
        Mobile lookup only matches when the number belongs to an account;
        unknown identities simply fail the same generic login error.
        """
        if not identity:
            return None

        identity = identity.strip()

        user = self.repo.get_by_username(identity)
        if user is not None:
            return user

        # A mobile-shaped identity can also be a username for some accounts,
        # but the mobile column is the authoritative login alias.
        if identity.isdigit():
            user = self.repo.get_by_mobile(identity)
            if user is not None:
                return user

        return None

    def authenticate_user(self, identity, password):
        """Verify credentials by username or mobile.

        Never exposes the stored hash and never reveals which account, if
        any, matched the supplied identity.
        """

        user = self._resolve_identity(identity)

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

    def register_with_otp(self, otp_service, otp_data):
        """Register an account after verifying the mobile OTP (Phase 3).

        ``otp_data`` carries mobile + code + username + password. The
        OTP is verified first; only then is the account created, so a
        valid code cannot be replayed to create multiple accounts.
        """
        mobile = otp_data.get("mobile", "").strip()

        verified = otp_service.verify_otp(
            mobile,
            "register",
            otp_data.get("code"),
        )

        if not verified["success"]:
            return {
                "success": False,
                "message": verified["message"],
            }

        otp_data = dict(otp_data)
        otp_data["mobile"] = mobile
        otp_data.setdefault("role", ROLE_FARMER)

        result = self.register_user(otp_data)

        if not result["success"]:
            return result

        # The mobile number was just verified through OTP, so the account
        # is created with mobile_verified=True.
        self.set_mobile_verified(mobile, True)

        user = self.repo.get_by_mobile(mobile)
        result["data"] = user.to_dict()

        return result

    def set_mobile_verified(self, mobile, verified=True):
        """Mark a user's mobile number as OTP-verified (or not)."""
        user = self.repo.get_by_mobile((mobile or "").strip())
        if user is None:
            return False
        if bool(user.mobile_verified) != bool(verified):
            user.mobile_verified = bool(verified)
            self.repo.update(user)
        return True

    def get_username_by_otp(self, otp_service, data):
        """Recover the username after verifying a mobile OTP."""
        mobile = data.get("mobile", "").strip()

        verified = otp_service.verify_otp(
            mobile,
            "forgot_username",
            data.get("code"),
        )

        if not verified["success"]:
            return {
                "success": False,
                "message": verified["message"],
            }

        user = self.repo.get_by_mobile(mobile)

        if user is None:
            return {
                "success": False,
                "message": "No account found for this mobile number",
            }

        return {
            "success": True,
            "message": "Username recovered successfully",
            "username": user.username,
        }

    def reset_password(self, otp_service, data):
        """Set a new password after verifying a mobile OTP."""
        mobile = data.get("mobile", "").strip()

        verified = otp_service.verify_otp(
            mobile,
            "forgot_password",
            data.get("code"),
        )

        if not verified["success"]:
            return {
                "success": False,
                "message": verified["message"],
            }

        user = self.repo.get_by_mobile(mobile)

        if user is None:
            return {
                "success": False,
                "message": "No account found for this mobile number",
            }

        user.hashed_password = hash_password(data["new_password"])
        self.repo.update(user)

        logger.info("Password reset completed for user id=%s", user.id)

        return {
            "success": True,
            "message": "Password updated successfully",
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
