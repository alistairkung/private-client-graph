"""Disposable persistent-workspace projection; all inputs are artifact records."""
from pathlib import Path

from sqlalchemy import Column, MetaData, Table, Text, select, text
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine import Engine

from .workspace_contracts import WorkspaceHistory, WorkspaceHistoryItem
from .workspaces import read_experiment

metadata = MetaData()
workspaces = Table('research_workspaces', metadata,
    Column('id', Text, primary_key=True), Column('name', Text, nullable=False),
    Column('detail', JSONB, nullable=False))


def rebuild_workspaces(engine: Engine, root: Path) -> int:
    identities = {path.parent.name for path in (root / 'experiments').glob('*/workspace.json')}
    with engine.begin() as connection:
        connection.execute(text('SELECT pg_advisory_xact_lock(1010002)'))
        identities.update(connection.scalars(select(workspaces.c.id)).all())
        for identity in sorted(identities):
            item = _history_item(root, identity)
            values = dict(id=item.id, name=item.name, detail=item.model_dump(mode='json'))
            statement = insert(workspaces).values(**values)
            connection.execute(statement.on_conflict_do_update(index_elements=[workspaces.c.id], set_=values))
    return len(identities)


def workspace_history(engine: Engine, root: Path) -> WorkspaceHistory:
    with engine.connect() as connection:
        identities: list[str] = list(connection.scalars(select(workspaces.c.id)).all())
    # Verify artifacts even when the index has not been rebuilt since deletion/corruption.
    items = [_history_item(root, identity) for identity in identities]
    return WorkspaceHistory(items=sorted(items, key=lambda item: (item.created_at or '', item.id)))


def _history_item(root: Path, identity: str) -> WorkspaceHistoryItem:
    try:
        workspace = read_experiment(root, identity)
        return WorkspaceHistoryItem.model_validate(workspace.model_dump())
    except (OSError, ValueError, KeyError, TypeError) as error:
        return WorkspaceHistoryItem(id=identity, name=f'Experiment {identity} (metadata unavailable)',
            metadata_available=False, integrity='missing' if isinstance(error, FileNotFoundError) else 'corrupt',
            reason='Authoritative workspace artifacts are missing or invalid; restore retained records.')
