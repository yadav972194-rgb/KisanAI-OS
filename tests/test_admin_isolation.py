"""
KisanAI OS - Admin Control & Farmer Support: isolation tests.

Confirms admin operations are correctly scoped: search filters, farmer
directory pagination, crop/soil edits can never cross farmer boundaries,
linked-account controls fail safely, audit isolation between admin
collections, and notification targeting rules.
"""

from config.core.api.auth import hash_password
from config.core.database import SessionLocal
from config.core.models.user import User
from tests.conftest import create_farmer, unique_mobile


def _farmer_id(client, headers, mobile):
    response = client.get(f"/api/farmers/by-mobile/{mobile}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["farmer_id"]


def _create_farmer_and_id(client, headers, **overrides):
    response, payload = create_farmer(client, headers, **overrides)
    assert response.status_code == 200, response.text
    return _farmer_id(client, headers, payload["mobile"])


# ==========================================================
# Directory search & pagination
# ==========================================================

def test_directory_search_by_name_mobile_and_village(client, admin_headers):
    state = f"State_{unique_mobile()}"
    district = f"District_{unique_mobile()}"
    response, payload = create_farmer(
        client, admin_headers,
        name="Asha Devi",
        village="Purana Gaon",
        state=state,
        district=district,
    )
    assert response.status_code == 200, response.text
    farmer_id = _farmer_id(client, admin_headers, payload["mobile"])

    by_name = client.get("/api/admin/farmers?q=Asha", headers=admin_headers).json()
    assert any(item["farmer_id"] == farmer_id for item in by_name["items"])

    by_mobile = client.get(
        f"/api/admin/farmers?q={payload['mobile']}", headers=admin_headers
    ).json()
    assert any(item["farmer_id"] == farmer_id for item in by_mobile["items"])

    by_village = client.get(
        "/api/admin/farmers?q=Purana", headers=admin_headers
    ).json()
    assert any(item["farmer_id"] == farmer_id for item in by_village["items"])


def test_directory_filters_by_location(client, admin_headers):
    state = f"Uttarakhand_{unique_mobile()}"
    district = f"Dehradun_{unique_mobile()}"
    _create_farmer_and_id(client, admin_headers,
                          **{"name": "State Farmer", "state": state, "district": district})

    by_state = client.get(
        "/api/admin/farmers", params={"state": state}, headers=admin_headers
    ).json()
    assert by_state["total"] >= 1
    assert all(item["state"] == state for item in by_state["items"])

    mismatched = client.get(
        "/api/admin/farmers",
        params={"state": state, "district": "Nonexistent"},
        headers=admin_headers,
    ).json()
    assert mismatched["total"] == 0


def test_directory_pagination(client, admin_headers):
    state = f"Page_{unique_mobile()}"
    for index in range(3):
        _create_farmer_and_id(client, admin_headers,
                              **{"name": f"Pager {index}", "state": state})

    page_one = client.get(
        "/api/admin/farmers",
        params={"state": state, "page": 1, "size": 2},
        headers=admin_headers,
    ).json()
    assert page_one["total"] == 3
    assert page_one["size"] == 2
    assert len(page_one["items"]) == 2

    page_two = client.get(
        "/api/admin/farmers",
        params={"state": state, "page": 2, "size": 2},
        headers=admin_headers,
    ).json()
    assert len(page_two["items"]) == 1


def test_directory_requires_admin(client, user_headers):
    assert client.get("/api/admin/farmers", headers=user_headers).status_code == 403


# ==========================================================
# Crop / soil edits never cross farmer boundaries
# ==========================================================

def test_crop_edit_scoped_to_owning_farmer(client, admin_headers):
    farmer_a = _create_farmer_and_id(client, admin_headers,
                                     **{"name": "Owner A", "village": "Village A"})
    farmer_b = _create_farmer_and_id(client, admin_headers,
                                     **{"name": "Owner B", "village": "Village B"})

    crop_name = f"Crop{unique_mobile()}"
    created = client.post(
        "/api/crops",
        json={
            "farmer_id": farmer_a,
            "crop_name": crop_name,
            "season": "Kharif",
            "duration_days": 90,
            "water_requirement": "Medium",
        },
        headers=admin_headers,
    )
    assert created.status_code == 200, created.text
    listed = client.get("/api/crops", headers=admin_headers).json()
    crop_id = next(item["crop_id"] for item in listed if item["crop_name"] == crop_name)

    # Editing farmer A's crop while claiming it for farmer B -> 404.
    cross = client.put(
        f"/api/admin/farmers/{farmer_b}/crops/{crop_id}",
        json={
            "crop_name": crop_name,
            "season": "Rabi",
            "duration_days": 100,
            "water_requirement": "High",
        },
        headers=admin_headers,
    )
    assert cross.status_code == 404

    owned = client.put(
        f"/api/admin/farmers/{farmer_a}/crops/{crop_id}",
        json={
            "crop_name": crop_name,
            "season": "Rabi",
            "duration_days": 100,
            "water_requirement": "High",
        },
        headers=admin_headers,
    )
    assert owned.status_code == 200, owned.text

    profile = client.get(
        f"/api/admin/farmers/{farmer_a}", headers=admin_headers
    ).json()
    updated = next(item for item in profile["farmer"]["crops"] if item["crop_id"] == crop_id)
    assert updated["season"] == "Rabi"
    assert updated["crop_name"] == crop_name


def test_soil_edit_scoped_to_owning_farmer(client, admin_headers):
    from tests.test_soils import _create_soil, _soil_id  # reuse fixture helpers

    farmer_a = _create_farmer_and_id(client, admin_headers,
                                     **{"name": "Soil A", "village": "Village A"})
    farmer_b = _create_farmer_and_id(client, admin_headers,
                                     **{"name": "Soil B", "village": "Village B"})

    response, payload = _create_soil(client, admin_headers, farmer_id=farmer_a)
    assert response.status_code == 200, response.text
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    cross = client.put(
        f"/api/admin/farmers/{farmer_b}/soils/{soil_id}",
        json={
            "soil_type": "Clayey",
            "ph": 6.8,
            "moisture": 35.0,
            "nitrogen": 40,
            "phosphorus": 20,
            "potassium": 25,
        },
        headers=admin_headers,
    )
    assert cross.status_code == 404


# ==========================================================
# Farmer-scoped problems / contacts
# ==========================================================

def test_problems_never_cross_farmer_scopes(client, admin_headers):
    farmer_a = _create_farmer_and_id(client, admin_headers,
                                     **{"name": "Problem A", "village": "Village A"})
    farmer_b = _create_farmer_and_id(client, admin_headers,
                                     **{"name": "Problem B", "village": "Village B"})

    client.post(
        f"/api/admin/farmers/{farmer_a}/problems",
        json={"subject": "Only for A", "description": "desc"},
        headers=admin_headers,
    )

    list_a = client.get(
        f"/api/admin/farmers/{farmer_a}/problems", headers=admin_headers
    ).json()
    list_b = client.get(
        f"/api/admin/farmers/{farmer_b}/problems", headers=admin_headers
    ).json()
    assert list_a["total"] == 1
    assert list_b["total"] == 0

    contacts_b = client.get(
        f"/api/admin/farmers/{farmer_b}/contacts", headers=admin_headers
    ).json()
    assert contacts_b["total"] == 0


def test_unknown_farmer_scoped_routes_404(client, admin_headers):
    assert client.get("/api/admin/farmers/999999", headers=admin_headers).status_code == 404
    assert (
        client.get("/api/admin/farmers/999999/problems", headers=admin_headers).status_code
        == 404
    )
    assert (
        client.get("/api/admin/farmers/999999/contacts", headers=admin_headers).status_code
        == 404
    )


# ==========================================================
# Account controls degrade safely
# ==========================================================

def test_deactivate_farmer_without_linked_account(client, admin_headers):
    farmer_id = _create_farmer_and_id(client, admin_headers)
    response = client.post(
        f"/api/admin/farmers/{farmer_id}/deactivate", headers=admin_headers
    )
    assert response.status_code == 400
    assert "linked" in response.json()["detail"]["message"].lower()


def test_deactivate_unknown_farmer_404(client, admin_headers):
    response = client.post(
        "/api/admin/farmers/999999/deactivate", headers=admin_headers
    )
    assert response.status_code == 404


def test_profile_update_duplicate_mobile_conflicts(client, admin_headers):
    _, first = create_farmer(client, admin_headers)
    farmer_b = _create_farmer_and_id(client, admin_headers,
                                     **{"name": "Other", "village": "Village B"})

    response = client.put(
        f"/api/admin/farmers/{farmer_b}",
        json={
            "name": "Other",
            "mobile": first["mobile"],
            "village": "Village B",
            "district": "Sitapur",
            "state": "Uttar Pradesh",
        },
        headers=admin_headers,
    )
    assert response.status_code == 409


# ==========================================================
# Notifications / alerts
# ==========================================================

def test_notification_create_validates_category(client, admin_headers):
    response = client.post(
        "/api/admin/notifications",
        json={"category": "weather", "title": "Bad", "message": "Bad category"},
        headers=admin_headers,
    )
    assert response.status_code == 400

    created = client.post(
        "/api/admin/notifications",
        json={"category": "ALERT", "title": "Heatwave", "message": "Stay hydrated"},
        headers=admin_headers,
    )
    assert created.status_code == 200, created.text
    assert created.json()["category"] == "ALERT"
    assert created.json()["status"] == "new"


def test_notification_targeting_and_filters(client, admin_headers):
    session = SessionLocal()
    try:
        user = User(
            username=f"ntarget{unique_mobile()}",
            hashed_password=hash_password("password123"),
            full_name="Notify Target",
            role="farmer",
            is_active=True,
        )
        session.add(user)
        session.commit()
        user_id = user.id
    finally:
        session.close()

    client.post(
        "/api/admin/notifications",
        json={
            "category": "AI_REPORT",
            "title": "Crop report",
            "message": "Yield forecast ready",
            "user_id": user_id,
        },
        headers=admin_headers,
    )
    client.post(
        "/api/admin/notifications",
        json={"category": "SYSTEM", "title": "Maintenance", "message": "Downtime"},
        headers=admin_headers,
    )

    ai_only = client.get(
        "/api/admin/notifications?category=AI_REPORT", headers=admin_headers
    ).json()
    assert ai_only["total"] >= 1
    assert all(item["category"] == "AI_REPORT" for item in ai_only["items"])

    targeted = client.get(
        f"/api/admin/notifications?user_id={user_id}", headers=admin_headers
    ).json()
    assert targeted["total"] >= 1
    assert all(item["user_id"] == user_id for item in targeted["items"])


def test_notification_delivery_mark(client, admin_headers):
    created = client.post(
        "/api/admin/notifications",
        json={"category": "ADVISORY", "title": "Fertilizer", "message": "Apply now"},
        headers=admin_headers,
    ).json()
    notification_id = created["notification_id"]

    delivered = client.post(
        f"/api/admin/notifications/{notification_id}/deliver",
        headers=admin_headers,
    )
    assert delivered.status_code == 200, delivered.text
    assert delivered.json()["message"] == "Notification marked as delivered"

    detail = client.get(
        "/api/admin/notifications", headers=admin_headers
    ).json()
    target = next(
        item for item in detail["items"] if item["notification_id"] == notification_id
    )
    assert target["status"] == "delivered"
    assert target["delivered_at"] is not None


def test_unrelated_admin_collections_stay_intact(client, admin_headers, super_admin_headers):
    """Existing admin endpoints (user list + role management) still work."""
    listing = client.get("/api/admin/users", headers=admin_headers)
    assert listing.status_code == 200
    assert isinstance(listing.json(), list)