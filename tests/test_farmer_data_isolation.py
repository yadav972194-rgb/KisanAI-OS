"""
KisanAI OS - Farmer data isolation (C-1 security regression).

Locked requirement: a farmer must never read another farmer's private
data. The legacy read endpoints (/api/farmers, /api/crops, /api/soils)
previously returned every farmer's rows to any authenticated user.

These tests cover farmer-to-farmer isolation (both directions), admin
and super_admin access, unauthenticated behaviour, the unchanged
/api/my-farm/* contract, and the unchanged response shape.

Note: soil has no self-service route (it is created by an admin against
a farmer_id), so soil fixtures go through POST /api/soils.
"""

import json

import pytest

from tests.conftest import unique_mobile


# ==========================================================
# Helpers
# ==========================================================

def _login_farmer(client):
    """Register + log in a fresh farmer through the public endpoints.

    A unique mobile is required because the self-service farm creation
    copies the account mobile into ``farmers.mobile``, which is unique.
    """
    username = f"isofarmer{unique_mobile()}"
    register = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "Isolation Farmer",
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


def _ensure_farm(client, headers, **overrides):
    """Create the caller's farm through the real self-service flow, or
    return the existing one so the helper is safe to call twice."""
    existing = client.get("/api/my-farm", headers=headers)
    if existing.status_code == 200:
        return existing.json()

    payload = {
        "village": "Sitapur",
        "district": "Sitapur",
        "state": "Uttar Pradesh",
        "farm_size": 2.5,
    }
    payload.update(overrides)

    created = client.post("/api/my-farm", json=payload, headers=headers)
    assert created.status_code == 200, created.text
    return client.get("/api/my-farm", headers=headers).json()


