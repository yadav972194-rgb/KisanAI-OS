"""
KisanAI OS - SQLite Database Integration (Advanced) tests.

Direct verification of the SQLite integration layer: engine/session
lifecycle, commit/rollback, foreign-key enforcement, unique constraint
handling, invalid-transaction atomicity, repository error recovery,
SQLite connection pragmas (WAL / FK / busy_timeout), and Alembic state.

All tests run against the isolated test database created by conftest;
the real kisanai.db is never touched.
"""

import sqlite3

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from config.core.database import SessionLocal, engine, get_db
from config.core.models.crop import Crop
from config.core.models.soil import Soil
from config.core.repositories.crop_repository import CropRepository
from tests.conftest import TEST_DB_PATH


def _raw_connection():
    conn = sqlite3.connect(TEST_DB_PATH)
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _unique_crop_name():
    import uuid
    return f"DbCrop{uuid.uuid4().hex[:12]}"


@pytest.fixture(autouse=True)
def _db_ready(client):
    """Ensure the isolated test DB is migrated before any DB test runs
    (the session-scoped client fixture builds the schema via alembic)."""
    yield


# ==========================================================
# Engine / session
# ==========================================================

def test_engine_connects_to_test_database():
    with engine.connect() as conn:
        assert conn.execute(select(1)).scalar() == 1


def test_session_creation_and_cleanup():
    session = SessionLocal()
    try:
        assert session.execute(select(1)).scalar() == 1
    finally:
        session.close()


def test_get_db_rolls_back_and_closes_yielded_session():
    """Pending (uncommitted) work on a yielded session must be rolled back
    when the dependency generator is closed."""
    name = _unique_crop_name()

    gen = get_db()
    db = next(gen)
    try:
        db.add(Crop(crop_name=name, season="Kharif",
                    duration_days=100, water_requirement="Low"))
    finally:
        gen.close()

    conn = _raw_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM crops WHERE crop_name = ?", (name,)
        ).fetchone()[0]
    finally:
        conn.close()

    assert count == 0


# ==========================================================
# SQLite connection settings (applied by engine event listener)
# ==========================================================

def test_wal_mode_enabled():
    with engine.connect() as conn:
        journal = conn.exec_driver_sql("PRAGMA journal_mode").scalar()
    assert journal == "wal"


def test_foreign_keys_enabled_on_engine_connections():
    with engine.connect() as conn:
        enabled = conn.exec_driver_sql("PRAGMA foreign_keys").scalar()
    assert enabled == 1


def test_busy_timeout_set_on_engine_connections():
    with engine.connect() as conn:
        timeout_ms = conn.exec_driver_sql("PRAGMA busy_timeout").scalar()
    assert timeout_ms >= 1000


# ==========================================================
# Commit / rollback / invalid transactions
# ==========================================================

def test_commit_persists_and_rollback_discards():
    name = _unique_crop_name()

    session = SessionLocal()
    try:
        session.add(Crop(crop_name=name, season="Kharif",
                         duration_days=100, water_requirement="Low"))
        session.commit()
    finally:
        session.close()

    session = SessionLocal()
    try:
        session.add(Crop(crop_name=name + "-rb", season="Kharif",
                         duration_days=100, water_requirement="Low"))
        session.rollback()
    finally:
        session.close()

    conn = _raw_connection()
    try:
        committed = conn.execute(
            "SELECT COUNT(*) FROM crops WHERE crop_name = ?", (name,)
        ).fetchone()[0]
        rolled_back = conn.execute(
            "SELECT COUNT(*) FROM crops WHERE crop_name = ?", (name + "-rb",)
        ).fetchone()[0]
    finally:
        conn.close()

    assert committed == 1
    assert rolled_back == 0

    _cleanup_crops([name, name + "-rb"])


def test_invalid_transaction_atomicity_no_partial_write():
    """A failing commit must leave zero rows behind (no partial insert)."""
    name = _unique_crop_name()

    session = SessionLocal()
    try:
        session.add(Crop(crop_name=name, season="Kharif",
                         duration_days=100, water_requirement="Low"))
        session.add(Crop(crop_name=name, season="Rabi",
                         duration_days=90, water_requirement="High"))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()

    conn = _raw_connection()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM crops WHERE crop_name = ?", (name,)
        ).fetchone()[0]
    finally:
        conn.close()

    assert count == 0


