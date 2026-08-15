"""add my-farm support: farmer-user link, farm size, per-farm crop names

Add farmers.user_id (one farm per authenticated user) and farmers.farm_size,
then relax the global crop-name uniqueness to (farmer_id, crop_name) so a
farmer can add the same crop as another farmer.

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-11
"""

from alembic import op
import sqlalchemy as sa


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. farmers: link an optional user account (one farm per user) and
    #    record the farm size in the same unit the mobile app uses (acres).
    with op.batch_alter_table("farmers", schema=None) as batch:
        batch.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("farm_size", sa.Float(), nullable=True))
        batch.create_unique_constraint("uq_farmers_user_id", ["user_id"])
        batch.create_foreign_key(
            "fk_farmers_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )

    # 2. crops: uniqueness is now per farm so farmers can grow the same
    #    crop names independently, while catalog rows (farmer_id NULL) stay
    #    globally unique. A plain (farmer_id, crop_name) composite unique
    #    would treat SQLite NULLs as distinct, so a COALESCE expression
    #    index is used instead (NULL -> 0; no farm has id 0).
    with op.batch_alter_table("crops", schema=None) as batch:
        batch.drop_constraint("uq_crops_crop_name", type_="unique")
    op.execute(
        "CREATE UNIQUE INDEX uq_crops_farmer_crop_name "
        "ON crops (COALESCE(farmer_id, 0), crop_name)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX uq_crops_farmer_crop_name")
    with op.batch_alter_table("crops", schema=None) as batch:
        batch.create_unique_constraint("uq_crops_crop_name", ["crop_name"])

    with op.batch_alter_table("farmers", schema=None) as batch:
        batch.drop_constraint("fk_farmers_user_id", type_="foreignkey")
        batch.drop_constraint("uq_farmers_user_id", type_="unique")
        batch.drop_column("farm_size")
        batch.drop_column("user_id")
