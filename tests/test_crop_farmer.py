"""
KisanAI OS - Phase 5.1 Farmer <-> Crop relationship tests.

Verifies farmer_id is accepted on crop create, invalid farmer_id returns
404, the relationship is never duplicated, and farmer detail exposes
associated crops.
"""

from tests.conftest import unique_mobile


def _create_farmer(client, headers, mobile=None, name="Farmer For Crop"):
    payload = {
        "name": name,
        "mobile": mobile or unique_mobile(),
        "village": "Sitapur",
        "district": "Sitapur",
        "state": "Uttar Pradesh",
    }
    response = client.post("/api/farmers", json=payload, headers=headers)
    return response, payload


def _farmer_id_by_mobile(client, headers, mobile):
    listed = client.get("/api/farmers", headers=headers).json()
    for farmer in listed:
        if farmer["mobile"] == mobile:
            return farmer["farmer_id"]
    raise AssertionError(f"farmer {mobile} not found")


def _create_crop(client, headers, farmer_id=None, crop_name=None):
    payload = {
        "farmer_id": farmer_id,
        "crop_name": crop_name or f"Crop{unique_mobile()}",
        "season": "Kharif",
        "duration_days": 120,
        "water_requirement": "High",
    }
    return client.post("/api/crops", json=payload, headers=headers)


def test_crop_create_with_valid_farmer_id(client, admin_headers):
    created, payload = _create_farmer(client, admin_headers)
    assert created.status_code == 200

    farmer_id = _farmer_id_by_mobile(
        client, admin_headers, payload["mobile"]
    )

    crop = _create_crop(client, admin_headers, farmer_id=farmer_id)
    assert crop.status_code == 200


def test_crop_create_with_invalid_farmer_id(client, admin_headers):
    crop = _create_crop(client, admin_headers, farmer_id=99999999)
    assert crop.status_code == 404
    assert crop.json()["message"] == "Farmer Not Found"


def test_crop_create_without_farmer_id_is_allowed(client, admin_headers):
    crop = _create_crop(client, admin_headers, farmer_id=None)
    assert crop.status_code == 200


def test_farmer_detail_exposes_crops(client, admin_headers):
    created, payload = _create_farmer(
        client, admin_headers, name="Farmer With Crops"
    )
    assert created.status_code == 200
    farmer_id = _farmer_id_by_mobile(
        client, admin_headers, payload["mobile"]
    )

    crop = _create_crop(
        client, admin_headers, farmer_id=farmer_id, crop_name="RicePlant"
    )
    assert crop.status_code == 200

    detail = client.get(f"/api/farmers/{farmer_id}", headers=admin_headers)
    assert detail.status_code == 200
    crops = detail.json()["crops"]
    assert any(
        c["crop_name"] == "RicePlant" and c["farmer_id"] == farmer_id
        for c in crops
    )


def test_farmer_relationship_single_column(client, admin_headers):
    """Crop stores exactly one farmer reference column (no duplication)."""
    from config.core.models.crop import Crop

    farmer_cols = [
        col.name
        for col in Crop.__table__.columns
        if "farmer" in col.name.lower()
    ]
    assert farmer_cols == ["farmer_id"]
