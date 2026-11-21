"""Admission and chronology checks for frozen Benchmark v2 Workbench Runs."""
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from itertools import combinations
import json
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from private_client_graph.models.source import Source
from private_client_graph.research.artifacts import Bundle, checksum
from private_client_graph.research.benchmark_decisions import DecisionTargets
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.provider import TokenUsage
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.retained_inputs import input_digests, value_digest
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.workbench.run_evaluation import retained_attempts
from private_client_graph.workbench.run_inspection import read_run


_PlanDigest = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]


class ConditionLabels(BaseModel):
    model_config = ConfigDict(extra='forbid')
    condition: str = Field(min_length=1)
    input_id: str = Field(min_length=1)
    targets: DecisionTargets


class ConditionCommitment(ConditionLabels):
    matter_family: str = Field(min_length=1)
    case_id: str = Field(min_length=1)
    observations: int = Field(ge=1)
    source_digest: str = Field(pattern=r'^[a-f0-9]{64}$')
    truth_digest: str = Field(pattern=r'^[a-f0-9]{64}$')
    extraction_digest: str = Field(pattern=r'^[a-f0-9]{64}$')
    annotation_digest: str = Field(pattern=r'^[a-f0-9]{64}$')

    @model_validator(mode='after')
    def verify_annotation(self) -> 'ConditionCommitment':
        labels = self.model_dump(mode='json', include={'condition', 'input_id', 'targets'})
        if value_digest(labels) != self.annotation_digest:
            raise ValueError(f'Annotation digest mismatch for {self.condition}')
        return self

    def mismatch(self, sample: ResearchInput) -> str | None:
        if sample.case_id != self.case_id or not sample.sources:
            return 'Case identity or explicit Sources differ from the study commitment.'
        differences = [kind for kind, digest in input_digests(sample).items() if getattr(self, kind) != digest]
        return f'Study commitment differs: {", ".join(differences)}.' if differences else None


class ReportManifest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    evaluator_version: str = Field(min_length=1)
    execution_mode: Literal['live', 'recorded', 'replay'] = 'live'
    baseline_plan_digests: list[_PlanDigest] | None = None
    final_plan_digests: list[_PlanDigest] | None = None
    final_attempt_cap: int = Field(default=8, ge=1)
    development_batches: list[list[str]] | None = None
    conditions: list[ConditionCommitment] = Field(min_length=1)

    @model_validator(mode='after')
    def verify_roster(self) -> 'ReportManifest':
        for field in ('condition', 'input_id'):
            if len({getattr(row, field) for row in self.conditions}) != len(self.conditions):
                raise ValueError(f'Study roster requires a unique {field} per condition')
        for digests in (self.baseline_plan_digests, self.final_plan_digests):
            if digests is not None and len(set(digests)) != len(digests):
                raise ValueError('Study Run plan digests must be unique within each arm')
        return self


class _Response(BaseModel):
    usage: TokenUsage = Field(default_factory=TokenUsage)
    returned_model: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class _Request(BaseModel):
    stage: str
    sources: list[Source] | None = None


class RetainedAttempt(BaseModel):
    attempt_id: str
    status: str
    started_at: AwareDatetime | None = None
    provider_seconds: FiniteFloat | None = Field(default=None, ge=0)
    response: _Response = Field(default_factory=_Response)
    request: _Request | None = None


@dataclass(frozen=True)
class RunRecord:
    plan: RunPlan
    provenance: dict[str, Any]
    results: dict[str, ResearchResult | None]
    states: dict[str, tuple[str, str, str | None]]
    attempts: dict[str, RetainedAttempt]
    authority_reasons: list[str]
    code_hashes: dict[str, str]
    task_ledger: Path


