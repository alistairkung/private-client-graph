"""Repository-owned inputs and immutable finite plans. No caller-supplied Matter data."""
import json
import os
import importlib.metadata
from pathlib import Path
from uuid import uuid4

from private_client_graph.research.artifacts import Bundle, checksum, write_json_once
from private_client_graph.research.fixtures import ROOT, load_inputs
from private_client_graph.research.plan import FiniteExperimentPlan
from private_client_graph.research.provider import ModelSettings, ModelRequest
from private_client_graph.research.demo import recording_key
from .execution_contracts import Capabilities, FrozenPlan, InputChoice, Preview, Proposal, TaskBudget
from private_client_graph.research.live_accounting import read_task, task_state


def live_budget(root: Path) -> TaskBudget:
    task = read_task(root)
    state = task_state(Path(task['ledger']))
    return TaskBudget(**state, remaining=max(0, state['cap'] - state['used']))


def require_live(root: Path) -> TaskBudget:
    if os.getenv('PCG_RESEARCH_LIVE_ENABLED') != '1':
        raise ValueError('Local live capability is disabled')
    return live_budget(root)


def capabilities(root: Path | None = None) -> Capabilities:
    result = Capabilities(inputs=[InputChoice(id=s.sample_id, case_id=s.case_id,
        cohort=s.cohort, hashes=s.origin_hashes) for s in load_inputs()])
    if root is not None and os.getenv('PCG_RESEARCH_LIVE_ENABLED') == '1':
        try:
            result.live_task = require_live(root)
            result.live_enabled = True
            result.live_reason = 'Live calls require approval of each frozen invocation.'
            result.provider = 'DeepSeek; explicit live approval or recorded responses'
        except (OSError, ValueError, KeyError):
            result.live_reason = 'Live task accounting unavailable. Restore or explicitly provision the local task.'
    return result


def preview(proposal: Proposal, root: Path | None = None) -> Preview:
    if proposal.retained_run_id or proposal.retained_experiment_id:
        raise ValueError('Retained inputs require Experiment Run planning')
    budget = None
    if proposal.execution_mode == 'live':
        if root is None:
            raise ValueError('Local live capability is disabled')
        budget = require_live(root)
        if proposal.task_call_cap < budget.cap or proposal.task_call_cap < budget.used:
            raise ValueError('Proposed task cap cannot reduce the existing task allowance or usage')
    samples = {s.sample_id: s for s in load_inputs()}
    if len(set(proposal.input_ids)) != len(proposal.input_ids) or any(i not in samples for i in proposal.input_ids):
        raise ValueError('Select distinct repository-owned input identities')
    if proposal.input_mode == 'saved' and proposal.extraction_samples != 1:
        raise ValueError('Saved snapshots are fixed; extraction sample count applies only to fresh inputs')
    extractions = proposal.extraction_samples if proposal.input_mode == 'fresh' else 0
    count = extractions or len(proposal.input_ids)
    resolutions = count * proposal.resolver_repetitions if proposal.resolver == 'generative' else 0
    maximum = extractions + resolutions
    _finite_plan(proposal, budget.task_id if budget else 'offline-preview', maximum)
    if proposal.invocation_cap > maximum or (maximum and not proposal.invocation_cap):
        raise ValueError('Invocation cap must be positive and no greater than the matrix maximum')
    choices = {s.id: s for s in capabilities().inputs}
    result = Preview(proposal=proposal, inputs=[choices[i] for i in proposal.input_ids],
        extraction_call_maximum=extractions, resolution_call_maximum=resolutions,
        matrix_call_maximum=maximum, planned_observations=count + resolutions,
        invocation_cap=proposal.invocation_cap)
    if budget:
        result.task_id, result.task_label = budget.task_id, budget.label
        result.task_paid_usage, result.task_paid_allowance = budget.used, budget.cap
        result.task_paid_remaining = budget.remaining
        result.cost_reason = ('USD estimate unavailable: no verified current pricing is frozen. '
            'Requested model: deepseek-flash; returned model and token usage are recorded when supplied. '
            'A call cap is not a guaranteed dollar cap.')
    return result


def _finite_plan(proposal: Proposal, task_id: str, maximum: int) -> FiniteExperimentPlan:
    samples = {s.sample_id: s for s in load_inputs()}
    return FiniteExperimentPlan(task_id=task_id,
        plan_version=3 if proposal.execution_mode == 'live' else 2,
        kind='live_experiment' if proposal.execution_mode == 'live' else 'demonstration',
        task_call_cap=proposal.task_call_cap, inputs=[samples[i] for i in proposal.input_ids],
        input_mode=proposal.input_mode, execution_mode=proposal.execution_mode,
        resolver=proposal.resolver, repetitions=proposal.resolver_repetitions,
        fresh_extractions=proposal.extraction_samples if proposal.input_mode == 'fresh' else 0,
        settings=ModelSettings(model=proposal.model, temperature=proposal.temperature, timeout_seconds=proposal.timeout_seconds),
        max_calls=maximum, invocation_cap=proposal.invocation_cap)


