"""
KisanAI OS - Stable error-code contract tests.

Every non-2xx response carries a machine-readable ``code`` so the mobile
app can classify failures (wrong credentials vs session expiry vs network
vs server) and show the correct Hindi message. These tests pin the codes.
"""

from tests.conftest import unique_mobile


def _register(client, username, mobile, password="password123"):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": password,
            "full_name": "Test User",
            "mobile": mobile,
        },
    )


def _login(client, username, password="password123"):
    return client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
    )


def _request_otp(client, mobile, purpose):
    return client.post(
        "/api/auth/otp/request",
        json={"mobile": mobile, "purpose": purpose},
    )


def _err_code(resp):
    body = resp.json()
    detail = body.get("detail")
    if isinstance(detail, dict):
        return detail.get("code")
    return body.get("code")


def test_login_wrong_password_code_auth_invalid(client):
    mobile = unique_mobile()
    username = f"code{unique_mobile()[-5:]}"
    assert _register(client, username, mobile).status_code == 200

    resp = _login(client, username, "wrongpassword")
    assert resp.status_code == 401
    assert _err_code(resp) == "AUTH_INVALID"


def test_login_rate_limited_code(client):
    mobile = unique_mobile()
    username = f"coderl{unique_mobile()[-5:]}"
    assert _register(client, username, mobile).status_code == 200

    for _ in range(5):
        _login(client, username, "wrongpassword")

    resp = _login(client, username, "password123")
    assert resp.status_code == 429
    assert _err_code(resp) == "RATE_LIMITED"


def test_duplicate_register_code_conflict(client):
    mobile = unique_mobile()
    username = f"codeconf{unique_mobile()[-5:]}"
    assert _register(client, username, mobile).status_code == 200

    resp = _register(client, username, mobile)
    assert resp.status_code == 409
    assert _err_code(resp) == "CONFLICT"


def test_session_rejected_after_logout_code_session_expired(client):
    mobile = unique_mobile()
    username = f"codesess{unique_mobile()[-5:]}"
    assert _register(client, username, mobile).status_code == 200

    token = _login(client, username).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    client.post("/api/auth/logout", headers=headers)

    resp = client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 401
    assert _err_code(resp) == "SESSION_EXPIRED"


def test_forgot_username_unknown_mobile_code_account_not_found(client):
    mobile = unique_mobile()
    code = _request_otp(client, mobile, "forgot_username").json()["dev_otp"]
    resp = client.post(
        "/api/auth/forgot-username",
        json={"mobile": mobile, "code": code},
    )
    assert resp.status_code == 400
    assert _err_code(resp) == "ACCOUNT_NOT_FOUND"


def test_reset_password_unknown_mobile_code_account_not_found(client):
    mobile = unique_mobile()
    code = _request_otp(client, mobile, "forgot_password").json()["dev_otp"]
    resp = client.post(
        "/api/auth/reset-password",
        json={"mobile": mobile, "code": code, "new_password": "newpass123"},
    )
    assert resp.status_code == 400
    assert _err_code(resp) == "ACCOUNT_NOT_FOUND"


def test_unknown_route_code_not_found(client):
    resp = client.get("/api/definitely-not-a-route")
    assert resp.status_code == 404
    assert _err_code(resp) == "NOT_FOUND"
