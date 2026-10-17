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
    assert snapshot['benchmark'] == {'case_count': 10, 'source_count': 14, 'expected_relationships': 39}
    assert [run['metrics']['tp'] for run in snapshot['runs']] == [37, 37, 39]
    download = client.get('/api/research-results/download')
    assert download.content == response.content
    assert 'attachment' in download.headers['content-disposition']
    assert client.get('/research-results').text == 'public shell'
    assert SESSION_COOKIE not in response.headers.get('set-cookie', '')
    assert client.post('/api/research-results', json={}).status_code == 405
