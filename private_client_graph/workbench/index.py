"""Rebuildable PostgreSQL projections and artifact freshness checks."""
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from sqlalchemy import Column, MetaData, Table, Text, func, select, text
from sqlalchemy.dialects.postgresql import JSONB, insert
from sqlalchemy.engine import Engine

from .artifacts import artifact_digest, read_artifact
from .contracts import ExperimentDetail, HistoryItem, HistoryPage

metadata = MetaData()
experiments = Table(
    'research_experiments', metadata,
    Column('id', Text, primary_key=True),
    Column('artifact_path', Text, nullable=False, unique=True),
    Column('search_text', Text, nullable=False),
    Column('lifecycle', Text, nullable=False),
    Column('kind', Text),
    Column('integrity', Text, nullable=False),
    Column('detail', JSONB, nullable=False),
)


def rebuild_index(engine: Engine, root: Path) -> int:
    """Atomically reconcile retained bundles. Never touch artifacts or task ledgers."""
    if not root.is_dir():
        raise ValueError('Research artifact root does not exist')
    paths = sorted({path.parent for name in ('manifest.json', 'manifest-checksum.json')
                    for path in root.rglob(name)})
    projections = [read_artifact(path, path.relative_to(root).as_posix()) for path in paths
                   if not _workspace_run(path)]
    with engine.begin() as connection:
        connection.execute(text('SELECT pg_advisory_xact_lock(1010001)'))
        retained = {detail.history.id for detail in projections}
        for row in connection.execute(select(experiments)).mappings():
            if row['id'] not in retained:
                detail = ExperimentDetail.model_validate(row['detail'])
                detail.history.integrity = 'missing'
                detail.history.integrity_reason = 'Retained artifact directory or manifest is missing.'
                detail.history.freshness = 'missing'
                detail.samples = []
                projections.append(detail)
        for detail in projections:
            detail.history.indexed_at = datetime.now(timezone.utc).isoformat()
            history = detail.history
            searchable = ' '.join(filter(None, [history.artifact_path, history.experiment_id,
                history.model, history.kind, *history.cases, *history.cohorts,
                'noop generative_full_source', str(detail.configuration)]))
            values = dict(id=history.id, artifact_path=history.artifact_path,
                search_text=searchable, lifecycle=history.lifecycle, kind=history.kind,
                integrity=history.integrity, detail=detail.model_dump(mode='json'))
            statement = insert(experiments).values(**values)
            connection.execute(statement.on_conflict_do_update(
                index_elements=[experiments.c.id], set_=values))
    from .workspace_index import rebuild_workspaces
    rebuild_workspaces(engine, root)
    return len(projections)


def _freshness(history: HistoryItem, root: Path) -> HistoryItem:
    path = root / history.artifact_path
    if not path.is_dir():
        history.freshness = 'missing'
    else:
        try:
            if artifact_digest(path) != history.digest:
                history.freshness = 'changed'
        except (OSError, ValueError):
            history.freshness = 'changed'
    return history


def history_page(engine: Engine, root: Path, *, query: str = '', lifecycle: str | None = None,
                 kind: str | None = None, integrity: str | None = None,
                 offset: int = 0, limit: int = 25) -> HistoryPage:
    conditions = []
    if query:
        conditions.append(experiments.c.search_text.icontains(query, autoescape=True))
    for name, value in (('lifecycle', lifecycle), ('kind', kind), ('integrity', integrity)):
        if value:
            conditions.append(experiments.c[name] == value)
    statement = select(experiments.c.detail).where(*conditions)
    with engine.connect() as connection:
        total = connection.scalar(select(func.count()).select_from(experiments).where(*conditions))
        rows: Sequence[dict[str, Any]] = connection.scalars(statement.order_by(experiments.c.artifact_path)
                                  .offset(offset).limit(limit)).all()
    return HistoryPage(items=[_freshness(ExperimentDetail.model_validate(row).history, root)
                              for row in rows], total=total or 0, offset=offset, limit=limit)


def experiment_detail(engine: Engine, root: Path, identity: str) -> ExperimentDetail | None:
    with engine.connect() as connection:
        row = connection.scalar(select(experiments.c.detail).where(experiments.c.id == identity))
    if row is None:
        return None
    detail = ExperimentDetail.model_validate(row)
    _freshness(detail.history, root)
    if detail.history.freshness != 'current':
        detail.samples = []
        detail.history.integrity_reason = 'Artifacts changed or disappeared after indexing. Rebuild the index to inspect results.'
    return detail


def _workspace_run(path: Path) -> bool:
    try:
        return json.loads((path / 'manifest.json').read_text()).get('schema_version') == 4
    except (OSError, ValueError, AttributeError):
        return False
