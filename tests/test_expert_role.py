"""
KisanAI OS - Phase 5.9 Expert Role Activation tests.

Adds admin-managed user role management (GET /api/admin/users and
PATCH /api/admin/users/{user_id}/role) and verifies the expert role
end-to-end:

  - The ROLE_EXPERT constant is a recognized role.
  - Admin-only access control on the new endpoints (401/403/200).
  - Promotion of an existing farmer to expert takes effect immediately
    (no token re-issue) and grants read + advisory access like farmer.
  - Experts never gain admin write access (403).
  - Admin role cannot be assigned via the API (bootstrap-only), and
    invalid roles are rejected (422).
  - Public self-registration as expert is preserved.
"""

import pytest

from config.constants import ROLE_EXPERT, ROLE_FARMER
from config.core.services.user_service import VALID_ROLES
from tests.conftest import farmer_payload, unique_mobile


def _register(client, username, role="farmer"):
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "Role Test User",
            "role": role,
        },
    )
    assert response.status_code == 200, response.text
    return username


def _login(client, username):
    response = client.post(
        "/api/auth/token",
        data={"username": username, "password": "password123"},
    )
    assert response.status_code == 200, response.text
    return {
        "Authorization": f"Bearer {response.json()['access_token']}"
    }


def _user_id(client, admin_headers, username):
    for user in client.get("/api/admin/users", headers=admin_headers).json():
        if user["username"] == username:
            return user["id"]
    raise AssertionError(f"user {username} not found")


def _fresh_username():
    return f"exp{unique_mobile()}"


def _role_of(client, headers):
    return client.get("/api/auth/me", headers=headers).json()["role"]


# ==========================================================
# A. Role constant and recognized roles
# ==========================================================

def test_expert_role_constant_defined():
    assert ROLE_EXPERT == "expert"
    assert ROLE_FARMER == "farmer"
    assert ROLE_EXPERT in VALID_ROLES
    assert ROLE_FARMER in VALID_ROLES


# ==========================================================
# B. Admin endpoints - authentication and authorization
# ==========================================================

def test_admin_user_list_requires_auth_401(client):
    assert client.get("/api/admin/users").status_code == 401


def test_admin_role_update_requires_auth_401(client):
    response = client.patch(
        "/api/admin/users/1/role", json={"role": ROLE_EXPERT}
    )
    assert response.status_code == 401


def test_admin_user_list_admin_only_403(client, user_headers):
    assert client.get(
        "/api/admin/users", headers=user_headers
    ).status_code == 403


def test_admin_role_update_admin_only_403(client, user_headers):
    response = client.patch(
        "/api/admin/users/1/role",
        json={"role": ROLE_EXPERT},
        headers=user_headers,
    )
    assert response.status_code == 403


def test_admin_lists_users(client, admin_headers):
    response = client.get("/api/admin/users", headers=admin_headers)
    assert response.status_code == 200
    users = response.json()
    assert isinstance(users, list)
    assert any(u["role"] == "admin" for u in users)
    for user in users:
        assert "hashed_password" not in user
        assert set(user.keys()) == {
            "id", "username", "full_name", "mobile", "role",
            "is_active", "created_at",
        }


# ==========================================================
# C. Promotion workflow
# ==========================================================

def test_admin_promotes_farmer_to_expert(client, admin_headers):
    username = _fresh_username()
    _register(client, username, role="farmer")
    headers = _login(client, username)
    user_id = _user_id(client, admin_headers, username)

    assert _role_of(client, headers) == "farmer"

    response = client.patch(
        f"/api/admin/users/{user_id}/role",
        json={"role": ROLE_EXPERT},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    assert _role_of(client, headers) == "expert"

    farmers = client.get("/api/farmers", headers=headers)
    assert farmers.status_code == 200

    advisory = client.post(
        "/api/advisory",
        json={
            "crop_name": "Wheat",
            "soil_type": "Loamy",
            "ph": 6.8,
            "moisture": 45,
            "nitrogen": 50,
            "phosphorus": 25,
            "potassium": 30,
            "temperature": 30.3,
            "humidity": 60.0,
            "condition": "Overcast",
            "wind_speed": 6.0,
            "disease_name": "",
            "disease_severity": "",
        },
        headers=headers,
    )
    assert advisory.status_code == 200

    write = client.post(
        "/api/farmers", json=farmer_payload(), headers=headers
    )
    assert write.status_code == 403


def test_promote_expert_then_demote_to_farmer(client, admin_headers):
    username = _fresh_username()
    _register(client, username, role="farmer")
    headers = _login(client, username)
    user_id = _user_id(client, admin_headers, username)

    promoted = client.patch(
        f"/api/admin/users/{user_id}/role",
        json={"role": ROLE_EXPERT},
        headers=admin_headers,
    )
    assert promoted.status_code == 200
    assert _role_of(client, headers) == "expert"

    demoted = client.patch(
        f"/api/admin/users/{user_id}/role",
        json={"role": ROLE_FARMER},
        headers=admin_headers,
    )
    assert demoted.status_code == 200
    assert _role_of(client, headers) == "farmer"


def test_promote_nonexistent_user_404(client, admin_headers):
    response = client.patch(
        "/api/admin/users/99999999/role",
        json={"role": ROLE_EXPERT},
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["message"] == "User Not Found"


def test_promote_to_admin_rejected_422(client, admin_headers):
    username = _fresh_username()
    _register(client, username, role="farmer")
    user_id = _user_id(client, admin_headers, username)

    response = client.patch(
        f"/api/admin/users/{user_id}/role",
        json={"role": "admin"},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_promote_invalid_role_422(client, admin_headers):
    username = _fresh_username()
    _register(client, username, role="farmer")
    user_id = _user_id(client, admin_headers, username)

    response = client.patch(
        f"/api/admin/users/{user_id}/role",
        json={"role": "superuser"},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ==========================================================
# D. Public expert self-registration preserved
# ==========================================================

def test_expert_self_registration_preserved(client):
    username = _fresh_username()
    _register(client, username, role=ROLE_EXPERT)
    headers = _login(client, username)

    assert _role_of(client, headers) == "expert"
    assert client.get("/api/farmers", headers=headers).status_code == 200
    assert client.post(
        "/api/farmers", json=farmer_payload(), headers=headers
    ).status_code == 403
