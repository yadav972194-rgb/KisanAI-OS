"""
KisanAI OS - My Farm persistence / app-restart tests.

The mobile app must survive a full restart: after the process is killed and
reopened the user's farm and crops are re-fetched from the backend, not from
memory. These tests prove the backend persists everything to the database by
simulating a restart with a brand-new application instance (new TestClient)
and checking the same data comes back.
"""

import random

from fastapi.testclient import TestClient

from config.core.api.main import app


def _mobile():
    return f"9{random.randint(100000000, 999999999)}"


def _register_user(client, role="farmer"):
    uniq = random.randint(100000, 999999)
    username = f"myfarmpersist{role}{uniq}"
    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "Persistence Tester",
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


def _farm_payload(**overrides):
    payload = {
        "farm_size": 3.5,
        "village": "Rampur",
        "block": "Sitapur",
        "district": "Sitapur",
        "state": "Uttar Pradesh",
    }
    payload.update(overrides)
    return payload


def _crop_payload(**overrides):
    payload = {
        "crop_name": f"PersistCrop{random.randint(100000, 999999)}",
        "season": "Rabi",
        "duration_days": 120,
        "water_requirement": "Medium",
    }
    payload.update(overrides)
    return payload


def _create_farm(client, headers):
    created = client.post("/api/my-farm", json=_farm_payload(), headers=headers)
    assert created.status_code == 200, created.text


def _restart():
    """A fresh application instance, exactly like reopening the app."""
    return TestClient(app)


def test_farm_fields_persist_after_restart(client):
    headers = _register_user(client)
    _create_farm(client, headers)

    restarted = _restart()
    farm = restarted.get("/api/my-farm", headers=headers)
    assert farm.status_code == 200
    body = farm.json()
    assert body["village"] == "Rampur"
    assert body["block"] == "Sitapur"
    assert body["district"] == "Sitapur"
    assert body["state"] == "Uttar Pradesh"
    assert body["farm_size"] == 3.5
    assert body["country"] == "India"
    assert body["crops"] == []


def test_crops_persist_after_restart(client):
    headers = _register_user(client)
    _create_farm(client, headers)
    payloads = [_crop_payload(), _crop_payload(season="Kharif")]
    for payload in payloads:
        added = client.post(
            "/api/my-farm/crops", json=payload, headers=headers
        )
        assert added.status_code == 200, added.text

    restarted = _restart()
    crops = restarted.get("/api/my-farm/crops", headers=headers)
    assert crops.status_code == 200
    names = sorted(c["crop_name"] for c in crops.json())
    seasons = sorted(c["season"] for c in crops.json())
    assert names == sorted(p["crop_name"] for p in payloads)
    assert seasons == sorted(p["season"] for p in payloads)


def test_update_persists_after_restart(client):
    headers = _register_user(client)
    _create_farm(client, headers)

    updated = client.put(
        "/api/my-farm",
        json={"village": "Lucknow", "farm_size": 8.0},
        headers=headers,
    )
    assert updated.status_code == 200, updated.text

    restarted = _restart()
    farm = restarted.get("/api/my-farm", headers=headers).json()
    assert farm["village"] == "Lucknow"
    assert farm["farm_size"] == 8.0
    assert farm["district"] == "Sitapur"


def test_delete_removes_farm_and_crops_after_restart(client):
    headers = _register_user(client)
    _create_farm(client, headers)
    added = client.post(
        "/api/my-farm/crops", json=_crop_payload(), headers=headers
    )
    assert added.status_code == 200, added.text

    deleted = client.delete("/api/my-farm", headers=headers)
    assert deleted.status_code == 200, deleted.text

    restarted = _restart()
    assert restarted.get("/api/my-farm", headers=headers).status_code == 404
    assert restarted.get("/api/my-farm/crops", headers=headers).status_code == 404


def test_farms_are_isolated_and_persist_per_user(client):
    headers_a = _register_user(client)
    headers_b = _register_user(client)

    client.post(
        "/api/my-farm",
        json=_farm_payload(village="Rampur", farm_size=3.5),
        headers=headers_a,
    )
    client.post(
        "/api/my-farm",
        json=_farm_payload(village="Kanpur", farm_size=6.0),
        headers=headers_b,
    )

    restarted = _restart()
    farm_a = restarted.get("/api/my-farm", headers=headers_a).json()
    farm_b = restarted.get("/api/my-farm", headers=headers_b).json()
    assert farm_a["village"] == "Rampur"
    assert farm_a["farm_size"] == 3.5
    assert farm_b["village"] == "Kanpur"
    assert farm_b["farm_size"] == 6.0
    assert farm_a["farmer_id"] != farm_b["farmer_id"]