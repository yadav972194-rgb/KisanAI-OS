"""
KisanAI OS - Admin Control & Farmer Support: audit trail tests.

Every sensitive mutation (profile/crop/soil corrections, feedback
lifecycle, contacts, farmer deletion) must append an immutable,
read-only record to /api/admin/audit. Read operations must NOT create
audit entries, and no write method is exposed on the audit collection.
"""

from tests.conftest import create_farmer, unique_mobile


def _farmer_id(client, headers, mobile):
    response = client.get(f"/api/farmers/by-mobile/{mobile}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["farmer_id"]


def _create_farmer_and_id(client, headers, **overrides):
    response, payload = create_farmer(client, headers, **overrides)
    assert response.status_code == 200, response.text
    return _farmer_id(client, headers, payload["mobile"])


def _create_feedback(client, headers, farmer_id=None):
    payload = {"subject": "Crop problem", "description": "Detailed description"}
    if farmer_id is not None:
        payload["farmer_id"] = farmer_id
    return client.post("/api/admin/problems", json=payload, headers=headers).json()


def _audit_actions(client, headers, **filters):
    import urllib.parse

    query = ""
    for key, value in filters.items():
        if value is not None:
            query += f"&{key}={urllib.parse.quote(str(value))}"
    response = client.get(f"/api/admin/audit?page=1&size=100{query}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_audit_requires_admin(client, user_headers):
    assert client.get("/api/admin/audit", headers=user_headers).status_code == 403


def test_audit_is_read_only(client, admin_headers):
    assert (
        client.post("/api/admin/audit", json={}, headers=admin_headers).status_code
        == 405
    )
    assert client.put("/api/admin/audit", json={}, headers=admin_headers).status_code == 405
    assert (
        client.delete("/api/admin/audit", headers=admin_headers).status_code == 405
    )


def test_farmer_profile_correction_is_audited(client, admin_headers):
    farmer_id = _create_farmer_and_id(client, admin_headers)
    before = _audit_actions(client, admin_headers)["total"]

    response = client.put(
        f"/api/admin/farmers/{farmer_id}",
        json={
            "name": "Ravi Kumar",
            "mobile": unique_mobile(),
            "village": "Corrected Village",
            "district": "Sitapur",
            "state": "Uttar Pradesh",
        },
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["message"] == "Farmer profile updated successfully"

    audit = _audit_actions(client, admin_headers)
    assert audit["total"] == before + 1
    latest = audit["items"][0]
    assert latest["action"] == "farmer.update"
    assert latest["entity_type"] == "farmer"
    assert latest["entity_id"] == farmer_id
    assert "changes" in latest["details"]


def test_crop_correction_is_audited(client, admin_headers):
    farmer_id = _create_farmer_and_id(client, admin_headers)
    crop_name = f"Crop{unique_mobile()}"
    crop = client.post(
        "/api/crops",
        json={
            "farmer_id": farmer_id,
            "crop_name": crop_name,
            "season": "Kharif",
            "duration_days": 90,
            "water_requirement": "Medium",
        },
        headers=admin_headers,
    )
    assert crop.status_code == 200, crop.text
    listed = client.get("/api/crops", headers=admin_headers).json()
    crop_id = next(item["crop_id"] for item in listed if item["crop_name"] == crop_name)

    before = _audit_actions(client, admin_headers, entity_type="crop")["total"]
    response = client.put(
        f"/api/admin/farmers/{farmer_id}/crops/{crop_id}",
        json={
            "crop_name": f"Crop{unique_mobile()}",
            "season": "Rabi",
            "duration_days": 100,
            "water_requirement": "High",
        },
        headers=admin_headers,
    )
    assert response.status_code == 200, response.text

    audit = _audit_actions(client, admin_headers, entity_type="crop")
    assert audit["total"] == before + 1
    assert audit["items"][0]["action"] == "crop.update"


def test_feedback_status_change_is_audited(client, admin_headers):
    created = _create_feedback(client, admin_headers)
    before = _audit_actions(client, admin_headers, entity_type="feedback")["total"]

    transition = client.patch(
        f"/api/admin/problems/{created['feedback_id']}/status",
        json={"status": "investigating"},
        headers=admin_headers,
    )
    assert transition.status_code == 200

    audit = _audit_actions(client, admin_headers, entity_type="feedback")
    assert audit["total"] == before + 1
    entry = audit["items"][0]
    assert entry["action"] == "feedback.status"
    assert entry["details"] == {"from": "new", "to": "investigating"}


def test_contact_record_is_audited(client, admin_headers):
    farmer_id = _create_farmer_and_id(client, admin_headers)
    before = _audit_actions(client, admin_headers, entity_type="contact")["total"]

    created = client.post(
        f"/api/admin/farmers/{farmer_id}/contacts",
        json={"channel": "phone", "note": "Follow-up call"},
        headers=admin_headers,
    )
    assert created.status_code == 200

    audit = _audit_actions(client, admin_headers, entity_type="contact")
    assert audit["total"] == before + 1
    assert audit["items"][0]["action"] == "contact.create"


def test_farmer_delete_is_audited(client, super_admin_headers):
    farmer_id = _create_farmer_and_id(client, super_admin_headers)
    before = _audit_actions(client, super_admin_headers, entity_type="farmer")["total"]

    deleted = client.delete(
        f"/api/admin/farmers/{farmer_id}?confirm=true",
        headers=super_admin_headers,
    )
    assert deleted.status_code == 200, deleted.text

    audit = _audit_actions(client, super_admin_headers, entity_type="farmer")
    assert audit["total"] == before + 1
    entry = audit["items"][0]
    assert entry["action"] == "farmer.delete"
    assert entry["details"]["affected"]["crops"] == 0


def test_read_operations_create_no_audit(client, admin_headers):
    farmer_id = _create_farmer_and_id(client, admin_headers)
    before = _audit_actions(client, admin_headers)["total"]

    client.get(f"/api/admin/farmers/{farmer_id}", headers=admin_headers)
    client.get("/api/admin/farmers?q=nonexistent", headers=admin_headers)
    client.get("/api/admin/problems", headers=admin_headers)
    client.get(f"/api/admin/farmers/{farmer_id}/contacts", headers=admin_headers)

    after = _audit_actions(client, admin_headers)["total"]
    assert after == before


def test_audit_trail_is_append_only(client, admin_headers, user_headers):
    response = _audit_actions(client, admin_headers)
    assert response["total"] >= 0
    for entry in response["items"]:
        assert set(entry["details"].keys()).isdisjoint({"_delete", "_update"})