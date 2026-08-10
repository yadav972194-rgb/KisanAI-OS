"""
KisanAI OS - Phase 5.4 Disease module tests.

Covers create/read/update/delete, validation and normalization,
duplicate handling (linked crop_id only, NULL crop_id exempt),
crop_name sync, update preserve-on-omit, delete behavior,
authentication/authorization on every disease endpoint, and the
crop-delete preserves diseases relationship.
"""

import pytest

from tests.conftest import unique_mobile


def _disease_payload(crop_id=None, crop_name="Rice", disease_name=None, **overrides):
    payload = {
        "crop_id": crop_id,
        "crop_name": crop_name,
        "disease_name": (
            disease_name if disease_name is not None else f"Dis{unique_mobile()}"
        ),
        "symptoms": "yellow spots on leaves",
        "solution": "spray recommended fungicide",
        "severity": "Medium",
    }
    payload.update(overrides)
    return payload


def _create_disease(client, headers, **overrides):
    payload = _disease_payload(**overrides)
    response = client.post("/api/diseases", json=payload, headers=headers)
    return response, payload


def _create_crop(client, headers):
    crop_name = f"CropDis{unique_mobile()}"
    response = client.post(
        "/api/crops",
        json={
            "crop_name": crop_name,
            "season": "Rabi",
            "duration_days": 110,
            "water_requirement": "Medium",
        },
        headers=headers,
    )
    assert response.status_code == 200, response.text

    listed = client.get("/api/crops", headers=headers).json()
    crop_id = next(c["crop_id"] for c in listed if c["crop_name"] == crop_name)
    return crop_id, crop_name


def _disease_id(client, headers, disease_name, crop_id=None):
    listed = client.get("/api/diseases", headers=headers).json()
    for disease in listed:
        if (
            disease["disease_name"] == disease_name
            and disease["crop_id"] == crop_id
        ):
            return disease["disease_id"]
    raise AssertionError(f"disease {disease_name} (crop {crop_id}) not found")


# ==========================================================
# A. Disease create
# ==========================================================

def test_create_disease_success(client, admin_headers):
    response, payload = _create_disease(client, admin_headers)
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["message"] == "Disease Added Successfully"

    disease = client.get(
        f"/api/diseases/{_disease_id(client, admin_headers, payload['disease_name'])}",
        headers=admin_headers,
    )
    assert disease.status_code == 200
    assert disease.json()["crop_id"] is None
    assert disease.json()["crop_name"] == "Rice"


def test_create_disease_with_crop(client, admin_headers):
    crop_id, crop_name = _create_crop(client, admin_headers)

    response, payload = _create_disease(
        client, admin_headers, crop_id=crop_id, crop_name="Ignored Name"
    )
    assert response.status_code == 200

    disease_id = _disease_id(
        client, admin_headers, payload["disease_name"], crop_id=crop_id
    )
    detail = client.get(f"/api/diseases/{disease_id}", headers=admin_headers).json()
    assert detail["crop_id"] == crop_id
    assert detail["crop_name"] == crop_name


def test_create_disease_severity_title_cased(client, admin_headers):
    response, payload = _create_disease(client, admin_headers, severity="high")
    assert response.status_code == 200

    disease = client.get(
        f"/api/diseases/{_disease_id(client, admin_headers, payload['disease_name'])}",
        headers=admin_headers,
    )
    assert disease.json()["severity"] == "High"


def test_create_disease_normalizes_text(client, admin_headers):
    response, _ = _create_disease(
        client, admin_headers, disease_name="  Rice   Blast  "
    )
    assert response.status_code == 200

    disease = client.get(
        f"/api/diseases/{_disease_id(client, admin_headers, 'Rice Blast')}",
        headers=admin_headers,
    )
    assert disease.json()["disease_name"] == "Rice Blast"


# ==========================================================
# B. Disease create with invalid crop_id
# ==========================================================

def test_create_disease_invalid_crop_404(client, admin_headers):
    response, _ = _create_disease(client, admin_headers, crop_id=99999999)
    assert response.status_code == 404
    assert response.json()["message"] == "Crop Not Found"


# ==========================================================
# C. Disease create validation failures
# ==========================================================

