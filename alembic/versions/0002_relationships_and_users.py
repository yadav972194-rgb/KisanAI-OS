"""relationships and users

Add foreign keys (soils.farmer_id, diseases.crop_id), unique
constraints, weather_id primary key, users table, cleanup of the
leftover test table and invalid placeholder rows.

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-09
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _table_exists(name):
    bind = op.get_bind()
    return name in inspect(bind).get_table_names()


def upgrade() -> None:
    # 1. Drop leftover test table (verified empty) if present.
    if _table_exists("test"):
        op.drop_table("test")

    # 2. Clean invalid placeholder rows (verified: exactly one each,
    #    created by earlier API testing, no business data).
    op.execute(
        "DELETE FROM farmers "
        "WHERE farmer_id = 0 AND name = 'string' AND mobile = 'string'"
    )
    op.execute(
        "DELETE FROM crops "
        "WHERE crop_id = 0 AND crop_name = 'string'"
    )

    # 3. soils: farmer relationship (1:N farmer -> soil).
    with op.batch_alter_table("soils", schema=None) as batch:
        batch.add_column(sa.Column("farmer_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_soils_farmer_id",
            "farmers",
            ["farmer_id"],
            ["farmer_id"],
            ondelete="SET NULL",
        )

    # 4. diseases: crop relationship (1:N crop -> disease).
    with op.batch_alter_table("diseases", schema=None) as batch:
        batch.add_column(sa.Column("crop_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_diseases_crop_id",
            "crops",
            ["crop_id"],
            ["crop_id"],
            ondelete="SET NULL",
        )

    # 5. Unique constraints (data verified: no duplicates).
    with op.batch_alter_table("farmers", schema=None) as batch:
        batch.create_unique_constraint(
            "uq_farmers_mobile", ["mobile"]
        )
    with op.batch_alter_table("crops", schema=None) as batch:
        batch.create_unique_constraint(
            "uq_crops_crop_name", ["crop_name"]
        )
    with op.batch_alter_table("diseases", schema=None) as batch:
        batch.create_unique_constraint(
            "uq_diseases_crop_disease", ["crop_id", "disease_name"]
        )

    # 6. weather: replace location primary key with weather_id.
    op.create_table(
        "weather_new",
        sa.Column("weather_id", sa.Integer(), primary_key=True),
        sa.Column("location", sa.Text()),
        sa.Column("temperature", sa.Float()),
        sa.Column("humidity", sa.Integer()),
        sa.Column("condition", sa.Text()),
        sa.Column("wind_speed", sa.Float()),
        sa.Column("updated_at", sa.Text()),
    )
    op.execute(
        "INSERT INTO weather_new "
        "(location, temperature, humidity, condition, wind_speed, updated_at) "
        "SELECT location, temperature, humidity, condition, wind_speed, updated_at "
        "FROM weather"
    )
    op.drop_table("weather")
    op.rename_table("weather_new", "weather")

    # 7. users table (authentication, Phase 3).
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(50), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(100)),
        sa.Column("mobile", sa.String(15)),
        sa.Column("role", sa.String(20), default="farmer"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.String(19)),
    )

    # 8. Indexes on new foreign keys.
    op.create_index("ix_soils_farmer_id", "soils", ["farmer_id"])
    op.create_index("ix_diseases_crop_id", "diseases", ["crop_id"])


def downgrade() -> None:
    op.drop_index("ix_soils_farmer_id", table_name="soils")
    op.drop_index("ix_diseases_crop_id", table_name="diseases")
    op.drop_table("users")

    # weather revert: weather_id PK back to location PK.
    op.create_table(
        "weather_old",
        sa.Column("location", sa.Text(), primary_key=True),
        sa.Column("temperature", sa.Float()),
        sa.Column("humidity", sa.Integer()),
        sa.Column("condition", sa.Text()),
        sa.Column("wind_speed", sa.Float()),
        sa.Column("updated_at", sa.Text()),
    )
    op.execute(
        "INSERT INTO weather_old "
        "(location, temperature, humidity, condition, wind_speed, updated_at) "
        "SELECT location, temperature, humidity, condition, wind_speed, updated_at "
        "FROM weather"
    )
    op.drop_table("weather")
    op.rename_table("weather_old", "weather")

    with op.batch_alter_table("diseases", schema=None) as batch:
        batch.drop_constraint("uq_diseases_crop_disease", type_="unique")
    with op.batch_alter_table("crops", schema=None) as batch:
        batch.drop_constraint("uq_crops_crop_name", type_="unique")
    with op.batch_alter_table("farmers", schema=None) as batch:
        batch.drop_constraint("uq_farmers_mobile", type_="unique")

    with op.batch_alter_table("diseases", schema=None) as batch:
        batch.drop_constraint("fk_diseases_crop_id", type_="foreignkey")
        batch.drop_column("crop_id")
    with op.batch_alter_table("soils", schema=None) as batch:
        batch.drop_constraint("fk_soils_farmer_id", type_="foreignkey")
        batch.drop_column("farmer_id")
