"""Real PostgreSQL and supervised subprocess integration; no live providers."""
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from private_client_graph.workbench.execution_api import create_execution_app
from private_client_graph.workbench.execution_contracts import Command, Proposal
from private_client_graph.workbench.planning import freeze
from private_client_graph.workbench.supervisor import active_lock, start, status

PREFIX = '/api/research/v1'
HEADERS = {'origin': 'http://testserver'}


def await_finished(root, identity):
    for _ in range(100):
        result = status(root, identity)
        if result.state not in ('running', 'stopping') and not result.active_plan_id:
            return result
        time.sleep(.1)
    raise AssertionError('Offline subprocess did not finish')


def test_api_subprocess_checkpoint_continue_and_rebuild(database, tmp_path, monkeypatch):
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(tmp_path))
    client = TestClient(create_execution_app())
    proposal = {'input_ids': ['case_03_fixture'], 'execution_mode': 'recorded',
                'resolver': 'generative', 'resolver_repetitions': 2, 'invocation_cap': 1}
    assert client.post(PREFIX + '/preview', json=proposal).status_code == 403
    assert client.post(PREFIX + '/preview', json=proposal, headers={'origin': 'http://evil.example'}).status_code == 403
    assert client.post(PREFIX + '/preview', json={**proposal, 'execution_mode': 'live'}, headers=HEADERS).status_code == 409
    plan_response = client.post(PREFIX + '/plans', json=proposal, headers=HEADERS)
    assert plan_response.status_code == 200, plan_response.text
    plan = plan_response.json()
    path = PREFIX + '/plans/' + plan['id']
    command = {'plan_digest': plan['digest'], 'request_id': 'first'}
    response = client.post(path + '/start', json=command, headers=HEADERS)
    assert response.status_code == 200, response.text
    assert client.post(path + '/start', json=command, headers=HEADERS).status_code == 200
    result = await_finished(tmp_path, plan['id'])
    assert result.state == 'stopped'
    assert result.attempts == 1
    assert result.completed_observations == 2
    assert client.post(path + '/start', json={**command, 'request_id': 'again'}, headers=HEADERS).status_code == 409
    continuation = {**command, 'request_id': 'continue'}
    assert client.post(path + '/continue', json=continuation, headers=HEADERS).status_code == 200
    result = await_finished(tmp_path, plan['id'])
    assert result.state == 'complete'
    assert result.attempts == 2
    assert result.completed_observations == 3
    # Recreate the API and remove all derived state; artifacts recover the same result.
    from sqlalchemy import create_engine, text
    with create_engine(database).begin() as connection:
        connection.execute(text('TRUNCATE research_experiments'))
    client = TestClient(create_execution_app())
    assert client.get(path).json()['state'] == 'complete'
    detail = client.get(PREFIX + '/experiments/' + result.result_id).json()
    assert detail['history']['integrity'] == 'verified'
    missing = [r for r in detail['samples'][0]['observations'][0]['relationships'] if r['outcome'] == 'missing']
    assert missing and missing[0]['expected'][0]['occurrences']
    assert client.post(path + '/continue', json=continuation, headers=HEADERS).status_code == 200
    assert await_finished(tmp_path, plan['id']).attempts == 2


def test_concurrent_duplicate_start_and_global_exclusion(database, tmp_path):
    frozen = freeze(tmp_path, Proposal(input_ids=['case_01_fixture']))
    command = Command(request_id='same', plan_digest=frozen.digest)
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(lambda _: start(tmp_path, frozen.id, command), range(2)))
    assert all(response.plan.id == frozen.id for response in responses)
    assert await_finished(tmp_path, frozen.id).completed_observations == 1
    assert len(list((tmp_path / frozen.id / 'commands').glob('*.json'))) == 1
    second = freeze(tmp_path, Proposal(input_ids=['case_02_fixture']))
    lock = active_lock(tmp_path)
    assert lock is not None
    try:
        import pytest
        with pytest.raises(ValueError, match='Another experiment'):
            start(tmp_path, second.id, Command(request_id='other', plan_digest=second.digest))
    finally:
        lock.close()


def test_stop_current_attempt_and_crash_require_continuation(database, tmp_path, monkeypatch):
    import subprocess
    from pathlib import Path
    from private_client_graph.workbench.supervisor import stop
    processes = []
    real_popen = subprocess.Popen
    def blocked_worker(args, **kwargs):
        child = real_popen([args[0], str(Path('tests/research_blocking_worker.py').resolve()), *args[3:]], **kwargs)
        processes.append(child)
        return child
    monkeypatch.setattr('private_client_graph.workbench.supervisor.subprocess.Popen', blocked_worker)
    request = Proposal(input_ids=['case_03_fixture'], execution_mode='recorded', resolver='generative',
                       resolver_repetitions=3, invocation_cap=3)
    frozen = freeze(tmp_path, request)
    command = Command(request_id='first', plan_digest=frozen.digest)
    try:
        start(tmp_path, frozen.id, command)
        for _ in range(100):
            if (tmp_path / '.boundary-entered').exists():
                break
            time.sleep(.05)
        assert (tmp_path / '.boundary-entered').exists()
        current = stop(tmp_path, frozen.id, command)
        assert current.state == 'stopping'
        assert current.attempts == 1
        (tmp_path / '.boundary-release').touch()
        stopped = await_finished(tmp_path, frozen.id)
        assert stopped.state == 'stopped'
        assert stopped.attempts == 1
        assert stopped.completed_observations == 2
        (tmp_path / '.boundary-entered').unlink()
        (tmp_path / '.boundary-release').unlink()
        start(tmp_path, frozen.id, Command(request_id='resume', plan_digest=frozen.digest), continuation=True)
        for _ in range(100):
            if (tmp_path / '.boundary-entered').exists():
                break
            time.sleep(.05)
        assert (tmp_path / '.boundary-entered').exists()
        processes[-1].kill()
        processes[-1].wait(timeout=5)
        interrupted = status(tmp_path, frozen.id)
        assert interrupted.state == 'interrupted'
        assert interrupted.uncertain_attempts == 1
        assert interrupted.attempts == 2
        (tmp_path / '.boundary-release').touch()
        start(tmp_path, frozen.id, Command(request_id='after-crash', plan_digest=frozen.digest), continuation=True)
        complete = await_finished(tmp_path, frozen.id)
        assert complete.state == 'complete'
        assert complete.attempts == 3
        assert complete.uncertain_attempts == 1
    finally:
        (tmp_path / '.boundary-release').touch()
        for process in processes:
            process.wait(timeout=15)
