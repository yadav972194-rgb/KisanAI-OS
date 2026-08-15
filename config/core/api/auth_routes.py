"""
KisanAI OS
Auth API Routes
Version: 2.0.0

POST /api/auth/register         - create a new user (username + password)
POST /api/auth/register/otp     - register after verifying a mobile OTP
POST /api/auth/token            - OAuth2 form login, returns JWT + session
GET  /api/auth/me               - current user details (bearer token required)
POST /api/auth/otp/request      - request an OTP (register / forgot flows)
POST /api/auth/otp/verify       - verify an OTP code
POST /api/auth/forgot-username  - recover username after OTP verification
POST /api/auth/reset-password   - set a new password after OTP verification
POST /api/auth/logout           - revoke the current session (bearer token)

Every login creates a server-side session; logout revokes it, so tokens
cannot be replayed after logout or once the session is revoked.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config.core.api.auth import (
    get_current_user,
    issue_user_session,
    revoke_user_session,
)
from config.core.database import get_db
from config.core.models.user import User
from config.core.security import RateLimiter
from config.core.schemas import (
    ForgotUsernameRequest,
    MessageOut,
    OtpRegister,
    OtpRequest,
    OtpRequestOut,
    OtpVerify,
    ResetPasswordRequest,
    Token,
    UsernameOut,
    UserCreate,
    UserOut,
)
from config.core.services.otp_service import OtpService
from config.core.services.user_service import UserService
from config.settings import settings


router = APIRouter(prefix="/api/auth", tags=["auth"])

user_service = UserService()

# Login attempt throttling keyed by identity (Phase 11 security).
# The identity can be a username or a mobile number.
_login_limiter = RateLimiter(
    settings.LOGIN_MAX_ATTEMPTS,
    settings.LOGIN_LOCKOUT_SECONDS,
)

# IP-based login failure throttling (password-spray protection).
# Reset on successful login so legitimate users are never affected.
_ip_login_limiter = RateLimiter(
    max(5, settings.LOGIN_MAX_ATTEMPTS * 3),
    settings.LOGIN_LOCKOUT_SECONDS,
)

# IP-based OTP request throttling (defense-in-depth against flooding
# many numbers from one source). Per-mobile limits remain the primary
# safeguard: OTP_REQUEST_LIMIT per sliding window + DB-backed.
_ip_otp_limiter = RateLimiter(
    settings.OTP_IP_REQUEST_LIMIT,
    settings.OTP_REQUEST_WINDOW_SECONDS,
)

# Bearer scheme for the logout endpoint.
_bearer = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def _fail(status_code: int, message: str, code: str | None = None):
    raise HTTPException(
        status_code=status_code,
        detail={
            "success": False,
            "message": message,
            "code": code or _default_error_code(status_code),
        },
    )


def _default_error_code(status_code: int) -> str:
    """Map an HTTP status to a stable machine-readable error code."""
    if status_code == 401:
        return "AUTH_INVALID"
    if status_code == 404:
        return "NOT_FOUND"
    if status_code == 409:
        return "CONFLICT"
    if status_code == 422:
        return "VALIDATION_ERROR"
    if status_code == 429:
        return "RATE_LIMITED"
    return "SERVER_ERROR"


def _client_ip(request: Request) -> str:
    """Best-effort client IP for rate limiting (never stored/leaked)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


# ==========================================================
# Registration
# ==========================================================

@router.post("/register", response_model=UserOut)
def register_user(data: UserCreate, db: Session = Depends(get_db)):
    result = UserService(db).register_user(data.model_dump())

    if not result["success"]:
        _fail(409, result["message"])

    return result["data"]


@router.post("/register/otp", response_model=UserOut)
def register_user_with_otp(
    data: OtpRegister,
    db: Session = Depends(get_db),
):
    """Register an account after verifying a mobile OTP."""
    result = UserService(db).register_with_otp(
        OtpService(db),
        data.model_dump(),
    )

    if not result["success"]:
        status_code = 400
        if "already" in result["message"].lower():
            status_code = 409
        _fail(status_code, result["message"])

    return result["data"]


# ==========================================================
# OTP flows
# ==========================================================

@router.post("/otp/request", response_model=OtpRequestOut)
def request_otp(
    data: OtpRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    if not _ip_otp_limiter.allow("otp-ip", _client_ip(request)):
        _fail(429, "Too many OTP requests. Please try again later.")

    result = OtpService(db).request_otp(data.mobile, data.purpose)

    if not result["success"]:
        _fail(429, result["message"])

    # Development mock mode returns dev_otp; it is stripped in production.
    return result


@router.post("/otp/verify", response_model=MessageOut)
def verify_otp(data: OtpVerify, db: Session = Depends(get_db)):
    result = OtpService(db).verify_otp(
        data.mobile,
        data.purpose,
        data.code,
    )

    if not result["success"]:
        _fail(400, result["message"])

    return result


@router.post("/forgot-username", response_model=UsernameOut)
def forgot_username(
    data: ForgotUsernameRequest,
    db: Session = Depends(get_db),
):
    result = UserService(db).get_username_by_otp(
        OtpService(db),
        data.model_dump(),
    )

    if not result["success"]:
        code = (
            "ACCOUNT_NOT_FOUND"
            if "No account found" in result["message"]
            else "VALIDATION_ERROR"
        )
        _fail(400, result["message"], code=code)

    return {
        "success": True,
        "message": result["message"],
        "username": result["username"],
    }


@router.post("/reset-password", response_model=MessageOut)
def reset_password(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    result = UserService(db).reset_password(
        OtpService(db),
        data.model_dump(),
    )

    if not result["success"]:
        code = (
            "ACCOUNT_NOT_FOUND"
            if "No account found" in result["message"]
            else "VALIDATION_ERROR"
        )
        _fail(400, result["message"], code=code)

    return result


# ==========================================================
# Login / session
# ==========================================================

@router.post("/token", response_model=Token)
def login_for_access_token(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    if not _login_limiter.allow("login", form_data.username):
        _fail(
            429,
            "Too many failed login attempts. Please try again later.",
        )

    result = UserService(db).authenticate_user(
        form_data.username,
        form_data.password,
    )

    if not result["success"]:
        # Password-spray protection: track *failed* attempts per client IP.
        # Successful logins reset the counter, so legit users are never
        # affected by their own successful traffic.
        if not _ip_login_limiter.allow("login-fail-ip", _client_ip(request)):
            _fail(
                429,
                "Too many login attempts. Please try again later.",
            )
        _fail(401, result["message"])

    _login_limiter.reset("login", form_data.username)
    _ip_login_limiter.reset("login-fail-ip", _client_ip(request))

    user = result["data"]
    access_token = issue_user_session(user, db)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/logout", response_model=MessageOut)
def logout(
    token: str = Depends(_bearer),
    db: Session = Depends(get_db),
):
    """Revoke the current session server-side."""
    from config.core.api.auth import decode_access_token

    try:
        payload = decode_access_token(token)
        jti = payload.get("jti")
    except Exception:
        _fail(401, "Invalid token", code="SESSION_EXPIRED")

    if not jti:
        _fail(401, "Invalid token", code="SESSION_EXPIRED")

    revoke_user_session(jti, db)

    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserOut)
def read_users_me(
    current_user: User = Depends(get_current_user),
):
    return current_user.to_dict()
