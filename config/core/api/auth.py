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
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select

from config.core.database import SessionLocal
from config.core.logger import logger
from config.core.models.user import User
from config.core.models.user_session import UserSession
from config.core.repositories.session_repository import SessionRepository
from config.settings import settings


# oauth2_scheme is the OAuth2 bearer token dependency used by
# /api/auth/me and future protected routes.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def _credentials_exception():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "message": "Could not validate credentials",
            "code": "SESSION_EXPIRED",
        },
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
    jti: str | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token for the given subject.

    ``jti`` uniquely identifies the login session so it can be revoked
    server-side (logout). When omitted the token carries no session
    (used for short-lived system tokens); protected routes require a
    valid session for normal users.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )

    payload: dict = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }

    if jti:
        payload["jti"] = jti

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
    """Dependency: resolve the current user from a bearer token.

    The token must carry a ``jti`` that matches an active (non-revoked,
    non-expired) session in the ``user_sessions`` ledger, so logged-out
    and revoked tokens are rejected before the user is resolved.
    """
    credentials_exception = _credentials_exception()

    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        jti = payload.get("jti")
        if username is None or jti is None:
            raise credentials_exception
    except jwt.PyJWTError as error:
        logger.warning("Invalid token: %s", error)
        raise credentials_exception from error

    session = SessionLocal()
    try:
        user = session.scalar(
            select(User).where(User.username == username)
        )

        if user is None or not user.is_active:
            raise credentials_exception

        # Session ledger check: the token's jti must exist, be
        # un-revoked and un-expired (server-side logout / expiry).
        session_repo = SessionRepository(session)
        user_session = session_repo.get_by_jti(jti)

        if user_session is None or user_session.revoked:
            logger.info(
                "Rejected token for user=%s: session %s not active",
                username,
                jti,
            )
            raise credentials_exception

        try:
            expires_at = datetime.strptime(
                user_session.expires_at, "%Y-%m-%d %H:%M:%S"
            )
            expired = datetime.now() > expires_at
        except (TypeError, ValueError):
            expired = True

        if expired:
            logger.info(
                "Rejected token for user=%s: session %s expired",
                username,
                jti,
            )
            raise credentials_exception
    finally:
        session.close()

    return user


def issue_user_session(user: User, db=None) -> str:
    """Create a session ledger row and return a signed JWT for it."""
    repo = SessionRepository(db)
    jti = secrets.token_hex(32)
    expires_at = (
        datetime.now() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    ).strftime("%Y-%m-%d %H:%M:%S")

    repo.add(
        UserSession(
            user_id=user.id,
            jti=jti,
            expires_at=expires_at,
            revoked=False,
        )
    )

    return create_access_token(user.username, jti=jti)


def revoke_user_session(jti: str, db=None) -> None:
    """Revoke the session matching ``jti`` (server-side logout)."""
    repo = SessionRepository(db)
    session_row = repo.get_by_jti(jti)

    if session_row is not None and not session_row.revoked:
        repo.revoke(
            session_row,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )


def revoke_all_user_sessions(user_id: int, db=None) -> None:
    """Revoke every active session for the user (admin/security use)."""
    SessionRepository(db).revoke_all_for_user(user_id)


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
