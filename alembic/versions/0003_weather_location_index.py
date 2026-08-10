"""weather location + updated_at index

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def _index_exists(name):
    bind = op.get_bind()
    return name in [
        row[0] for row in bind.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='index'"
        ).fetchall()
    ]


def upgrade() -> None:
    """Add an index on weather(location, updated_at) for time-series queries.

    Backs future weather history lookups. Data preserving: only adds an
    index, no rows or columns are touched.
    """
    if not _index_exists("ix_weather_location_updated"):
        op.create_index(
            "ix_weather_location_updated",
            "weather",
            ["location", "updated_at"],
        )


def downgrade() -> None:
    """Drop the weather lookup index."""
    if _index_exists("ix_weather_location_updated"):
        op.drop_index(
            "ix_weather_location_updated",
            table_name="weather",
        )
