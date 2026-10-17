"""The public publication is one immutable artifact, without research authority."""
import json

from fastapi.testclient import TestClient

from private_client_graph.api.app import create_app
from private_client_graph.api.auth import SESSION_COOKIE


def test_public_research_serves_the_same_artifact_for_inspection_and_download(tmp_path):
    (tmp_path / 'index.html').write_text('public shell')
    client = TestClient(create_app(tmp_path))
    response = client.get('/api/research-results')
    assert response.status_code == 200
    snapshot = response.json()
    assert snapshot['experiment_id'] == '83b5778e74ba5e6e882d334fd4f87f09'
    assert snapshot['benchmark']['case_count'] == 10
    assert snapshot['benchmark']['source_count'] == 14
    assert snapshot['benchmark']['expected_relationships'] == 39
    assert snapshot['benchmark']['evaluator_version'] == 'semantic_edges_v1'
    assert [run['metrics']['tp'] for run in snapshot['runs']] == [37, 37, 39]
    download = client.get('/api/research-results/download')
    assert download.content == response.content
    assert 'attachment' in download.headers['content-disposition']
    assert client.get('/research-results').text == 'public shell'
    assert SESSION_COOKIE not in response.headers.get('set-cookie', '')
    assert client.post('/api/research-results', json={}).status_code == 405


def test_missing_or_corrupted_publication_is_unavailable_without_fallback(tmp_path, monkeypatch):
    from private_client_graph.application import public_research

    missing = tmp_path / 'missing.json'
    monkeypatch.setattr(public_research, 'PUBLISHED_SNAPSHOT', missing)
    client = TestClient(create_app(tmp_path))
    assert client.get('/api/research-results').status_code == 503
    assert client.get('/api/research-results/download').status_code == 503
    missing.write_text('{"schema_version":1,"integrity":{}}')
    response = client.get('/api/research-results')
    assert response.status_code == 503
    assert response.json() == {'error': {'message': 'Published research results are unavailable.'}}
    assert str(tmp_path) not in response.text


def test_publication_integrity_covers_original_sources_and_download(tmp_path, monkeypatch):
    from private_client_graph.application import public_research

    snapshot = json.loads(public_research.PUBLISHED_SNAPSHOT.read_bytes())
    snapshot['cases'][0]['sources'][0]['text'] += ' changed'
    modified = tmp_path / 'corrupt.json'
    modified.write_text(json.dumps(snapshot))
    monkeypatch.setattr(public_research, 'PUBLISHED_SNAPSHOT', modified)
    client = TestClient(create_app(tmp_path))
    assert client.get('/api/research-results').status_code == 503
    assert client.get('/api/research-results/download').status_code == 503


def test_publication_runtime_does_not_import_private_research_or_execution():
    import subprocess
    import sys

    result = subprocess.run([sys.executable, '-c', '''
import sys
from private_client_graph.application.public_research import read_public_research
assert read_public_research()
for module in sys.modules:
    assert not module.startswith(('private_client_graph.research', 'private_client_graph.workbench',
        'private_client_graph.persistence', 'private_client_graph.pipeline',
        'private_client_graph.extraction', 'private_client_graph.evaluation',
        'langchain', 'sqlalchemy'))
'''], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
