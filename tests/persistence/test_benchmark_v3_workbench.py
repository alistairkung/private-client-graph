"""Opt-in private end-to-end import and custody regression with disposable PostgreSQL."""
import os
import shutil
from pathlib import Path

from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete

from private_client_graph.persistence.database import database_engine
from private_client_graph.workbench.api import create_app
from private_client_graph.workbench import benchmark_v3_import
from private_client_graph.workbench.index import rebuild_index
from private_client_graph.workbench.workspace_index import workspaces


@pytest.fixture
def custody(tmp_path: Path):
    configured = os.getenv('PCG_V3_PRIVATE_BASELINE_CUSTODY')
    if not configured:
        pytest.skip('Opt in with the private Benchmark v3 development custody root')
    original = Path(configured).resolve()
    archive = tmp_path / 'archive'
    source = original / 'live-baseline-2026-11-24'
    shutil.copytree(source, archive)
    admissions = original / 'admissions-2026-11-24' / 'ADMISSIONS.json'
    return archive, admissions, source


def test_verified_baseline_reappears_after_index_rebuild_and_refuses_bad_custody(
    database, custody, tmp_path, monkeypatch,
):
    archive, admissions, source = custody
    artifacts = tmp_path / 'workbench'
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(artifacts))
    monkeypatch.delenv('DEEPSEEK_API_KEY', raising=False)
    importer = benchmark_v3_import.import_first_live_baseline
    original_inventory = (source / 'CHECKSUMS.json').read_bytes()

    with monkeypatch.context() as interrupted:
        def fail_publication(*args):
            raise InterruptedError('Simulated interruption before membership publication')

        interrupted.setattr(benchmark_v3_import, '_publish_workspace', fail_publication)
        with pytest.raises(InterruptedError):
            importer(artifacts, archive, admissions)

    client = TestClient(create_app())
    url = '/api/research/v2/experiments'
    rebuild_index(database_engine(), artifacts)
    assert client.get(url).json()['items'] == []
    run_id = importer(artifacts, archive, admissions)
    assert importer(artifacts, archive, admissions) == run_id
    assert (source / 'CHECKSUMS.json').read_bytes() == original_inventory
    with pytest.raises(ValueError, match='different custody'):
        importer(artifacts, source, admissions)

    engine = database_engine()
    rebuild_index(engine, artifacts)
    workspace, = client.get(url).json()['items']
    assert workspace['run_ids'] == [run_id]
    with engine.begin() as connection:
        connection.execute(delete(workspaces))
    assert client.get(url).json()['items'] == []
    rebuild_index(engine, artifacts)
    assert client.get(url).json()['items'] == [workspace]

    run_path = f"{url}/{workspace['id']}/runs/{run_id}"
    detail = client.get(run_path)
    assert detail.status_code == 200
    result = detail.json()
    assert len(result['observations']) == 34
    protocol = result['benchmark']
    assert len(protocol['families']) == 19
    counts = protocol['cohort']
    assert counts['all_conditions'] == {'tp': 91, 'fp': 10, 'fn': 22}
    assert counts['all_condition_micro_f1'] == 182 / 214
    assert counts['valid_graph_only_micro_f1'] == 182 / 197
    assert protocol['family_macro_f1'] == pytest.approx(0.8307504873294347, abs=1e-15)
    assert (counts['valid_graphs'], counts['exact_graphs'], counts['planned_conditions']) == (30, 20, 34)
    assert (counts['complete_proofs'], counts['planned_proofs']) == (18, 71)
    assert (counts['complete_joint_proofs'], counts['planned_joint_proofs']) == (0, 30)
    provider_cost = result['evaluation']['cost']
    assert (provider_cost['currency'], provider_cost['total']) == ('USD', 0.027418308)
    assert (provider_cost['attempts'], provider_cost['unpriced_attempts'], provider_cost['reasons']) == (34, 0, [])
    assert client.get('/health').json()['read_only'] is True
    assert client.post(f'{run_path}/start', json={}).status_code == 404

    for identity, graph, proofs in [('E000', 2, 2), ('T000', 4, 5), ('C2', None, 0)]:
        response = client.get(f'{run_path}/observations/{identity}')
        assert response.status_code == 200
        observation = response.json()
        condition = observation['benchmark']
        assert len(condition['proof_targets']) == proofs
        if graph is None:
            assert observation['result']['state'] is None
            assert len(condition['expected_relationships']) == 10
            assert 'does not occur verbatim' in condition['failure_detail']
            assert condition['parsed_prediction']['relationships']
        else:
            assert len(observation['result']['state']['relationships']) == graph

    modified = archive / 'RESULTS.json'
    previous = modified.read_bytes()
    modified.write_bytes(previous + b' ')
    assert client.get(run_path).status_code == 409
    assert client.get(url).json()['items'][0]['integrity'] == 'corrupt'
    modified.write_bytes(previous)

    moved = archive.with_name('archive-removed')
    archive.rename(moved)
    try:
        assert client.get(run_path).status_code == 409
        assert client.get(url).json()['items'][0]['integrity'] == 'missing'
    finally:
        moved.rename(archive)
