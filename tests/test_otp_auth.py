"""
KisanAI OS - Phase 3 OTP authentication tests.

Covers mobile OTP request/verify, OTP registration, forgot username,
password reset, server-side logout/session revocation, login rate
limiting and the OTP rate limiter itself. All OTP codes are exercised in
mock mode (OTP_MOCK=true) where the code is returned as ``dev_otp``.
"""

import logging

import httpx

import pytest

from config.core.providers import get_otp_provider
from config.core.providers.otp_provider import (
    ConsoleOtpProvider,
    MockOtpProvider,
    OtpProviderError,
    TwilioOtpProvider,
)
from config.settings import settings
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


# ==========================================================
# Twilio OTP provider (Phase 1.5)
# ==========================================================

_TEST_SID = "AC" + "a" * 32
_TEST_TOKEN = "tok" + "b" * 32
_TEST_MESSAGING_SID = "MG" + "c" * 32
_TEST_FROM = "+15551234567"


class _FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class _FakeClient:
    """Injected httpx-like client - never makes a real network call."""

    def __init__(self, status_code=200):
        self.status_code = status_code
        self.calls = []

    def post(self, url, data):
        self.calls.append((url, data))
        return _FakeResponse(self.status_code)


class _RaisingClient:
    """Client that always raises a transport error."""

    def post(self, url, data):
        raise httpx.ConnectError("connection failed")


def _twilio_provider(client=None, **kwargs):
    defaults = {
        "account_sid": _TEST_SID,
        "auth_token": _TEST_TOKEN,
        "messaging_service_sid": _TEST_MESSAGING_SID,
        "from_number": None,
    }
    defaults.update(kwargs)
    return TwilioOtpProvider(**defaults, http_client=client)


def test_factory_twilio_selected_when_configured(monkeypatch):
    monkeypatch.setattr(settings, "OTP_PROVIDER", "twilio")
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", _TEST_SID)
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TEST_TOKEN)
    monkeypatch.setattr(
        settings, "TWILIO_MESSAGING_SERVICE_SID", _TEST_MESSAGING_SID
    )
    monkeypatch.setattr(settings, "TWILIO_FROM_NUMBER", "")

    provider = get_otp_provider()
    assert isinstance(provider, TwilioOtpProvider)
    assert provider.account_sid == _TEST_SID


def test_factory_twilio_missing_credentials_falls_back(monkeypatch):
    monkeypatch.setattr(settings, "OTP_PROVIDER", "twilio")
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "")
    monkeypatch.setattr(settings, "TWILIO_MESSAGING_SERVICE_SID", "")
    monkeypatch.setattr(settings, "TWILIO_FROM_NUMBER", "")
    assert isinstance(get_otp_provider(), ConsoleOtpProvider)


def test_factory_twilio_missing_sender_falls_back(monkeypatch):
    monkeypatch.setattr(settings, "OTP_PROVIDER", "twilio")
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", _TEST_SID)
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", _TEST_TOKEN)
    monkeypatch.setattr(settings, "TWILIO_MESSAGING_SERVICE_SID", "")
    monkeypatch.setattr(settings, "TWILIO_FROM_NUMBER", "")
    assert isinstance(get_otp_provider(), ConsoleOtpProvider)


def test_twilio_send_http_200_success():
    client = _FakeClient(200)
    provider = _twilio_provider(client)

    provider.send("+919999999999", "123456", "register")

    assert len(client.calls) == 1
    url, data = client.calls[0]
    assert url.endswith(
        f"/2010-04-01/Accounts/{_TEST_SID}/Messages.json"
    )
    assert data["To"] == "+919999999999"
    assert data["MessagingServiceSid"] == _TEST_MESSAGING_SID
    assert "123456" in data["Body"]


def test_twilio_send_http_201_success():
    client = _FakeClient(201)
    provider = _twilio_provider(
        client, messaging_service_sid=None, from_number=_TEST_FROM
    )

    provider.send("+919999999999", "123456", "register")

    assert len(client.calls) == 1
    url, data = client.calls[0]
    assert data["From"] == _TEST_FROM
    assert "MessagingServiceSid" not in data


def test_twilio_send_http_4xx_raises():
    provider = _twilio_provider(_FakeClient(400))
    with pytest.raises(OtpProviderError):
        provider.send("+919999999999", "123456", "register")


def test_twilio_send_http_5xx_raises():
    provider = _twilio_provider(_FakeClient(500))
    with pytest.raises(OtpProviderError):
        provider.send("+919999999999", "123456", "register")


def test_twilio_send_network_error_raises():
    provider = _twilio_provider(_RaisingClient())
    with pytest.raises(OtpProviderError):
        provider.send("+919999999999", "123456", "register")


def test_twilio_send_missing_credentials_raises():
    provider = _twilio_provider(
        _FakeClient(200), account_sid="", auth_token=""
    )
    with pytest.raises(OtpProviderError):
        provider.send("+919999999999", "123456", "register")


def test_twilio_send_missing_sender_raises():
    provider = _twilio_provider(
        _FakeClient(200), messaging_service_sid=None, from_number=None
    )
    with pytest.raises(OtpProviderError):
        provider.send("+919999999999", "123456", "register")


def test_twilio_no_credential_leakage(caplog, monkeypatch):
    kisanai_logger = logging.getLogger("KisanAI")
    monkeypatch.setattr(kisanai_logger, "disabled", False)
    caplog.set_level(logging.INFO)
    provider = _twilio_provider(_FakeClient(500))

    with pytest.raises(OtpProviderError) as exc:
        provider.send("+919999999999", "123456", "register")

    assert "Unable to send OTP" in str(exc.value)
    assert _TEST_SID not in str(exc.value)
    assert _TEST_TOKEN not in str(exc.value)
    assert _TEST_MESSAGING_SID not in str(exc.value)
    assert "123456" not in str(exc.value)
    assert _TEST_SID not in caplog.text
    assert _TEST_TOKEN not in caplog.text
    assert _TEST_MESSAGING_SID not in caplog.text


def test_mock_provider_makes_no_network_calls(caplog, monkeypatch):
    kisanai_logger = logging.getLogger("KisanAI")
    monkeypatch.setattr(kisanai_logger, "disabled", False)
    caplog.set_level(logging.INFO)
    provider = MockOtpProvider()

    provider.send("+919999999999", "123456", "register")

    assert "MOCK OTP" in caplog.text


def test_factory_backward_compatible(monkeypatch):
    monkeypatch.setattr(settings, "OTP_PROVIDER", "mock")
    assert isinstance(get_otp_provider(), MockOtpProvider)

    monkeypatch.setattr(settings, "OTP_PROVIDER", "console")
    assert isinstance(get_otp_provider(), ConsoleOtpProvider)

    monkeypatch.setattr(settings, "OTP_PROVIDER", "bogus")
    assert isinstance(get_otp_provider(), ConsoleOtpProvider)
