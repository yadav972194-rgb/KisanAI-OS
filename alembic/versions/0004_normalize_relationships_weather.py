"""normalize farmer-crop and disease-crop relationships, weather snapshot

Add crops.farmer_id foreign key (farmer -> crop, 1:N), deduplicate the
weather table to one row per location with a unique constraint, and
backfill/normalize the diseases.crop_id / crop_name linkage.

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. crops: farmer relationship (1:N farmer -> crop).
    with op.batch_alter_table("crops", schema=None) as batch:
        batch.add_column(sa.Column("farmer_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_crops_farmer_id",
            "farmers",
            ["farmer_id"],
            ["farmer_id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_crops_farmer_id", "crops", ["farmer_id"])

    # 2. weather: keep the latest snapshot per location only, then lock
    #    it with a unique constraint so history stops growing.
    op.execute(
        "DELETE FROM weather "
        "WHERE weather_id NOT IN ("
        "  SELECT MAX(weather_id) FROM weather GROUP BY location"
        ")"
    )
    with op.batch_alter_table("weather", schema=None) as batch:
        batch.create_unique_constraint(
            "uq_weather_location", ["location"]
        )

    # 3. diseases: link rows whose crop_name matches an existing crop,
    #    then sync crop_name from the linked crop so the denormalized
    #    column cannot drift.
    op.execute(
        "UPDATE diseases "
        "SET crop_id = ("
        "  SELECT c.crop_id FROM crops c WHERE c.crop_name = diseases.crop_name"
        ") "
        "WHERE crop_id IS NULL "
        "AND EXISTS ("
        "  SELECT 1 FROM crops c WHERE c.crop_name = diseases.crop_name"
        ")"
    )
    op.execute(
        "UPDATE diseases "
        "SET crop_name = ("
        "  SELECT c.crop_name FROM crops c WHERE c.crop_id = diseases.crop_id"
        ") "
        "WHERE crop_id IS NOT NULL"
    )


def downgrade() -> None:
    with op.batch_alter_table("weather", schema=None) as batch:
        batch.drop_constraint("uq_weather_location", type_="unique")

    op.drop_index("ix_crops_farmer_id", table_name="crops")
    with op.batch_alter_table("crops", schema=None) as batch:
        batch.drop_constraint("fk_crops_farmer_id", type_="foreignkey")
        batch.drop_column("farmer_id")
