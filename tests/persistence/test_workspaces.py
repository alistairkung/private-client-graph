"""Versioned API journey using real PostgreSQL, subprocess, pipeline and evaluator."""
import time

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from private_client_graph.workbench.api import create_app
from private_client_graph.workbench.execution_api import create_execution_app
from private_client_graph.workbench.index import rebuild_index

PREFIX = '/api/research/v2'
HEADERS = {'origin': 'http://testserver'}


def request(client, method, path, value):
    response = getattr(client, method)(PREFIX + path, json=value, headers=HEADERS)
    assert response.status_code == 200, response.text
    return response.json()


def wait_for_run(client, path):
    for _ in range(150):
        response = client.get(PREFIX + path)
        if response.status_code == 409:
            time.sleep(.05)
            continue
        assert response.status_code == 200, response.text
        detail = response.json()
        if detail['lifecycle'] in ('complete', 'stopped', 'failed'):
            return detail
        time.sleep(.1)
    raise AssertionError('Run did not finish')


def test_api_persistent_experiment_multiple_runs_evidence_and_rebuild(database, tmp_path, monkeypatch):
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(tmp_path))
    with TestClient(create_execution_app()) as client:
        workspace = request(client, 'post', '/experiments', {
            'request_id': 'create', 'name': 'Does alias resolution improve consistency?',
            'hypothesis': 'Resolution improves relationship recall'})
        experiment = '/experiments/' + workspace['id']
        assert len(workspace['draft']['configuration']['input_ids']) == 3
        first = request(client, 'post', experiment + '/runs', {'request_id': 'run1', 'expected_revision': 0})
        first_path = experiment + '/runs/' + first['id']
        assert client.get(PREFIX + first_path).json()['lifecycle'] == 'frozen'
        command = {'request_id': 'start', 'plan_digest': first['digest']}
        request(client, 'post', first_path + '/start', command)
        request(client, 'post', first_path + '/start', command)
        first_detail = wait_for_run(client, first_path)
        assert first_detail['lifecycle'] == 'complete'
        assert len(first_detail['observations']) == 3
        relationship = next(r for o in first_detail['observations'] for r in o['relationships'] if r['expected'])
        assert relationship['expected'][0]['occurrences']
        retained_manifest = (tmp_path / first['id'] / 'manifest.json').read_bytes()
        configuration = {**workspace['draft']['configuration'], 'input_ids': ['case_03_fixture'],
            'resolver': 'generative', 'execution_mode': 'recorded', 'invocation_cap': 1}
        request(client, 'put', experiment + '/draft', {'request_id': 'edit', 'expected_revision': 0,
                                                      'configuration': configuration})
        second = request(client, 'post', experiment + '/runs', {'request_id': 'run2', 'expected_revision': 1})
        second_path = experiment + '/runs/' + second['id']
        request(client, 'post', second_path + '/start', {'request_id': 'start', 'plan_digest': second['digest']})
        second_detail = wait_for_run(client, second_path)
        assert len(second_detail['observations']) == 1
        assert second_detail['observations'][0]['configuration'] == 'generative_full_source'
        third = request(client, 'post', experiment + '/runs', {'request_id': 'run3', 'expected_revision': 1})
        assert third['id'] != second['id']
        assert (tmp_path / first['id'] / 'manifest.json').read_bytes() == retained_manifest
        assert client.get(PREFIX + first_path).json() == first_detail
        assert client.get(PREFIX + experiment).json()['draft']['configuration'] == configuration
        records = {p: p.read_bytes() for p in tmp_path.rglob('*') if p.is_file() and not p.name.startswith('.')}
        # Reconstruct after total projection deletion, with artifacts unchanged.
        with create_engine(database).begin() as connection:
            connection.execute(text('TRUNCATE research_experiments, research_workspaces'))
        rebuild_index(create_engine(database), tmp_path)
        assert client.get(PREFIX + first_path).json() == first_detail
        assert client.get(PREFIX + second_path).json() == second_detail
        assert client.get(PREFIX + '/experiments').json()['items'][0]['name'] == workspace['name']
        assert all(path.read_bytes() == value for path, value in records.items())
    # Standalone read composition has no commands; historical reads never reconcile/write.
    reader = TestClient(create_app())
    assert reader.post(PREFIX + '/experiments', json={}).status_code == 405
    assert reader.get(PREFIX + first_path).json() == first_detail