def execution_code_digest() -> str:
    paths = sorted((ROOT / 'private_client_graph/workbench').glob('*.py'))
    return checksum(json.dumps({p.name: p.read_text() for p in paths}, sort_keys=True).encode())


def freeze(root: Path, proposal: Proposal) -> FrozenPlan:
    reviewed = preview(proposal, root)
    identity = uuid4().hex
    task_id = reviewed.task_id or f'offline-{identity}'
    return publish_plan(root, identity, _finite_plan(proposal, task_id, reviewed.matrix_call_maximum), reviewed)


def publish_plan(root: Path, identity: str, plan: FiniteExperimentPlan, reviewed: Preview) -> FrozenPlan:
    task_id = plan.task_id
    ledger = root.resolve() / 'task-ledgers' / task_id
    if plan.execution_mode != 'live':
        write_json_once(ledger / 'offline.json', {'task_id': task_id, 'paid_allowance': 0})
    bundle = Bundle.create(root / identity, plan, task_ledger=ledger)
    records = json.loads((ROOT / 'research/fixtures/demonstration_responses.json').read_text())
    if getattr(plan, 'plan_version', 0) == 4:
        for sample in plan.inputs:
            key = recording_key(ModelRequest(stage='extraction', source=sample.source, sources=sample.sources,
                                             settings=plan.settings))
            extraction = sample.sourced_extraction if sample.sources is not None else sample.extraction
            assert extraction is not None
            records.setdefault('extraction', {}).setdefault(key, extraction.model_dump(mode='json'))
    write_json_once(bundle.path / 'recorded-responses.json', records)
    binding = {
        'recordings_digest': checksum((bundle.path / 'recorded-responses.json').read_bytes()),
        'bundle_path': str(bundle.path.resolve()),
        'execution_code_digest': execution_code_digest(),
        'dependencies': execution_dependencies(),
        'preview': reviewed.model_dump(mode='json'),
    }
    write_json_once(bundle.path / 'execution-binding.json', binding)
    frozen = FrozenPlan(id=identity, digest=_plan_digest(bundle.path),
        task_id=task_id, preview=reviewed, created_at=bundle.manifest['created_at'])
    write_json_once(bundle.path / 'execution.json', frozen.model_dump(mode='json'))
    return FrozenPlan.model_validate_json((bundle.path / 'execution.json').read_text())


def open_executable(root: Path, identity: str) -> tuple[Bundle, FrozenPlan]:
    if len(identity) != 32 or any(c not in '0123456789abcdef' for c in identity):
        raise ValueError('Unknown executable plan')
    path = root / identity
    if path.is_symlink():
        raise ValueError('Executable artifacts cannot be symlinks')
    bundle = Bundle.open(path)
    if not isinstance(bundle.plan, FiniteExperimentPlan):
        raise ValueError('Historical imports do not confer execution authority')
    authority = json.loads((path / 'execution-binding.json').read_text())
    frozen = FrozenPlan.model_validate_json((path / 'execution.json').read_text())
    if frozen.task_id != bundle.plan.task_id or frozen.preview.invocation_cap != bundle.plan.invocation_cap:
        raise ValueError('Frozen accounting or invocation cap mismatch')
    if frozen.id != identity or frozen.digest != _plan_digest(path):
        raise ValueError('Frozen plan digest mismatch')
    if Preview.model_validate(authority['preview']) != frozen.preview:
        raise ValueError('Frozen preview mismatch')
    if authority['dependencies'] != execution_dependencies():
        raise ValueError('Execution dependencies changed since freezing')
    if authority['bundle_path'] != str(path.resolve()):
        raise ValueError('Executable artifact relocation is unsafe')
    expected = root.resolve() / 'task-ledgers' / frozen.task_id
    if bundle.task_ledger != expected or expected.is_symlink():
        raise ValueError('Task ledger relocation is unsafe')
    if bundle.plan.kind == 'live_experiment':
        if live_budget(root).task_id != frozen.task_id:
            raise ValueError('Live task identity mismatch')
    else:
        ledger = json.loads((expected / 'offline.json').read_text())
        if ledger != {'task_id': frozen.task_id, 'paid_allowance': 0}:
            raise ValueError('Missing or mismatched offline accounting')
    if authority['recordings_digest'] != checksum((path / 'recorded-responses.json').read_bytes()):
        raise ValueError('Recorded provider responses changed since freezing')
    if authority['execution_code_digest'] != execution_code_digest():
        raise ValueError('Execution code changed since the plan was frozen')
    return bundle, frozen


def _plan_digest(path: Path) -> str:
    return checksum((path / 'manifest.json').read_bytes() + (path / 'execution-binding.json').read_bytes())


def execution_dependencies() -> dict[str, str]:
    return {name: importlib.metadata.version(name) for name in ('fastapi', 'starlette', 'sqlalchemy', 'psycopg', 'uvicorn')}
