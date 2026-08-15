"""
KisanAI OS - JWT Authentication milestone tests.

Covers the full JWT security surface: registration, OAuth2 token
login, valid bearer access, missing/malformed/expired/invalid-signature
tokens -> 401, invalid credentials -> 401, inactive users -> 401,
password-hash never leaking in any response, /me, and the 403/401
role/authorization split on admin-only writes.
"""

from datetime import datetime, timedelta, timezone

import jwt as pyjwt
from sqlalchemy import select

from config.core.api.auth import create_access_token, decode_access_token
from config.core.database import SessionLocal
from config.core.models.user import User
from tests.conftest import farmer_payload, unique_mobile

WRONG_SECRET = "a-completely-different-secret-key-for-signature-testing"


def _register(client, username, password="password123", role="farmer"):
    return client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": password,
            "full_name": "JWT Test User",
            "role": role,
        },
    )


def _login(client, username, password="password123"):
    return client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
    )


def _unique_user():
    return f"jwttest{datetime.now().strftime('%H%M%S%f')}"


def _deactivate_user(username):
    session = SessionLocal()
    try:
        user = session.scalar(select(User).where(User.username == username))
        user.is_active = False
        session.commit()
    finally:
        session.close()


# ==========================================================
# Registration
# ==========================================================

def test_register_user_success(client):
    username = _unique_user()
    response = _register(client, username)
    assert response.status_code == 200
    body = response.json()
    assert body["username"] == username
    assert body["role"] == "farmer"
    assert body["is_active"] is True
    assert set(body.keys()) == {
        "id", "username", "full_name", "mobile", "mobile_verified", "role", "is_active", "created_at",
    }


def test_register_duplicate_username_409(client):
    username = _unique_user()
    assert _register(client, username).status_code == 200
    assert _register(client, username).status_code == 409


def test_register_short_password_422(client):
    response = _register(client, _unique_user(), password="short")
    assert response.status_code == 422


def test_register_cannot_self_assign_admin(client):
    response = _register(client, _unique_user(), role="admin")
    assert response.status_code == 409


# ==========================================================
# Token login
# ==========================================================

def test_login_success_returns_valid_bearer_token(client):
    username = _unique_user()
    _register(client, username)

    response = _login(client, username)
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert len(body["access_token"]) > 20

    payload = decode_access_token(body["access_token"])
    assert payload["sub"] == username
    assert "exp" in payload
    assert "iat" in payload


def test_login_invalid_credentials_401(client):
    username = _unique_user()
    _register(client, username)

    assert _login(client, username, password="wrongpass").status_code == 401
    assert _login(client, "no-such-user", password="password123").status_code == 401


def test_login_inactive_user_401(client):
    username = _unique_user()
    _register(client, username)
    _deactivate_user(username)

    response = _login(client, username)
    assert response.status_code == 401
    assert response.json()["detail"]["message"] == "Inactive user"


# ==========================================================
# /api/auth/me
# ==========================================================

def test_me_endpoint(client):
    username = _unique_user()
    _register(client, username)
    token = _login(client, username).json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == username
    assert "hashed_password" not in response.json()
    assert "password" not in response.json()


def test_me_requires_token(client):
    assert client.get("/api/auth/me").status_code == 401


# ==========================================================
# Bearer token access + rejection matrix
# ==========================================================

def test_valid_bearer_token_allows_read(client, user_headers):
    response = client.get("/api/farmers", headers=user_headers)
    assert response.status_code == 200


def test_missing_token_401(client):
    assert client.get("/api/farmers").status_code == 401


def test_malformed_token_401(client):
    response = client.get(
        "/api/farmers", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert response.status_code == 401


def test_malformed_token_three_parts_401(client):
    response = client.get(
        "/api/farmers", headers={"Authorization": "Bearer aaa.bbb.ccc"}
    )
    assert response.status_code == 401


def test_invalid_signature_token_401(client):
    token = pyjwt.encode(
        {
            "sub": "anyone",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        WRONG_SECRET,
        algorithm="HS256",
    )
    response = client.get(
        "/api/farmers", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_expired_token_401(client):
    token = create_access_token(
        "someone",
        expires_delta=timedelta(seconds=-60),
    )
    response = client.get(
        "/api/farmers", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


def test_token_for_deleted_user_401(client):
    username = _unique_user()
    _register(client, username)
    token = _login(client, username).json()["access_token"]

    session = SessionLocal()
    try:
        user = session.scalar(select(User).where(User.username == username))
        session.delete(user)
        session.commit()
    finally:
        session.close()

    response = client.get(
        "/api/farmers", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401


# ==========================================================
# Password hash is never exposed
# ==========================================================

def test_register_response_never_returns_password(client):
    response = _register(client, _unique_user())
    body = response.json()
    assert "hashed_password" not in body
    assert "password" not in body
    assert "password_hash" not in body


def test_login_response_never_returns_password(client):
    username = _unique_user()
    _register(client, username)
    body = _login(client, username).json()
    assert "hashed_password" not in body
    assert "password" not in body


def test_admin_users_list_never_returns_password(client, admin_headers):
    _register(client, _unique_user())
    response = client.get("/api/admin/users", headers=admin_headers)
    assert response.status_code == 200
    for user in response.json():
        assert "hashed_password" not in user
        assert "password" not in user


# ==========================================================
# Authorization split: 401 vs 403
# ==========================================================

def test_authenticated_normal_user_can_read(client, user_headers):
    assert client.get("/api/farmers", headers=user_headers).status_code == 200
    assert client.get("/api/crops", headers=user_headers).status_code == 200
    assert client.get("/api/soils", headers=user_headers).status_code == 200
    assert client.get("/api/diseases", headers=user_headers).status_code == 200


def test_non_admin_write_403(client, user_headers):
    assert client.post(
        "/api/farmers", json=farmer_payload(), headers=user_headers
    ).status_code == 403
    assert client.post(
        "/api/crops",
        json={
            "crop_name": f"AuthCrop{unique_mobile()}",
            "season": "Rabi",
            "duration_days": 100,
            "water_requirement": "Low",
        },
        headers=user_headers,
    ).status_code == 403
    assert client.post(
        "/api/soils",
        json={
            "soil_type": "Loamy",
            "ph": 6.5,
            "moisture": 40.0,
            "nitrogen": 40,
            "phosphorus": 20,
            "potassium": 15,
        },
        headers=user_headers,
    ).status_code == 403
    assert client.post(
        "/api/diseases",
        json={
            "crop_name": "Rice",
            "disease_name": "Blast",
            "symptoms": "spots",
            "solution": "spray",
            "severity": "High",
        },
        headers=user_headers,
    ).status_code == 403


def test_admin_write_allowed(client, admin_headers):
    response = client.post(
        "/api/farmers", json=farmer_payload(), headers=admin_headers
    )
    assert response.status_code == 200


def test_missing_token_write_401(client):
    assert client.post("/api/farmers", json=farmer_payload()).status_code == 401
