"""
KisanAI OS - Farmer-side Feedback API (Farmer Feedback / "Kisan ki Baat").

Self-service feedback endpoints:

  POST /api/feedback  - raise own feedback (ownership bound server-side)
  GET  /api/feedback  - read own feedback only

Locked requirement: a farmer must never be able to create or read another
farmer's feedback by supplying another farmer_id or user_id. Ownership is
therefore derived from the bearer token on every call; the payload and the
query string can never re-point a record at somebody else.
"""

from tests.conftest import unique_mobile


# ==========================================================
# Helpers
# ==========================================================

def _login_farmer(client, prefix="fbfarmer"):
    """Register + log in a fresh farmer account; return auth headers."""
    username = f"{prefix}{unique_mobile()}"
    register = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "Feedback Farmer",
            "mobile": unique_mobile(),
        },
    )
    assert register.status_code == 200, register.text

    login = client.post(
        "/api/auth/token",
        data={"username": username, "password": "password123"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def _own_user_id(client, headers):
    """Authenticated user id, resolved from the real identity endpoint."""
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _ensure_farm(client, headers):
    """Create the caller's farm through the self-service flow (idempotent)."""
    existing = client.get("/api/my-farm", headers=headers)
    if existing.status_code == 200:
        return existing.json()

    created = client.post(
        "/api/my-farm",
        json={
            "village": "Sitapur",
            "district": "Sitapur",
            "state": "Uttar Pradesh",
            "farm_size": 2.5,
        },
        headers=headers,
    )
    assert created.status_code == 200, created.text

    farm = client.get("/api/my-farm", headers=headers)
    assert farm.status_code == 200, farm.text
    return farm.json()


def _payload(**overrides):
    body = {
        "subject": "Irrigation pump failure",
        "description": "Water pump stopped working after the storm",
        "priority": "high",
    }
    body.update(overrides)
    return body


# ==========================================================
# Tests
# ==========================================================

def test_authenticated_farmer_creates_own_feedback(client):
    headers = _login_farmer(client)
    farm = _ensure_farm(client, headers)
    own_id = _own_user_id(client, headers)

    response = client.post("/api/feedback", json=_payload(), headers=headers)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["feedback_id"] > 0
    assert body["subject"] == "Irrigation pump failure"
    assert body["description"] == "Water pump stopped working after the storm"
    assert body["priority"] == "high"
    assert body["status"] == "new"
    # Ownership comes from the token; the farm is resolved server-side.
    assert body["user_id"] == own_id
    assert body["farmer_id"] == farm["farmer_id"]

    listed = client.get("/api/feedback", headers=headers).json()
    assert listed["total"] == 1
    assert listed["items"][0]["feedback_id"] == body["feedback_id"]
    assert all(item["user_id"] == own_id for item in listed["items"])

    # A farmer token can never reach the admin-only feedback endpoints.
    admin_list = client.get(
        f"/api/admin/farmers/{farm['farmer_id']}/problems",
        headers=headers,
    )
    assert admin_list.status_code == 403


def test_authenticated_farmer_retrieves_own_feedback(client):
    headers = _login_farmer(client)
    _ensure_farm(client, headers)
    own_id = _own_user_id(client, headers)

    created_ids = []
    for overrides in (
        {"subject": "Seed quality issue", "description": "Germination below expectation"},
        {"subject": "Fertilizer shortage", "description": "Local dealer out of stock"},
    ):
        created = client.post(
            "/api/feedback", json=_payload(**overrides), headers=headers
        )
        assert created.status_code == 200, created.text
        created_ids.append(created.json()["feedback_id"])

    listed = client.get("/api/feedback", headers=headers).json()
    assert listed["total"] == 2
    assert listed["page"] == 1
    assert {item["feedback_id"] for item in listed["items"]} == set(created_ids)
    assert all(item["user_id"] == own_id for item in listed["items"])
    # Newest first.
    order = [item["feedback_id"] for item in listed["items"]]
    assert order == sorted(order, reverse=True)


def test_farmer_cannot_read_another_farmers_feedback(client):
    owner_headers = _login_farmer(client, "fbowner")
    owner_farm = _ensure_farm(client, owner_headers)

    stranger_headers = _login_farmer(client, "fbstranger")
    _ensure_farm(client, stranger_headers)

    created = client.post(
        "/api/feedback",
        json=_payload(subject="Private problem A", description="Only for owner"),
        headers=owner_headers,
    )
    assert created.status_code == 200, created.text

    stranger_list = client.get("/api/feedback", headers=stranger_headers).json()
    assert stranger_list["total"] == 0
    assert stranger_list["items"] == []

    # Client-supplied farmer_id in the query string is never honoured.
    forged = client.get(
        f"/api/feedback?farmer_id={owner_farm['farmer_id']}",
        headers=stranger_headers,
    )
    assert forged.status_code == 200, forged.text
    assert forged.json()["total"] == 0
    assert forged.json()["items"] == []


def test_supplied_ids_cannot_override_server_side_ownership(client):
    farmer_a = _login_farmer(client, "fbmine")
    farm_a = _ensure_farm(client, farmer_a)
    user_a = _own_user_id(client, farmer_a)

    farmer_b = _login_farmer(client, "fbtheirs")
    farm_b = _ensure_farm(client, farmer_b)
    user_b = _own_user_id(client, farmer_b)

    # Deliberate override attempt: claim B's farmer_id and B's user_id.
    created = client.post(
        "/api/feedback",
        json=_payload(
            subject="Owned record",
            description="Filed by farmer A",
            priority="medium",
            farmer_id=farm_b["farmer_id"],
            user_id=user_b,
        ),
        headers=farmer_a,
    )
    assert created.status_code == 200, created.text

    body = created.json()
    assert body["farmer_id"] == farm_a["farmer_id"]
    assert body["farmer_id"] != farm_b["farmer_id"]
    assert body["user_id"] == user_a
    assert body["user_id"] != user_b

    a_list = client.get("/api/feedback", headers=farmer_a).json()
    b_list = client.get("/api/feedback", headers=farmer_b).json()

    assert [item["subject"] for item in a_list["items"]] == ["Owned record"]
    assert b_list["total"] == 0
    assert b_list["items"] == []


def test_feedback_requires_authentication(client):
    unauthenticated = client.post(
        "/api/feedback", json=_payload(subject="No token", description="Should fail")
    )
    assert unauthenticated.status_code == 401

    listing = client.get("/api/feedback")
    assert listing.status_code == 401
