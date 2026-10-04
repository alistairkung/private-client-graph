"""Persist global fixed-window showcase provider attempts.

Revision ID: 0002
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "showcase_live_quota",
        sa.Column("window_seconds", sa.Integer(), primary_key=True),
        sa.Column("bucket_start", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("attempts", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("window_seconds > 0", name="showcase_quota_positive_window"),
        sa.CheckConstraint("attempts > 0", name="showcase_quota_positive_attempts"),
    )


def downgrade() -> None:
    op.drop_table("showcase_live_quota")
