"""Persist complete current Matters.

Revision ID: 0001
Revises: None
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "matters",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("external_reference", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_title", sa.Text(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("current_graph", postgresql.JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("matters")
