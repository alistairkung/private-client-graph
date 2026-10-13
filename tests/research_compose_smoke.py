"""CI acceptance of real Compose persistence and disposable-index recovery."""
import json
import subprocess
import time
from urllib.request import Request, urlopen


def compose(*args: str) -> str:
    return subprocess.check_output(['docker', 'compose', *args], text=True)


def read(path: str):
    with urlopen(f'http://127.0.0.1:8080{path}', timeout=5) as response:
        return json.load(response)


def wait_ready() -> None:
    for _ in range(60):
        try:
            if read('/health')['status'] == 'ok':
                return
        except (OSError, ValueError):
            pass
        time.sleep(1)
    raise RuntimeError('Research Compose service never became ready')


def command(path, body):
    request = Request(f'http://127.0.0.1:8080/api/research/v1{path}',
        data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'Origin': 'http://127.0.0.1:8080'})
    with urlopen(request, timeout=10) as response:
        return json.load(response)


def wait_state(identity, expected):
    for _ in range(100):
        state = read(f'/api/research/v1/plans/{identity}')
        if state['state'] == expected and not state['active_plan_id']:
            return state
        time.sleep(.1)
    raise AssertionError(f'Experiment did not reach {expected}: {state}')


def offline_journey():
    plan = command('/plans', {'input_ids': ['case_03_fixture'], 'execution_mode': 'recorded',
        'resolver': 'generative', 'resolver_repetitions': 2, 'invocation_cap': 1})
    identity = plan['id']
    first = {'request_id': 'first', 'plan_digest': plan['digest']}
    command(f'/plans/{identity}/start', first)
    command(f'/plans/{identity}/start', first)
    checkpoint = wait_state(identity, 'stopped')
    assert checkpoint['attempts'] == 1
    compose('restart', 'research')
    wait_ready()
    assert wait_state(identity, 'stopped')['attempts'] == 1
    command(f'/plans/{identity}/continue', {'request_id': 'continue', 'plan_digest': plan['digest']})
    finished = wait_state(identity, 'complete')
    assert finished['attempts'] == 2
    result = read(f"/api/research/v1/experiments/{finished['result_id']}")
    relationships = result['samples'][0]['observations'][0]['relationships']
    assert any(row['outcome'] == 'missing' and row['expected'][0]['occurrences'] for row in relationships)


def snapshot():
    page = read('/api/research/v1/experiments')
    details = []
    for item in page['items']:
        detail = read(f"/api/research/v1/experiments/{item['id']}")
        detail['history'].pop('indexed_at')
        details.append(detail)
    return details


def main() -> None:
    try:
        compose('up', '--build', '-d', 'research')
        wait_ready()
        offline_journey()
        original = snapshot()
        assert any(item['history']['kind'] == 'task_b_pilot' for item in original)
        assert all(item['history']['integrity'] == 'verified' for item in original)
        compose('stop', 'research')
        compose('restart', 'research-database')
        compose('up', '-d', '--wait', 'research-database')
        compose('start', 'research')
        wait_ready()
        assert snapshot() == original
        compose('exec', '-T', 'research-database', 'psql', '-U', 'pcg', '-d', 'pcg_research',
                '-c', 'TRUNCATE research_experiments')
        assert compose('exec', '-T', 'research-database', 'psql', '-U', 'pcg', '-d', 'pcg_research', '-tAc', 'SELECT count(*) FROM research_experiments').strip() == '0'
        compose('exec', '-T', 'research', 'python', '-m', 'private_client_graph.workbench', '/artifacts')
        assert snapshot() == original
        compose('exec', '-T', 'research', 'python', '-m', 'private_client_graph.workbench', '/artifacts')
        assert snapshot() == original
        print('Compose offline execution, explicit continuation, restart, artifact retention, empty-index rebuild and idempotence passed.')
    finally:
        print(compose('logs', '--no-color', 'research'))
        compose('down')


if __name__ == '__main__':
    main()
