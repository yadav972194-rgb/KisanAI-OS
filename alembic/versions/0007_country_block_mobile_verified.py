"""country + block/tehsil location fields and mobile verification flag

Phase 6 / V3: farmers gain ``country`` (default India) and ``block``
(block/tehsil) columns so the location hierarchy
Country -> State -> District -> Block/Tehsil -> Village can be stored;
``users`` gains ``mobile_verified`` so OTP-verified mobiles are tracked.

Purely additive: no existing rows or columns are altered. The country
column is backfilled to 'India' because every legacy farmer record was
created through the Indian-market app.

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. farmers: location hierarchy additions.
    with op.batch_alter_table("farmers", schema=None) as batch:
        batch.add_column(
            sa.Column("country", sa.String(length=100), nullable=True)
        )
        batch.add_column(
            sa.Column("block", sa.String(length=100), nullable=True)
        )
    # Backfill: every existing farmer record is in India.
    op.execute("UPDATE farmers SET country = 'India' WHERE country IS NULL")

    # 2. users: OTP-verified mobile flag (defaults false for legacy rows).
    with op.batch_alter_table("users", schema=None) as batch:
        batch.add_column(
            sa.Column(
                "mobile_verified",
                sa.Boolean(),
                nullable=False,
                server_default="0",
            )
        )

    # 3. Useful lookup index for location-aware weather/advisory queries.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_farmers_state_district "
        "ON farmers (state, district)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_farmers_state_district")
    with op.batch_alter_table("users", schema=None) as batch:
        batch.drop_column("mobile_verified")
    with op.batch_alter_table("farmers", schema=None) as batch:
        batch.drop_column("block")
        batch.drop_column("country")
