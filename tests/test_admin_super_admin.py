"""
KisanAI OS - Admin Control & Farmer Support: super-admin escalation tests.

Base admins can run shared support features but are FORBIDDEN from
farmer deletion, user deletion and privilege assignment. Super admins
can escalate/de-escalate other admins, but never themselves, and the
"at least one active super-admin remains" invariant is enforced.
"""

from config.core.api.auth import hash_password
from config.core.database import SessionLocal
from config.core.models.user import User
from config.core.services.admin_user_service import AdminUserService
from tests.conftest import create_farmer, unique_mobile


def _create_user(session, username, role="admin", super_admin=False, active=True):
    user = User(
        username=username,
        hashed_password=hash_password("password123"),
        full_name="Test Account",
        role=role,
        is_active=active,
        super_admin=super_admin,
    )
    session.add(user)
    session.commit()
    return user.id


def _farmer_id(client, headers, mobile):
    response = client.get(f"/api/farmers/by-mobile/{mobile}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()["farmer_id"]


def _create_farmer_and_id(client, headers, **overrides):
    response, payload = create_farmer(client, headers, **overrides)
    assert response.status_code == 200, response.text
    return _farmer_id(client, headers, payload["mobile"])


def _super_username():
    import random

    return f"supermgr{random.randint(100000, 999999)}"


def _plain_username():
    import random

    return f"plainmgr{random.randint(100000, 999999)}"


# ==========================================================
# Base admin is locked out of super-admin capabilities
# ==========================================================

def test_plain_admin_cannot_toggle_super_admin(client, admin_headers):
    # A plain admin must be forbidden from changing ANY account's flag,
    # even when it has no permission to know which accounts are super.
    response = client.post(
        "/api/admin/users/1/super-admin",
        json={"super_admin": True},
        headers=admin_headers,
    )
    assert response.status_code == 403


def test_plain_admin_cannot_preview_or_delete_farmer(client, admin_headers, super_admin_headers):
    farmer_id = _create_farmer_and_id(client, super_admin_headers)
    assert (
        client.post(
            f"/api/admin/farmers/{farmer_id}/delete/preview", headers=admin_headers
        ).status_code
        == 403
    )
    assert (
        client.delete(
            f"/api/admin/farmers/{farmer_id}?confirm=true", headers=admin_headers
        ).status_code
        == 403
    )


def test_plain_admin_cannot_delete_user(client, admin_headers):
    response = client.delete(
        "/api/admin/users/999999?confirm=true", headers=admin_headers
    )
    assert response.status_code == 403


# ==========================================================
# Farmer deletion requires super-admin + explicit confirmation
# ==========================================================

def test_delete_requires_confirmation(client, super_admin_headers):
    farmer_id = _create_farmer_and_id(client, super_admin_headers)
    response = client.delete(
        f"/api/admin/farmers/{farmer_id}", headers=super_admin_headers
    )
    assert response.status_code == 400
    assert "confirmation" in response.json()["detail"]["message"].lower()

    preview = client.post(
        f"/api/admin/farmers/{farmer_id}/delete/preview",
        headers=super_admin_headers,
    )
    assert preview.status_code == 200
    assert preview.json()["farmer_id"] == farmer_id

    deleted = client.delete(
        f"/api/admin/farmers/{farmer_id}?confirm=true",
        headers=super_admin_headers,
    )
    assert deleted.status_code == 200, deleted.text
    missing = client.get(
        f"/api/admin/farmers/{farmer_id}", headers=super_admin_headers
    )
    assert missing.status_code == 404


def test_super_admin_can_escalate_and_deescalate_other_admin(
    client, super_admin_headers
):
    username = _plain_username()
    target_id = _create_user(SessionLocal(), username)

    enabled = client.post(
        f"/api/admin/users/{target_id}/super-admin",
        json={"super_admin": True},
        headers=super_admin_headers,
    )
    assert enabled.status_code == 200, enabled.text

    session = SessionLocal()
    try:
        target = session.query(User).filter_by(id=target_id).first()
        assert target.super_admin is True
    finally:
        session.close()

    disabled = client.post(
        f"/api/admin/users/{target_id}/super-admin",
        json={"super_admin": False},
        headers=super_admin_headers,
    )
    assert disabled.status_code == 200, disabled.text

    session = SessionLocal()
    try:
        target = session.query(User).filter_by(id=target_id).first()
        assert target.super_admin is False
    finally:
        session.close()


def test_super_admin_cannot_change_own_privileges(client, super_admin_headers):
    super_username = _super_username()
    created_id = _create_user(
        SessionLocal(), super_username, super_admin=True
    )
    token = client.post(
        "/api/auth/token",
        data={"username": super_username, "password": "password123"},
    )
    own_headers = {"Authorization": f"Bearer {token.json()['access_token']}"}

    response = client.post(
        f"/api/admin/users/{created_id}/super-admin",
        json={"super_admin": False},
        headers=own_headers,
    )
    assert response.status_code == 403
    assert "own privileges" in response.json()["detail"]["message"].lower()


def test_super_admin_cannot_deactivate_self(client, super_admin_headers):
    super_username = _super_username()
    created_id = _create_user(
        SessionLocal(), super_username, super_admin=True
    )
    token = client.post(
        "/api/auth/token",
        data={"username": super_username, "password": "password123"},
    )
    own_headers = {"Authorization": f"Bearer {token.json()['access_token']}"}

    response = client.post(
        f"/api/admin/users/{created_id}/deactivate", headers=own_headers
    )
    assert response.status_code == 403


def test_user_delete_requires_confirmation(client, super_admin_headers):
    username = _plain_username()
    target_id = _create_user(SessionLocal(), username)

    response = client.delete(
        f"/api/admin/users/{target_id}", headers=super_admin_headers
    )
    assert response.status_code == 400
    assert "confirmation" in response.json()["detail"]["message"].lower()

    deleted = client.delete(
        f"/api/admin/users/{target_id}?confirm=true",
        headers=super_admin_headers,
    )
    assert deleted.status_code == 200, deleted.text

    session = SessionLocal()
    try:
        assert session.query(User).filter_by(id=target_id).first() is None
    finally:
        session.close()


# ==========================================================
# "Last active super-admin" invariant (service level)
# ==========================================================

def test_last_active_super_admin_cannot_be_demoted(client, super_admin_headers, monkeypatch):
    """Once only one active super-admin remains, demotion is blocked."""
    session = SessionLocal()
    try:
        actor_id = _create_user(session, _super_username(), super_admin=True)
        victim_id = _create_user(session, _plain_username(), super_admin=True)

        service = AdminUserService(session)
        # Simulate the guard: only one active super-admin remains in the
        # system (the actor), so the victim may not be demoted.
        monkeypatch.setattr(
            service.user_repo,
            "count_active_super_admins",
            lambda: 1,
        )
        result = service.set_super_admin(actor_id, victim_id, False)
        assert result["success"] is False
        assert "super-admin" in result["message"].lower()

        result = service.delete_user(actor_id, victim_id, confirm=True)
        assert result["success"] is False
    finally:
        session.close()


def test_farmer_deactivate_and_restore(client, super_admin_headers):
    """Deactivating a farmer turns off the linked user account."""
    username = f"link2farmer{unique_mobile()}"
    session = SessionLocal()
    try:
        user_id = _create_user(session, username, role="farmer")
        from config.core.models.farmer import Farmer

        farmer = Farmer(
            user_id=user_id,
            name="Linked Farmer",
            mobile=unique_mobile(),
            village="Sitapur",
            district="Sitapur",
            state="Uttar Pradesh",
        )
        session.add(farmer)
        session.commit()
        farmer_id = farmer.farmer_id
    finally:
        session.close()

    deactivated = client.post(
        f"/api/admin/farmers/{farmer_id}/deactivate",
        headers=super_admin_headers,
    )
    assert deactivated.status_code == 200, deactivated.text

    token = client.post(
        "/api/auth/token", data={"username": username, "password": "password123"}
    )
    assert token.status_code == 401

    restored = client.post(
        f"/api/admin/farmers/{farmer_id}/restore",
        headers=super_admin_headers,
    )
    assert restored.status_code == 200, restored.text

    token = client.post(
        "/api/auth/token", data={"username": username, "password": "password123"}
    )
    assert token.status_code == 200