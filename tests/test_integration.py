"""
KisanAI OS - Phase 5.8 Integration Tests.

End-to-end integration coverage across all six production modules
(farmer, crop, soil, disease, weather, advisory) exercised through the
real FastAPI application against the migrated test database.

Sections:
  A. Authentication & authorization sweep (401 / 403 / 200).
  B. Realistic cross-module farm lifecycle (linked graph + mutations).
  C. Cross-module 404 chains and per-module missing-resource 404s.
  D. 409 conflict matrix across modules.
  E. Validation (422) sweep.
  F. Weather + advisory end-to-end flow with a seeded cache.

Note: 400 is intentionally not asserted anywhere because no endpoint in
the application produces HTTP 400; input validation is handled as 422
and business/duplicate failures as 404/409 (verified against
config/core/api/main.py error mapping).
"""

import sqlite3
from datetime import datetime

import pytest

from config.settings import settings
from tests.conftest import TEST_DB_PATH, create_farmer, unique_mobile


# ==========================================================
# Helpers
# ==========================================================

def _name(prefix):
    return f"{prefix}{unique_mobile()}"


def _farmer_id_by_mobile(client, headers, mobile):
    for farmer in client.get("/api/farmers", headers=headers).json():
        if farmer["mobile"] == mobile:
            return farmer["farmer_id"]
    raise AssertionError(f"farmer {mobile} not found")


def _make_farmer(client, headers, mobile=None):
    if mobile is None:
        response, payload = create_farmer(client, headers)
    else:
        response, payload = create_farmer(client, headers, mobile=mobile)
    assert response.status_code == 200, response.text
    return _farmer_id_by_mobile(client, headers, payload["mobile"])


def _crop_id(client, headers, crop_name):
    for crop in client.get("/api/crops", headers=headers).json():
        if crop["crop_name"] == crop_name:
            return crop["crop_id"]
    raise AssertionError(f"crop {crop_name} not found")


