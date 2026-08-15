"""
KisanAI OS - My Farm module tests.

Covers the self-service farm endpoints: the authenticated farmer creates
their own farm (name/mobile taken from the linked account), updates farm
size and location, manages their own crops, and can never touch another
user's farm. Also covers auth (401), ownership isolation (404/403) and
validation.
"""

import random

import pytest


def _mobile():
    return f"9{random.randint(100000000, 999999999)}"


def _register_user(client, role="farmer"):
    uniq = random.randint(100000, 999999)
    username = f"myfarm{role}{uniq}"
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "My Farm Tester",
            "mobile": _mobile(),
            "role": role,
        },
    )
    assert response.status_code == 200, response.text
    login = client.post(
        "/api/auth/token",
        data={"username": username, "password": "password123"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.fixture
def farm_headers(client):
    """A fresh authenticated farmer for each test (the session-scoped
    farm_headers fixture is shared, but farm state must be isolated)."""
    return _register_user(client)


def _farm_payload(**overrides):
    payload = {
        "farm_size": 4.5,
        "village": "Sitapur",
        "district": "Sitapur",
        "state": "Uttar Pradesh",
    }
    payload.update(overrides)
    return payload


def _crop_payload(**overrides):
    payload = {
        "crop_name": f"Crop{random.randint(100000, 999999)}",
        "season": "Kharif",
        "duration_days": 120,
        "water_requirement": "High",
    }
    payload.update(overrides)
    return payload


# ==========================================================
# A. Authentication (401)
# ==========================================================

def test_my_farm_requires_auth(client):
    assert client.get("/api/my-farm").status_code == 401
    assert client.post("/api/my-farm", json=_farm_payload()).status_code == 401
    assert client.put("/api/my-farm", json={}).status_code == 401
    assert client.delete("/api/my-farm").status_code == 401
    assert client.get("/api/my-farm/crops").status_code == 401
    assert client.post("/api/my-farm/crops", json=_crop_payload()).status_code == 401
    assert client.put("/api/my-farm/crops/1", json=_crop_payload()).status_code == 401
    assert client.delete("/api/my-farm/crops/1").status_code == 401


# ==========================================================
# B. Farm profile lifecycle
# ==========================================================

def test_get_my_farm_404_before_creation(client, farm_headers):
    response = client.get("/api/my-farm", headers=farm_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Farm Not Found"


def test_create_and_get_my_farm(client, farm_headers):
    created = client.post(
        "/api/my-farm", json=_farm_payload(), headers=farm_headers
    )
    assert created.status_code == 200
    assert created.json()["message"] == "Farm Created Successfully"

    farm = client.get("/api/my-farm", headers=farm_headers)
    assert farm.status_code == 200
    body = farm.json()
    assert body["village"] == "Sitapur"
    assert body["district"] == "Sitapur"
    assert body["state"] == "Uttar Pradesh"
    assert body["farm_size"] == 4.5
    assert body["user_id"] is not None
    assert body["crops"] == []


def test_create_my_farm_takes_name_and_mobile_from_user(client, farm_headers):
    created = client.post(
        "/api/my-farm", json=_farm_payload(), headers=farm_headers
    )
    assert created.status_code == 200

    farm = client.get("/api/my-farm", headers=farm_headers).json()
    assert farm["name"] == "My Farm Tester"
    assert farm["mobile"] != ""


def test_create_my_farm_duplicate_409(client, farm_headers):
    first = client.post(
        "/api/my-farm", json=_farm_payload(), headers=farm_headers
    )
    assert first.status_code == 200

    second = client.post(
        "/api/my-farm", json=_farm_payload(), headers=farm_headers
    )
    assert second.status_code == 409
    assert second.json()["message"] == "Farm already exists"


def test_update_my_farm_partial(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)

    updated = client.put(
        "/api/my-farm",
        json={"farm_size": 8.0, "village": "Lucknow"},
        headers=farm_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["message"] == "Farm Updated Successfully"

    farm = client.get("/api/my-farm", headers=farm_headers).json()
    assert farm["farm_size"] == 8.0
    assert farm["village"] == "Lucknow"
    # Unsupplied fields are preserved.
    assert farm["district"] == "Sitapur"
    assert farm["state"] == "Uttar Pradesh"


def test_update_my_farm_404_without_farm(client, farm_headers):
    response = client.put(
        "/api/my-farm", json={"farm_size": 5.0}, headers=farm_headers
    )
    assert response.status_code == 404


def test_delete_my_farm(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)

    deleted = client.delete("/api/my-farm", headers=farm_headers)
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Farm Deleted Successfully"

    gone = client.get("/api/my-farm", headers=farm_headers)
    assert gone.status_code == 404


def test_farm_size_validation(client, farm_headers):
    response = client.post(
        "/api/my-farm",
        json=_farm_payload(farm_size=-1),
        headers=farm_headers,
    )
    assert response.status_code == 422


# ==========================================================
# C. Farm crops lifecycle
# ==========================================================

def test_add_and_list_crops(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)

    payload = _crop_payload()
    added = client.post(
        "/api/my-farm/crops", json=payload, headers=farm_headers
    )
    assert added.status_code == 200
    assert added.json()["message"] == "Crop Added Successfully"

    listed = client.get("/api/my-farm/crops", headers=farm_headers)
    assert listed.status_code == 200
    crops = listed.json()
    assert len(crops) == 1
    assert crops[0]["crop_name"] == payload["crop_name"]
    assert crops[0]["season"] == "Kharif"
    assert crops[0]["duration_days"] == 120


def test_crop_same_name_twice_on_one_farm_409(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)

    name = f"Wheat{random.randint(100000, 999999)}"
    first = client.post(
        "/api/my-farm/crops", json=_crop_payload(crop_name=name),
        headers=farm_headers,
    )
    assert first.status_code == 200

    second = client.post(
        "/api/my-farm/crops", json=_crop_payload(crop_name=name),
        headers=farm_headers,
    )
    assert second.status_code == 409
    assert second.json()["message"] == "Crop already added to this farm"


def test_same_crop_name_allowed_on_different_farms(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)
    other_headers = _register_user(client)

    client.post(
        "/api/my-farm",
        json=_farm_payload(village="Lucknow"),
        headers=other_headers,
    )

    name = f"Paddy{random.randint(100000, 999999)}"
    for headers in (farm_headers, other_headers):
        added = client.post(
            "/api/my-farm/crops", json=_crop_payload(crop_name=name),
            headers=headers,
        )
        assert added.status_code == 200


def test_update_own_crop(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)
    payload = _crop_payload()
    client.post("/api/my-farm/crops", json=payload, headers=farm_headers)

    crop_id = client.get("/api/my-farm/crops", headers=farm_headers).json()[0]["crop_id"]

    updated = client.put(
        f"/api/my-farm/crops/{crop_id}",
        json=_crop_payload(
            crop_name=payload["crop_name"],
            season="Rabi",
            duration_days=90,
            water_requirement="Low",
        ),
        headers=farm_headers,
    )
    assert updated.status_code == 200

    crop = client.get("/api/my-farm/crops", headers=farm_headers).json()[0]
    assert crop["season"] == "Rabi"
    assert crop["duration_days"] == 90
    assert crop["water_requirement"] == "Low"


def test_delete_own_crop(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)
    client.post("/api/my-farm/crops", json=_crop_payload(), headers=farm_headers)

    crop_id = client.get("/api/my-farm/crops", headers=farm_headers).json()[0]["crop_id"]

    deleted = client.delete(
        f"/api/my-farm/crops/{crop_id}", headers=farm_headers
    )
    assert deleted.status_code == 200

    listed = client.get("/api/my-farm/crops", headers=farm_headers).json()
    assert listed == []


def test_crop_validation_422(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)

    response = client.post(
        "/api/my-farm/crops",
        json=_crop_payload(duration_days=0),
        headers=farm_headers,
    )
    assert response.status_code == 422


# ==========================================================
# D. Ownership isolation
# ==========================================================

def test_crop_update_not_owned_404(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)
    client.post("/api/my-farm/crops", json=_crop_payload(), headers=farm_headers)
    crop_id = client.get("/api/my-farm/crops", headers=farm_headers).json()[0]["crop_id"]

    other_headers = _register_user(client)
    client.post(
        "/api/my-farm",
        json=_farm_payload(village="Kanpur"),
        headers=other_headers,
    )

    response = client.put(
        f"/api/my-farm/crops/{crop_id}",
        json=_crop_payload(),
        headers=other_headers,
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Crop Not Found"


def test_crop_delete_not_owned_404(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)
    client.post("/api/my-farm/crops", json=_crop_payload(), headers=farm_headers)
    crop_id = client.get("/api/my-farm/crops", headers=farm_headers).json()[0]["crop_id"]

    other_headers = _register_user(client)
    client.post(
        "/api/my-farm",
        json=_farm_payload(village="Kanpur"),
        headers=other_headers,
    )

    response = client.delete(
        f"/api/my-farm/crops/{crop_id}", headers=other_headers
    )
    assert response.status_code == 404

    still_there = client.get("/api/my-farm/crops", headers=farm_headers).json()
    assert len(still_there) == 1


def test_user_cannot_read_others_farm(client, farm_headers):
    client.post("/api/my-farm", json=_farm_payload(), headers=farm_headers)

    other_headers = _register_user(client)
    response = client.get("/api/my-farm", headers=other_headers)
    assert response.status_code == 404
