"""
KisanAI OS - Phase 5.1 Farmer module tests.

Covers create/read/update/delete, mobile validation + uniqueness,
input normalization, 404 handling, and the delete referential policy.
"""

import pytest

from tests.conftest import create_farmer, farmer_payload, unique_mobile


def test_create_farmer_success(client, admin_headers):
    response, payload = create_farmer(client, admin_headers)

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["message"] == "Farmer Added Successfully"


def test_create_farmer_requires_name(client, admin_headers):
    payload = farmer_payload()
    del payload["name"]
    response = client.post("/api/farmers", json=payload, headers=admin_headers)
    assert response.status_code == 422


def test_create_farmer_requires_mobile(client, admin_headers):
    payload = farmer_payload()
    del payload["mobile"]
    response = client.post("/api/farmers", json=payload, headers=admin_headers)
    assert response.status_code == 422


@pytest.mark.parametrize(
    "bad_mobile",
    [
        "12345",
        "1234567890",
        "98765432100",
        "987654321",
        "987654321a",
        "5987654321",
    ],
)
def test_create_farmer_invalid_mobile(client, admin_headers, bad_mobile):
    response, _ = create_farmer(client, admin_headers, mobile=bad_mobile)
    assert response.status_code == 422


@pytest.mark.parametrize("field", ["name", "village", "district", "state"])
def test_create_farmer_blank_text_422(client, admin_headers, field):
    """Blank text fields are rejected, matching crop/soil/disease."""
    payload = farmer_payload()
    payload[field] = "   "
    response = client.post("/api/farmers", json=payload, headers=admin_headers)
    assert response.status_code == 422


def test_create_farmer_blank_mobile_422(client, admin_headers):
    payload = farmer_payload()
    payload["mobile"] = "   "
    response = client.post("/api/farmers", json=payload, headers=admin_headers)
    assert response.status_code == 422


def test_create_farmer_normalizes_input(client, admin_headers):
    response, payload = create_farmer(
        client,
        admin_headers,
        name="   Ravi   Kumar  ",
        mobile=f"  {unique_mobile()}  ",
        village="  Sitapur  ",
        district="  Sitapur  ",
        state="  Uttar Pradesh  ",
    )
    assert response.status_code == 200

    lookup = client.get(
        f"/api/farmers/by-mobile/{payload['mobile'].strip()}",
        headers=admin_headers,
    )
    assert lookup.status_code == 200
    body = lookup.json()
    assert body["name"] == "Ravi Kumar"
    assert body["village"] == "Sitapur"
    assert body["state"] == "Uttar Pradesh"


def test_create_farmer_duplicate_mobile(client, admin_headers):
    mobile = unique_mobile()

    first, _ = create_farmer(client, admin_headers, mobile=mobile)
    assert first.status_code == 200

    second, _ = create_farmer(
        client, admin_headers, name="Another Farmer", mobile=mobile
    )
    assert second.status_code == 409
    assert second.json()["message"] == "Mobile number already exists"


def test_get_farmer_by_id(client, admin_headers):
    response, payload = create_farmer(client, admin_headers)

    farmer_id = _find_farmer_id(client, admin_headers, payload["mobile"])
    detail = client.get(
        f"/api/farmers/{farmer_id}", headers=admin_headers
    )
    assert detail.status_code == 200
    body = detail.json()
    assert body["farmer_id"] == farmer_id
    assert body["name"] == payload["name"]
    assert body["mobile"] == payload["mobile"]
    assert body["village"] == payload["village"]
    assert body["district"] == payload["district"]
    assert body["state"] == payload["state"]
    assert "created_at" in body
    assert body["crops"] == []


