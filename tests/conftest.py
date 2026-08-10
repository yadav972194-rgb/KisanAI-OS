"""
KisanAI OS - Phase 5.1 test suite.

Tests run against an isolated temporary SQLite database so the real
development database (including the production admin account) is never
touched, reset or wiped.
"""

import os
import random
import tempfile

TEST_DB_PATH = os.path.join(tempfile.gettempdir(), "kisanai_phase51_test.db")

os.environ["DATABASE_URL"] = "sqlite:///" + TEST_DB_PATH.replace("\\", "/")
os.environ["SECRET_KEY"] = "kisanai-phase57-test-secret-key-32chars-min"

for suffix in ("", "-wal", "-shm"):
    path = TEST_DB_PATH + suffix
    if os.path.exists(path):
        os.remove(path)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from config.core.api.main import app  # noqa: E402


def _migrate_test_db():
    """Build the test schema with the real alembic migrations (0001-0004)
    so the test database matches the production schema exactly."""
    from alembic import command
    from alembic.config import Config

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cfg = Config(os.path.join(project_root, "alembic.ini"))
    command.upgrade(cfg, "head")


def _uniq():
    return random.randint(100000, 999999)


def unique_mobile():
    return f"9{random.randint(100000000, 999999999)}"


def farmer_payload(**overrides):
    payload = {
        "name": "Ravi Kumar",
        "mobile": unique_mobile(),
        "village": "Sitapur",
        "district": "Sitapur",
        "state": "Uttar Pradesh",
    }
    payload.update(overrides)
    return payload


@pytest.fixture(scope="session")
def client():
    _migrate_test_db()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def admin_headers(client):
    token = _register_and_login(client, "admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def user_headers(client):
    token = _register_and_login(client, "farmer")
    return {"Authorization": f"Bearer {token}"}


def _register_and_login(client, role):
    uniq = _uniq()
    username = f"{role}{uniq}"

    if role == "admin":
        # Admin accounts are created the way production creates them
        # (direct bootstrap), never via the public register endpoint,
        # which intentionally rejects self-assigned admin roles.
        from config.core.api.auth import hash_password
        from config.core.database import SessionLocal
        from config.core.models.user import User

        session = SessionLocal()
        try:
            user = User(
                username=username,
                hashed_password=hash_password("password123"),
                full_name="Test Admin",
                role="admin",
                is_active=True,
            )
            session.add(user)
            session.commit()
        finally:
            session.close()
    else:
        register = client.post(
            "/api/auth/register",
            json={
                "username": username,
                "password": "password123",
                "full_name": "Test User",
                "role": role,
            },
        )
        assert register.status_code == 200, register.text

    login = client.post(
        "/api/auth/token",
        data={"username": username, "password": "password123"},
    )
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def create_farmer(client, headers, **overrides):
    """Create a farmer via the API and return (response, payload)."""
    payload = farmer_payload(**overrides)
    response = client.post("/api/farmers", json=payload, headers=headers)
    return response, payload
