"""admin control & farmer support module

Add ``users.super_admin`` (additive admin escalation flag) and the
append-only admin tables backing the Admin Control & Farmer Support
module: ``feedback`` (farmer problems/feedback lifecycle), ``contact_records``
(outbound admin contacts), ``notifications`` (admin AI-report/alert records)
and ``admin_audit_log`` (immutable audit trail of admin mutations).

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-10
"""

from alembic import op
import sqlalchemy as sa


revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. users: additive super-admin escalation flag (defaults to false).
    with op.batch_alter_table("users", schema=None) as batch:
        batch.add_column(
            sa.Column(
                "super_admin",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )

    # 2. feedback: farmer problems / feedback lifecycle.
    op.create_table(
        "feedback",
        sa.Column("feedback_id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("farmer_id", sa.Integer(), nullable=True),
        sa.Column("subject", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("priority", sa.String(length=10), nullable=False, server_default="medium"),
        sa.Column("created_at", sa.String(length=19), nullable=True),
        sa.Column("updated_at", sa.String(length=19), nullable=True),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.farmer_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_feedback_farmer_id", "feedback", ["farmer_id"])
    op.create_index("ix_feedback_user_id", "feedback", ["user_id"])

    # 3. contact_records: outbound admin contacts (phone/email).
    op.create_table(
        "contact_records",
        sa.Column("contact_id", sa.Integer(), primary_key=True),
        sa.Column("farmer_id", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(length=10), nullable=False),
        sa.Column("reason", sa.String(length=150), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=19), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.farmer_id"], ondelete="CASCADE"),
    )
    op.create_index("ix_contact_records_farmer_id", "contact_records", ["farmer_id"])

    # 4. notifications: admin AI-report / alert / notice records.
    op.create_table(
        "notifications",
        sa.Column("notification_id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("farmer_id", sa.Integer(), nullable=True),
        sa.Column("category", sa.String(length=30), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="new"),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(length=19), nullable=True),
        sa.Column("delivered_at", sa.String(length=19), nullable=True),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.farmer_id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_farmer_id", "notifications", ["farmer_id"])

    # 5. admin_audit_log: append-only audit trail (no UPDATE/DELETE in app).
    op.create_table(
        "admin_audit_log",
        sa.Column("audit_id", sa.Integer(), primary_key=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=True),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=19), nullable=True),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_admin_audit_log_actor_user_id", "admin_audit_log", ["actor_user_id"])


def downgrade() -> None:
    op.drop_index("ix_admin_audit_log_actor_user_id", table_name="admin_audit_log")
    op.drop_table("admin_audit_log")
    op.drop_index("ix_notifications_farmer_id", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_index("ix_contact_records_farmer_id", table_name="contact_records")
    op.drop_table("contact_records")
    op.drop_index("ix_feedback_user_id", table_name="feedback")
    op.drop_index("ix_feedback_farmer_id", table_name="feedback")
    op.drop_table("feedback")

    with op.batch_alter_table("users", schema=None) as batch:
        batch.drop_column("super_admin")