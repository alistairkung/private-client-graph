"""CI acceptance of real Compose persistence and disposable-index recovery."""
import json
import subprocess
import time
from urllib.request import urlopen


def compose(*args: str) -> str:
    return subprocess.check_output(['docker', 'compose', *args], text=True)


def read(path: str):
    with urlopen(f'http://127.0.0.1:8080{path}', timeout=5) as response:
        return json.load(response)


def wait_ready() -> None:
    for _ in range(60):
        try:
            if read('/health')['read_only']:
                return
        except (OSError, ValueError):
            pass
        time.sleep(1)
    raise RuntimeError('Research Compose service never became ready')


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
        assert read('/api/research/v1/experiments')['total'] == 0
        compose('exec', '-T', 'research', 'python', '-m', 'private_client_graph.workbench', '/artifacts')
        assert snapshot() == original
        compose('exec', '-T', 'research', 'python', '-m', 'private_client_graph.workbench', '/artifacts')
        assert snapshot() == original
        print('Compose restart, artifact retention, empty-index rebuild and idempotence passed.')
    finally:
        print(compose('logs', '--no-color', 'research'))
        compose('down')


if __name__ == '__main__':
    main()
