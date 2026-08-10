"""
KisanAI OS
API Authentication Module
Version: 2.0.0

Provides password hashing, JWT token helpers, the ``get_current_user``
dependency and the ``require_role`` authorization factory.

Authentication is fully wired into the API routes: protected endpoints
require a valid bearer token (401 on missing/invalid/expired tokens)
and admin-only write endpoints require the admin role (403 otherwise).
"""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from config.core.database import SessionLocal
from config.core.logger import logger
from config.core.models.user import User
from config.settings import settings


# oauth2_scheme is the OAuth2 bearer token dependency used by
# /api/auth/me and future protected routes.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def _credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"success": False, "message": "Could not validate credentials"},
        headers={"WWW-Authenticate": "Bearer"},
    )


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for the given subject."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )

    payload = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token."""
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
) -> User:
    """Dependency: resolve the current user from a bearer token."""
    credentials_exception = _credentials_exception()

    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError as error:
        logger.warning("Invalid token: %s", error)
        raise credentials_exception from error

    session = SessionLocal()
    try:
        user = session.scalar(
            select(User).where(User.username == username)
        )
    finally:
        session.close()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


def require_role(*roles):
    """Dependency factory: restrict access to specific user roles.

    Usage:
        @app.get("/admin")
        def admin_route(user: User = Depends(require_role("admin"))):
            ...
    """
    def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Insufficient permissions",
                },
            )
        return current_user

    return role_checker


if __name__ == "__main__":

    print("=" * 50)
    print("KisanAI Auth Module Test")
    print("=" * 50)

    print()
    print("HASH / VERIFY:")

    hashed = hash_password("secret123")
    print("hash:", hashed)
    print("verify ok:", verify_password("secret123", hashed))
    print("verify wrong:", verify_password("nope", hashed))

    print()
    print("TOKEN ROUND TRIP:")

    token = create_access_token("testuser")
    print("token:", token[:60], "...")
    print("decoded sub:", decode_access_token(token)["sub"])

    print()
    print("KisanAI Auth Module Test Completed")