def test_unique_constraint_duplicate_409_style_integrity():
    name = _unique_crop_name()

    repo = CropRepository()
    try:
        repo.add_crop(Crop(crop_name=name, season="Kharif",
                           duration_days=100, water_requirement="Low"))
        with pytest.raises(IntegrityError):
            repo.add_crop(Crop(crop_name=name, season="Rabi",
                               duration_days=90, water_requirement="High"))
    finally:
        repo.close()

    _cleanup_crops([name])


def test_repository_recovers_after_failed_commit():
    """After a failed commit (rolled back) the repository must still work."""
    name = _unique_crop_name()

    repo = CropRepository()
    try:
        repo.add_crop(Crop(crop_name=name, season="Kharif",
                           duration_days=100, water_requirement="Low"))
        with pytest.raises(IntegrityError):
            repo.add_crop(Crop(crop_name=name, season="Rabi",
                               duration_days=90, water_requirement="High"))

        second = name + "-2"
        repo.add_crop(Crop(crop_name=second, season="Rabi",
                           duration_days=90, water_requirement="High"))
        found = repo.get_crop_by_name(second)
        assert found is not None
        assert found.crop_name == second
    finally:
        repo.close()

    _cleanup_crops([name, second])


# ==========================================================
# Foreign-key enforcement (ON DELETE SET NULL)
# ==========================================================

def test_foreign_key_violation_rejected():
    """Inserting a soil with a non-existent farmer must raise IntegrityError
    because PRAGMA foreign_keys=ON is active on engine connections."""
    session = SessionLocal()
    try:
        session.add(Soil(farmer_id=99999999, soil_type="Loamy", ph=6.5,
                         moisture=40.0, nitrogen=50, phosphorus=25,
                         potassium=30))
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
    finally:
        session.close()


def test_farmer_delete_sets_crop_farmer_null():
    """Locked policy: deleting a farmer keeps its crops but nulls farmer_id."""
    import random

    from config.core.models.farmer import Farmer
    from config.core.repositories.farmer_repository import FarmerRepository

    mobile = "9" + str(random.randint(100000000, 999999999))

    farmer_repo = FarmerRepository()
    crop_repo = CropRepository()
    try:
        farmer = Farmer(name="FK Farmer", mobile=mobile, village="Sitapur",
                        district="Sitapur", state="Uttar Pradesh")
        farmer_repo.insert_farmer(farmer)
        farmer = farmer_repo.get_farmer_by_mobile(mobile)

        crop_repo.add_crop(Crop(farmer_id=farmer.farmer_id,
                                crop_name=_unique_crop_name(), season="Kharif",
                                duration_days=100, water_requirement="Low"))

        crop = crop_repo.get_crops_by_farmer(farmer.farmer_id)[0]

        farmer_repo.delete_farmer(farmer.farmer_id)

        crop_repo.session.expire_all()
        reloaded = crop_repo.get_crop_by_id(crop.crop_id)
        assert reloaded.farmer_id is None
    finally:
        farmer_repo.close()
        crop_repo.close()


# ==========================================================
# Alembic + integrity on the test database
# ==========================================================

def test_test_database_alembic_head_is_0004():
    conn = _raw_connection()
    try:
        version = conn.execute(
            "SELECT version_num FROM alembic_version"
        ).fetchone()[0]
    finally:
        conn.close()
    assert version == "0004"


def test_test_database_integrity_check_ok():
    conn = _raw_connection()
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        conn.close()
    assert result == "ok"


def test_test_database_has_expected_tables():
    conn = _raw_connection()
    try:
        tables = {
            row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
    finally:
        conn.close()

    for expected in ("farmers", "crops", "soils", "diseases",
                     "weather", "users", "alembic_version"):
        assert expected in tables


# ==========================================================
# Application import
# ==========================================================

def test_application_imports():
    import importlib
    module = importlib.import_module("config.core.api.main")
    assert module.app is not None


def _cleanup_crops(names):
    conn = _raw_connection()
    try:
        for name in names:
            conn.execute("DELETE FROM crops WHERE crop_name = ?", (name,))
        conn.commit()
    finally:
        conn.close()
