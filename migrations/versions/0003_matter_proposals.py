"""Persist complete Matter Proposals and cross-resource reference reservations.

Revision ID: 0003
Revises: 0002
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "matter_proposals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("external_reference", sa.Text(), nullable=False),
        sa.Column("matter_title", sa.Text(), nullable=False),
        sa.Column("source_title", sa.Text(), nullable=False),
        sa.Column("source_text", sa.Text(), nullable=False),
        sa.Column("proposed_graph", postgresql.JSONB(), nullable=False),
    )
    claims = op.create_table(
        "external_matter_reference_claims",
        sa.Column("canonical_reference", sa.Text(), primary_key=True),
        sa.Column("resource_kind", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Uuid(), nullable=False),
        sa.CheckConstraint("resource_kind IN ('matter_proposal', 'matter')", name="reference_claim_resource_kind"),
    )
    connection = op.get_bind()
    # Python case folding is authoritative; PostgreSQL lower() is not equivalent.
    for row in connection.execute(sa.text("SELECT id, external_reference FROM matters")).mappings():
        connection.execute(claims.insert().values(
            canonical_reference=row["external_reference"].strip().casefold(),
            resource_kind="matter", resource_id=row["id"],
        ))


def downgrade() -> None:
    op.drop_table("external_matter_reference_claims")
    op.drop_table("matter_proposals")
