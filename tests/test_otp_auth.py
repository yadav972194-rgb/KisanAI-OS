"""
KisanAI OS - Phase 3 OTP authentication tests.

Covers mobile OTP request/verify, OTP registration, forgot username,
password reset, server-side logout/session revocation, login rate
limiting and the OTP rate limiter itself. All OTP codes are exercised in
mock mode (OTP_MOCK=true) where the code is returned as ``dev_otp``.
"""

import pytest

from tests.conftest import unique_mobile


# ==========================================================
# Helpers
# ==========================================================

def _request_otp(client, mobile, purpose="register"):
    return client.post(
        "/api/auth/otp/request",
        json={"mobile": mobile, "purpose": purpose},
    )


def _register_with_otp(client, mobile, username, password="password123",
                       code=None):
    if code is None:
        resp = _request_otp(client, mobile, "register")
        assert resp.status_code == 200, resp.text
        code = resp.json()["dev_otp"]

    return client.post(
        "/api/auth/register/otp",
        json={
            "mobile": mobile,
            "code": code,
            "username": username,
            "password": password,
            "full_name": "Test Farmer",
        },
    )


def _login(client, username, password="password123"):
    return client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
    )


def _err(resp):
    """Extract the human-readable message from an error response body."""
    body = resp.json()
    detail = body.get("detail")
    if isinstance(detail, dict):
        return detail.get("message", "")
    return body.get("message", "")


# ==========================================================
# OTP request
# ==========================================================

def test_otp_request_success_returns_dev_otp(client):
    mobile = unique_mobile()
    resp = _request_otp(client, mobile, "register")

    assert resp.status_code == 200
    body = resp.json()
    assert body["success"] is True
    assert len(body["dev_otp"]) == 6
    assert body["dev_otp"].isdigit()


def test_otp_request_invalid_purpose_422(client):
    mobile = unique_mobile()
    resp = client.post(
        "/api/auth/otp/request",
        json={"mobile": mobile, "purpose": "bogus"},
    )
    assert resp.status_code == 422


def test_otp_request_invalid_mobile_422(client):
    resp = client.post(
        "/api/auth/otp/request",
        json={"mobile": "12345", "purpose": "register"},
    )
    assert resp.status_code == 422


def test_otp_request_cooldown_blocks_resend(client):
    mobile = unique_mobile()
    first = _request_otp(client, mobile, "register")
    assert first.status_code == 200

    second = _request_otp(client, mobile, "register")
    assert second.status_code == 429
    assert "already sent" in _err(second).lower()


def test_otp_request_different_purpose_allowed(client):
    mobile = unique_mobile()
    _request_otp(client, mobile, "register")
    resp = _request_otp(client, mobile, "forgot_username")
    assert resp.status_code == 200


# ==========================================================
# OTP verify
# ==========================================================