def test_get_farmer_not_found(client, admin_headers):
    response = client.get("/api/farmers/99999999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"


def test_get_farmer_by_mobile(client, admin_headers):
    response, payload = create_farmer(client, admin_headers)

    lookup = client.get(
        f"/api/farmers/by-mobile/{payload['mobile']}",
        headers=admin_headers,
    )
    assert lookup.status_code == 200
    assert lookup.json()["mobile"] == payload["mobile"]


def test_get_farmer_by_mobile_not_found(client, admin_headers):
    response = client.get(
        "/api/farmers/by-mobile/9000000000", headers=admin_headers
    )
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"


def test_list_farmers(client, admin_headers):
    created = []
    for _ in range(3):
        response, payload = create_farmer(client, admin_headers)
        created.append(payload["mobile"])

    listed = client.get("/api/farmers", headers=admin_headers)
    assert listed.status_code == 200
    mobiles = [farmer["mobile"] for farmer in listed.json()]
    for mobile in created:
        assert mobile in mobiles


def test_update_farmer(client, admin_headers):
    response, payload = create_farmer(client, admin_headers)
    farmer_id = _find_farmer_id(client, admin_headers, payload["mobile"])

    new_payload = {
        "name": "Ravi Updated",
        "mobile": unique_mobile(),
        "village": "Lucknow",
        "district": "Lucknow",
        "state": "Uttar Pradesh",
    }
    updated = client.put(
        f"/api/farmers/{farmer_id}", json=new_payload, headers=admin_headers
    )
    assert updated.status_code == 200
    assert updated.json()["message"] == "Farmer Updated Successfully"

    detail = client.get(f"/api/farmers/{farmer_id}", headers=admin_headers)
    assert detail.json()["name"] == "Ravi Updated"
    assert detail.json()["mobile"] == new_payload["mobile"]
    assert detail.json()["village"] == "Lucknow"


def test_update_farmer_not_found(client, admin_headers):
    payload = farmer_payload()
    response = client.put("/api/farmers/99999999", json=payload,
                          headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"


def test_update_farmer_invalid_mobile(client, admin_headers):
    response, payload = create_farmer(client, admin_headers)
    farmer_id = _find_farmer_id(client, admin_headers, payload["mobile"])

    payload["mobile"] = "12345"
    updated = client.put(
        f"/api/farmers/{farmer_id}", json=payload, headers=admin_headers
    )
    assert updated.status_code == 422


@pytest.mark.parametrize("field", ["name", "village", "district", "state"])
def test_update_farmer_blank_text_422(client, admin_headers, field):
    response, payload = create_farmer(client, admin_headers)
    farmer_id = _find_farmer_id(client, admin_headers, payload["mobile"])

    payload[field] = "   "
    updated = client.put(
        f"/api/farmers/{farmer_id}", json=payload, headers=admin_headers
    )
    assert updated.status_code == 422


def test_update_farmer_duplicate_mobile(client, admin_headers):
    mobile_a = unique_mobile()
    mobile_b = unique_mobile()

    create_farmer(client, admin_headers, mobile=mobile_a)
    second, payload_b = create_farmer(client, admin_headers, mobile=mobile_b)
    farmer_id_b = _find_farmer_id(client, admin_headers, mobile_b)

    payload_b["mobile"] = mobile_a
    updated = client.put(
        f"/api/farmers/{farmer_id_b}", json=payload_b, headers=admin_headers
    )
    assert updated.status_code == 409
    assert updated.json()["message"] == "Mobile number already exists"


def test_update_farmer_keeps_own_mobile(client, admin_headers):
    response, payload = create_farmer(client, admin_headers)
    farmer_id = _find_farmer_id(client, admin_headers, payload["mobile"])

    payload["name"] = "Renamed"
    updated = client.put(
        f"/api/farmers/{farmer_id}", json=payload, headers=admin_headers
    )
    assert updated.status_code == 200

    detail = client.get(f"/api/farmers/{farmer_id}", headers=admin_headers)
    assert detail.json()["name"] == "Renamed"
    assert detail.json()["mobile"] == payload["mobile"]


def test_delete_farmer_policy_crops_set_null_soils_deleted(client, admin_headers):
    response, payload = create_farmer(client, admin_headers)
    farmer_id = _find_farmer_id(client, admin_headers, payload["mobile"])

    crop = client.post(
        "/api/crops",
        json={
            "farmer_id": farmer_id,
            "crop_name": f"CropPolicy{farmer_id}",
            "season": "Kharif",
            "duration_days": 120,
            "water_requirement": "High",
        },
        headers=admin_headers,
    )
    assert crop.status_code == 200
    crop_id = _find_crop_id(client, admin_headers, f"CropPolicy{farmer_id}")

    soil = client.post(
        "/api/soils",
        json={
            "farmer_id": farmer_id,
            "soil_type": "Loamy",
            "ph": 6.5,
            "moisture": 40.0,
            "nitrogen": 40,
            "phosphorus": 20,
            "potassium": 15,
        },
        headers=admin_headers,
    )
    assert soil.status_code == 200
    soil_id = _find_soil_id(client, admin_headers, farmer_id)

    deleted = client.delete(
        f"/api/farmers/{farmer_id}", headers=admin_headers
    )
    assert deleted.status_code == 200
    assert deleted.json()["message"] == "Farmer Deleted Successfully"

    gone = client.get(f"/api/farmers/{farmer_id}", headers=admin_headers)
    assert gone.status_code == 404

    crop_after = client.get(f"/api/crops/{crop_id}", headers=admin_headers)
    assert crop_after.status_code == 200
    assert crop_after.json()["farmer_id"] is None

    soil_after = client.get(f"/api/soils/{soil_id}", headers=admin_headers)
    assert soil_after.status_code == 404


def test_delete_farmer_not_found(client, admin_headers):
    response = client.delete("/api/farmers/99999999", headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["message"] == "Farmer Not Found"


def _find_farmer_id(client, headers, mobile):
    listed = client.get("/api/farmers", headers=headers).json()
    for farmer in listed:
        if farmer["mobile"] == mobile:
            return farmer["farmer_id"]
    raise AssertionError(f"farmer with mobile {mobile} not found")


def _find_crop_id(client, headers, crop_name):
    listed = client.get("/api/crops", headers=headers).json()
    for crop in listed:
        if crop["crop_name"] == crop_name:
            return crop["crop_id"]
    raise AssertionError(f"crop {crop_name} not found")


def _find_soil_id(client, headers, farmer_id):
    listed = client.get("/api/soils", headers=headers).json()
    for soil in listed:
        if soil["farmer_id"] == farmer_id:
            return soil["soil_id"]
    raise AssertionError(f"soil for farmer {farmer_id} not found")
