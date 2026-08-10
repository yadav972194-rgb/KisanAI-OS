"""
KisanAI OS - Phase 5.7 API Security & Production Hardening tests.

Covers prevention of self-assigned admin privilege escalation through
public registration, clean error responses (no internal detail
leakage), JWT secret strength, and the absence of permissive CORS
headers. Admin-only write protection on farmer/crop/soil/disease is
verified in test_auth_regression.py and the per-module suites.
"""

from config.settings import settings
from tests.conftest import farmer_payload, unique_mobile


# ==========================================================
# A. Public registration cannot self-assign the admin role
# ==========================================================

def test_register_rejects_admin_role(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": f"evil_admin_{unique_mobile()}",
            "password": "hackerpass1",
            "full_name": "Attacker",
            "role": "admin",
        },
    )
    assert response.status_code == 409
    assert response.json()["detail"]["message"] == "Invalid role"


def test_register_as_farmer_still_works(client):
    username = f"farmer_sec_{unique_mobile()}"
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "farmerpass1",
            "full_name": "Farmer",
            "role": "farmer",
        },
    )
    assert response.status_code == 200
    assert response.json()["role"] == "farmer"


def test_register_default_role_is_farmer(client):
    response = client.post(
        "/api/auth/register",
        json={
            "username": f"default_sec_{unique_mobile()}",
            "password": "farmerpass1",
        },
    )
    assert response.status_code == 200
    assert response.json()["role"] == "farmer"


def test_registered_farmer_cannot_perform_admin_writes(client):
    username = f"farmer_nopriv_{unique_mobile()}"
    register = client.post(
        "/api/auth/register",
        json={"username": username, "password": "farmerpass1"},
    )
    assert register.status_code == 200

    token = client.post(
        "/api/auth/token",
        data={"username": username, "password": "farmerpass1"},
    ).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    assert client.get("/api/farmers", headers=headers).status_code == 200

    response = client.post(
        "/api/farmers", json=farmer_payload(), headers=headers
    )
    assert response.status_code == 403
    assert response.json()["detail"]["message"] == "Insufficient permissions"


# ==========================================================
# B. JWT secret strength
# ==========================================================

def test_jwt_secret_is_strong(client):
    assert settings.SECRET_KEY != "change-me-in-production"
    assert len(settings.SECRET_KEY) >= 32


# ==========================================================
# C. Error responses do not leak internals
# ==========================================================

def test_invalid_token_no_internal_leak(client):
    response = client.get(
        "/api/farmers",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401
    body = response.text.lower()
    assert "traceback" not in body
    assert "exception" not in body
    assert "hashed_password" not in body


def test_malformed_json_clean_validation_error(client, admin_headers):
    response = client.post(
        "/api/farmers",
        content="{not valid json",
        headers=admin_headers,
    )
    assert response.status_code == 422
    body = response.text.lower()
    assert "traceback" not in body
    assert "hashed_password" not in body


def test_not_found_clean_error(client, admin_headers):
    response = client.get("/api/farmers/99999999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"
    assert "traceback" not in response.text.lower()


def test_duplicate_error_no_sql_leak(client, admin_headers):
    payload = farmer_payload()

    first = client.post("/api/farmers", json=payload, headers=admin_headers)
    assert first.status_code == 200

    second = client.post("/api/farmers", json=payload, headers=admin_headers)
    assert second.status_code == 409
    body = second.text.lower()
    assert "integrityerror" not in body
    assert "sqlalchemy" not in body


def test_user_out_never_exposes_password_hash(client, user_headers):
    response = client.get("/api/auth/me", headers=user_headers)
    assert response.status_code == 200
    body = response.json()
    assert "hashed_password" not in body
    assert "password" not in body


# ==========================================================
# D. No permissive CORS headers
# ==========================================================

def test_no_permissive_cors_headers(client):
    get_response = client.get("/api/farmers")
    assert get_response.headers.get("access-control-allow-origin") is None

    options_response = client.options("/api/farmers")
    assert options_response.headers.get("access-control-allow-origin") is None
