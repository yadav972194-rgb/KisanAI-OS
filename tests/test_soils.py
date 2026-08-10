"""
KisanAI OS - Phase 5.3 Soil module tests.

Covers create/read/update/delete, validation, duplicate handling,
farmer linkage, referential integrity on farmer delete, and
authentication/authorization on every soil endpoint.

Regression coverage:
- BUG1: update preserves farmer_id when farmer_id is omitted.
- BUG2: invalid farmer_id returns 404 "Farmer Not Found", never leaks
  a raw IntegrityError / SQL / stack trace.
- BUG3: soil_type is normalized + blank rejected; nutrient values are
  non-negative.
"""

import pytest

from tests.conftest import create_farmer, unique_mobile


def _soil_payload(**overrides):
    payload = {
        "farmer_id": None,
        "soil_type": f"SoilType{unique_mobile()}",
        "ph": 6.5,
        "moisture": 40.0,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
    }
    payload.update(overrides)
    return payload


def _create_soil(client, headers, **overrides):
    payload = _soil_payload(**overrides)
    response = client.post("/api/soils", json=payload, headers=headers)
    return response, payload


def _soil_id(client, headers, soil_type):
    listed = client.get("/api/soils", headers=headers).json()
    for soil in listed:
        if soil["soil_type"] == soil_type:
            return soil["soil_id"]
    raise AssertionError(f"soil {soil_type} not found")


def _farmer_id(client, headers, mobile):
    listed = client.get("/api/farmers", headers=headers).json()
    for farmer in listed:
        if farmer["mobile"] == mobile:
            return farmer["farmer_id"]
    raise AssertionError(f"farmer {mobile} not found")


def _create_farmer(client, headers):
    response, payload = create_farmer(client, headers)
    assert response.status_code == 200
    return _farmer_id(client, headers, payload["mobile"])


# ==========================================================
# Create
# ==========================================================

