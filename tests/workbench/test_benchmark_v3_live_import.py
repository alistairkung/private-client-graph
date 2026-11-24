"""Opt-in verification of the private first-live archive; never runs in CI by default."""

import os
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest
from fastapi.testclient import TestClient

from private_client_graph.workbench.api import create_app
from private_client_graph.workbench.benchmark_v3_import import (
    EXPERIMENT_NAMESPACE, import_first_live_baseline,
)


ARCHIVE = os.getenv('PCG_BENCHMARK_V3_LIVE_ARCHIVE')
ADMISSIONS = os.getenv('PCG_BENCHMARK_V3_ADMISSIONS')
pytestmark = pytest.mark.skipif(not ARCHIVE or not ADMISSIONS,
    reason='Set private Benchmark v3 custody paths to run the opt-in regression.')


def test_private_baseline_import_is_idempotent_and_readable(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path / 'artifacts'
    archive, admissions = Path(ARCHIVE), Path(ADMISSIONS)
    run_id = import_first_live_baseline(root, archive, admissions)
    assert import_first_live_baseline(root, archive, admissions) == run_id
    experiment_id = uuid5(NAMESPACE_URL, f'{EXPERIMENT_NAMESPACE}:{run_id}').hex
    monkeypatch.setenv('PCG_RESEARCH_ARTIFACTS', str(root))

    response = TestClient(create_app()).get(
        f'/api/research/v2/experiments/{experiment_id}/runs/{run_id}',
    )

    assert response.status_code == 200
    detail = response.json()
    benchmark = detail['benchmark']
    assert benchmark['scope']['observation_origin'] == 'live'
    assert len(detail['observations']) == 34
    assert len(benchmark['families']) == 19
    assert [benchmark['cohort'][key] for key in ('planned_conditions', 'valid_graphs', 'exact_graphs')] == [34, 30, 20]
    assert [benchmark['cohort']['all_conditions'][key] for key in ('tp', 'fp', 'fn')] == [91, 10, 22]
    assert [benchmark['cohort'][key] for key in ('complete_proofs', 'planned_proofs',
            'complete_joint_proofs', 'planned_joint_proofs')] == [18, 71, 0, 30]
