"""
KisanAI OS Database Module
Version: 3.0.0

SQLAlchemy engine, session factory and declarative base.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


# Milliseconds SQLite will wait on a locked database before raising
# "database is locked" under concurrent writer contention (WAL still
# allows one writer; this avoids immediate failures in busy periods).
SQLITE_BUSY_TIMEOUT_MS = 5000


def _connect_args(database_url: str) -> dict:
    """Connection arguments that only apply to SQLite.

    ``check_same_thread`` is a sqlite3-only option; passing it to
    PostgreSQL (or any other SQLAlchemy dialect) would break startup.
    """
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args(settings.DATABASE_URL),
    future=True,
    # Verify a stale pooled connection is still alive before use. Harmless
    # for SQLite and important for PostgreSQL behind proxies/NAT.
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable safe SQLite connection settings.

    Applies only to SQLite backends; other databases (e.g. a future
    PostgreSQL deployment) are left untouched. The settings themselves
    are per-connection, so they must be set on every new connection.
    """
    if not dbapi_connection.__class__.__module__.startswith("sqlite3"):
        return

    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
    cursor.close()


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


def get_db():
    """FastAPI dependency that yields a database session.

    The session is rolled back (if a transaction is still open) and
    closed when the request finishes, so failed transactions cannot
    leak into the next request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
