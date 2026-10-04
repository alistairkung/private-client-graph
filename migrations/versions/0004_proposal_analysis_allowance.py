"""Persist the independent authenticated proposal provider-attempt allowance.

Revision ID: 0004
Revises: 0003
"""

from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "proposal_analysis_allowance",
        sa.Column("window_seconds", sa.Integer(), primary_key=True),
        sa.Column("bucket_start", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("attempts", sa.BigInteger(), nullable=False),
        sa.CheckConstraint("window_seconds > 0", name="proposal_allowance_positive_window"),
        sa.CheckConstraint("attempts > 0", name="proposal_allowance_positive_attempts"),
    )


def downgrade() -> None:
    op.drop_table("proposal_analysis_allowance")