def open_run(path: Path) -> RunRecord:
    bundle = Bundle.open(path)
    plan = bundle.plan
    if not isinstance(plan, RunPlan) or not plan.experiment_id or not plan.run_id:
        raise ValueError(f'Expected a frozen Workbench Run at {path}')
    detail = read_run(path.parent, plan.experiment_id, path.name)
    retained, reasons = retained_attempts(bundle)
    if retained != detail.attempts:
        raise ValueError(f'Run attempt records changed during inspection: {path}')
    records = [RetainedAttempt.model_validate(row) for row in retained]
    attempts = {row.attempt_id: row for row in records}
    if len(attempts) != len(records):
        raise ValueError(f'Duplicate retained attempt identity in Run: {path}')
    coverage = detail.evaluation.aggregate.observations
    return RunRecord(
        plan=plan,
        provenance={
            'run_id': plan.run_id,
            'task_id': plan.task_id,
            'task_call_cap': plan.task_call_cap,
            'max_calls': plan.max_calls,
            'invocation_cap': plan.invocation_cap,
            'plan_digest': detail.plan.digest,
            'artifact_digest': detail.artifact_digest,
            'lifecycle': detail.lifecycle,
            'execution_mode': plan.execution_mode,
            'input_mode': plan.input_mode,
            'resolver': plan.resolver,
            'evaluator_version': plan.evaluator_version,
            'effective_model': plan.effective_model or plan.settings.model,
            'settings': plan.settings.model_dump(mode='json'),
            'pricing': detail.pricing,
            'code': {key: detail.provenance[key] for key in ('git_sha', 'dirty', 'code_digest',
                                                            'dependencies', 'prompt_hashes')},
        },
        results={row.id: row.result for row in detail.observations},
        states={row.observation_id: (row.state, row.status, row.reason) for row in coverage},
        attempts=attempts,
        authority_reasons=reasons,
        task_ledger=bundle.task_ledger.resolve(),
        code_hashes={path: checksum(contents.encode()) for path, contents in bundle.manifest['provenance']['code'].items()},
    )


def development_batches(manifest: ReportManifest, *, require_approval: bool) -> dict[str, list[str]]:
    by_condition = {row.condition: row for row in manifest.conditions}
    batches = manifest.development_batches
    if batches is None or any(not batch or len(set(batch)) != len(batch) for batch in batches) or (
        Counter(condition for batch in batches for condition in batch)
        != {condition: row.observations for condition, row in by_condition.items()}
    ):
        raise ValueError('Live development reporting requires the committed batch order and allocations')
    digests = manifest.baseline_plan_digests
    if not digests and not require_approval:
        return {}
    if digests is None or len(digests) != len(batches):
        raise ValueError('Live development reporting requires an approved Run plan digest for each batch')
    return {digest: [by_condition[condition].input_id for condition in batch]
            for digest, batch in zip(digests, batches, strict=True)}


def inspect_protocol(
    manifest: ReportManifest, runs: list[RunRecord], arm: Literal['baseline', 'final'],
    batches: dict[str, list[str]] | None, task_issue: str | None,
) -> tuple[dict[str | None, str | None], dict[str, Any] | None]:
    issues = {run.plan.run_id: _protocol_mismatch(run, manifest, arm) or task_issue for run in runs}
    chronology = None
    if batches is not None:
        task_cap = sum(row.observations for row in manifest.conditions)
        for run in runs:
            if issues[run.plan.run_id] is None:
                inputs = batches[run.provenance['plan_digest']]
                issues[run.plan.run_id] = _batch_mismatch(run, inputs, task_cap)
        admitted = [run for run in runs if issues[run.plan.run_id] is None]
        if mismatch := shared_task_mismatch(admitted):
            for run in admitted:
                issues[run.plan.run_id] = mismatch
            admitted = []
        chronology = _batch_chronology(batches, admitted)
    return issues, chronology


def shared_task_mismatch(runs: list[RunRecord]) -> str | None:
    if len({(run.plan.task_id, run.task_ledger) for run in runs}) > 1:
        return 'Approved Runs do not share one task identity and authoritative ledger.'
    if len({run.plan.task_call_cap for run in runs}) > 1:
        return 'Approved Runs declare different shared task call caps.'
    if runs and sum(run.plan.max_calls for run in runs) > runs[0].plan.task_call_cap:
        return 'Supplied approved matrices exceed the shared task call cap.'
    return None


