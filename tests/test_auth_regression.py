"""
KisanAI OS - Phase 4 authentication / authorization regression tests.

Public routes stay public, protected routes require a bearer token,
and admin-only write routes reject non-admin roles.
"""

from tests.conftest import farmer_payload, unique_mobile


def test_home_is_public(client):
    response = client.get("/")
    assert response.status_code == 200


def test_farmer_list_requires_auth(client):
    response = client.get("/api/farmers")
    assert response.status_code == 401


def test_farmer_create_requires_auth(client):
    response = client.post("/api/farmers", json=farmer_payload())
    assert response.status_code == 401


def test_farmer_get_by_id_requires_auth(client):
    response = client.get("/api/farmers/1")
    assert response.status_code == 401


def test_farmer_by_mobile_requires_auth(client):
    response = client.get("/api/farmers/by-mobile/9000000000")
    assert response.status_code == 401


def test_farmer_create_admin_only(client, user_headers):
    response = client.post(
        "/api/farmers", json=farmer_payload(), headers=user_headers
    )
    assert response.status_code == 403


def test_farmer_update_admin_only(client, user_headers, admin_headers):
    created = client.post(
        "/api/farmers", json=farmer_payload(), headers=admin_headers
    )
    assert created.status_code == 200

    listed = client.get("/api/farmers", headers=admin_headers).json()
    farmer_id = listed[-1]["farmer_id"]

    response = client.put(
        f"/api/farmers/{farmer_id}",
        json=farmer_payload(),
        headers=user_headers,
    )
    assert response.status_code == 403


def test_farmer_delete_admin_only(client, user_headers, admin_headers):
    created = client.post(
        "/api/farmers", json=farmer_payload(), headers=admin_headers
    )
    assert created.status_code == 200

    listed = client.get("/api/farmers", headers=admin_headers).json()
    farmer_id = listed[-1]["farmer_id"]

    response = client.delete(f"/api/farmers/{farmer_id}", headers=user_headers)
    assert response.status_code == 403


def test_authenticated_user_can_read(client, user_headers):
    response = client.get("/api/farmers", headers=user_headers)
    assert response.status_code == 200


def test_admin_can_create_crop(client, admin_headers):
    response = client.post(
        "/api/crops",
        json={
            "crop_name": f"AuthCrop{unique_mobile()}",
            "season": "Rabi",
            "duration_days": 100,
            "water_requirement": "Low",
        },
        headers=admin_headers,
    )
    assert response.status_code == 200


def test_weather_requires_auth(client):
    assert client.get("/api/weather").status_code == 401


def test_advisory_requires_auth(client):
    response = client.post(
        "/api/advisory",
        json={
            "crop_name": "Rice",
            "soil_type": "Loamy",
            "ph": 6.5,
            "moisture": 40,
            "nitrogen": 30,
            "phosphorus": 20,
            "potassium": 15,
            "temperature": 28.0,
            "humidity": 60.0,
            "condition": "Clear",
            "wind_speed": 5.0,
        },
    )
    assert response.status_code == 401


def test_soil_requires_auth(client):
    response = client.post(
        "/api/soils",
        json={
            "soil_type": "Loamy",
            "ph": 6.5,
            "moisture": 40.0,
            "nitrogen": 40,
            "phosphorus": 20,
            "potassium": 15,
        },
    )
    assert response.status_code == 401


def test_disease_requires_auth(client):
    response = client.post(
        "/api/diseases",
        json={
            "crop_name": "Rice",
            "disease_name": "Blast",
            "symptoms": "spots",
            "solution": "spray",
            "severity": "High",
        },
    )
    assert response.status_code == 401


def test_invalid_token_rejected(client):
    response = client.get(
        "/api/farmers",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401
