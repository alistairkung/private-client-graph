import json

import pytest

from private_client_graph.research.artifacts import Bundle, BudgetExceeded
from private_client_graph.research.plan import ExperimentPlan
from private_client_graph.research.fixtures import load_inputs


def test_attempt_reservation_survives_interruption_and_resume_does_not_reset_budget(tmp_path):
    plan = ExperimentPlan(kind='task_a_diagnostic', inputs=load_inputs()[-2:], max_calls=1)
    bundle = Bundle.create(tmp_path / 'experiment', plan, task_ledger=tmp_path / 'ledger')
    bundle.reserve('alias_merge-resolve-1', {'stage': 'resolution'})
    resumed = Bundle.open(bundle.path)
    assert resumed.attempts()[0]['status'] == 'uncertain'
    with pytest.raises(BudgetExceeded):
        resumed.reserve('alias_distinct-resolve-1', {'stage': 'resolution'})
    assert resumed.attempt_count == 1
    with pytest.raises(FileExistsError):
        resumed.reserve('alias_merge-resolve-1', {'stage': 'resolution'})
    resumed.complete('alias_merge-resolve-1', {'status': 'failed', 'error_type': 'TimeoutError'})
    assert Bundle.open(bundle.path).attempts()[0]['status'] == 'failed'
    with pytest.raises(FileExistsError):
        resumed.complete('alias_merge-resolve-1', {'status': 'completed'})


def test_manifest_tampering_is_rejected(tmp_path):
    bundle = Bundle.create(tmp_path / 'experiment', ExperimentPlan(inputs=load_inputs()[-2:]))
    p = bundle.path / 'manifest.json'
    data = json.loads(p.read_text()); data['plan']['max_calls'] = 999
    p.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='checksum'):
        Bundle.open(bundle.path)


def test_development_allowance_is_shared_across_experiment_bundles(tmp_path):
    plan = ExperimentPlan(kind='task_a_diagnostic', inputs=load_inputs()[-2:])
    ledger = tmp_path / 'task-ledger'
    first = Bundle.create(tmp_path / 'first', plan, task_ledger=ledger)
    second = Bundle.create(tmp_path / 'second', plan, task_ledger=ledger)
    for index in range(3):
        first.reserve(f'first-{index}', {})
    for index in range(2):
        second.reserve(f'second-{index}', {})
    with pytest.raises(BudgetExceeded):
        second.reserve('sixth', {})
    assert second.task_attempt_count == 5


def test_concurrent_execution_is_rejected_without_reserving_calls(tmp_path):
    bundle = Bundle.create(tmp_path / 'exclusive', ExperimentPlan(inputs=load_inputs()[-2:]))
    other = Bundle.open(bundle.path)
    with bundle.execution_lock():
        with pytest.raises(ValueError, match='Another process'):
            with other.execution_lock():
                pass
    assert bundle.attempt_count == 0


def test_resume_rejects_changed_code_without_making_calls(tmp_path, monkeypatch):
    from private_client_graph.research.runner import execute
    bundle = Bundle.create(tmp_path / 'versioned', ExperimentPlan(inputs=load_inputs()[-2:]))
    # An edited on-disk frozen manifest is independently rejected by the checksum test.
    bundle.manifest['provenance']['code'] = {'wrong': 'revision'}
    with pytest.raises(ValueError, match='Code changed'):
        execute(bundle, provider=lambda request: pytest.fail('No dispatch'))
    assert bundle.attempt_count == 0
