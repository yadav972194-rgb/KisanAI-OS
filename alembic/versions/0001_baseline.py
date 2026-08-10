"""baseline schema

Revision ID: 0001
Revises:
Create Date: 2026-08-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def _table_exists(name):
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def upgrade() -> None:
    """Baseline: create the current application schema if missing.

    On an existing database these tables already exist, so this
    migration only creates them for a fresh setup.
    """

    if not _table_exists("farmers"):
        op.create_table(
            "farmers",
            sa.Column("farmer_id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.Text(), nullable=False),
            sa.Column("mobile", sa.Text()),
            sa.Column("village", sa.Text()),
            sa.Column("district", sa.Text()),
            sa.Column("state", sa.Text()),
            sa.Column("created_at", sa.Text()),
        )

    if not _table_exists("crops"):
        op.create_table(
            "crops",
            sa.Column("crop_id", sa.Integer(), primary_key=True),
            sa.Column("crop_name", sa.Text()),
            sa.Column("season", sa.Text()),
            sa.Column("duration_days", sa.Integer()),
            sa.Column("water_requirement", sa.Text()),
            sa.Column("created_at", sa.Text()),
        )

    if not _table_exists("soils"):
        op.create_table(
            "soils",
            sa.Column("soil_id", sa.Integer(), primary_key=True),
            sa.Column("soil_type", sa.Text()),
            sa.Column("ph", sa.Float()),
            sa.Column("moisture", sa.Float()),
            sa.Column("nitrogen", sa.Integer()),
            sa.Column("phosphorus", sa.Integer()),
            sa.Column("potassium", sa.Integer()),
            sa.Column("created_at", sa.Text()),
        )

    if not _table_exists("weather"):
        op.create_table(
            "weather",
            sa.Column("location", sa.Text(), primary_key=True),
            sa.Column("temperature", sa.Float()),
            sa.Column("humidity", sa.Integer()),
            sa.Column("condition", sa.Text()),
            sa.Column("wind_speed", sa.Float()),
            sa.Column("updated_at", sa.Text()),
        )

    if not _table_exists("diseases"):
        op.create_table(
            "diseases",
            sa.Column("disease_id", sa.Integer(), primary_key=True),
            sa.Column("crop_name", sa.Text(), nullable=False),
            sa.Column("disease_name", sa.Text(), nullable=False),
            sa.Column("symptoms", sa.Text()),
            sa.Column("solution", sa.Text()),
            sa.Column("severity", sa.Text()),
            sa.Column("created_at", sa.Text()),
        )


def downgrade() -> None:
    """Baseline downgrade drops the application tables."""
    op.drop_table("diseases")
    op.drop_table("weather")
    op.drop_table("soils")
    op.drop_table("crops")
    op.drop_table("farmers")
