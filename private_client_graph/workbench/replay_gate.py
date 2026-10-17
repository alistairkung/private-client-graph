"""Require an exact zero-call replay before authorizing retained resolver treatment."""
import json

from private_client_graph.research.artifacts import Bundle, write_json_once
from private_client_graph.research.retained_inputs import value_digest
from private_client_graph.research.run_plan import RunPlan
from .artifacts import artifact_digest
from .retained_inputs import load_retained_inputs
from .run_evaluation import evaluate_run
from .run_inspection import read_run
from .workspaces import read_experiment


SEMANTIC_FIELDS = ('case_id', 'status', 'stage', 'graph', 'state', 'sourced_extraction',
                   'source_attribution', 'evaluation', 'identity', 'extraction', 'error_type')


def require_replay_control(bundle: Bundle, invocation: str) -> str | None:
    """Bind approval to verified original/control artifacts; never execute a Run."""
    plan = bundle.plan
    if not isinstance(plan, RunPlan) or plan.retained_input_lineage is None or plan.resolver != 'generative':
        return None
    root, lineage = bundle.path.parent, plan.retained_input_lineage
    inputs, _, verified = load_retained_inputs(root, lineage.experiment_id, lineage.run_id)
    original = Bundle.open(root / lineage.run_id)
    if not isinstance(original.plan, RunPlan):
        raise ValueError('Retained original must be a verified Run')
    if (verified != lineage or plan.inputs != inputs or plan.experiment_id != lineage.experiment_id
            or plan.input_mode != 'saved' or plan.repetitions != 1
            or plan.settings != original.plan.settings or plan.effective_model != original.plan.effective_model
            or plan.task_id != original.plan.task_id or bundle.task_ledger != original.task_ledger
            or plan.evaluator_version != original.plan.evaluator_version
            or plan.aggregate_version != original.plan.aggregate_version):
        raise ValueError('Retained treatment differs from the frozen original inputs, settings or task authority')
    expected = _completed_projection(original)
    path = bundle.path / 'replay-gates' / f'{invocation}.json'
    retained = json.loads(path.read_text()) if path.exists() else None
    candidates = ([retained['control_run_id']] if retained else
        sorted(read_experiment(root, lineage.experiment_id).run_ids))
    for identity in candidates:
        if identity in (lineage.run_id, plan.run_id):
            continue
        try:
            record = _control_record(bundle, identity, invocation, expected)
        except (OSError, ValueError, KeyError, TypeError):
            if retained is not None:
                raise
            # Unrelated damaged or incomplete Runs cannot prevent a valid control.
            continue
        if record is None:
            continue
        if retained is not None and retained != record:
            raise ValueError('Replay control evidence changed after authorization')
        if retained is None:
            write_json_once(path, record)
        return value_digest(record)
    raise ValueError('A completed exact zero-call replay control is required before resolver authorization')


def _control_record(treatment: Bundle, identity: str, invocation: str,
                    expected: dict[str, dict]) -> dict | None:
    plan = treatment.plan
    assert isinstance(plan, RunPlan) and plan.retained_input_lineage is not None
    lineage = plan.retained_input_lineage
    root = treatment.path.parent
    control = Bundle.open(root / identity)
    candidate = control.plan
    if (not isinstance(candidate, RunPlan) or candidate.retained_input_lineage != lineage
            or candidate.experiment_id != plan.experiment_id or candidate.input_mode != 'saved'
            or candidate.execution_mode != 'replay' or candidate.resolver != 'none'
            or candidate.inputs != plan.inputs or candidate.settings != plan.settings
            or candidate.effective_model != plan.effective_model
            or candidate.evaluator_version != plan.evaluator_version
            or candidate.aggregate_version != plan.aggregate_version):
        return None
    detail = read_run(root, lineage.experiment_id, identity)
    if detail.lifecycle != 'complete' or control.attempt_count or control.attempts():
        return None
    if _completed_projection(control) != expected:
        return None
    return {'version': 1, 'invocation_id': invocation, 'treatment_run_id': plan.run_id,
        'original_run_id': lineage.run_id, 'original_plan_digest': lineage.plan_digest,
        'original_artifact_digest': lineage.artifact_digest, 'control_run_id': identity,
        'control_plan_digest': detail.plan.digest, 'control_artifact_digest': artifact_digest(control.path),
        'semantic_result_digest': value_digest(expected), 'matched_samples': len(expected)}


def _completed_projection(bundle: Bundle) -> dict[str, dict]:
    plan = bundle.plan
    if not isinstance(plan, RunPlan) or plan.resolver != 'none' or plan.repetitions != 1:
        raise ValueError('Replay control requires one no-resolution observation per original sample')
    evaluation = evaluate_run(bundle)
    results = bundle.results()
    samples = {slot.sample_id for slot in plan.planned_slots}
    if (evaluation.aggregate.state != 'complete' or len(samples) != len(plan.planned_slots)
            or len(results) != len(samples) or {row['sample_id'] for row in results} != samples):
        raise ValueError('Replay control requires complete scored original sample coverage')
    return {row['sample_id']: {field: row.get(field) for field in SEMANTIC_FIELDS} for row in results}
