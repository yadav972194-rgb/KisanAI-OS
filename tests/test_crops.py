"""
KisanAI OS - Phase 5.2 Crop module tests.

Covers create/read/update/delete, validation, duplicate handling,
farmer linkage, farmer-wise listing, delete-disease referential
integrity, and authentication/authorization on every crop endpoint.
"""

import pytest

from tests.conftest import create_farmer, unique_mobile


def _crop_payload(crop_name=None, farmer_id=None, **overrides):
    payload = {
        "farmer_id": farmer_id,
        "crop_name": (
            crop_name if crop_name is not None else f"Crop{unique_mobile()}"
        ),
        "season": "Kharif",
        "duration_days": 120,
        "water_requirement": "High",
    }
    payload.update(overrides)
    return payload


def _create_crop(client, headers, crop_name=None, farmer_id=None, **overrides):
    payload = _crop_payload(crop_name=crop_name, farmer_id=farmer_id, **overrides)
    response = client.post("/api/crops", json=payload, headers=headers)
    return response, payload


def _crop_id(client, headers, crop_name):
    listed = client.get("/api/crops", headers=headers).json()
    for crop in listed:
        if crop["crop_name"] == crop_name:
            return crop["crop_id"]
    raise AssertionError(f"crop {crop_name} not found")


def _farmer_id(client, headers, mobile):
    listed = client.get("/api/farmers", headers=headers).json()
    for farmer in listed:
        if farmer["mobile"] == mobile:
            return farmer["farmer_id"]
    raise AssertionError(f"farmer {mobile} not found")


# ==========================================================
# A. Crop create
# ==========================================================

def test_create_crop_success(client, admin_headers):
    response, payload = _create_crop(client, admin_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["message"] == "Crop Added Successfully"


def test_create_crop_normalizes_text(client, admin_headers):
    response, _ = _create_crop(client, admin_headers, crop_name="  Basmati   Rice  ")
    assert response.status_code == 200

    crop = client.get(
        f"/api/crops/{_crop_id(client, admin_headers, 'Basmati Rice')}",
        headers=admin_headers,
    )
    assert crop.status_code == 200
    assert crop.json()["crop_name"] == "Basmati Rice"


def test_create_crop_with_valid_farmer_id(client, admin_headers):
    _, payload = create_farmer(client, admin_headers)
    farmer_id = _farmer_id(client, admin_headers, payload["mobile"])

    response, _ = _create_crop(client, admin_headers, farmer_id=farmer_id)
    assert response.status_code == 200


# ==========================================================
# B. Crop create with invalid farmer_id
# ==========================================================

def test_create_crop_invalid_farmer_404(client, admin_headers):
    response, _ = _create_crop(client, admin_headers, farmer_id=99999999)
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"


# ==========================================================
# C. Crop create validation failures
# ==========================================================

@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"crop_name": ""}, "crop_name"),
        ({"crop_name": "   "}, "crop_name"),
        ({"crop_name": None}, "crop_name"),
        ({"season": ""}, "season"),
        ({"season": "   "}, "season"),
        ({"water_requirement": ""}, "water_requirement"),
        ({"duration_days": 0}, "duration_days"),
        ({"duration_days": -10}, "duration_days"),
        ({"duration_days": "abc"}, "duration_days"),
        ({"duration_days": None}, "duration_days"),
    ],
)
def test_create_crop_validation_422(client, admin_headers, overrides, field):
    payload = _crop_payload(**overrides)
    payload.pop("crop_name") if field == "crop_name" and overrides.get("crop_name") is None else None
    payload.pop("season") if field == "season" and overrides.get("season") is None else None
    payload.pop("duration_days") if field == "duration_days" and overrides.get("duration_days") is None else None

    response = client.post("/api/crops", json=payload, headers=admin_headers)
    assert response.status_code == 422


# ==========================================================
# D. Duplicate crop
# ==========================================================

def test_create_duplicate_crop_409(client, admin_headers):
    crop_name = f"DupCrop{unique_mobile()}"
    first, _ = _create_crop(client, admin_headers, crop_name=crop_name)
    assert first.status_code == 200

    second, _ = _create_crop(client, admin_headers, crop_name=crop_name)
    assert second.status_code == 409
    assert second.json()["message"] == "Crop name already exists"


def test_update_to_duplicate_crop_409(client, admin_headers):
    name_a = f"UpdateA{unique_mobile()}"
    name_b = f"UpdateB{unique_mobile()}"

    _create_crop(client, admin_headers, crop_name=name_a)
    _, second_payload = _create_crop(client, admin_headers, crop_name=name_b)
    crop_b_id = _crop_id(client, admin_headers, name_b)

    response = client.put(
        f"/api/crops/{crop_b_id}",
        json=_crop_payload(crop_name=name_a),
        headers=admin_headers,
    )
    assert response.status_code == 409
    assert response.json()["message"] == "Crop name already exists"


