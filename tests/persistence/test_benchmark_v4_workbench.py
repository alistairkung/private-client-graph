"""Opt-in exact custody and PostgreSQL test through the substituted worker boundary."""
import os
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from private_client_graph.research.live_accounting import initialize_task
from private_client_graph.workbench import supervisor


# Use the real worker subprocess and replace its only provider entry point
# before importing the worker. Keep the credential unset as a second boundary.
SUBSTITUTED_WORKER = '''
import runpy
from private_client_graph.research import provider

def substitute(request, *, api_key):
    assert not api_key
    return provider.ModelResponse(
        payload={'relationships': []},
        usage=provider.TokenUsage(input_tokens=1, output_tokens=2),
        returned_model='test-provider',
    )

provider.invoke_deepseek = substitute
runpy.run_module('private_client_graph.workbench.worker', run_name='__main__', alter_sys=True)
'''


def test_exact_v4_owner_workbench_freezes_authorizes_starts_and_indexes(database, tmp_path, monkeypatch):
    location = os.getenv('PCG_V3_PRIVATE_BASELINE_CUSTODY')
    if not location:
        pytest.skip('Set PCG_V3_PRIVATE_BASELINE_CUSTODY for the exact private Workbench test')
    root = tmp_path / 'workbench'
    root.mkdir(mode=0o700)
    task = initialize_task(root, 'Substituted private integration test')
    owner_token = 'private-v4-integration-test-token'
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(root))
    monkeypatch.setenv('PCG_BENCHMARK_V4_CUSTODY', str(Path(location).resolve()))
    monkeypatch.setenv('PCG_BENCHMARK_V4_OWNER_TOKEN', owner_token)
    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    from private_client_graph.workbench.execution_api import create_execution_app

    popen = supervisor.subprocess.Popen
    children = []

    def launch(args, *pargs, **kwargs):
        if args[1:3] == ['-m', 'private_client_graph.workbench.worker']:
            child = popen([args[0], '-c', SUBSTITUTED_WORKER, *args[3:]], *pargs, **kwargs)
            children.append(child)
            return child
        return popen(args, *pargs, **kwargs)

    monkeypatch.setattr(supervisor.subprocess, 'Popen', launch)
    with TestClient(create_execution_app(), client=('127.0.0.1', 50000)) as client:
        client.auth = ('owner', owner_token)
        client.headers['origin'] = 'http://testserver'
        workspace_url = '/api/research/v2/experiments'
        response = client.post(workspace_url, json={'request_id': 'new', 'name': 'Benchmark v4 integration'})
        assert response.status_code == 200
        workspace = response.json()
        assert len(workspace['draft']['configuration']['input_ids']) == 35
        response = client.post(f"{workspace_url}/{workspace['id']}/runs",
                               json={'request_id': 'freeze', 'expected_revision': 0})
        assert response.status_code == 200
        plan = response.json()
        run_url = f"{workspace_url}/{workspace['id']}/runs/{plan['id']}"
        assert client.get(run_url).json()['benchmark_v4']['state'] == 'unmeasured'

        command = {'request_id': 'approve', 'plan_digest': plan['digest']}
        response = client.post(f'{run_url}/authorize', json={
            **command, 'approved': True, 'task_id': task['task_id'], 'expected_task_usage': 0,
            'expected_task_cap': 0, 'task_cap': 35,
        })
        assert response.status_code == 200
        assert response.json()['started'] is False
        assert children == []
        response = client.post(f'{run_url}/start', json=command)
        assert response.status_code == 200
        child, = children
        assert child.wait(timeout=30) == 0

        response = client.get(f'{run_url}/aggregate')
        assert response.status_code == 200
        mixed = response.json()
        assert mixed['benchmark_v4']['state'] == 'complete'
        assert mixed['benchmark_v4']['combined']['valid_graphs'] == 35
        assert mixed['benchmark_v4']['combined']['counts'] == {'tp': 0, 'fp': 0, 'fn': 119}
        assert mixed['qualified_protocol']['cohort']['planned_proofs'] == 71
        assert mixed['benchmark_v4']['consensus_evidence']['matched_citations'] == 0
        assert client.get(workspace_url).json()['items'][0]['run_ids'] == [plan['id']]
