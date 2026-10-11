"""Disposable persistent-workspace projection; all inputs are artifact records."""
from pathlib import Path

from sqlalchemy import Column, MetaData, Table, Text, select, text
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine import Engine

from .workspace_contracts import WorkspaceDetail, WorkspaceHistory
from .workspaces import read_experiment

metadata = MetaData()
workspaces = Table('research_workspaces', metadata,
    Column('id', Text, primary_key=True), Column('name', Text, nullable=False),
    Column('detail', JSONB, nullable=False))


def rebuild_workspaces(engine: Engine, root: Path) -> int:
    details = [read_experiment(root, path.parent.name)
               for path in sorted((root / 'experiments').glob('*/workspace.json'))]
    with engine.begin() as connection:
        connection.execute(text('SELECT pg_advisory_xact_lock(1010002)'))
        connection.execute(workspaces.delete())
        for detail in details:
            connection.execute(insert(workspaces).values(id=detail.id, name=detail.name,
                                detail=detail.model_dump(mode='json')))
    return len(details)


def workspace_history(engine: Engine, root: Path) -> WorkspaceHistory:
    with engine.connect() as connection:
        identities = connection.scalars(select(workspaces.c.id).order_by(workspaces.c.id)).all()
    # Artifact verification also detects deletion or corruption since projection rebuild.
    return WorkspaceHistory(items=[read_experiment(root, identity) for identity in identities])
