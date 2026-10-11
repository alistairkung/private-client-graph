"""Local HTTP authority and real supervised subprocess with a substituted provider."""
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from private_client_graph.research.live_accounting import initialize_task
from private_client_graph.workbench.execution_api import create_execution_app
from private_client_graph.workbench.planning import live_budget
from tests.persistence.test_research_execution import await_finished

PREFIX = '/api/research/v1'
HEADERS = {'origin': 'http://testserver'}


def test_explicit_live_http_subprocess_restart_and_empty_index(database, tmp_path, monkeypatch):
    initialize_task(tmp_path, 'Substituted integration task')
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(tmp_path))
    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-secret-credential')
    real_popen = subprocess.Popen
    def substituted(args, **kwargs):
        return real_popen([args[0], str(Path('tests/research_live_worker.py').resolve()), *args[3:]], **kwargs)
    monkeypatch.setattr('private_client_graph.workbench.supervisor.subprocess.Popen', substituted)
    client = TestClient(create_execution_app())
    proposal = dict(input_ids=['case_03_fixture'], execution_mode='live', resolver='generative',
                    resolver_repetitions=2, invocation_cap=1, task_call_cap=2)
    response = client.post(PREFIX + '/plans', json=proposal, headers=HEADERS)
    assert response.status_code == 200, response.text
    plan = response.json()
    path = PREFIX + '/plans/' + plan['id']
    command = dict(plan_digest=plan['digest'], request_id='approved', approved=True,
                   task_id=plan['task_id'], expected_task_usage=0, expected_task_cap=0, task_cap=2)
    assert client.post(path + '/start', json={'plan_digest': plan['digest'], 'request_id': 'no'}, headers=HEADERS).status_code == 409
    assert client.post(path + '/authorize', json=command).status_code == 403
    assert client.post(path + '/authorize', json=command, headers={'origin': 'http://evil'}).status_code == 403
    assert client.post(path + '/authorize', json=command, headers={'origin': 'http://evil', 'host': 'evil'}).status_code in (400, 403)
    assert client.post(path + '/authorize', json=command | {'approved': False}, headers=HEADERS).status_code == 422
    assert client.post(path + '/authorize', json=command | {'plan_digest': 'a' * 64}, headers=HEADERS).status_code == 409
    # Concurrent duplicates publish one command and one invocation approval.
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: client.post(path + '/authorize', json=command, headers=HEADERS), range(2)))
    assert [r.status_code for r in responses] == [200, 200], [r.text for r in responses]
    result = await_finished(tmp_path, plan['id'])
    assert result.state == 'stopped' and result.attempts == 1
    assert result.task_budget.used == 1
    assert len(list((tmp_path / plan['id'] / 'authorizations').glob('*.json'))) == 1
    # Recreate service and all derived state. Nothing resumes without a new approval.
    with create_engine(database).begin() as connection:
        connection.execute(text('TRUNCATE research_experiments'))
    with TestClient(create_execution_app()) as restarted:
        assert restarted.get(path).json()['state'] == 'stopped'
        assert restarted.get(path).json()['task_budget']['used'] == 1
        detail = restarted.get(PREFIX + '/experiments/' + result.result_id).json()
        assert detail['history']['kind'] == 'live_experiment'
        assert len(detail['operations']['authorizations']) == 1
        assert restarted.post(path + '/authorize', json=command, headers=HEADERS).status_code == 200
        assert await_finished(tmp_path, plan['id']).attempts == 1
        continuation = command | dict(request_id='continue', continuation=True, expected_task_usage=1, expected_task_cap=2)
        response = restarted.post(path + '/authorize', json=continuation, headers=HEADERS)
        assert response.status_code == 200, response.text
        assert await_finished(tmp_path, plan['id']).state == 'complete'
        assert live_budget(tmp_path).used == 2
        # A new bundle shares exhausted authority and cannot silently increase it.
        other = restarted.post(PREFIX + '/plans', json=proposal, headers=HEADERS).json()
        exhausted = command | dict(request_id='other', plan_digest=other['digest'], expected_task_usage=2, expected_task_cap=2)
        assert restarted.post(PREFIX + '/plans/' + other['id'] + '/authorize', json=exhausted, headers=HEADERS).status_code == 409
    # The server-side test credential never appears in retained artifacts.
    assert 'test-secret-credential' not in ''.join(p.read_text() for p in tmp_path.rglob('*.json'))


def test_live_capability_disabled_even_for_preapproved_bundle(database, tmp_path, monkeypatch):
    from tests.workbench.test_live_execution import frozen, approved_bundle
    initialize_task(tmp_path, 'Capability test')
    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    plan = frozen(tmp_path)
    approved_bundle(tmp_path, plan)
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(tmp_path))
    monkeypatch.delenv('PCG_RESEARCH_LIVE_ENABLED')
    client = TestClient(create_execution_app())
    assert not client.get(PREFIX + '/capabilities').json()['live_enabled']
    command = dict(request_id='disabled', plan_digest=plan.digest, approved=True, task_id=plan.task_id,
                   expected_task_usage=0, expected_task_cap=3, task_cap=3)
    assert client.post(PREFIX + '/plans/' + plan.id + '/authorize', json=command, headers=HEADERS).status_code == 409
