"""Synthetic tests for the read-only Benchmark v3 import seam."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from benchmark_v3.evaluation_protocol import EvaluationScope, GraphCounts, Metrics
from private_client_graph.workbench.benchmark_contracts import BenchmarkRun
from private_client_graph.workbench.benchmark_v3_import import register_offline_fixture_for_tests
from private_client_graph.workbench.execution_contracts import FrozenPlan, Preview, Proposal
from private_client_graph.workbench.run_inspection import RunDetail, read_run
from private_client_graph.workbench.run_evaluation_contracts import RunAggregate, RunCost, RunEvaluation
from private_client_graph.workbench.api import create_app


def _metrics() -> Metrics:
    return Metrics(
        planned_conditions=1, valid_graphs=1, exact_graphs=1,
        construction_success_rate=1.0, exact_graph_accuracy=1.0,
        valid_graph_only_exact_accuracy=1.0,
        all_conditions=GraphCounts(0, 0, 0), all_condition_micro_f1=0.0,
        valid_graph_only=GraphCounts(0, 0, 0), valid_graph_only_micro_f1=0.0,
        expected_edges_without_graph=0, planned_proofs=0, complete_proofs=0,
        proof_completion_rate=None, planned_joint_proofs=0, complete_joint_proofs=0,
        joint_proof_completion_rate=None, incomplete_proofs=0, missed_proofs=0,
        proofs_without_graph=0, quote_passed=0, quote_assessed=0,
        attribution_passed=0, attribution_assessed=0, outcomes={'scored': 1},
    )


def _detail() -> RunDetail:
    scope = EvaluationScope(
        benchmark_sha256='a' * 64, conditions=(), observation_origin='offline_fixture',
    )
    benchmark = BenchmarkRun(
        scope=scope, cohort=_metrics(), families={'A': _metrics()},
        family_macro_f1=0.0, valid_graph_only_family_macro_f1=0.0,
        valid_graph_only_macro_family_count=1, observations=[],
    )
    run_id = '1' * 32
    preview = Preview(proposal=Proposal(input_ids=['synthetic']), inputs=[], extraction_call_maximum=0,
        resolution_call_maximum=0, matrix_call_maximum=0, planned_observations=0,
        invocation_cap=0)
    plan = FrozenPlan(id='3' * 32, digest='c' * 64, task_id='synthetic',
        preview=preview, created_at='2026-11-24T00:00:00+00:00')
    return RunDetail(
        id=run_id, experiment_id='2' * 32, plan=plan, lifecycle='complete',
        evaluation=RunEvaluation(run_id=run_id, aggregate=RunAggregate(), cost=RunCost()),
        benchmark=benchmark, observations=[], provenance={},
        artifact_digest='b' * 64, authorized_invocations=[], attempts=[],
    )


def test_offline_fixture_import_uses_run_read_seam_and_keeps_origin(tmp_path: Path) -> None:
    original = _detail()
    register_offline_fixture_for_tests(tmp_path, original)

    observed = read_run(tmp_path, original.experiment_id, original.id)

    assert observed.benchmark is not None
    assert observed.benchmark.scope.observation_origin == 'offline_fixture'
    assert observed.plan.id == original.plan.id
    assert observed.evaluation.run_id == original.evaluation.run_id
    assert observed.benchmark.as_protocol_result().scope == original.benchmark.scope


def test_offline_fixture_projection_tampering_fails_closed(tmp_path: Path) -> None:
    original = _detail()
    register_offline_fixture_for_tests(tmp_path, original)
    projection = tmp_path / 'benchmark_v3' / 'imports' / original.id / 'projection.json'
    projection.chmod(0o600)
    projection.write_text('{}')

    with pytest.raises(ValueError, match='projection changed'):
        read_run(tmp_path, original.experiment_id, original.id)


def test_offline_fixture_projection_must_match_workspace_membership(tmp_path: Path) -> None:
    original = _detail()
    register_offline_fixture_for_tests(tmp_path, original)
    membership_path = (tmp_path / 'experiments' / original.experiment_id / 'runs'
                       / f'{original.id}.json')
    from private_client_graph.workbench.workspaces import read_record, write_record
    membership = read_record(membership_path)
    membership['projection_sha256'] = '0' * 64
    membership_path.unlink()
    write_record(membership_path, membership)

    with pytest.raises(ValueError, match='membership'):
        read_run(tmp_path, original.experiment_id, original.id)


def test_read_only_api_serves_imported_projection_without_mutation_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = _detail()
    register_offline_fixture_for_tests(tmp_path, original)
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(tmp_path))
    app = create_app()

    response = TestClient(app).get(
        f'/api/research/v2/experiments/{original.experiment_id}/runs/{original.id}',
    )

    assert response.status_code == 200
    assert response.json()['benchmark']['scope']['observation_origin'] == 'offline_fixture'
    # This fixture reuses admitted Family A without sharing its admission.
    assert response.json()['family_context'] is None
    assert not any(route.path.endswith('/authorize') or route.path.endswith('/start')
                   for route in app.routes)
