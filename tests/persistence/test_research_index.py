import shutil
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, delete, text

from private_client_graph.workbench.api import create_app
from private_client_graph.workbench.artifacts import artifact_digest
from private_client_graph.workbench.index import experiments, rebuild_index
from private_client_graph.workbench.restore import restore_archive


def test_migration_rebuild_restart_search_and_readonly_api(database, tmp_path, monkeypatch):
    root = tmp_path / 'artifacts'
    for name in ('issue-91-demonstration', 'issue-92-pilot'):
        restore_archive(Path('research/history') / f'{name}.zip', root / name)
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(root))
    engine = create_engine(database)
    before = artifact_digest(root)
    assert rebuild_index(engine, root) == 2
    client = TestClient(create_app())
    page = client.get('/api/research/v1/experiments').json()
    assert page['total'] == 2
    pilot = next(item for item in page['items'] if item['kind'] == 'task_b_pilot')
    endpoint = f"/api/research/v1/experiments/{pilot['id']}"
    detail = client.get(endpoint).json()
    assert detail['history']['freshness'] == 'current'
    assert len(detail['samples']) == 11
    assert client.get('/api/research/v1/experiments?q=ISSUE-92&limit=1').json()['total'] == 1
    assert client.get('/api/research/v1/experiments?kind=demonstration').json()['total'] == 1
    assert client.get('/api/research/v1/experiments?lifecycle=complete&offset=1&limit=1').json()['items'][0]['id'] != page['items'][0]['id']
    assert client.get('/api/research/v1/experiments?q=%25').json()['total'] == 0
    assert client.get('/api/research/v1/experiments?limit=101').status_code == 422
    assert client.get('/api/research/v1/experiments/missing').status_code == 404
    compared = client.get('/api/research/v1/comparison', params={'left': page['items'][0]['id'], 'right': page['items'][1]['id']}).json()
    assert compared['matched_inputs'] >= 6
    for action in ('execute', 'start', 'stop', 'authorize', 'plan', 'rebuild'):
        assert client.post(f'/api/research/v1/{action}').status_code in (404, 405)
    assert client.post(endpoint).status_code == 405
    assert client.get('/health').json()['read_only']
    assert client.get('/api/matters').status_code == 404
    assert client.get('/health', headers={'host': 'untrusted.example'}).status_code == 400
    assert rebuild_index(engine, root) == 2
    with engine.begin() as connection:
        connection.execute(delete(experiments))
    assert rebuild_index(engine, root) == 2
    restarted = TestClient(create_app()).get(endpoint).json()
    restarted['history'].pop('indexed_at')
    detail['history'].pop('indexed_at')
    assert restarted == detail
    assert artifact_digest(root) == before
    # Current reads must never silently serve stale Evidence.
    (root / 'issue-92-pilot' / 'unexpected.json').write_text('{}')
    stale = client.get(endpoint).json()
    assert stale['history']['freshness'] == 'changed'
    assert stale['samples'] == []
    assert client.get('/api/research/v1/comparison', params={'left': page['items'][0]['id'], 'right': page['items'][1]['id']}).status_code == 409
    rebuild_index(engine, root)
    assert client.get(endpoint).json()['history']['integrity'] == 'corrupt'
    shutil.rmtree(root / 'issue-92-pilot')
    rebuild_index(engine, root)
    assert client.get(endpoint).json()['history']['integrity'] == 'missing'
    engine.dispose()


def test_research_migration_downgrade_is_isolated(database):
    from alembic import command
    from alembic.config import Config
    engine = create_engine(database)
    config = Config('alembic.ini')
    command.downgrade(config, '0006')
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT to_regclass('research_experiments')")) is None
        assert connection.scalar(text("SELECT to_regclass('matters')")) is not None
    command.upgrade(config, 'head')
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT count(*) FROM research_experiments")) == 0
    engine.dispose()
