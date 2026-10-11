"""Persistent Experiment projections, rebuildable from workspace artifacts."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0008'
down_revision = '0007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('research_workspaces',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False),
        sa.Column('detail', JSONB(), nullable=False))


def downgrade() -> None:
    op.drop_table('research_workspaces')
