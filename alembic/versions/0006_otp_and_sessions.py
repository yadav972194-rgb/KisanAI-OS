"""otp codes and user sessions for phase 3 authentication

Add ``otp_codes`` (hashed one-time passwords for registration / forgot
username / forgot password) and ``user_sessions`` (server-side session
ledger for JWT revocation and logout).

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-12
"""

from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "otp_codes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mobile", sa.String(length=15), nullable=False),
        sa.Column("purpose", sa.String(length=30), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.String(length=19), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.String(length=19), nullable=True),
    )
    op.create_index("ix_otp_codes_mobile", "otp_codes", ["mobile"])

    op.create_table(
        "user_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=64), nullable=False, unique=True),
        sa.Column("created_at", sa.String(length=19), nullable=True),
        sa.Column("expires_at", sa.String(length=19), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("revoked_at", sa.String(length=19), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="CASCADE"
        ),
    )
    op.create_index(
        "ix_user_sessions_user_id", "user_sessions", ["user_id"]
    )


def downgrade() -> None:
    op.drop_table("user_sessions")
    op.drop_index("ix_otp_codes_mobile", table_name="otp_codes")
    op.drop_table("otp_codes")