def _add_own_crop(client, headers, crop_name):
    """Add a crop to the caller's own farm and return the stored record.

    The create endpoint answers with MessageOut, so the id is resolved
    through the caller's own (scoped) crop list.
    """
    response = client.post(
        "/api/my-farm/crops",
        json={
            "crop_name": crop_name,
            "season": "Kharif",
            "duration_days": 110,
            "water_requirement": "Medium",
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text

    listed = client.get("/api/crops", headers=headers).json()
    match = [c for c in listed if c["crop_name"] == crop_name]
    assert match, f"crop {crop_name!r} not visible to its owner: {listed}"
    return match[0]


def _add_admin_soil(client, owner_headers, admin_headers, farmer_id, **overrides):
    """Create a soil reading for a farm (admin-only route) and return it."""
    soil_type = f"IsoLoam{unique_mobile()}"
    payload = {
        "farmer_id": farmer_id,
        "soil_type": soil_type,
        "ph": 6.5,
        "moisture": 40.0,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
    }
    payload.update(overrides)

    created = client.post("/api/soils", json=payload, headers=admin_headers)
    assert created.status_code == 200, created.text

    listed = client.get("/api/soils", headers=owner_headers).json()
    match = [s for s in listed if s["soil_type"] == soil_type]
    assert match, f"soil {soil_type!r} not visible to its owner: {listed}"
    return match[0]


@pytest.fixture
def farmer_a(client):
    return _login_farmer(client)


@pytest.fixture
def farmer_b(client):
    return _login_farmer(client)


# ==========================================================
# A. A farmer can read their own record
# ==========================================================

def test_farmer_reads_own_farm_record(client, farmer_a):
    own = _ensure_farm(client, farmer_a)

    response = client.get(f"/api/farmers/{own['farmer_id']}", headers=farmer_a)
    assert response.status_code == 200
    assert response.json()["farmer_id"] == own["farmer_id"]


def test_farmer_list_returns_only_own_farm(client, farmer_a, farmer_b):
    own = _ensure_farm(client, farmer_a)
    _ensure_farm(client, farmer_b)

    listed = client.get("/api/farmers", headers=farmer_a).json()
    assert [f["farmer_id"] for f in listed] == [own["farmer_id"]]


def test_farmer_reads_own_crop_and_soil(client, farmer_a, admin_headers):
    own = _ensure_farm(client, farmer_a)
    crop = _add_own_crop(client, farmer_a, "Isolation Basmati")
    soil = _add_admin_soil(
        client, farmer_a, admin_headers, own["farmer_id"]
    )

    crops = client.get("/api/crops", headers=farmer_a).json()
    assert [c["crop_id"] for c in crops] == [crop["crop_id"]]

    soils = client.get("/api/soils", headers=farmer_a).json()
    assert [s["soil_id"] for s in soils] == [soil["soil_id"]]

    assert client.get(
        f"/api/crops/{crop['crop_id']}", headers=farmer_a
    ).status_code == 200
    assert client.get(
        f"/api/soils/{soil['soil_id']}", headers=farmer_a
    ).status_code == 200


def test_farmer_can_lookup_own_mobile(client, farmer_a):
    own = _ensure_farm(client, farmer_a)

    response = client.get(
        f"/api/farmers/by-mobile/{own['mobile']}", headers=farmer_a
    )
    assert response.status_code == 200
    assert response.json()["farmer_id"] == own["farmer_id"]


# ==========================================================
# B/C. Farmer A cannot read Farmer B (both directions)
# ==========================================================

def test_farmer_a_cannot_read_farmer_b_record(client, farmer_a, farmer_b):
    farm_b = _ensure_farm(client, farmer_b)

    response = client.get(
        f"/api/farmers/{farm_b['farmer_id']}", headers=farmer_a
    )
    assert response.status_code == 404
    assert farm_b["mobile"] not in response.text
    assert farm_b["village"] not in response.text


def test_farmer_b_cannot_read_farmer_a_record(client, farmer_a, farmer_b):
    farm_a = _ensure_farm(client, farmer_a)

    response = client.get(
        f"/api/farmers/{farm_a['farmer_id']}", headers=farmer_b
    )
    assert response.status_code == 404


def test_farmer_a_cannot_enumerate_farmer_b_via_list(
    client, farmer_a, farmer_b
):
    farm_b = _ensure_farm(client, farmer_b)

    listed = client.get("/api/farmers", headers=farmer_a).json()
    payload = json.dumps(listed)
    assert str(farm_b["farmer_id"]) not in [
        str(f["farmer_id"]) for f in listed
    ]
    assert farm_b["mobile"] not in payload


def test_farmer_a_cannot_probe_farmer_b_mobile(client, farmer_a, farmer_b):
    farm_b = _ensure_farm(client, farmer_b)

    response = client.get(
        f"/api/farmers/by-mobile/{farm_b['mobile']}", headers=farmer_a
    )
    assert response.status_code == 404


def test_farmer_a_cannot_read_farmer_b_crop_or_soil(
    client, farmer_a, farmer_b, admin_headers
):
    _ensure_farm(client, farmer_a)
    farm_b = _ensure_farm(client, farmer_b)

    crop_b = _add_own_crop(client, farmer_b, "B Only Isolation")
    soil_b = _add_admin_soil(
        client, farmer_b, admin_headers, farm_b["farmer_id"]
    )

    crop_response = client.get(
        f"/api/crops/{crop_b['crop_id']}", headers=farmer_a
    )
    soil_response = client.get(
        f"/api/soils/{soil_b['soil_id']}", headers=farmer_a
    )

    assert crop_response.status_code == 404
    assert soil_response.status_code == 404
    assert crop_b["crop_name"] not in crop_response.text
    assert soil_b["soil_type"] not in soil_response.text


def test_farmer_id_filter_cannot_select_another_farm(
    client, farmer_a, farmer_b
):
    _ensure_farm(client, farmer_a)
    farm_b = _ensure_farm(client, farmer_b)
    _add_own_crop(client, farmer_b, "Filter Probe Wheat")

    response = client.get(
        f"/api/crops?farmer_id={farm_b['farmer_id']}", headers=farmer_a
    )
    assert response.status_code == 200
    assert "Filter Probe Wheat" not in response.text


def test_farmer_without_farm_sees_empty_lists(client, farmer_a):
    assert client.get("/api/farmers", headers=farmer_a).json() == []
    assert client.get("/api/crops", headers=farmer_a).json() == []
    assert client.get("/api/soils", headers=farmer_a).json() == []


# ==========================================================
# D. Admin / super_admin access preserved
# ==========================================================

def test_admin_still_reads_every_record(
    client, farmer_a, farmer_b, admin_headers
):
    farm_a = _ensure_farm(client, farmer_a)
    farm_b = _ensure_farm(client, farmer_b)

    listed = client.get("/api/farmers", headers=admin_headers).json()
    ids = [f["farmer_id"] for f in listed]
    assert farm_a["farmer_id"] in ids
    assert farm_b["farmer_id"] in ids

    assert client.get(
        f"/api/farmers/{farm_b['farmer_id']}", headers=admin_headers
    ).status_code == 200
    assert client.get(
        f"/api/farmers/by-mobile/{farm_b['mobile']}", headers=admin_headers
    ).status_code == 200
    assert client.get(
        f"/api/crops?farmer_id={farm_a['farmer_id']}", headers=admin_headers
    ).status_code == 200


def test_super_admin_still_reads_every_record(
    client, farmer_a, super_admin_headers
):
    farm_a = _ensure_farm(client, farmer_a)

    listed = client.get("/api/farmers", headers=super_admin_headers).json()
    assert farm_a["farmer_id"] in [f["farmer_id"] for f in listed]


# ==========================================================
# E. Unauthenticated behaviour preserved
# ==========================================================

def test_unauthenticated_reads_still_rejected(client):
    assert client.get("/api/farmers").status_code == 401
    assert client.get("/api/crops").status_code == 401
    assert client.get("/api/soils").status_code == 401
    assert client.get("/api/farmers/1").status_code == 401
    assert client.get("/api/crops/1").status_code == 401
    assert client.get("/api/soils/1").status_code == 401
    assert client.get("/api/farmers/by-mobile/9000000000").status_code == 401


# ==========================================================
# F. /api/my-farm/* contract untouched
# ==========================================================

def test_my_farm_contract_still_works(client, farmer_a):
    own = _ensure_farm(client, farmer_a)
    assert client.get("/api/my-farm", headers=farmer_a).json() == own

    crop = _add_own_crop(client, farmer_a, "My Farm Isolation Wheat")
    listed = client.get("/api/my-farm/crops", headers=farmer_a).json()
    assert [c["crop_id"] for c in listed] == [crop["crop_id"]]


def test_my_farm_rejects_second_farm_for_same_user(client, farmer_a):
    _ensure_farm(client, farmer_a)

    response = client.post(
        "/api/my-farm",
        json={"village": "Other", "district": "Other", "state": "Uttar Pradesh"},
        headers=farmer_a,
    )
    assert response.status_code == 409


# ==========================================================
# G. Response shape preserved
# ==========================================================

def test_response_shape_unchanged(client, farmer_a, admin_headers):
    own = _ensure_farm(client, farmer_a)
    _add_own_crop(client, farmer_a, "Shape Check Sorghum")
    _add_admin_soil(client, farmer_a, admin_headers, own["farmer_id"])

    for path, key in (
        ("/api/farmers", "farmer_id"),
        ("/api/crops", "crop_id"),
        ("/api/soils", "soil_id"),
    ):
        scoped = client.get(path, headers=farmer_a)
        staff = client.get(path, headers=admin_headers)

        assert scoped.status_code == 200
        assert staff.status_code == 200
        assert len(scoped.json()) == 1
        assert key in scoped.json()[0]
        assert set(scoped.json()[0].keys()) == set(staff.json()[0].keys())