def test_create_soil_success(client, admin_headers):
    response, _ = _create_soil(client, admin_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["message"] == "Soil Added Successfully"


def test_create_soil_with_valid_farmer(client, admin_headers):
    farmer_id = _create_farmer(client, admin_headers)
    response, _ = _create_soil(client, admin_headers, farmer_id=farmer_id)
    assert response.status_code == 200


def test_create_soil_normalizes_type(client, admin_headers):
    response, _ = _create_soil(client, admin_headers, soil_type="  Clay   Loam  ")
    assert response.status_code == 200

    detail = client.get(
        f"/api/soils/{_soil_id(client, admin_headers, 'Clay Loam')}",
        headers=admin_headers,
    )
    assert detail.status_code == 200
    assert detail.json()["soil_type"] == "Clay Loam"


# ==========================================================
# BUG2: invalid farmer must be a clean 404, never raw IntegrityError
# ==========================================================

def test_create_soil_invalid_farmer_404_no_leak(client, admin_headers):
    response, _ = _create_soil(client, admin_headers, farmer_id=99999999)
    assert response.status_code == 404
    body = response.text.lower()
    assert response.json()["message"] == "Farmer Not Found"
    assert "integrityerror" not in body
    assert "foreign key" not in body
    assert "sqlite" not in body
    assert "traceback" not in body


# ==========================================================
# BUG3: validation
# ==========================================================

@pytest.mark.parametrize(
    "overrides",
    [
        {"soil_type": ""},
        {"soil_type": "   "},
        {"ph": -0.1},
        {"ph": 14.1},
        {"moisture": -0.1},
        {"moisture": 100.1},
        {"nitrogen": -1},
        {"phosphorus": -1},
        {"potassium": -1},
        {"nitrogen": "abc"},
    ],
)
def test_create_soil_validation_422(client, admin_headers, overrides):
    response, _ = _create_soil(client, admin_headers, **overrides)
    assert response.status_code == 422


def test_create_soil_missing_required_field_422(client, admin_headers):
    payload = _soil_payload()
    del payload["soil_type"]
    response = client.post("/api/soils", json=payload, headers=admin_headers)
    assert response.status_code == 422


# ==========================================================
# Soil uniqueness = auto-generated PK (no business unique key)
# ==========================================================

def test_soils_get_unique_autoincrement_ids(client, admin_headers):
    _, payload_a = _create_soil(client, admin_headers)
    _, payload_b = _create_soil(client, admin_headers)

    id_a = _soil_id(client, admin_headers, payload_a["soil_type"])
    id_b = _soil_id(client, admin_headers, payload_b["soil_type"])

    assert id_a != id_b


# ==========================================================
# Get / list
# ==========================================================

def test_get_soil(client, admin_headers):
    _, payload = _create_soil(client, admin_headers)
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    detail = client.get(f"/api/soils/{soil_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["soil_type"] == payload["soil_type"]
    assert detail.json()["ph"] == 6.5
    assert "created_at" in detail.json()


def test_get_soil_not_found_404(client, admin_headers):
    response = client.get("/api/soils/99999999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Soil Not Found"


def test_list_soils(client, admin_headers):
    _create_soil(client, admin_headers)
    _create_soil(client, admin_headers)

    listed = client.get("/api/soils", headers=admin_headers)
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)
    assert len(listed.json()) >= 2


# ==========================================================
# Update
# ==========================================================

def test_update_soil(client, admin_headers):
    _, payload = _create_soil(client, admin_headers)
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    response = client.put(
        f"/api/soils/{soil_id}",
        json=_soil_payload(
            soil_type=f"Updated{unique_mobile()}",
            ph=7.1,
            nitrogen=80,
            phosphorus=40,
            potassium=60,
        ),
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Soil Updated Successfully"


def test_update_soil_preserves_farmer_id_when_omitted(client, admin_headers):
    """BUG1 regression: update without farmer_id must not wipe the link."""
    farmer_id = _create_farmer(client, admin_headers)

    _, payload = _create_soil(client, admin_headers, farmer_id=farmer_id)
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    before = client.get(f"/api/soils/{soil_id}", headers=admin_headers).json()
    assert before["farmer_id"] == farmer_id

    response = client.put(
        f"/api/soils/{soil_id}",
        json=_soil_payload(soil_type=f"KeptFarmer{unique_mobile()}", ph=7.0),
        headers=admin_headers,
    )
    assert response.status_code == 200

    after = client.get(f"/api/soils/{soil_id}", headers=admin_headers).json()
    assert after["farmer_id"] == farmer_id


def test_update_soil_reassigns_farmer(client, admin_headers):
    farmer_a = _create_farmer(client, admin_headers)
    farmer_b = _create_farmer(client, admin_headers)

    _, payload = _create_soil(client, admin_headers, farmer_id=farmer_a)
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    response = client.put(
        f"/api/soils/{soil_id}",
        json=_soil_payload(farmer_id=farmer_b),
        headers=admin_headers,
    )
    assert response.status_code == 200

    after = client.get(f"/api/soils/{soil_id}", headers=admin_headers).json()
    assert after["farmer_id"] == farmer_b


def test_update_soil_invalid_farmer_404(client, admin_headers):
    _, payload = _create_soil(client, admin_headers)
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    response = client.put(
        f"/api/soils/{soil_id}",
        json=_soil_payload(farmer_id=99999999),
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"
    assert "integrityerror" not in response.text.lower()


def test_update_soil_not_found_404(client, admin_headers):
    response = client.put(
        "/api/soils/99999999",
        json=_soil_payload(),
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Soil Not Found"


# ==========================================================
# Delete
# ==========================================================

def test_delete_soil(client, admin_headers):
    _, payload = _create_soil(client, admin_headers)
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    response = client.delete(f"/api/soils/{soil_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Soil Deleted Successfully"

    detail = client.get(f"/api/soils/{soil_id}", headers=admin_headers)
    assert detail.status_code == 404


def test_delete_soil_not_found_404(client, admin_headers):
    response = client.delete("/api/soils/99999999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Soil Not Found"


# ==========================================================
# Farmer <-> Soil relationship
# ==========================================================

def test_multiple_soils_link_to_farmer(client, admin_headers):
    """One farmer can own many soils (1:N via soils.farmer_id)."""
    farmer_id = _create_farmer(client, admin_headers)

    _, payload_a = _create_soil(client, admin_headers, farmer_id=farmer_id)
    _, payload_b = _create_soil(client, admin_headers, farmer_id=farmer_id)

    listed = client.get("/api/soils", headers=admin_headers).json()
    linked = [
        soil for soil in listed
        if soil["farmer_id"] == farmer_id
        and soil["soil_type"] in (payload_a["soil_type"], payload_b["soil_type"])
    ]
    assert len(linked) == 2


def test_soil_identifies_farmer(client, admin_headers):
    farmer_id = _create_farmer(client, admin_headers)

    _, payload = _create_soil(client, admin_headers, farmer_id=farmer_id)
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    detail = client.get(f"/api/soils/{soil_id}", headers=admin_headers).json()
    assert detail["farmer_id"] == farmer_id


def test_farmer_delete_cascades_soils(client, admin_headers):
    """Locked Phase 5.1 policy: deleting a farmer removes its soils."""
    farmer_id = _create_farmer(client, admin_headers)

    _, payload = _create_soil(client, admin_headers, farmer_id=farmer_id)
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    deleted = client.delete(f"/api/farmers/{farmer_id}", headers=admin_headers)
    assert deleted.status_code == 200

    soil = client.get(f"/api/soils/{soil_id}", headers=admin_headers)
    assert soil.status_code == 404


# ==========================================================
# Authentication / Authorization
# ==========================================================

def test_soil_reads_require_auth(client):
    assert client.get("/api/soils").status_code == 401
    assert client.get("/api/soils/1").status_code == 401


def test_soil_writes_require_auth(client):
    payload = _soil_payload()
    assert client.post("/api/soils", json=payload).status_code == 401
    assert client.put("/api/soils/1", json=payload).status_code == 401
    assert client.delete("/api/soils/1").status_code == 401


def test_soil_writes_admin_only(client, user_headers):
    payload = _soil_payload()
    assert client.post("/api/soils", json=payload, headers=user_headers).status_code == 403
    assert client.put("/api/soils/1", json=payload, headers=user_headers).status_code == 403
    assert client.delete("/api/soils/1", headers=user_headers).status_code == 403


def test_authenticated_user_can_read_soils(client, user_headers, admin_headers):
    _, payload = _create_soil(client, admin_headers)
    soil_id = _soil_id(client, admin_headers, payload["soil_type"])

    assert client.get("/api/soils", headers=user_headers).status_code == 200
    assert client.get(f"/api/soils/{soil_id}", headers=user_headers).status_code == 200
