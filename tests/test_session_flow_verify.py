"""
KisanAI OS - V3 session persistence verification.

Verifies the exact mobile-app journey end-to-end against the real backend:

    Registration -> logout -> login (same account) -> app restart
    -> session persistence

An "app restart" is simulated by using the persisted token against the
same API the mobile `restoreSession()` calls (GET /api/auth/me) and by
verifying the token keeps working across multiple requests.
"""

import random

from tests.conftest import unique_mobile

_uniq = lambda: random.randint(100000, 999999)  # noqa: E731


def _login(client, username, password="password123"):
    return client.post(
        "/api/auth/token",
        data={"username": username, "password": password},
    )


def test_full_session_flow_with_server_side_logout(client):
    """Registration -> server logout -> re-login -> restart persistence."""
    username = f"flow{_uniq()}"
    password = "password123"

    register = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": password,
            "full_name": "Flow User",
            "role": "farmer",
        },
    )
    assert register.status_code == 200, register.text
    assert register.json()["username"] == username

    login1 = _login(client, username, password)
    assert login1.status_code == 200, login1.text
    token1 = login1.json()["access_token"]

    headers1 = {"Authorization": f"Bearer {token1}"}
    assert client.get("/api/auth/me", headers=headers1).status_code == 200

    logout = client.post("/api/auth/logout", headers=headers1)
    assert logout.status_code == 200, logout.text

    revoked = client.get("/api/auth/me", headers=headers1)
    assert revoked.status_code == 401, revoked.text

    login2 = _login(client, username, password)
    assert login2.status_code == 200, login2.text
    token2 = login2.json()["access_token"]

    headers2 = {"Authorization": f"Bearer {token2}"}
    me = client.get("/api/auth/me", headers=headers2)
    assert me.status_code == 200, me.text
    assert me.json()["username"] == username

    me_again = client.get("/api/auth/me", headers=headers2)
    assert me_again.status_code == 200, me_again.text


def test_session_persists_across_restart_simulation(client):
    """A logged-in token keeps working across repeated /me calls (restart)."""
    username = f"restart{_uniq()}"
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "Restart User",
            "role": "farmer",
        },
    )

    login = _login(client, username)
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for _ in range(3):
        me = client.get("/api/auth/me", headers=headers)
        assert me.status_code == 200, me.text
        assert me.json()["username"] == username


def test_login_after_app_local_logout_works(client):
    """App logout clears only local storage; re-login must still work.

    This mirrors the mobile AuthController.logout() which clears the
    persisted token without calling the server-side /api/auth/logout.
    """
    username = f"applogout{_uniq()}"
    client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "App Logout User",
            "role": "farmer",
        },
    )

    first = _login(client, username)
    assert first.status_code == 200, first.text
    token1 = first.json()["access_token"]
    assert client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token1}"}
    ).status_code == 200

    second = _login(client, username)
    assert second.status_code == 200, second.text
    token2 = second.json()["access_token"]
    assert client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {token2}"}
    ).status_code == 200
    assert token2 != token1


def test_registration_then_login_with_unique_mobile(client):
    mobile = unique_mobile()
    username = f"mob{_uniq()}"
    register = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": "password123",
            "full_name": "Mobile User",
            "mobile": mobile,
            "role": "farmer",
        },
    )
    assert register.status_code == 200, register.text

    by_mobile = client.post(
        "/api/auth/token",
        data={"username": mobile, "password": "password123"},
    )
    assert by_mobile.status_code == 200, by_mobile.text