"""Pure reads of immutable Run plans, slots, results and exact Evidence."""
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from private_client_graph.research.benchmark_v4_scoring import BenchmarkV4Summary
from private_client_graph.research.evidence_grounded import QualityProjection
from private_client_graph.research.benchmark_v4_operations import BenchmarkV4Operations
from private_client_graph.research.artifacts import Bundle, checksum
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.models.source import Source
from private_client_graph.research.case_metadata import CaseMetadata
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.research.tracing import trace_id
from .artifacts import artifact_digest, _verify_execution_binding
from .family_context import RunFamilyContext
from .contracts import RelationshipOutcome
from .evidence import relationship_outcomes
from .execution_contracts import FrozenPlan
from .run_evaluation import evaluate_run, retained_attempts
from .run_evaluation_contracts import RunEvaluation
from .benchmark_contracts import BenchmarkCondition, BenchmarkRun
from .workspaces import read_experiment


class RunObservation(BaseModel):
    id: str
    sample_id: str
    case_id: str
    configuration: str
    repetition: int
    status: str
    reason: str | None = None
    metadata: CaseMetadata | None = None
    source: str | None = None
    sources: list[Source] | None = None
    result: ResearchResult | None = None
    langfuse_trace_ids: list[str] = Field(default_factory=list)
    relationships: list[RelationshipOutcome] = Field(default_factory=list)
    benchmark: BenchmarkCondition | None = None


class RunDetail(BaseModel):
    api_version: Literal['2'] = '2'
    id: str
    experiment_id: str
    plan: FrozenPlan
    lifecycle: str
    evaluation: RunEvaluation
    family_context: RunFamilyContext | None = None
    benchmark: BenchmarkRun | None = None
    benchmark_v4: BenchmarkV4Summary | None = Field(default=None, exclude_if=lambda value: value is None,
        json_schema_extra={'x-typescript-optional': True})
    quality: QualityProjection | None = Field(default=None, exclude_if=lambda value: value is None,
        json_schema_extra={'x-typescript-optional': True})
    pipeline_usage: BenchmarkV4Operations | None = Field(default=None, exclude_if=lambda value: value is None,
        json_schema_extra={'x-typescript-optional': True})
    observations: list[RunObservation]
    provenance: dict[str, Any]
    artifact_digest: str
    authorized_invocations: list[str]
    attempts: list[dict[str, Any]]
    pricing: dict[str, Any] | None = None


def read_run(root: Path, experiment_id: str, identity: str) -> RunDetail:
    workspace = read_experiment(root, experiment_id)
    if identity not in workspace.run_ids:
        raise ValueError('Run does not belong to this Experiment')
    membership_path = root / 'experiments' / experiment_id / 'runs' / f'{identity}.json'
    if membership_path.exists():
        from .workspaces import read_record
        membership = read_record(membership_path)
        if membership.get('read_only_import'):
            from .benchmark_v3_import import read_imported_run
            return read_imported_run(root, experiment_id, identity)
    path = root / identity
    digest = artifact_digest(path)
    bundle = Bundle.open(path)
    if not isinstance(bundle.plan, RunPlan) or bundle.plan.experiment_id != experiment_id:
        raise ValueError('Run membership does not match its frozen plan')
    _verify_execution_binding(path)
    frozen = FrozenPlan.model_validate_json((path / 'execution.json').read_text())
    if frozen.id != identity or bundle.plan.run_id != identity or frozen.task_id != bundle.plan.task_id:
        raise ValueError('Frozen Run identity mismatch')
    lifecycle = [json.loads(p.read_text()) for p in (path / 'lifecycle').glob('*.json')]
    state = max(lifecycle, key=lambda item: item['at'])['state'] if lifecycle else 'frozen'
    provenance = {key: value for key, value in bundle.manifest['provenance'].items() if key != 'code'}
    provenance['code_digest'] = checksum(json.dumps(bundle.manifest['provenance']['code'], sort_keys=True).encode())
    evaluation = evaluate_run(bundle)
    result = RunDetail(id=identity, experiment_id=experiment_id, plan=frozen,
        lifecycle=state, evaluation=evaluation, observations=_observations(bundle, evaluation),
        provenance=provenance, artifact_digest=digest,
        authorized_invocations=[p.stem for p in sorted((path / 'authorizations').glob('*.json'))],
        attempts=retained_attempts(bundle)[0], pricing=bundle.plan.pricing.model_dump() if bundle.plan.pricing else None)
    if bundle.plan.benchmark_v4_sha256:
        from .benchmark_v4_inspection import attach_benchmark_v4
        attach_benchmark_v4(result, bundle)
    if artifact_digest(path) != digest:
        raise ValueError('Run artifacts changed during inspection; retry the read')
    return result


def _observations(bundle: Bundle, evaluation: RunEvaluation) -> list[RunObservation]:
    assert isinstance(bundle.plan, RunPlan)
    inputs = {sample.sample_id: sample for sample in bundle.plan.inputs}
    for path in (bundle.path / 'fresh_inputs').glob('*.json'):
        snapshot = ResearchInput.model_validate_json(path.read_text())
        if snapshot.sample_id in inputs:
            raise ValueError('Duplicate frozen input identity')
        inputs[snapshot.sample_id] = snapshot
    results = {(row['sample_id'], row['configuration'], row['repetition']): ResearchResult.model_validate(row)
               for row in bundle.results()}
    coverage = {item.observation_id: item for item in evaluation.aggregate.observations}
    observations = []
    for slot in bundle.plan.planned_slots:
        row = results.get((slot.sample_id, slot.configuration, slot.repetition))
        sample = inputs.get(slot.sample_id)
        paired = bundle.plan.benchmark_v4_sha256 and bundle.plan.retained_input_lineage
        template_id = slot.sample_id.rsplit('_fresh_', 1)[0] if slot.extraction_attempt_id or paired else slot.sample_id
        metadata = bundle.plan.case_metadata.get(template_id)
        template = inputs.get(template_id)
        source = sample.source if sample else template.source if template else None
        outcome = coverage.get(slot.observation_id)
        correlation_keys = (slot.observation_id, slot.extraction_attempt_id)
        trace_ids = [identity for key in correlation_keys if key and (identity := trace_id(bundle, key))]
        observations.append(RunObservation(id=slot.observation_id, sample_id=slot.sample_id,
            case_id=slot.case_id, configuration=slot.configuration, repetition=slot.repetition,
            status=outcome.status if outcome else row.status if row else 'not_attempted',
            reason=outcome.reason if outcome else 'Evaluation unavailable for this planned observation',
            metadata=metadata, source=source, result=row, langfuse_trace_ids=trace_ids,
            sources=row.state.sources if row and row.state is not None else None,
            relationships=relationship_outcomes(sample, row) if sample and row else []))
    return observations