def _create_crop(client, headers, farmer_id=None, crop_name=None):
    crop_name = crop_name or _name("Crop")
    payload = {
        "farmer_id": farmer_id,
        "crop_name": crop_name,
        "season": "Kharif",
        "duration_days": 120,
        "water_requirement": "High",
    }
    response = client.post("/api/crops", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return _crop_id(client, headers, crop_name)


def _soil_id(client, headers, soil_type):
    for soil in client.get("/api/soils", headers=headers).json():
        if soil["soil_type"] == soil_type:
            return soil["soil_id"]
    raise AssertionError(f"soil {soil_type} not found")


def _create_soil(client, headers, farmer_id=None, soil_type=None):
    soil_type = soil_type or _name("Soil")
    payload = {
        "farmer_id": farmer_id,
        "soil_type": soil_type,
        "ph": 6.5,
        "moisture": 40.0,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
    }
    response = client.post("/api/soils", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return _soil_id(client, headers, soil_type)


def _disease_id(client, headers, crop_id, disease_name):
    for disease in client.get("/api/diseases", headers=headers).json():
        if disease["disease_name"] == disease_name and disease["crop_id"] == crop_id:
            return disease["disease_id"]
    raise AssertionError(f"disease {disease_name} on crop {crop_id} not found")


def _create_disease(client, headers, crop_id, disease_name, crop_name):
    payload = {
        "crop_id": crop_id,
        "crop_name": crop_name,
        "disease_name": disease_name,
        "symptoms": "Yellow spots on leaves",
        "solution": "Apply recommended fungicide",
        "severity": "Medium",
    }
    response = client.post("/api/diseases", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    return _disease_id(client, headers, crop_id, disease_name)


def _seed_weather():
    """Replace the weather cache with a fresh row so GET /api/weather is a
    deterministic cache hit (no live provider call)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(TEST_DB_PATH)
    try:
        conn.execute("DELETE FROM weather")
        conn.execute(
            "INSERT INTO weather "
            "(location, temperature, humidity, condition, wind_speed, updated_at) "
            "VALUES (:location, :temperature, :humidity, :condition, "
            ":wind_speed, :updated_at)",
            {
                "location": settings.WEATHER_LOCATION,
                "temperature": 27.5,
                "humidity": 68,
                "condition": "Partly Cloudy",
                "wind_speed": 12.0,
                "updated_at": now,
            },
        )
        conn.commit()
    finally:
        conn.close()


# ==========================================================
# A. Authentication & authorization sweep
# ==========================================================

READ_LIST_ENDPOINTS = [
    ("GET", "/api/farmers"),
    ("GET", "/api/crops"),
    ("GET", "/api/diseases"),
    ("GET", "/api/soils"),
    ("GET", "/api/weather"),
]

READ_DETAIL_ENDPOINTS = [
    ("GET", "/api/farmers/by-mobile/9999999999"),
    ("GET", "/api/farmers/99999999"),
    ("GET", "/api/crops/99999999"),
    ("GET", "/api/diseases/99999999"),
    ("GET", "/api/soils/99999999"),
]


def _write_sweeps():
    """(method, path, payload) pairs for every admin-only write endpoint.

    Auth checks run before payload validation, so minimal payloads are
    sufficient to assert 401/403.
    """
    farmer_payload = {
        "name": "Ravi Kumar",
        "mobile": "9999999999",
        "village": "Sitapur",
        "district": "Sitapur",
        "state": "Uttar Pradesh",
    }
    crop_payload = {
        "farmer_id": None,
        "crop_name": "CropX",
        "season": "Kharif",
        "duration_days": 120,
        "water_requirement": "High",
    }
    disease_payload = {
        "crop_id": None,
        "crop_name": "CropX",
        "disease_name": "DiseaseX",
        "symptoms": "Spots",
        "solution": "Spray",
        "severity": "Medium",
    }
    soil_payload = {
        "farmer_id": None,
        "soil_type": "SoilX",
        "ph": 6.5,
        "moisture": 40.0,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
    }
    return [
        ("POST", "/api/farmers", farmer_payload),
        ("PUT", "/api/farmers/1", farmer_payload),
        ("DELETE", "/api/farmers/1", None),
        ("POST", "/api/crops", crop_payload),
        ("PUT", "/api/crops/1", crop_payload),
        ("DELETE", "/api/crops/1", None),
        ("POST", "/api/diseases", disease_payload),
        ("PUT", "/api/diseases/1", disease_payload),
        ("DELETE", "/api/diseases/1", None),
        ("POST", "/api/soils", soil_payload),
        ("PUT", "/api/soils/1", soil_payload),
        ("DELETE", "/api/soils/1", None),
    ]


@pytest.mark.parametrize("method,path", READ_LIST_ENDPOINTS)
def test_unauthenticated_reads_401(client, method, path):
    response = client.request(method, path)
    assert response.status_code == 401


@pytest.mark.parametrize("method,path", READ_DETAIL_ENDPOINTS)
def test_unauthenticated_detail_reads_401(client, method, path):
    response = client.request(method, path)
    assert response.status_code == 401


@pytest.mark.parametrize("method,path,payload", _write_sweeps())
def test_unauthenticated_writes_401(client, method, path, payload):
    response = client.request(method, path, json=payload)
    assert response.status_code == 401


def test_unauthenticated_advisory_401(client):
    payload = {
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
    }
    assert client.post("/api/advisory", json=payload).status_code == 401


@pytest.mark.parametrize("method,path,payload", _write_sweeps())
def test_non_admin_writes_403(client, user_headers, method, path, payload):
    response = client.request(method, path, json=payload, headers=user_headers)
    assert response.status_code == 403


@pytest.mark.parametrize("method,path", READ_LIST_ENDPOINTS)
def test_non_admin_reads_200(client, user_headers, method, path):
    response = client.request(method, path, headers=user_headers)
    assert response.status_code == 200


@pytest.mark.parametrize("method,path", READ_DETAIL_ENDPOINTS)
def test_non_admin_detail_reads_authorized(client, user_headers, method, path):
    """Non-admin authenticated reads are authorized; missing resources
    still surface 404 rather than 401/403 (data absence is not an
    authorization failure)."""
    response = client.request(method, path, headers=user_headers)
    assert response.status_code not in (401, 403)


def test_non_admin_advisory_200(client, user_headers):
    payload = {
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
    }
    response = client.post("/api/advisory", json=payload, headers=user_headers)
    assert response.status_code == 200


# ==========================================================
# B. Realistic cross-module farm lifecycle
# ==========================================================

def test_full_linked_graph_farmer_crop_soil_disease(client, admin_headers):
    farmer_id = _make_farmer(client, admin_headers)

    crop_name = _name("Rice")
    crop_id = _create_crop(client, admin_headers, farmer_id=farmer_id, crop_name=crop_name)
    soil_type = _name("LoamySoil")
    soil_id = _create_soil(client, admin_headers, farmer_id=farmer_id, soil_type=soil_type)
    disease_name = _name("Blast")
    disease_id = _create_disease(client, admin_headers, crop_id, disease_name, crop_name)

    farmer = client.get(f"/api/farmers/{farmer_id}", headers=admin_headers).json()
    assert any(
        c["crop_id"] == crop_id and c["farmer_id"] == farmer_id
        for c in farmer["crops"]
    )

    crop = client.get(f"/api/crops/{crop_id}", headers=admin_headers).json()
    assert crop["farmer_id"] == farmer_id

    soil = client.get(f"/api/soils/{soil_id}", headers=admin_headers).json()
    assert soil["farmer_id"] == farmer_id

    disease = client.get(f"/api/diseases/{disease_id}", headers=admin_headers).json()
    assert disease["crop_id"] == crop_id
    assert disease["crop_name"] == crop_name

    by_farmer = client.get(
        f"/api/crops?farmer_id={farmer_id}", headers=admin_headers
    ).json()
    assert any(c["crop_id"] == crop_id for c in by_farmer)


def test_multiple_crops_per_farmer_end_to_end(client, admin_headers):
    farmer_id = _make_farmer(client, admin_headers)
    crops = [_name("CropA"), _name("CropB"), _name("CropC")]

    for name in crops:
        _create_crop(client, admin_headers, farmer_id=farmer_id, crop_name=name)

    by_farmer = client.get(
        f"/api/crops?farmer_id={farmer_id}", headers=admin_headers
    ).json()
    returned_names = {c["crop_name"] for c in by_farmer}
    assert set(crops).issubset(returned_names)
    for crop in by_farmer:
        assert crop["farmer_id"] == farmer_id


def test_crop_delete_nulls_disease_crop_id_preserves_record(client, admin_headers):
    farmer_id = _make_farmer(client, admin_headers)
    crop_name = _name("Wheat")
    crop_id = _create_crop(client, admin_headers, farmer_id=farmer_id, crop_name=crop_name)
    disease_name = _name("Rust")
    disease_id = _create_disease(client, admin_headers, crop_id, disease_name, crop_name)

    deleted = client.delete(f"/api/crops/{crop_id}", headers=admin_headers)
    assert deleted.status_code == 200

    disease = client.get(f"/api/diseases/{disease_id}", headers=admin_headers).json()
    assert disease["crop_id"] is None
    assert disease["disease_name"] == disease_name
    assert disease["crop_name"] == crop_name


def test_farmer_delete_unlinks_crops_and_cascades_soils(client, admin_headers):
    """Established referential policy: crops survive with farmer_id set to
    NULL while soils are cascade-deleted with the farmer."""
    farmer_id = _make_farmer(client, admin_headers)
    crop_id = _create_crop(client, admin_headers, farmer_id=farmer_id)
    soil_id = _create_soil(client, admin_headers, farmer_id=farmer_id)

    deleted = client.delete(f"/api/farmers/{farmer_id}", headers=admin_headers)
    assert deleted.status_code == 200

    crop = client.get(f"/api/crops/{crop_id}", headers=admin_headers).json()
    assert crop["farmer_id"] is None

    soil = client.get(f"/api/soils/{soil_id}", headers=admin_headers)
    assert soil.status_code == 404


def test_cross_module_update_integrity(client, admin_headers):
    farmer_id = _make_farmer(client, admin_headers)
    crop_id = _create_crop(client, admin_headers, farmer_id=farmer_id)
    soil_id = _create_soil(client, admin_headers, farmer_id=farmer_id)

    new_crop_name = _name("RenamedCrop")
    crop_update = {
        "farmer_id": farmer_id,
        "crop_name": new_crop_name,
        "season": "Rabi",
        "duration_days": 100,
        "water_requirement": "Medium",
    }
    assert client.put(
        f"/api/crops/{crop_id}", json=crop_update, headers=admin_headers
    ).status_code == 200
    crop = client.get(f"/api/crops/{crop_id}", headers=admin_headers).json()
    assert crop["crop_name"] == new_crop_name
    assert crop["farmer_id"] == farmer_id

    soil_update = {
        "soil_type": _name("SoilRenamed"),
        "ph": 7.0,
        "moisture": 50.0,
        "nitrogen": 60,
        "phosphorus": 30,
        "potassium": 35,
    }
    assert client.put(
        f"/api/soils/{soil_id}", json=soil_update, headers=admin_headers
    ).status_code == 200
    soil = client.get(f"/api/soils/{soil_id}", headers=admin_headers).json()
    assert soil["farmer_id"] == farmer_id

    bad_farmer_update = dict(crop_update, farmer_id=99999999)
    response = client.put(
        f"/api/crops/{crop_id}", json=bad_farmer_update, headers=admin_headers
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"

    bad_soil_update = dict(soil_update, farmer_id=99999999)
    response = client.put(
        f"/api/soils/{soil_id}", json=bad_soil_update, headers=admin_headers
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"


def test_farmer_by_mobile_lookup(client, admin_headers):
    mobile = unique_mobile()
    farmer_id = _make_farmer(client, admin_headers, mobile=mobile)

    by_mobile = client.get(
        f"/api/farmers/by-mobile/{mobile}", headers=admin_headers
    )
    assert by_mobile.status_code == 200
    assert by_mobile.json()["farmer_id"] == farmer_id


# ==========================================================
# C. Cross-module 404 chains
# ==========================================================

def test_cross_module_invalid_reference_404(client, admin_headers):
    crop_payload = {
        "farmer_id": 99999999,
        "crop_name": _name("CropBadFarmer"),
        "season": "Kharif",
        "duration_days": 120,
        "water_requirement": "High",
    }
    response = client.post("/api/crops", json=crop_payload, headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"

    soil_payload = {
        "farmer_id": 99999999,
        "soil_type": _name("SoilBadFarmer"),
        "ph": 6.5,
        "moisture": 40.0,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
    }
    response = client.post("/api/soils", json=soil_payload, headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"

    disease_payload = {
        "crop_id": 99999999,
        "crop_name": _name("CropName"),
        "disease_name": _name("DiseaseBadCrop"),
        "symptoms": "Browning",
        "solution": "Remove affected leaves",
        "severity": "Medium",
    }
    response = client.post("/api/diseases", json=disease_payload, headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Crop Not Found"


@pytest.mark.parametrize(
    "module,update_payload",
    [
        (
            "farmers",
            {
                "name": "Missing Farmer",
                "mobile": "9999999999",
                "village": "Sitapur",
                "district": "Sitapur",
                "state": "Uttar Pradesh",
            },
        ),
        (
            "crops",
            {
                "farmer_id": None,
                "crop_name": _name("CropMissing"),
                "season": "Kharif",
                "duration_days": 120,
                "water_requirement": "High",
            },
        ),
        (
            "soils",
            {
                "farmer_id": None,
                "soil_type": _name("SoilMissing"),
                "ph": 6.5,
                "moisture": 40.0,
                "nitrogen": 50,
                "phosphorus": 25,
                "potassium": 30,
            },
        ),
        (
            "diseases",
            {
                "crop_id": None,
                "crop_name": _name("CropMissing"),
                "disease_name": _name("DiseaseMissing"),
                "symptoms": "Wilting",
                "solution": "Remove",
                "severity": "Medium",
            },
        ),
    ],
)
def test_missing_resource_404_sweep(client, admin_headers, module, update_payload):
    assert client.get(
        f"/api/{module}/99999999", headers=admin_headers
    ).status_code == 404
    assert client.put(
        f"/api/{module}/99999999",
        json=update_payload,
        headers=admin_headers,
    ).status_code == 404
    assert client.delete(
        f"/api/{module}/99999999", headers=admin_headers
    ).status_code == 404


def test_farmer_by_mobile_missing_404(client, admin_headers):
    response = client.get(
        "/api/farmers/by-mobile/9999999999", headers=admin_headers
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"


# ==========================================================
# D. 409 conflict matrix
# ==========================================================

def test_duplicate_farmer_mobile_409(client, admin_headers):
    mobile = unique_mobile()
    _make_farmer(client, admin_headers, mobile=mobile)

    response, _ = create_farmer(client, admin_headers, mobile=mobile)
    assert response.status_code == 409
    assert response.json()["message"] == "Mobile number already exists"


def test_duplicate_crop_name_409(client, admin_headers):
    crop_name = _name("CropDup")
    _create_crop(client, admin_headers, crop_name=crop_name)

    payload = {
        "farmer_id": None,
        "crop_name": crop_name,
        "season": "Kharif",
        "duration_days": 120,
        "water_requirement": "High",
    }
    response = client.post("/api/crops", json=payload, headers=admin_headers)
    assert response.status_code == 409
    assert response.json()["message"] == "Crop name already exists"


def test_duplicate_disease_linked_crop_409(client, admin_headers):
    crop_name = _name("CropForDup")
    crop_id = _create_crop(client, admin_headers, crop_name=crop_name)
    disease_name = _name("LeafBlight")

    _create_disease(client, admin_headers, crop_id, disease_name, crop_name)

    payload = {
        "crop_id": crop_id,
        "crop_name": crop_name,
        "disease_name": disease_name,
        "symptoms": "Brown patches",
        "solution": "Spray copper fungicide",
        "severity": "High",
    }
    response = client.post("/api/diseases", json=payload, headers=admin_headers)
    assert response.status_code == 409
    assert response.json()["message"] == "Disease already exists"


def test_duplicate_disease_unlinked_crop_allowed(client, admin_headers):
    disease_name = _name("UnlinkedDisease")
    payload = {
        "crop_id": None,
        "crop_name": _name("CropName"),
        "disease_name": disease_name,
        "symptoms": "Wilting",
        "solution": "Improve drainage",
        "severity": "Low",
    }
    first = client.post("/api/diseases", json=payload, headers=admin_headers)
    second = client.post("/api/diseases", json=payload, headers=admin_headers)
    assert first.status_code == 200
    assert second.status_code == 200


def test_duplicate_username_register_409(client):
    username = _name("dupuser").lower()
    payload = {
        "username": username,
        "password": "password123",
        "full_name": "Dup User",
        "role": "farmer",
    }
    first = client.post("/api/auth/register", json=payload)
    second = client.post("/api/auth/register", json=payload)
    assert first.status_code == 200
    assert second.status_code == 409
    assert second.json()["detail"]["message"] == "Username already exists"


# ==========================================================
# E. Validation (422) sweep
# ==========================================================

def test_farmer_missing_required_name_422(client, admin_headers):
    payload = {
        "name": "",
        "mobile": unique_mobile(),
        "village": "Sitapur",
        "district": "Sitapur",
        "state": "Uttar Pradesh",
    }
    payload.pop("name")
    assert client.post("/api/farmers", json=payload, headers=admin_headers).status_code == 422


def test_farmer_invalid_mobile_422(client, admin_headers):
    payload = {
        "name": "Ravi Kumar",
        "mobile": "12345",
        "village": "Sitapur",
        "district": "Sitapur",
        "state": "Uttar Pradesh",
    }
    assert client.post("/api/farmers", json=payload, headers=admin_headers).status_code == 422


def test_crop_blank_name_422(client, admin_headers):
    payload = {
        "farmer_id": None,
        "crop_name": "   ",
        "season": "Kharif",
        "duration_days": 120,
        "water_requirement": "High",
    }
    assert client.post("/api/crops", json=payload, headers=admin_headers).status_code == 422


def test_soil_blank_type_and_negative_ph_422(client, admin_headers):
    blank = {
        "farmer_id": None,
        "soil_type": "   ",
        "ph": 6.5,
        "moisture": 40.0,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
    }
    assert client.post("/api/soils", json=blank, headers=admin_headers).status_code == 422

    negative = dict(blank, soil_type=_name("Soil"), ph=-1.0)
    assert client.post("/api/soils", json=negative, headers=admin_headers).status_code == 422


def test_disease_invalid_severity_422(client, admin_headers):
    payload = {
        "crop_id": None,
        "crop_name": _name("CropName"),
        "disease_name": _name("DiseaseBadSev"),
        "symptoms": "Wilting",
        "solution": "Remove",
        "severity": "Extreme",
    }
    assert client.post("/api/diseases", json=payload, headers=admin_headers).status_code == 422


# ==========================================================
# F. Weather + advisory end-to-end flow
# ==========================================================

def test_weather_end_to_end_seeded_cache(client, admin_headers):
    _seed_weather()

    response = client.get("/api/weather", headers=admin_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["location"] == settings.WEATHER_LOCATION
    assert body["temperature"] == 27.5
    assert body["humidity"] == 68
    assert body["condition"] == "Partly Cloudy"
    assert body["wind_speed"] == 12.0
    assert "updated_at" in body


def test_advisory_end_to_end_from_created_records(client, admin_headers):
    farmer_id = _make_farmer(client, admin_headers)
    crop_name = _name("AdvisoryCrop")
    crop_id = _create_crop(client, admin_headers, farmer_id=farmer_id, crop_name=crop_name)
    soil_type = _name("AdvisorySoil")
    _create_soil(client, admin_headers, farmer_id=farmer_id, soil_type=soil_type)
    disease_name = _name("AdvisoryDisease")
    _create_disease(client, admin_headers, crop_id, disease_name, crop_name)

    payload = {
        "crop_name": crop_name,
        "soil_type": soil_type,
        "ph": 6.5,
        "moisture": 40.0,
        "nitrogen": 50,
        "phosphorus": 25,
        "potassium": 30,
        "temperature": 30.3,
        "humidity": 60.0,
        "condition": "Overcast",
        "wind_speed": 6.0,
        "disease_name": disease_name,
        "disease_severity": "Medium",
    }
    response = client.post("/api/advisory", json=payload, headers=admin_headers)
    assert response.status_code == 200

    body = response.json()
    assert body["crop"] == crop_name
    assert body["soil"]["type"] == soil_type
    assert body["disease"]["name"] == disease_name
    assert body["disease"]["severity"] == "Medium"
    assert isinstance(body["recommendations"], list)
    assert len(body["recommendations"]) >= 1
    assert any(
        f"monitor the crop for symptoms of {disease_name.lower()}"
        in r.lower()
        for r in body["recommendations"]
    )
