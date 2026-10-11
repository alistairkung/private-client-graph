"""Public v2 lifecycle integration; only the external provider is substituted."""
from pathlib import Path
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

from private_client_graph.research.live_accounting import initialize_task
from private_client_graph.workbench.api import create_app
from private_client_graph.workbench.execution_api import create_execution_app

PREFIX = '/api/research/v2'
HEADERS = {'origin': 'http://testserver'}


@pytest.fixture
def workspace_client(database, tmp_path, monkeypatch):
    initialize_task(tmp_path, 'Workspace lifecycle integration')
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(tmp_path))
    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-only-substituted-provider')
    real_popen = subprocess.Popen

    def substituted(args, **kwargs):
        return real_popen([args[0], str(Path('tests/research_live_worker.py').resolve()),
                           *args[3:]], **kwargs)

    monkeypatch.setattr('private_client_graph.workbench.supervisor.subprocess.Popen', substituted)
    with TestClient(create_execution_app()) as client:
        yield client


def post(client, path, body):
    response = client.post(PREFIX + path, json=body, headers=HEADERS)
    assert response.status_code == 200, response.text
    return response.json()


def experiment(client, request='workspace'):
    workspace = post(client, '/experiments', {'request_id': request, 'name': 'Resolver consistency'})
    identity = workspace['id']
    response = client.put(PREFIX + f'/experiments/{identity}/draft', headers=HEADERS,
        json={'request_id': 'configure', 'expected_revision': 0, 'configuration': {
            'input_ids': ['case_03_fixture'], 'execution_mode': 'live', 'resolver': 'generative',
            'resolver_repetitions': 1, 'invocation_cap': 1, 'task_call_cap': 2}})
    assert response.status_code == 200, response.text
    return identity


def freeze(client, identity, request):
    plan = post(client, f'/experiments/{identity}/runs',
                {'request_id': request, 'expected_revision': 1})
    return f'/experiments/{identity}/runs/{plan["id"]}', plan


def approval(plan, request, used=0, cap=0):
    return {'request_id': request, 'plan_digest': plan['digest'], 'approved': True,
            'task_id': plan['task_id'], 'task_cap': 2,
            'expected_task_usage': used, 'expected_task_cap': cap}


def start_command(plan, request):
    return {'request_id': request, 'plan_digest': plan['digest']}


def completed(client, path):
    for _ in range(150):
        response = client.get(PREFIX + path)
        if response.status_code == 200 and response.json()['lifecycle'] == 'complete':
            # Terminal results publish before the supervised process releases its lock.
            status = client.get('/api/research/v1/plans/' + path.rsplit('/', 1)[-1])
            if status.status_code == 200 and not status.json()['active_plan_id']:
                return response.json()
        time.sleep(.05)
    raise AssertionError(f'Run did not complete: {response.text}')


def retained_bytes(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*.json')}


def test_authorization_does_not_dispatch_and_copy_does_not_transfer_authority(workspace_client, tmp_path):
    client = workspace_client
    identity = experiment(client)
    path, plan = freeze(client, identity, 'first-run')
    command = start_command(plan, 'consent')
    assert client.post(PREFIX + path + '/start', json=command, headers=HEADERS).status_code == 409
    consent = approval(plan, 'consent')
    assert client.post(PREFIX + path + '/authorize', json=consent).status_code == 403
    assert client.post(PREFIX + path + '/authorize', json=consent | {'approved': False}, headers=HEADERS).status_code == 422
    accepted = post(client, path + '/authorize', consent)
    assert accepted['started'] is False
    assert post(client, path + '/authorize', consent) == accepted
    detail = client.get(PREFIX + path).json()
    assert detail['lifecycle'] == 'frozen'
    assert not list(tmp_path.glob('*/attempts/*.started.json'))
    post(client, path + '/start', command)
    post(client, path + '/start', command)
    result = completed(client, path)
    assert len(list(tmp_path.glob('*/attempts/*.started.json'))) == 1
    assert result['observations'][0]['result']['evaluation'] is not None
    old_snapshot = retained_bytes(tmp_path / plan['id'])
    copied = post(client, f'/experiments/{identity}/draft/copy', {
        'request_id': 'copy', 'expected_revision': 1, 'run_id': plan['id']})
    assert copied['revision'] == 2
    next_plan = post(client, f'/experiments/{identity}/runs', {
        'request_id': 'copied-run', 'expected_revision': 2})
    next_path = f'/experiments/{identity}/runs/{next_plan["id"]}'
    assert client.post(PREFIX + next_path + '/start',
        json=start_command(next_plan, 'consent'), headers=HEADERS).status_code == 409
    assert client.get(PREFIX + next_path).json()['authorized_invocations'] == []
    assert retained_bytes(tmp_path / plan['id']) == old_snapshot


def test_other_run_spending_invalidates_pending_start_and_budget_survives_new_experiment(workspace_client):
    client = workspace_client
    first_exp = experiment(client, 'first-experiment')
    second_exp = experiment(client, 'second-experiment')
    first_path, first = freeze(client, first_exp, 'first-run')
    second_path, second = freeze(client, second_exp, 'second-run')
    post(client, first_path + '/authorize', approval(first, 'first'))
    post(client, second_path + '/authorize', approval(second, 'second', cap=2))
    post(client, first_path + '/start', start_command(first, 'first'))
    completed(client, first_path)
    response = client.post(PREFIX + second_path + '/start',
        json=start_command(second, 'second'), headers=HEADERS)
    assert response.status_code == 409
    assert 'budget changed' in response.text.lower()
    post(client, second_path + '/authorize', approval(second, 'fresh-consent', used=1, cap=2))
    post(client, second_path + '/start', start_command(second, 'fresh-consent'))
    completed(client, second_path)
    third_path, third = freeze(client, first_exp, 'third-run')
    response = client.post(PREFIX + third_path + '/authorize',
        json=approval(third, 'exhausted', used=2, cap=2), headers=HEADERS)
    assert response.status_code == 409
    assert 'exhausted' in response.text.lower()


def test_historical_inspection_and_read_only_composition_do_not_mutate_authority(workspace_client, tmp_path):
    client = workspace_client
    identity = experiment(client)
    path, plan = freeze(client, identity, 'inspectable')
    post(client, path + '/authorize', approval(plan, 'pending-consent'))
    before = retained_bytes(tmp_path)
    with TestClient(create_app()) as read_only:
        assert read_only.get(PREFIX + path).status_code == 200
        assert read_only.get(PREFIX + f'/experiments/{identity}/runs').status_code == 200
        response = read_only.post(PREFIX + path + '/start',
                                 json=start_command(plan, 'pending-consent'), headers=HEADERS)
        assert response.status_code in (404, 405)
    assert retained_bytes(tmp_path) == before
