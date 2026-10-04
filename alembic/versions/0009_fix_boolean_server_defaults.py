"""fix PostgreSQL-incompatible Boolean server defaults

Corrective migration: four ``Boolean`` columns were created by revisions
0006/0007/0008 with ``server_default="0"``. SQLAlchemy renders that string
default verbatim, so the emitted DDL is ``DEFAULT '0'``. SQLite tolerates
it (dynamically typed storage), but PostgreSQL rejects it when the column
is created, because ``'0'`` is not a valid ``boolean`` input and there is
no implicit text-to-boolean cast for a column default.

This revision re-declares those defaults as ``DEFAULT false`` via
``sa.text("false")``, which is valid on both SQLite and PostgreSQL and
preserves the original semantics exactly (an unset flag means false).

Affected columns (4):
  * ``otp_codes.verified``        - created in 0006
  * ``user_sessions.revoked``     - created in 0006
  * ``users.mobile_verified``     - added in 0007
  * ``users.super_admin``         - added in 0008

Scope: column defaults only. No tables, columns, indexes, constraints or
rows are added, dropped or rewritten. No data is backfilled.

Note: ``otp_codes.attempts`` also uses ``server_default="0"`` in 0006 but
is an ``Integer`` column, not a ``Boolean``, so it is already valid
PostgreSQL DDL and is intentionally left untouched.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-30
"""

from alembic import op
import sqlalchemy as sa


revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


# (table, column) pairs whose Boolean server default must be false.
_BOOLEAN_FALSE_DEFAULTS = (
    ("otp_codes", "verified"),
    ("user_sessions", "revoked"),
    ("users", "mobile_verified"),
    ("users", "super_admin"),
)


def upgrade() -> None:
    for table_name, column_name in _BOOLEAN_FALSE_DEFAULTS:
        # batch_alter_table emits a plain ALTER TABLE ... SET DEFAULT on
        # PostgreSQL and transparently recreates the table on SQLite, so
        # the same statement is valid on both dialects.
        with op.batch_alter_table(table_name, schema=None) as batch:
            batch.alter_column(
                column_name,
                existing_type=sa.Boolean(),
                existing_nullable=False,
                server_default=sa.text("false"),
            )


def downgrade() -> None:
    # Intentionally not reversible.
    #
    # The pre-0009 default was the literal '0', which is invalid
    # PostgreSQL DDL, so there is no dialect-safe prior state to restore.
    # Reinstating it would re-introduce the exact defect this revision
    # corrects. The columns keep a Boolean-false default, which is the
    # original intent of the '0' default.
    pass
