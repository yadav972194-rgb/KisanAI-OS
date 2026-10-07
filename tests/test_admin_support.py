"""
KisanAI OS - Admin Control & Farmer Support: Rechnungen/feedback module tests.

Covers the farmer problem (feedback) workflow endpoints under /api/admin:
create/list/get/update, valid + invalid status transitions, contact
records, permission gates (admins only), and path-scoped farmer routes.
"""

import random

from tests.conftest import create_farmer, unique_mobile


def _farmer_id(client, headers, mobile):
    response = client.get(f"/api/farmers/by-mobile/{mobile}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["farmer_id"]


def _create_farmer_and_id(client, headers, **overrides):
    response, payload = create_farmer(client, headers, **overrides)
    assert response.status_code == 200, response.text
    return _farmer_id(client, headers, payload["mobile"]), payload


# ==========================================================
# Access control
# ==========================================================

def test_admin_endpoints_require_auth(client):
    assert client.get("/api/admin/me").status_code == 401
    assert client.get("/api/admin/farmers").status_code == 401
    assert client.get("/api/admin/problems").status_code == 401
    assert client.get("/api/admin/audit").status_code == 401


def test_farmer_role_cannot_use_admin_module(client, user_headers):
    assert client.get("/api/admin/farmers", headers=user_headers).status_code == 403


def test_expert_role_cannot_use_admin_module(client):
    import random

    uniq = random.randint(100000, 999999)
    client.post(
        "/api/auth/register",
        json={
            "username": f"expert{uniq}",
            "password": "password123",
            "full_name": "Expert",
            "mobile": unique_mobile(),
            "role": "expert",
        },
    )
    login = client.post(
        "/api/auth/token",
        data={"username": f"expert{uniq}", "password": "password123"},
    )
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.get("/api/admin/me", headers=headers).status_code == 403


def test_admin_me_returns_identity(client, admin_headers):
    response = client.get("/api/admin/me", headers=admin_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["role"] == "admin"
    assert "super_admin" in body
    assert "username" in body


# ==========================================================
# Farmer problems / feedback
# ==========================================================

def test_create_problem_for_farmer(client, admin_headers):
    farmer_id, _ = _create_farmer_and_id(client, admin_headers)
    response = client.post(
        f"/api/admin/farmers/{farmer_id}/problems",
        json={"subject": "Poor germination", "description": "Seeds did not sprout"},
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["farmer_id"] == farmer_id
    assert body["status"] == "new"
    assert body["priority"] == "medium"
    assert body["subject"] == "Poor germination"


def test_create_problem_globally_with_farmer_id(client, admin_headers):
    farmer_id, _ = _create_farmer_and_id(client, admin_headers)
    response = client.post(
        "/api/admin/problems",
        json={
            "subject": "Pest attack",
            "description": "Whitefly on cotton",
            "farmer_id": farmer_id,
            "priority": "high",
        },
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["priority"] == "high"


def test_create_problem_rejects_unknown_farmer(client, admin_headers):
    response = client.post(
        "/api/admin/farmers/999999/problems",
        json={"subject": "X", "description": "Y"},
        headers=admin_headers,
    )
    assert response.status_code == 404


def test_create_problem_rejects_invalid_priority(client, admin_headers):
    farmer_id, _ = _create_farmer_and_id(client, admin_headers)
    response = client.post(
        f"/api/admin/farmers/{farmer_id}/problems",
        json={
            "subject": "X",
            "description": "Y",
            "priority": "urgent",
        },
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_list_and_filter_problems(client, admin_headers):
    farmer_id, _ = _create_farmer_and_id(client, admin_headers)
    client.post(
        f"/api/admin/farmers/{farmer_id}/problems",
        json={"subject": "Low yield", "description": "About 20% below normal"},
        headers=admin_headers,
    )
    client.post(
        "/api/admin/problems",
        json={"subject": "High priority", "description": "Immediate", "priority": "high"},
        headers=admin_headers,
    )

    all_problems = client.get("/api/admin/problems", headers=admin_headers).json()
    assert all_problems["total"] >= 2
    assert all_problems["size"] == 20

    high = client.get(
        "/api/admin/problems?priority=high", headers=admin_headers
    ).json()
    assert high["total"] >= 1
    assert all(item["priority"] == "high" for item in high["items"])

    farmer_problems = client.get(
        f"/api/admin/farmers/{farmer_id}/problems", headers=admin_headers
    ).json()
    assert farmer_problems["total"] >= 1
    assert all(item["farmer_id"] == farmer_id for item in farmer_problems["items"])


def test_get_and_partial_update_problem(client, admin_headers):
    farmer_id, _ = _create_farmer_and_id(client, admin_headers)
    created = client.post(
        f"/api/admin/farmers/{farmer_id}/problems",
        json={"subject": "Leaf curl", "description": "Young leaves curling"},
        headers=admin_headers,
    ).json()

    fetched = client.get(
        f"/api/admin/problems/{created['feedback_id']}", headers=admin_headers
    )
    assert fetched.status_code == 200
    assert fetched.json()["feedback_id"] == created["feedback_id"]

    updated = client.put(
        f"/api/admin/problems/{created['feedback_id']}",
        json={"priority": "high"},
        headers=admin_headers,
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["priority"] == "high"
    assert updated.json()["subject"] == "Leaf curl"


def test_valid_status_workflow(client, admin_headers):
    created = client.post(
        "/api/admin/problems",
        json={"subject": "Water shortage", "description": "Channel dry"},
        headers=admin_headers,
    ).json()
    feedback_id = created["feedback_id"]

    flow = ["investigating", "contacted", "in_progress", "resolved", "closed"]
    for expected in flow:
        response = client.patch(
            f"/api/admin/problems/{feedback_id}/status",
            json={"status": expected},
            headers=admin_headers,
        )
        assert response.status_code == 200, response.text
        assert response.json()["status"] == expected

    reopened = client.patch(
        f"/api/admin/problems/{feedback_id}/status",
        json={"status": "new"},
        headers=admin_headers,
    )
    assert reopened.status_code == 200
    assert reopened.json()["status"] == "new"


def test_invalid_transition_is_rejected(client, admin_headers):
    created = client.post(
        "/api/admin/problems",
        json={"subject": "Unknown", "description": "Case"},
        headers=admin_headers,
    ).json()
    response = client.patch(
        f"/api/admin/problems/{created['feedback_id']}/status",
        json={"status": "resolved"},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_invalid_status_value_is_rejected(client, admin_headers):
    created = client.post(
        "/api/admin/problems",
        json={"subject": "X", "description": "Y"},
        headers=admin_headers,
    ).json()
    response = client.patch(
        f"/api/admin/problems/{created['feedback_id']}/status",
        json={"status": "escalated"},
        headers=admin_headers,
    )
    assert response.status_code == 422


# ==========================================================
# Contact records
# ==========================================================

def test_record_and_list_contact(client, admin_headers):
    farmer_id, _ = _create_farmer_and_id(client, admin_headers)
    created = client.post(
        f"/api/admin/farmers/{farmer_id}/contacts",
        json={
            "channel": "phone",
            "reason": "Follow up on reported pest problem",
            "note": "Farmer was unavailable, trying again tomorrow",
        },
        headers=admin_headers,
    )
    assert created.status_code == 200, created.text
    body = created.json()
    assert body["farmer_id"] == farmer_id
    assert body["channel"] == "phone"
    assert body["reason"] == "Follow up on reported pest problem"

    listed = client.get(
        f"/api/admin/farmers/{farmer_id}/contacts", headers=admin_headers
    ).json()
    assert listed["total"] == 1
    assert listed["items"][0]["contact_id"] == body["contact_id"]


def test_contact_rejects_invalid_channel(client, admin_headers):
    farmer_id, _ = _create_farmer_and_id(client, admin_headers)
    response = client.post(
        f"/api/admin/farmers/{farmer_id}/contacts",
        json={"channel": "whatsapp", "reason": "test"},
        headers=admin_headers,
    )
    assert response.status_code == 422


def test_contact_rejects_unknown_farmer(client, admin_headers):
    response = client.post(
        "/api/admin/farmers/999999/contacts",
        json={"channel": "phone"},
        headers=admin_headers,
    )
    assert response.status_code == 404