def test_otp_verify_success(client):
    mobile = unique_mobile()
    otp = _request_otp(client, mobile, "register").json()["dev_otp"]

    resp = client.post(
        "/api/auth/otp/verify",
        json={"mobile": mobile, "purpose": "register", "code": otp},
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_otp_verify_wrong_code(client):
    mobile = unique_mobile()
    _request_otp(client, mobile, "register")

    resp = client.post(
        "/api/auth/otp/verify",
        json={"mobile": mobile, "purpose": "register", "code": "000000"},
    )
    assert resp.status_code == 400


def test_otp_verify_exhausted_attempts(client):
    mobile = unique_mobile()
    _request_otp(client, mobile, "register")

    for _ in range(5):
        client.post(
            "/api/auth/otp/verify",
            json={"mobile": mobile, "purpose": "register", "code": "999999"},
        )

    resp = client.post(
        "/api/auth/otp/verify",
        json={"mobile": mobile, "purpose": "register", "code": "999999"},
    )
    assert resp.status_code == 400
    assert "attempts" in _err(resp).lower()


def test_otp_verify_expired_code_rejected(client):
    from config.core.database import SessionLocal
    from config.core.models.otp import OtpCode
    from sqlalchemy import select

    mobile = unique_mobile()
    otp = _request_otp(client, mobile, "register").json()["dev_otp"]

    session = SessionLocal()
    try:
        row = session.scalar(
            select(OtpCode).where(OtpCode.mobile == mobile)
        )
        row.expires_at = "2020-01-01 00:00:00"
        session.commit()
    finally:
        session.close()

    resp = client.post(
        "/api/auth/otp/verify",
        json={"mobile": mobile, "purpose": "register", "code": otp},
    )
    assert resp.status_code == 400
    assert "expired" in _err(resp).lower()


# ==========================================================
# OTP registration
# ==========================================================

def test_register_with_otp_then_login(client):
    mobile = unique_mobile()
    username = f"otpuser{unique_mobile()[-5:]}"

    resp = _register_with_otp(client, mobile, username)
    assert resp.status_code == 200
    assert resp.json()["username"] == username

    login = _login(client, username)
    assert login.status_code == 200
    assert login.json()["access_token"]


def test_register_with_otp_wrong_code(client):
    mobile = unique_mobile()
    username = f"badotp{unique_mobile()[-5:]}"

    resp = _register_with_otp(client, mobile, username, code="111111")
    assert resp.status_code == 400


def test_register_with_otp_code_not_reusable(client):
    mobile = unique_mobile()
    username = f"reuse{unique_mobile()[-5:]}"
    code = _request_otp(client, mobile, "register").json()["dev_otp"]

    first = _register_with_otp(client, mobile, username, code=code)
    assert first.status_code == 200

    second = _register_with_otp(
        client, mobile, f"{username}2", code=code
    )
    assert second.status_code == 400


def test_register_with_otp_duplicate_mobile(client):
    mobile = unique_mobile()
    username = f"dup{unique_mobile()[-5:]}"

    assert _register_with_otp(client, mobile, username).status_code == 200

    second_user = f"{username}2"
    second = _register_with_otp(client, mobile, second_user)
    assert second.status_code == 409
    assert "mobile" in _err(second).lower()


# ==========================================================
# Forgot username
# ==========================================================

def test_forgot_username_returns_username(client):
    mobile = unique_mobile()
    username = f"forgot{unique_mobile()[-5:]}"
    _register_with_otp(client, mobile, username)

    code = _request_otp(client, mobile, "forgot_username").json()["dev_otp"]
    resp = client.post(
        "/api/auth/forgot-username",
        json={"mobile": mobile, "code": code},
    )
    assert resp.status_code == 200
    assert resp.json()["username"] == username


def test_forgot_username_unknown_mobile(client):
    mobile = unique_mobile()
    code = _request_otp(client, mobile, "forgot_username").json()["dev_otp"]

    resp = client.post(
        "/api/auth/forgot-username",
        json={"mobile": mobile, "code": code},
    )
    assert resp.status_code == 400
    assert "no account" in _err(resp).lower()


# ==========================================================
# Password reset
# ==========================================================

def test_reset_password_flow(client):
    mobile = unique_mobile()
    username = f"reset{unique_mobile()[-5:]}"
    _register_with_otp(client, mobile, username)

    code = _request_otp(client, mobile, "forgot_password").json()["dev_otp"]
    resp = client.post(
        "/api/auth/reset-password",
        json={"mobile": mobile, "code": code, "new_password": "newpass123"},
    )
    assert resp.status_code == 200

    old_login = _login(client, username, "password123")
    assert old_login.status_code == 401

    new_login = _login(client, username, "newpass123")
    assert new_login.status_code == 200


def test_reset_password_wrong_code(client):
    mobile = unique_mobile()
    username = f"rbad{unique_mobile()[-5:]}"
    _register_with_otp(client, mobile, username)

    resp = client.post(
        "/api/auth/reset-password",
        json={"mobile": mobile, "code": "000000", "new_password": "newpass123"},
    )
    assert resp.status_code == 400


# ==========================================================
# Session / logout
# ==========================================================

def test_logout_revokes_session(client):
    mobile = unique_mobile()
    username = f"logout{unique_mobile()[-5:]}"
    _register_with_otp(client, mobile, username)

    login = _login(client, username)
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200

    logout = client.post("/api/auth/logout", headers=headers)
    assert logout.status_code == 200

    me_after = client.get("/api/auth/me", headers=headers)
    assert me_after.status_code == 401


def test_login_wrong_password_401(client):
    mobile = unique_mobile()
    username = f"wrongpwd{unique_mobile()[-5:]}"
    _register_with_otp(client, mobile, username)

    resp = _login(client, username, "wrongpassword")
    assert resp.status_code == 401
    assert "invalid" in _err(resp).lower()


def test_login_rate_limit_after_failures(client):
    mobile = unique_mobile()
    username = f"ratelimit{unique_mobile()[-5:]}"
    _register_with_otp(client, mobile, username)

    for _ in range(5):
        _login(client, username, "wrongpassword")

    resp = _login(client, username, "password123")
    assert resp.status_code == 429


# ==========================================================
# Rate limiter unit tests
# ==========================================================

def test_rate_limiter_blocks_after_limit():
    from config.core.security import RateLimiter

    limiter = RateLimiter(3, 60)
    assert limiter.allow("ns", "user1") is True
    assert limiter.allow("ns", "user1") is True
    assert limiter.allow("ns", "user1") is True
    assert limiter.allow("ns", "user1") is False

    assert limiter.allow("ns", "user2") is True
    assert limiter.remaining("ns", "user1") == 0


def test_rate_limiter_reset_restores_capacity():
    from config.core.security import RateLimiter

    limiter = RateLimiter(2, 60)
    limiter.allow("ns", "user1")
    limiter.allow("ns", "user1")
    assert limiter.allow("ns", "user1") is False

    limiter.reset("ns", "user1")
    assert limiter.allow("ns", "user1") is True