def _protocol_mismatch(run: RunRecord, manifest: ReportManifest, arm: Literal['baseline', 'final']) -> str | None:
    plan = run.plan
    if plan.execution_mode != manifest.execution_mode:
        return 'Execution mode differs from the study protocol.'
    if plan.evaluator_version != manifest.evaluator_version:
        return 'Evaluator version differs from the study protocol.'
    digests = manifest.baseline_plan_digests if arm == 'baseline' else manifest.final_plan_digests
    if digests is not None and run.provenance['plan_digest'] not in digests:
        return 'Run plan digest differs from the study protocol.'
    expected = {row.input_id: row for row in manifest.conditions}
    if any(sample.sample_id not in expected for sample in plan.inputs):
        return 'Run contains an input outside the committed roster.'
    for sample in plan.inputs:
        if mismatch := expected[sample.sample_id].mismatch(sample):
            return mismatch
    if manifest.execution_mode != 'live':
        return None
    if plan.input_mode != 'fresh':
        return 'Live study Observations require a fresh extraction.'
    allowed_attempts = {slot.extraction_attempt_id for slot in plan.planned_slots}
    if plan.resolver == 'generative':
        allowed_attempts.update(slot.observation_id for slot in plan.planned_slots)
    if set(run.attempts) - allowed_attempts:
        return 'Run contains an attempt outside its committed call allocation.'
    if arm == 'final':
        return None
    pin = json.loads(Path(__file__).with_name('baseline.json').read_text())
    if plan.resolver != 'none' or (plan.effective_model or plan.settings.model) != 'deepseek-flash':
        return 'Live baseline requires full context, no resolver and the pinned model.'
    if (value_digest(plan.settings.model_dump()) != pin['settings']
            or run.provenance['code']['prompt_hashes']['sourced_extraction'] != pin['prompt']):
        return 'Run settings or sourced prompt differ from the live baseline pin.'
    if run.provenance['code']['dependencies'] != pin['dependencies']:
        return 'Recorded dependencies differ from the baseline Run.'
    if any(run.code_hashes.get(path) != expected for path, expected in pin['files'].items() if path != 'uv.lock'):
        return 'Run code snapshot differs from the live baseline pin.'
    return None


def _batch_mismatch(run: RunRecord, inputs: list[str], task_cap: int) -> str | None:
    plan = run.plan
    if [sample.sample_id for sample in plan.inputs] != inputs:
        return 'Run does not match its committed ordered input group.'
    if plan.fresh_extractions != 1 or plan.max_calls != len(inputs) or plan.invocation_cap != len(inputs):
        return 'Run differs from the committed fresh Observation allocation or call caps.'
    if plan.task_call_cap != task_cap:
        return 'Shared task call cap differs from the committed development cap.'
    return None


def _batch_chronology(batches: dict[str, list[str]], admitted: list[RunRecord]) -> dict[str, Any]:
    runs = {run.provenance['plan_digest']: run for run in admitted}
    events: list[tuple[str, str | None]] = []
    for digest, inputs in batches.items():
        run = runs.get(digest)
        if run is None:
            events.extend((f'{digest}/{input_id}', None) for input_id in inputs)
            continue
        for slot in run.plan.planned_slots:
            attempt = run.attempts.get(slot.extraction_attempt_id) if slot.extraction_attempt_id else None
            started = attempt.started_at.isoformat() if attempt and attempt.started_at else None
            events.append((f'{run.plan.run_id}/{slot.observation_id}', started))
    return compare_chronology(events)


def compare_chronology(events: list[tuple[str, str | None]]) -> dict[str, Any]:
    observed = [(key, datetime.fromisoformat(start)) for key, start in events if start is not None]
    deviations = [[left, right] for (left, before), (right, after) in combinations(observed, 2) if before > after]
    verified = bool(events) and len(observed) == len(events) and len({time for _, time in observed}) == len(events)
    return {
        'state': 'deviation' if deviations else 'verified' if verified else 'partial',
        'expected_order': [key for key, _ in events],
        'observed_start_order': [key for key, _ in sorted(observed, key=lambda event: event[1])],
        'deviations': deviations,
    }