@pytest.mark.parametrize(
    "overrides, field",
    [
        ({"crop_name": ""}, "crop_name"),
        ({"crop_name": "   "}, "crop_name"),
        ({"crop_name": None}, "crop_name"),
        ({"disease_name": ""}, "disease_name"),
        ({"disease_name": "   "}, "disease_name"),
        ({"disease_name": None}, "disease_name"),
        ({"symptoms": ""}, "symptoms"),
        ({"symptoms": "   "}, "symptoms"),
        ({"symptoms": None}, "symptoms"),
        ({"solution": ""}, "solution"),
        ({"solution": "   "}, "solution"),
        ({"solution": None}, "solution"),
        ({"severity": ""}, "severity"),
        ({"severity": "Extreme"}, "severity"),
        ({"severity": None}, "severity"),
    ],
)
def test_create_disease_validation_422(client, admin_headers, overrides, field):
    payload = _disease_payload(**overrides)
    payload.pop(field) if overrides.get(field) is None else None

    response = client.post("/api/diseases", json=payload, headers=admin_headers)
    assert response.status_code == 422


# ==========================================================
# D. Duplicate handling
# ==========================================================

def test_create_duplicate_disease_409(client, admin_headers):
    crop_id, _ = _create_crop(client, admin_headers)
    disease_name = f"DupDis{unique_mobile()}"

    first, _ = _create_disease(
        client, admin_headers, crop_id=crop_id, disease_name=disease_name
    )
    assert first.status_code == 200

    second, _ = _create_disease(
        client, admin_headers, crop_id=crop_id, disease_name=disease_name
    )
    assert second.status_code == 409
    assert second.json()["message"] == "Disease already exists"


def test_duplicate_disease_null_crop_allowed(client, admin_headers):
    disease_name = f"NullDup{unique_mobile()}"

    first, _ = _create_disease(client, admin_headers, disease_name=disease_name)
    assert first.status_code == 200

    second, _ = _create_disease(client, admin_headers, disease_name=disease_name)
    assert second.status_code == 200


def test_same_name_different_crop_allowed(client, admin_headers):
    crop_a, _ = _create_crop(client, admin_headers)
    crop_b, _ = _create_crop(client, admin_headers)
    disease_name = f"CrossCrop{unique_mobile()}"

    first, _ = _create_disease(
        client, admin_headers, crop_id=crop_a, disease_name=disease_name
    )
    assert first.status_code == 200

    second, _ = _create_disease(
        client, admin_headers, crop_id=crop_b, disease_name=disease_name
    )
    assert second.status_code == 200


def test_update_to_duplicate_disease_409(client, admin_headers):
    crop_id, _ = _create_crop(client, admin_headers)
    name_a = f"UpA{unique_mobile()}"
    name_b = f"UpB{unique_mobile()}"

    _create_disease(client, admin_headers, crop_id=crop_id, disease_name=name_a)
    _create_disease(client, admin_headers, crop_id=crop_id, disease_name=name_b)
    disease_b_id = _disease_id(client, admin_headers, name_b, crop_id=crop_id)

    response = client.put(
        f"/api/diseases/{disease_b_id}",
        json=_disease_payload(crop_id=crop_id, disease_name=name_a),
        headers=admin_headers,
    )
    assert response.status_code == 409
    assert response.json()["message"] == "Disease already exists"


def test_update_keeps_own_disease_name(client, admin_headers):
    crop_id, _ = _create_crop(client, admin_headers)
    disease_name = f"KeepDis{unique_mobile()}"

    _create_disease(client, admin_headers, crop_id=crop_id, disease_name=disease_name)
    disease_id = _disease_id(client, admin_headers, disease_name, crop_id=crop_id)

    response = client.put(
        f"/api/diseases/{disease_id}",
        json=_disease_payload(crop_id=crop_id, disease_name=disease_name),
        headers=admin_headers,
    )
    assert response.status_code == 200


# ==========================================================
# E/F. Disease get
# ==========================================================

def test_get_disease(client, admin_headers):
    response, payload = _create_disease(client, admin_headers)
    disease_id = _disease_id(client, admin_headers, payload["disease_name"])

    detail = client.get(f"/api/diseases/{disease_id}", headers=admin_headers)
    assert detail.status_code == 200
    assert detail.json()["disease_name"] == payload["disease_name"]
    assert detail.json()["symptoms"] == "yellow spots on leaves"
    assert detail.json()["solution"] == "spray recommended fungicide"
    assert detail.json()["severity"] == "Medium"
    assert "created_at" in detail.json()


def test_get_disease_not_found_404(client, admin_headers):
    response = client.get("/api/diseases/99999999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Disease Not Found"


# ==========================================================
# G. Disease list
# ==========================================================

def test_list_diseases(client, admin_headers):
    _create_disease(client, admin_headers)
    _create_disease(client, admin_headers)

    listed = client.get("/api/diseases", headers=admin_headers)
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)
    assert len(listed.json()) >= 2


# ==========================================================
# H/I. Disease update
# ==========================================================