def test_update_keeps_own_crop_name(client, admin_headers):
    crop_name = f"KeepName{unique_mobile()}"
    _create_crop(client, admin_headers, crop_name=crop_name)
    crop_id = _crop_id(client, admin_headers, crop_name)

    response = client.put(
        f"/api/crops/{crop_id}",
        json=_crop_payload(crop_name=crop_name),
        headers=admin_headers,
    )
    assert response.status_code == 200


# ==========================================================
# E/F. Crop get
# ==========================================================

def test_get_crop(client, admin_headers):
    response, payload = _create_crop(client, admin_headers)
    crop_id = _crop_id(client, admin_headers, payload["crop_name"])

    detail = client.get(f"/api/crops/{crop_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["crop_name"] == payload["crop_name"]
    assert detail.json()["season"] == "Kharif"
    assert detail.json()["duration_days"] == 120
    assert "created_at" in detail.json()


def test_get_crop_not_found_404(client, admin_headers):
    response = client.get("/api/crops/99999999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Crop Not Found"


# ==========================================================
# G. Crop list
# ==========================================================

def test_list_crops(client, admin_headers):
    _create_crop(client, admin_headers)
    _create_crop(client, admin_headers)

    listed = client.get("/api/crops", headers=admin_headers)
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)
    assert len(listed.json()) >= 2


# ==========================================================
# H. Farmer-wise crop listing
# ==========================================================

def test_crops_by_farmer(client, admin_headers):
    _, payload = create_farmer(client, admin_headers)
    farmer_id = _farmer_id(client, admin_headers, payload["mobile"])

    _create_crop(client, admin_headers, crop_name=f"F1Crop{unique_mobile()}", farmer_id=farmer_id)
    _create_crop(client, admin_headers, crop_name=f"F1Crop{unique_mobile()}", farmer_id=farmer_id)
    _create_crop(client, admin_headers)

    listed = client.get(
        f"/api/crops?farmer_id={farmer_id}", headers=admin_headers
    )
    assert listed.status_code == 200
    assert len(listed.json()) == 2
    assert all(c["farmer_id"] == farmer_id for c in listed.json())


def test_crops_by_farmer_empty_list(client, admin_headers):
    _, payload = create_farmer(client, admin_headers)
    farmer_id = _farmer_id(client, admin_headers, payload["mobile"])

    listed = client.get(
        f"/api/crops?farmer_id={farmer_id}", headers=admin_headers
    )
    assert listed.status_code == 200
    assert listed.json() == []


def test_crops_by_farmer_invalid_404(client, admin_headers):
    listed = client.get("/api/crops?farmer_id=99999999", headers=admin_headers)
    assert listed.status_code == 404
    assert listed.json()["message"] == "Farmer Not Found"


# ==========================================================
# I/J. Crop update
# ==========================================================

def test_update_crop_preserves_created_at(client, admin_headers):
    _, payload = _create_crop(client, admin_headers)
    crop_id = _crop_id(client, admin_headers, payload["crop_name"])

    before = client.get(f"/api/crops/{crop_id}", headers=admin_headers).json()

    response = client.put(
        f"/api/crops/{crop_id}",
        json=_crop_payload(
            crop_name=f"Updated{unique_mobile()}",
            season="Rabi",
            duration_days=90,
            water_requirement="Low",
        ),
        headers=admin_headers,
    )
    assert response.status_code == 200

    after = client.get(f"/api/crops/{crop_id}", headers=admin_headers).json()
    assert after["season"] == "Rabi"
    assert after["duration_days"] == 90
    assert after["water_requirement"] == "Low"
    assert after["created_at"] == before["created_at"]
    assert after["crop_id"] == crop_id


def test_update_crop_invalid_farmer_404(client, admin_headers):
    _, payload = _create_crop(client, admin_headers)
    crop_id = _crop_id(client, admin_headers, payload["crop_name"])

    response = client.put(
        f"/api/crops/{crop_id}",
        json=_crop_payload(farmer_id=99999999),
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"


def test_update_crop_reassigns_farmer(client, admin_headers):
    _, payload = _create_crop(client, admin_headers)
    crop_id = _crop_id(client, admin_headers, payload["crop_name"])

    _, farmer_payload = create_farmer(client, admin_headers)
    farmer_id = _farmer_id(client, admin_headers, farmer_payload["mobile"])

    response = client.put(
        f"/api/crops/{crop_id}",
        json=_crop_payload(farmer_id=farmer_id),
        headers=admin_headers,
    )
    assert response.status_code == 200

    detail = client.get(f"/api/crops/{crop_id}", headers=admin_headers).json()
    assert detail["farmer_id"] == farmer_id


def test_update_crop_not_found_404(client, admin_headers):
    response = client.put(
        "/api/crops/99999999",
        json=_crop_payload(),
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Crop Not Found"


# ==========================================================
# K. Crop delete + disease referential integrity
# ==========================================================

def test_delete_crop(client, admin_headers):
    _, payload = _create_crop(client, admin_headers)
    crop_id = _crop_id(client, admin_headers, payload["crop_name"])

    response = client.delete(f"/api/crops/{crop_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Crop Deleted Successfully"

    detail = client.get(f"/api/crops/{crop_id}", headers=admin_headers)
    assert detail.status_code == 404


def test_delete_crop_preserves_diseases(client, admin_headers):
    _, payload = _create_crop(client, admin_headers)
    crop_id = _crop_id(client, admin_headers, payload["crop_name"])

    disease = client.post(
        "/api/diseases",
        json={
            "crop_id": crop_id,
            "crop_name": payload["crop_name"],
            "disease_name": f"Blast{unique_mobile()}",
            "symptoms": "brown spots",
            "solution": "spray fungicide",
            "severity": "Medium",
        },
        headers=admin_headers,
    )
    assert disease.status_code == 200
    disease_id = client.get("/api/diseases", headers=admin_headers).json()[-1]["disease_id"]

    deleted = client.delete(f"/api/crops/{crop_id}", headers=admin_headers)
    assert deleted.status_code == 200

    remaining = client.get(f"/api/diseases/{disease_id}", headers=admin_headers)
    assert remaining.status_code == 200
    assert remaining.json()["crop_id"] is None
    assert remaining.json()["crop_name"] == payload["crop_name"]


def test_delete_crop_not_found_404(client, admin_headers):
    response = client.delete("/api/crops/99999999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Crop Not Found"


# ==========================================================
# L. Authentication (401) on every crop endpoint
# ==========================================================

def test_crop_reads_require_auth(client):
    assert client.get("/api/crops").status_code == 401
    assert client.get("/api/crops/1").status_code == 401
    assert client.get("/api/crops?farmer_id=1").status_code == 401


def test_crop_writes_require_auth(client):
    payload = _crop_payload()
    assert client.post("/api/crops", json=payload).status_code == 401
    assert client.put("/api/crops/1", json=payload).status_code == 401
    assert client.delete("/api/crops/1").status_code == 401


# ==========================================================
# M. Authorization (403 for non-admin writes)
# ==========================================================

def test_crop_writes_admin_only(client, user_headers):
    payload = _crop_payload()
    assert client.post("/api/crops", json=payload, headers=user_headers).status_code == 403
    assert client.put("/api/crops/1", json=payload, headers=user_headers).status_code == 403
    assert client.delete("/api/crops/1", headers=user_headers).status_code == 403


def test_authenticated_user_can_read_crops(client, user_headers, admin_headers):
    _, payload = _create_crop(client, admin_headers)
    crop_id = _crop_id(client, admin_headers, payload["crop_name"])

    assert client.get("/api/crops", headers=user_headers).status_code == 200
    assert client.get(f"/api/crops/{crop_id}", headers=user_headers).status_code == 200


# ==========================================================
# N. Farmer <-> Crop relationship
# ==========================================================

def test_farmer_has_multiple_crops(client, admin_headers):
    _, payload = create_farmer(client, admin_headers)
    farmer_id = _farmer_id(client, admin_headers, payload["mobile"])

    crop_ids = []
    for _ in range(3):
        response, crop_payload = _create_crop(
            client, admin_headers, farmer_id=farmer_id
        )
        assert response.status_code == 200
        crop_ids.append(_crop_id(client, admin_headers, crop_payload["crop_name"]))

    detail = client.get(f"/api/farmers/{farmer_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert len(detail.json()["crops"]) == 3

    for crop in detail.json()["crops"]:
        assert crop["farmer_id"] == farmer_id


def test_crop_identifies_its_farmer(client, admin_headers):
    _, payload = create_farmer(client, admin_headers)
    farmer_id = _farmer_id(client, admin_headers, payload["mobile"])

    response, crop_payload = _create_crop(client, admin_headers, farmer_id=farmer_id)
    assert response.status_code == 200
    crop_id = _crop_id(client, admin_headers, crop_payload["crop_name"])

    detail = client.get(f"/api/crops/{crop_id}", headers=admin_headers).json()
    assert detail["farmer_id"] == farmer_id
