"""Opt-in exact custody and PostgreSQL test through the substituted worker boundary."""
import json
import os
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.live_accounting import initialize_task
from private_client_graph.workbench import supervisor


# Use the real worker subprocess and replace its only provider entry point
# before importing the worker. Keep the credential unset as a second boundary.
SUBSTITUTED_WORKER = '''
import runpy
from private_client_graph.research import provider

def substitute(request, *, api_key):
    assert not api_key
    if request.stage == 'resolution':
        assert request.extraction.relationships == []
        return provider.ModelResponse(payload={'edits': []},
            usage=provider.TokenUsage(input_tokens=3, output_tokens=4), returned_model='test-provider')
    return provider.ModelResponse(payload={'relationships': []},
        usage=provider.TokenUsage(input_tokens=1, output_tokens=2), returned_model='test-provider')

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
    pricing = tmp_path / 'pricing.json'
    pricing.write_text(json.dumps({'model': 'deepseek-flash', 'input_per_million': 1, 'output_per_million': 2,
        'cached_input_per_million': 1, 'source_url': 'https://example.test', 'retrieved_at': '2026-11-27'}))
    monkeypatch.setenv('PCG_BENCHMARK_V4_PRICING_FILE', str(pricing))
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

        experiment_url = f"{workspace_url}/{workspace['id']}"
        copied = client.post(f'{experiment_url}/draft/copy',
            json={'request_id': 'copy', 'expected_revision': 0, 'run_id': plan['id']})
        assert copied.status_code == 200
        draft = copied.json()
        config = dict(draft['configuration'], input_mode='saved', resolver='generative', task_call_cap=70,
                      invocation_cap=18, retained_run_id=plan['id'], retained_experiment_id=workspace['id'])
        preview = client.post('/api/research/v2/preview', json=config)
        assert preview.status_code == 200
        assert (preview.json()['extraction_call_maximum'], preview.json()['resolution_call_maximum']) == (0, 35)
        updated = client.put(f'{experiment_url}/draft', json={'request_id': 'configure',
            'expected_revision': draft['revision'], 'configuration': config})
        assert updated.status_code == 200
        frozen = client.post(f'{experiment_url}/runs',
            json={'request_id': 'freeze-paired', 'expected_revision': updated.json()['revision']})
        assert frozen.status_code == 200
        paired = frozen.json()
        paired_url = f"{experiment_url}/runs/{paired['id']}"

        # A metrics export does not change the immutable original extraction lineage.
        subprocess.run([sys.executable, '-m', 'private_client_graph.research', 'summarize', str(root / plan['id'])],
                       check=True, capture_output=True)

        def run_resolver(invocation, previous_usage, previous_cap, *, continuation=False):
            command = {'request_id': invocation, 'plan_digest': paired['digest']}
            authorized = client.post(f'{paired_url}/authorize', json={
                **command, 'approved': True, 'task_id': task['task_id'], 'expected_task_usage': previous_usage,
                'expected_task_cap': previous_cap, 'task_cap': 70, 'continuation': continuation,
            })
            assert authorized.status_code == 200
            path = f"{paired_url}/{'continue' if continuation else 'start'}"
            response = client.post(path, json=command)
            assert response.status_code == 200
            assert children[-1].wait(timeout=30) == 0

        run_resolver('resolve', 35, 35)
        stopped = client.get(paired_url).json()
        assert stopped['lifecycle'] == 'stopped' and len(stopped['attempts']) == 18
        run_resolver('resume', 53, 70, continuation=True)
        resolved = client.get(paired_url).json()
        assert resolved['lifecycle'] == 'complete' and len(resolved['attempts']) == 35
        assert {attempt['request']['stage'] for attempt in resolved['attempts']} == {'resolution'}
        assert len({attempt['attempt_id'] for attempt in resolved['attempts']}) == 35
        assert resolved['benchmark_v4'] == mixed['benchmark_v4']
        assert resolved['pipeline_usage']['incremental']['estimated_cost'] == pytest.approx(0.000385)
        assert resolved['pipeline_usage']['inherited_extraction']['estimated_cost'] == pytest.approx(0.000175)
        assert resolved['pipeline_usage']['full_pipeline']['estimated_cost'] == pytest.approx(0.00056)
        usage = resolved['pipeline_usage']
        assert usage['full_pipeline']['tokens']['input_tokens'] == 140
        assert usage['full_pipeline']['provider_seconds'] == pytest.approx(
            usage['incremental']['provider_seconds'] + usage['inherited_extraction']['provider_seconds'])
        assert usage['full_pipeline_seconds'] >= usage['full_pipeline']['provider_seconds']
        assert client.get('/api/research/v2/status').json()['task_budget']['used'] == 70
        comparison = client.get(f"{experiment_url}/comparison", params={'left': plan['id'], 'right': paired['id']}).json()
        assert comparison['matched_inputs'] == 35 and comparison['comparable_scope']
        assert comparison['benchmark_v4']['shared_extraction_run_id'] == plan['id']
        assert comparison['benchmark_v4']['right_usage'] == usage
        subprocess.run([sys.executable, '-m', 'private_client_graph.research', 'summarize', str(root / paired['id'])],
                       check=True, capture_output=True)
        summary = json.loads((root / paired['id'] / 'summary.json').read_text())
        assert summary['pipeline_usage'] == usage
        assert summary['benchmark_v4'] == resolved['benchmark_v4']

        assert resolved['reference_cost']['total'] == pytest.approx(0.00056)
        reference_pricing = json.loads(pricing.read_text())
        reference_pricing['output_per_million'] *= 2
        pricing.write_text(json.dumps(reference_pricing))
        at_new_rate = client.get(paired_url).json()
        assert at_new_rate['reference_cost']['total'] == pytest.approx(0.00098)
        assert at_new_rate['pipeline_usage'] == usage

        unused = client.post(f'{experiment_url}/runs', json={
            'request_id': 'unused', 'expected_revision': updated.json()['revision'],
        }).json()
        unused_url = f"{experiment_url}/runs/{unused['id']}"
        assert client.get(unused_url).json()['can_archive']
        failed = client.post(f'{experiment_url}/runs', json={
            'request_id': 'failed-worker', 'expected_revision': updated.json()['revision'],
        }).json()
        failed_url = f"{experiment_url}/runs/{failed['id']}"
        supervisor.event(Bundle.open(root / failed['id']), 'failed', 'Substituted worker failure.', 'fixture')
        assert client.get(failed_url).json()['execution_message'] == 'Substituted worker failure.'
        assert client.post(f'{paired_url}/archive', json={}).status_code == 409
        assert client.post(f'{unused_url}/archive', json={}, headers={'origin': 'https://example.test'}).status_code == 403
        for _ in range(2):
            archived = client.post(f'{unused_url}/archive', json={}).raise_for_status().json()
            assert archived['run_ids'] == [plan['id'], paired['id'], failed['id']]
            assert archived['run_numbers'][failed['id']] == 4
        assert (root / unused['id'] / 'manifest.json').exists()
        assert client.get(unused_url).status_code == 409
        assert client.post(f'{unused_url}/start', json=command).status_code == 409
        assert client.post(f"/api/research/v1/plans/{unused['id']}/start", json={
            'request_id': 'archive-restart', 'plan_digest': unused['digest'],
        }).status_code == 409
        assert client.post(f'{failed_url}/archive', json={}).json()['run_ids'] == [plan['id'], paired['id']]
        assert client.get('/api/research/v2/status').json()['task_budget']['used'] == 70