def test_update_disease(client, admin_headers):
    _, payload = _create_disease(client, admin_headers)
    disease_id = _disease_id(client, admin_headers, payload["disease_name"])

    response = client.put(
        f"/api/diseases/{disease_id}",
        json=_disease_payload(
            crop_name="Rice",
            disease_name=f"Updated{unique_mobile()}",
            symptoms="brown lesions",
            solution="remove infected leaves",
            severity="High",
        ),
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Disease Updated Successfully"

    detail = client.get(f"/api/diseases/{disease_id}", headers=admin_headers).json()
    assert detail["symptoms"] == "brown lesions"
    assert detail["solution"] == "remove infected leaves"
    assert detail["severity"] == "High"
    assert detail["crop_id"] == payload["crop_id"]
    assert "created_at" in detail


def test_update_disease_preserves_crop_id_when_omitted(client, admin_headers):
    crop_id, crop_name = _create_crop(client, admin_headers)

    _, payload = _create_disease(
        client, admin_headers, crop_id=crop_id, crop_name=crop_name
    )
    disease_id = _disease_id(
        client, admin_headers, payload["disease_name"], crop_id=crop_id
    )

    response = client.put(
        f"/api/diseases/{disease_id}",
        json=_disease_payload(
            crop_name="SentButIgnored",
            disease_name=payload["disease_name"],
        ),
        headers=admin_headers,
    )
    assert response.status_code == 200

    detail = client.get(f"/api/diseases/{disease_id}", headers=admin_headers).json()
    assert detail["crop_id"] == crop_id
    assert detail["crop_name"] == crop_name


def test_update_disease_reassigns_crop(client, admin_headers):
    crop_b, crop_b_name = _create_crop(client, admin_headers)

    _, payload = _create_disease(client, admin_headers)
    disease_id = _disease_id(client, admin_headers, payload["disease_name"])

    response = client.put(
        f"/api/diseases/{disease_id}",
        json=_disease_payload(crop_id=crop_b, crop_name=crop_b_name),
        headers=admin_headers,
    )
    assert response.status_code == 200

    detail = client.get(f"/api/diseases/{disease_id}", headers=admin_headers).json()
    assert detail["crop_id"] == crop_b
    assert detail["crop_name"] == crop_b_name


def test_update_disease_invalid_crop_404(client, admin_headers):
    _, payload = _create_disease(client, admin_headers)
    disease_id = _disease_id(client, admin_headers, payload["disease_name"])

    response = client.put(
        f"/api/diseases/{disease_id}",
        json=_disease_payload(crop_id=99999999),
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Crop Not Found"


def test_update_disease_not_found_404(client, admin_headers):
    response = client.put(
        "/api/diseases/99999999",
        json=_disease_payload(),
        headers=admin_headers,
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Disease Not Found"


# ==========================================================
# J. Disease delete
# ==========================================================

def test_delete_disease(client, admin_headers):
    _, payload = _create_disease(client, admin_headers)
    disease_id = _disease_id(client, admin_headers, payload["disease_name"])

    response = client.delete(f"/api/diseases/{disease_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["message"] == "Disease Deleted Successfully"

    detail = client.get(f"/api/diseases/{disease_id}", headers=admin_headers)
    assert detail.status_code == 404


def test_delete_disease_not_found_404(client, admin_headers):
    response = client.delete("/api/diseases/99999999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Disease Not Found"


# ==========================================================
# K. Authentication (401) on every disease endpoint
# ==========================================================

def test_disease_reads_require_auth(client):
    assert client.get("/api/diseases").status_code == 401
    assert client.get("/api/diseases/1").status_code == 401


def test_disease_writes_require_auth(client):
    payload = _disease_payload()
    assert client.post("/api/diseases", json=payload).status_code == 401
    assert client.put("/api/diseases/1", json=payload).status_code == 401
    assert client.delete("/api/diseases/1").status_code == 401


# ==========================================================
# L. Authorization (403 for non-admin writes)
# ==========================================================

def test_disease_writes_admin_only(client, user_headers):
    payload = _disease_payload()
    assert client.post("/api/diseases", json=payload, headers=user_headers).status_code == 403
    assert client.put("/api/diseases/1", json=payload, headers=user_headers).status_code == 403
    assert client.delete("/api/diseases/1", headers=user_headers).status_code == 403


def test_authenticated_user_can_read_diseases(client, user_headers, admin_headers):
    _, payload = _create_disease(client, admin_headers)
    disease_id = _disease_id(client, admin_headers, payload["disease_name"])

    assert client.get("/api/diseases", headers=user_headers).status_code == 200
    assert client.get(f"/api/diseases/{disease_id}", headers=user_headers).status_code == 200
