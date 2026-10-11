"""Repository-owned inputs and immutable offline plans. No caller-supplied Matter data."""
import json
import importlib.metadata
from pathlib import Path
from uuid import uuid4

from private_client_graph.research.artifacts import Bundle, checksum, write_json_once
from private_client_graph.research.fixtures import ROOT, load_inputs
from private_client_graph.research.plan import FiniteExperimentPlan
from private_client_graph.research.provider import ModelSettings
from .execution_contracts import Capabilities, FrozenPlan, InputChoice, Preview, Proposal


def capabilities() -> Capabilities:
    return Capabilities(inputs=[InputChoice(id=s.sample_id, case_id=s.case_id,
        cohort=s.cohort, hashes=s.origin_hashes) for s in load_inputs()])


def preview(proposal: Proposal) -> Preview:
    samples = {s.sample_id: s for s in load_inputs()}
    if len(set(proposal.input_ids)) != len(proposal.input_ids) or any(i not in samples for i in proposal.input_ids):
        raise ValueError('Select distinct repository-owned input identities')
    if proposal.input_mode == 'saved' and proposal.extraction_samples != 1:
        raise ValueError('Saved snapshots are fixed; extraction sample count applies only to fresh inputs')
    extractions = proposal.extraction_samples if proposal.input_mode == 'fresh' else 0
    count = extractions or len(proposal.input_ids)
    resolutions = count * proposal.resolver_repetitions if proposal.resolver == 'generative' else 0
    maximum = extractions + resolutions
    _finite_plan(proposal, 'offline-preview', maximum)
    if proposal.invocation_cap > maximum or (maximum and not proposal.invocation_cap):
        raise ValueError('Invocation cap must be positive and no greater than the matrix maximum')
    choices = {s.id: s for s in capabilities().inputs}
    return Preview(proposal=proposal, inputs=[choices[i] for i in proposal.input_ids],
        extraction_call_maximum=extractions, resolution_call_maximum=resolutions,
        matrix_call_maximum=maximum, planned_observations=count + resolutions,
        invocation_cap=proposal.invocation_cap)


def _finite_plan(proposal: Proposal, task_id: str, maximum: int) -> FiniteExperimentPlan:
    samples = {s.sample_id: s for s in load_inputs()}
    return FiniteExperimentPlan(task_id=task_id, inputs=[samples[i] for i in proposal.input_ids],
        input_mode=proposal.input_mode, execution_mode=proposal.execution_mode,
        resolver=proposal.resolver, repetitions=proposal.resolver_repetitions,
        fresh_extractions=proposal.extraction_samples if proposal.input_mode == 'fresh' else 0,
        settings=ModelSettings(model=proposal.model, temperature=proposal.temperature, timeout_seconds=proposal.timeout_seconds),
        max_calls=maximum, invocation_cap=proposal.invocation_cap)


def execution_code_digest() -> str:
    paths = sorted((ROOT / 'private_client_graph/workbench').glob('*.py'))
    return checksum(json.dumps({p.name: p.read_text() for p in paths}, sort_keys=True).encode())


def freeze(root: Path, proposal: Proposal) -> FrozenPlan:
    reviewed = preview(proposal)
    identity = uuid4().hex
    task_id = f'offline-{identity}'
    ledger = root.resolve() / 'task-ledgers' / task_id
    write_json_once(ledger / 'offline.json', {'task_id': task_id, 'paid_allowance': 0})
    bundle = Bundle.create(root / identity, _finite_plan(proposal, task_id, reviewed.matrix_call_maximum), task_ledger=ledger)
    records = json.loads((ROOT / 'research/fixtures/demonstration_responses.json').read_text())
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
    return frozen


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
    if authority['preview'] != frozen.preview.model_dump(mode='json'):
        raise ValueError('Frozen preview mismatch')
    if authority['dependencies'] != execution_dependencies():
        raise ValueError('Execution dependencies changed since freezing')
    if authority['bundle_path'] != str(path.resolve()):
        raise ValueError('Executable artifact relocation is unsafe')
    expected = root.resolve() / 'task-ledgers' / frozen.task_id
    if bundle.task_ledger != expected or expected.is_symlink():
        raise ValueError('Task ledger relocation is unsafe')
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
