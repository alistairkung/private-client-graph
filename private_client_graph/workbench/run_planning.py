"""Resolve next-run drafts into immutable, single-configuration executable plans."""
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from private_client_graph.research.artifacts import Bundle, write_json_once
from .case_catalog import repository_inputs, frozen_case_metadata
from private_client_graph.research.provider import ModelSettings
from private_client_graph.research.run_plan import RunPlan
from .execution_contracts import FrozenPlan, InputChoice, Preview
from .planning import publish_plan, require_live
from .workspace_contracts import CopyRunDraft, DraftUpdate, FreezeRun, RunConfiguration, RunDraft
from .workspaces import experiment_path, read_experiment, save_draft, workspace_lock, read_record, write_record


def preview_run(configuration: RunConfiguration, root: Path) -> Preview:
    samples = {sample.sample_id: sample for sample in repository_inputs()}
    if len(set(configuration.input_ids)) != len(configuration.input_ids) or any(
            identity not in samples for identity in configuration.input_ids):
        raise ValueError('Select distinct repository-owned input identities')
    if configuration.input_mode == 'saved' and configuration.extraction_samples != 1:
        raise ValueError('Saved inputs have fixed extraction identities')
    budget = require_live(root) if configuration.execution_mode == 'live' else None
    if budget and configuration.task_call_cap < budget.cap:
        raise ValueError('Proposed task cap cannot reduce the existing allowance')
    extractions = len(configuration.input_ids) * configuration.extraction_samples if configuration.input_mode == 'fresh' else 0
    observations = extractions or len(configuration.input_ids)
    resolutions = observations * configuration.resolver_repetitions if configuration.resolver == 'generative' else 0
    maximum = extractions + resolutions
    reviewed = Preview(proposal=configuration,
        inputs=[InputChoice(id=samples[i].sample_id, case_id=samples[i].case_id,
            cohort=samples[i].cohort, hashes=samples[i].origin_hashes) for i in configuration.input_ids],
        extraction_call_maximum=extractions, resolution_call_maximum=resolutions,
        matrix_call_maximum=maximum, planned_observations=resolutions or observations,
        invocation_cap=configuration.invocation_cap)
    if budget:
        reviewed.task_id, reviewed.task_label = budget.task_id, budget.label
        reviewed.task_paid_usage, reviewed.task_paid_allowance = budget.used, budget.cap
        reviewed.task_paid_remaining = budget.remaining
        reviewed.cost_reason = 'Pricing is unavailable; live attempt costs remain explicitly unpriced.'
    _run_plan(configuration, reviewed.task_id or 'offline-preview', maximum)
    return reviewed


def _run_plan(configuration: RunConfiguration, task_id: str, maximum: int) -> RunPlan:
    samples = {sample.sample_id: sample for sample in repository_inputs()}
    inputs = [samples[i] for i in configuration.input_ids]
    return RunPlan(task_id=task_id, inputs=inputs, case_metadata=frozen_case_metadata(inputs),
        kind='live_experiment' if configuration.execution_mode == 'live' else 'demonstration',
        task_call_cap=configuration.task_call_cap, input_mode=configuration.input_mode,
        execution_mode=configuration.execution_mode, resolver=configuration.resolver,
        repetitions=configuration.resolver_repetitions,
        fresh_extractions=configuration.extraction_samples if configuration.input_mode == 'fresh' else 0,
        settings=ModelSettings(model=configuration.model, temperature=configuration.temperature,
                               timeout_seconds=configuration.timeout_seconds),
        max_calls=maximum, invocation_cap=configuration.invocation_cap)


def freeze_run(root: Path, experiment_id: str, command: FreezeRun) -> FrozenPlan:
    with workspace_lock(root):
        workspace = read_experiment(root, experiment_id)
        identity = uuid5(NAMESPACE_URL, f'pcg-run:{experiment_id}:{command.request_id}').hex
        membership = experiment_path(root, experiment_id) / 'runs' / f'{identity}.json'
        if membership.exists():
            from .artifacts import _verify_execution_binding
            _verify_execution_binding(root / identity)
            record = read_record(membership)
            if record['command'] != command.model_dump():
                raise ValueError('Idempotency key was already used for another Run')
            return FrozenPlan.model_validate_json((root / identity / 'execution.json').read_text())
        if workspace.draft.revision != command.expected_revision:
            raise ValueError('Draft revision changed; review the current draft')
        reviewed = preview_run(workspace.draft.configuration, root)
        if (root / identity).exists():
            from .artifacts import _verify_execution_binding
            _verify_execution_binding(root / identity)
            retained = Bundle.open(root / identity)
            if not isinstance(retained.plan, RunPlan) or retained.plan.experiment_id != experiment_id or retained.plan.draft_revision != command.expected_revision:
                raise ValueError('Interrupted publication does not match the requested Run')
            frozen = FrozenPlan.model_validate_json((root / identity / 'execution.json').read_text())
        else:
            plan = _run_plan(workspace.draft.configuration, reviewed.task_id or f'offline-{identity}', reviewed.matrix_call_maximum)
            plan.experiment_id = experiment_id
            plan.run_id = identity
            plan.draft_revision = workspace.draft.revision
            frozen = publish_plan(root, identity, plan, reviewed)
        write_record(membership, {'run_id': identity, 'experiment_id': experiment_id,
            'created_at': frozen.created_at, 'command': command.model_dump(),
            'draft_revision': workspace.draft.revision, 'plan_digest': frozen.digest})
        return frozen


def copy_run_draft(root: Path, experiment_id: str, command: CopyRunDraft) -> RunDraft:
    with workspace_lock(root):
        workspace = read_experiment(root, experiment_id)
        if command.run_id not in workspace.run_ids:
            raise ValueError('Run does not belong to this Experiment')
        # Read the immutable plan; do not validate current execution authority or copy it.
        Bundle.open(root / command.run_id)
        frozen = FrozenPlan.model_validate_json((root / command.run_id / 'execution.json').read_text())
        configuration = RunConfiguration.model_validate(frozen.preview.proposal.model_dump())
        return save_draft(root, experiment_id, DraftUpdate(request_id=command.request_id,
            expected_revision=command.expected_revision, configuration=configuration), copied_from=command.run_id)
