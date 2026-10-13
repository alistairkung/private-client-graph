"""Disposable research projections; artifacts remain authoritative."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'research_experiments',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('artifact_path', sa.Text(), nullable=False, unique=True),
        sa.Column('search_text', sa.Text(), nullable=False),
        sa.Column('lifecycle', sa.Text(), nullable=False),
        sa.Column('kind', sa.Text()),
        sa.Column('integrity', sa.Text(), nullable=False),
        sa.Column('detail', JSONB(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('research_experiments')
