"""Project frozen Benchmark v2 labels and Workbench Runs into a read-only JSON report."""
import argparse
from collections import Counter
from collections.abc import Sequence
import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator

from private_client_graph.models.evaluation_result import EvaluationResult
from private_client_graph.models.source import Source
from private_client_graph.research.artifacts import Bundle, checksum
from private_client_graph.research.benchmark_decisions import DecisionTargets, diagnose
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.metrics import estimate_cost
from private_client_graph.research.provider import TokenUsage
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.retained_inputs import input_digests, value_digest
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.workbench.run_evaluation import incurred_cost, retained_attempts
from private_client_graph.workbench.run_evaluation_contracts import AttemptCost, Coverage
from private_client_graph.workbench.run_inspection import read_run


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
    baseline_plan_digests: list[str] | None = None
    final_plan_digests: list[str] | None = None
    conditions: list[ConditionCommitment] = Field(min_length=1)

    @model_validator(mode='after')
    def verify_roster(self) -> 'ReportManifest':
        for field in ('condition', 'input_id'):
            if len({getattr(row, field) for row in self.conditions}) != len(self.conditions):
                raise ValueError(f'Study roster requires a unique {field} per condition')
        return self


class _Response(BaseModel):
    usage: TokenUsage = Field(default_factory=TokenUsage)
    returned_model: str | None = None
    raw_response: dict[str, Any] = Field(default_factory=dict)


class _Request(BaseModel):
    stage: str
    sources: list[Source] | None = None


class _Attempt(BaseModel):
    attempt_id: str
    status: str
    provider_seconds: FiniteFloat | None = Field(default=None, ge=0)
    response: _Response = Field(default_factory=_Response)
    request: _Request | None = None


@dataclass(frozen=True)
class _Run:
    plan: RunPlan
    provenance: dict[str, Any]
    results: dict[str, ResearchResult | None]
    states: dict[str, tuple[str, str, str | None]]
    attempts: dict[str, _Attempt]
    authority_reasons: list[str]
    code_hashes: dict[str, str]


def development_report(manifest: ReportManifest, baseline: Sequence[Path]) -> dict[str, Any]:
    """Report all planned baseline Observations, including missing Runs and unscored slots."""
    return {
        **_report_header(manifest),
        'baseline': _arm(manifest, baseline, 'baseline'),
    }


def final_report(manifest: ReportManifest, baseline: Sequence[Path], final: Sequence[Path]) -> dict[str, Any]:
    """Compare independent fresh Observations on each committed Matter family."""
    if any(row.observations != 1 for row in manifest.conditions) or (
        len({row.matter_family for row in manifest.conditions}) != len(manifest.conditions)
    ):
        raise ValueError('Final reporting requires one condition and Observation per Matter family in each arm')
    if manifest.execution_mode == 'live' and not (manifest.baseline_plan_digests and manifest.final_plan_digests):
        raise ValueError('Live final reporting requires the predeclared plan digests for both arms')
    left = _arm(manifest, baseline, 'baseline')
    right = _arm(manifest, final, 'final')
    if {row['run_id'] for row in left['runs']} & {row['run_id'] for row in right['runs']}:
        raise ValueError('Final arms must use independent Runs')
    pairs = [_pair(a, b) for a, b in zip(left['conditions'], right['conditions'], strict=True)]
    scored = [pair for pair in pairs if pair['delta'] is not None]
    return {
        **_report_header(manifest),
        'baseline': left,
        'final': right,
        'paired_coverage': {'planned': len(pairs), 'scored': len(scored)},
        'pairs': pairs,
        'paired_graph': {arm: _pool([pair[arm] for pair in scored])['graph'] for arm in ('baseline', 'final')},
    }


def _pair(baseline: dict[str, Any], final: dict[str, Any]) -> dict[str, Any]:
    left, right = baseline['observations'][0], final['observations'][0]
    reason = None
    if left['state'] != 'scored' or right['state'] != 'scored':
        reason = 'Both committed Observations must be scored.'
    elif not left['extraction_request_matches'] or not right['extraction_request_matches']:
        reason = 'Both fresh extraction requests must match the exact ordered Sources.'
    elif left['evaluator_digest'] != right['evaluator_digest'] or left['evaluator_digest'] is None:
        reason = 'Frozen evaluator implementations could not be matched.'
    return {
        'condition': baseline['condition'],
        'matter_family': baseline['matter_family'],
        'baseline': left,
        'final': right,
        'exclusion_reason': reason,
        'delta': _paired_delta(left, right) if reason is None else None,
    }


def _paired_delta(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    before, after = left['graph'], right['graph']
    resources_before, resources_after = left['resources'], right['resources']
    cost_before, cost_after = resources_before['cost'], resources_after['cost']
    currency = cost_before['currency'] if cost_before['currency'] == cost_after['currency'] else None
    return {
        'graph': {key: after[key] - before[key] for key in ('tp', 'fp', 'fn', 'f1', 'exact_graph')},
        'fp_fixed': sorted(set(before['false_positive_edges']) - set(after['false_positive_edges'])),
        'fp_regressed': sorted(set(after['false_positive_edges']) - set(before['false_positive_edges'])),
        'fn_fixed': sorted(set(before['false_negative_edges']) - set(after['false_negative_edges'])),
        'fn_regressed': sorted(set(after['false_negative_edges']) - set(before['false_negative_edges'])),
        **_evidence_delta(left, right),
        'tokens': {key: _difference(resources_before['tokens'][key]['total'], metric['total'])
                   for key, metric in resources_after['tokens'].items()},
        'provider_seconds': _difference(resources_before['provider_seconds']['total'],
                                        resources_after['provider_seconds']['total']),
        'cost': {'currency': currency,
                 'total': _difference(cost_before['total'], cost_after['total']) if currency else None},
        'fingerprints_changed': _fingerprint_change(resources_before, resources_after),
    }


def _evidence_delta(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    quote_before, quote_after = left['quote_provenance'], right['quote_provenance']
    source_before, source_after = left['source_attribution'], right['source_attribution']
    decisions_before, decisions_after = left['decisions'], right['decisions']
    sufficiency = None
    source_attribution = None
    if decisions_before is not None and decisions_after is not None:
        sufficiency = _evidence_change(decisions_before['sufficiency'], decisions_after['sufficiency'],
                                       'complete', 'accuracy')
    if source_before is not None and source_after is not None:
        source_attribution = {
            'passed': source_after['passed'] - source_before['passed'],
            'assessed': source_after['assessed'] - source_before['assessed'],
            'accuracy': _difference(source_before['accuracy'], source_after['accuracy']),
        }
    return {
        'quote_provenance': _evidence_change(quote_before, quote_after, 'passes', 'accuracy'),
        'source_attribution': source_attribution,
        'sufficiency': sufficiency,
    }


def _evidence_change(before: dict[str, Any], after: dict[str, Any], edges: str, accuracy: str) -> dict[str, Any]:
    return {
        f'{edges}_gained': sorted(set(after[edges]) - set(before[edges])),
        f'{edges}_lost': sorted(set(before[edges]) - set(after[edges])),
        'accuracy': _difference(before[accuracy], after[accuracy]),
        'assessed': after['assessed'] - before['assessed'],
    }


def _difference(before: int | float | None, after: int | float | None) -> int | float | None:
    if before is None or after is None:
        return None
    if isinstance(before, int) and isinstance(after, int):
        return after - before
    return float(Decimal(str(after)) - Decimal(str(before)))


def _fingerprint_change(before: dict[str, Any], after: dict[str, Any]) -> bool | None:
    left = {row['system_fingerprint'] for row in before['attempts']}
    right = {row['system_fingerprint'] for row in after['attempts']}
    return left != right if left and right and None not in left | right else None


def _report_header(manifest: ReportManifest) -> dict[str, Any]:
    return {
        'manifest_digest': value_digest(manifest.model_dump(mode='json')),
        'evaluator_version': manifest.evaluator_version,
        'execution_mode': manifest.execution_mode,
        'live_observations': manifest.execution_mode == 'live',
        'matter_families': len({row.matter_family for row in manifest.conditions}),
        'conditions': len(manifest.conditions),
    }


def _arm(manifest: ReportManifest, paths: Sequence[Path], arm: Literal['baseline', 'final']) -> dict[str, Any]:
    runs = [_read_run(path) for path in paths]
    if len({run.plan.run_id for run in runs}) != len(runs):
        raise ValueError('One arm cannot include a Run more than once')
    expected = {row.input_id for row in manifest.conditions}
    unexpected = [
        {'run_id': run.plan.run_id, 'input_id': sample.sample_id}
        for run in runs for sample in run.plan.inputs if sample.sample_id not in expected
    ]
    issues = {run.plan.run_id: _protocol_mismatch(run, manifest, arm) for run in runs}
    conditions = [_condition(row, runs, issues) for row in manifest.conditions]
    observations = [row for condition in conditions for row in condition['observations']]
    return {
        **_pool(observations),
        'conditions': conditions,
        'runs': [{**run.provenance, 'protocol_mismatch': issues[run.plan.run_id]} for run in runs],
        'unexpected_inputs': unexpected,
        'resources': _resources([(run, list(run.attempts.values())) for run in runs]),
    }


def _protocol_mismatch(run: _Run, manifest: ReportManifest, arm: Literal['baseline', 'final']) -> str | None:
    plan = run.plan
    if plan.execution_mode != manifest.execution_mode:
        return 'Execution mode differs from the study protocol.'
    if plan.evaluator_version != manifest.evaluator_version:
        return 'Evaluator version differs from the study protocol.'
    digests = manifest.baseline_plan_digests if arm == 'baseline' else manifest.final_plan_digests
    if digests is not None and run.provenance['plan_digest'] not in digests:
        return 'Run plan digest differs from the study protocol.'
    if manifest.execution_mode != 'live':
        return None
    if plan.input_mode != 'fresh':
        return 'Live study Observations require a fresh extraction.'
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


def _read_run(path: Path) -> _Run:
    bundle = Bundle.open(path)
    plan = bundle.plan
    if not isinstance(plan, RunPlan) or not plan.experiment_id or not plan.run_id:
        raise ValueError(f'Expected a frozen Workbench Run at {path}')
    detail = read_run(path.parent, plan.experiment_id, path.name)
    retained, reasons = retained_attempts(bundle)
    if retained != detail.attempts:
        raise ValueError(f'Run attempt records changed during inspection: {path}')
    records = [_Attempt.model_validate(row) for row in retained]
    attempts = {row.attempt_id: row for row in records}
    if len(attempts) != len(records):
        raise ValueError(f'Duplicate retained attempt identity in Run: {path}')
    coverage = detail.evaluation.aggregate.observations
    return _Run(
        plan=plan,
        provenance={
            'run_id': plan.run_id,
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
        code_hashes={path: checksum(contents.encode()) for path, contents in bundle.manifest['provenance']['code'].items()},
    )


def _condition(labels: ConditionCommitment, runs: list[_Run],
               protocol_issues: dict[str | None, str | None]) -> dict[str, Any]:
    observations: list[dict[str, Any]] = []
    for run in runs:
        sample = next((sample for sample in run.plan.inputs if sample.sample_id == labels.input_id), None)
        if sample is None:
            continue
        mismatch = protocol_issues[run.plan.run_id] or labels.mismatch(sample)
        observations.extend(_observe(run, slot.observation_id, slot.extraction_attempt_id, sample, labels, mismatch)
                            for slot in run.plan.planned_slots
                            if _template_id(slot.sample_id, slot.extraction_attempt_id) == sample.sample_id)

    exclusions = []
    if len(observations) > labels.observations:
        exclusions = observations
        observations = [_unavailable('The supplied Runs contain more slots than the study predeclared.')
                        for _ in range(labels.observations)]
    observations.extend(_unavailable('No supplied Run froze this planned study slot.')
                        for _ in range(labels.observations - len(observations)))
    return {
        'condition': labels.condition,
        'matter_family': labels.matter_family,
        'input_id': labels.input_id,
        'target_counts_per_observation': {name: len(getattr(labels.targets, name))
                                          for name in ('required', 'forbidden', 'unaffected', 'sufficiency')},
        **_pool(observations),
        'observations': observations,
        'excluded_observations': exclusions,
    }


def _template_id(sample_id: str, extraction_attempt_id: str | None) -> str:
    return sample_id.rsplit('_fresh_', 1)[0] if extraction_attempt_id else sample_id


def _unavailable(reason: str) -> dict[str, Any]:
    return {
        'state': 'unavailable', 'status': 'unavailable', 'reason': reason,
        'run_id': None, 'observation_id': None,
        'graph': None, 'quote_provenance': None, 'source_attribution': None,
        'decisions': None, 'resources': None,
    }


def _observe(run: _Run, observation_id: str, extraction_id: str | None, sample: ResearchInput,
             labels: ConditionCommitment, mismatch: str | None) -> dict[str, Any]:
    state, status, reason = run.states[observation_id]
    result = run.results[observation_id]
    attempts = [run.attempts[key] for key in (extraction_id, observation_id) if key in run.attempts]
    row = _unavailable(mismatch or reason or '')
    row.update(run_id=run.plan.run_id, observation_id=observation_id, status=status,
               resources=_resources([(run, attempts)]))
    if mismatch:
        return row
    extraction = run.attempts.get(extraction_id) if extraction_id else None
    request = extraction.request if extraction else None
    row.update(state=state, reason=reason,
               evaluator_digest=run.code_hashes.get('private_client_graph/evaluation.py'),
               extraction_request_matches=(request is not None and request.stage == 'extraction'
                                           and request.sources == sample.sources))
    if state == 'scored' and extraction_id and not row['extraction_request_matches']:
        row.update(state='unavailable', reason='The retained extraction request does not match the ordered Sources.')
        return row
    if state == 'scored' and result is not None and result.evaluation is not None:
        row.update(_scored_observation(result, result.evaluation, sample, labels.targets))
    return row


def _scored_observation(result: ResearchResult, score: EvaluationResult,
                        sample: ResearchInput, labels: DecisionTargets) -> dict[str, Any]:
    decisions = None
    results_sources_match = result.state is not None and result.state.sources == sample.sources
    if result.state is not None and results_sources_match:
        decisions = diagnose(result.state, sample.truth, labels)
        critical = set(decisions['required']['absent'])
        forbidden = set(decisions['forbidden']['present'])
        decisions.update(
            critical_omissions=sorted(critical),
            other_false_negatives=sorted(set(score.false_negative_edges) - critical),
            other_false_positives=sorted(set(score.false_positive_edges) - forbidden),
        )
        for group in ('required', 'forbidden', 'unaffected'):
            decisions[group]['present_count'] = len(decisions[group]['present'])
        decisions['sufficiency']['complete_count'] = len(decisions['sufficiency']['complete'])
    return {
        'graph': {
            'tp': score.tp, 'fp': score.fp, 'fn': score.fn, 'f1': score.f1,
            'exact_graph': score.fp == score.fn == 0,
            'true_positive_edges': score.true_positive_edges,
            'false_positive_edges': score.false_positive_edges,
            'false_negative_edges': score.false_negative_edges,
        },
        'quote_provenance': {
            'passed': score.provenance_passed, 'assessed': score.tp,
            'accuracy': score.provenance_accuracy,
            'passes': score.provenance_passes, 'failures': score.provenance_failures,
        },
        'source_attribution': result.source_attribution.model_dump()
                              if result.source_attribution and results_sources_match else None,
        'decisions': decisions,
        'decision_diagnostic_reason': None if decisions else 'No attached Evidence from the committed Sources.',
    }


def _pool(observations: list[dict[str, Any]]) -> dict[str, Any]:
    coverage = Coverage(planned=len(observations))
    for row in observations:
        state = row['state']
        setattr(coverage, state, getattr(coverage, state) + 1)
    scores = [row['graph'] for row in observations if row['state'] == 'scored']
    tp, fp, fn = (sum(score[key] for score in scores) for key in ('tp', 'fp', 'fn'))
    denominator = 2 * tp + fp + fn
    return {
        'coverage': coverage.model_dump(),
        'graph': {'tp': tp, 'fp': fp, 'fn': fn,
                  'f1': (2 * tp / denominator if denominator else 0.0) if scores else None,
                  'exact_graphs': sum(score['exact_graph'] for score in scores)},
    }


def _measurement(values: Sequence[int | float | None], authority_reasons: list[str]) -> dict[str, Any]:
    measured = [value for value in values if value is not None]
    subtotal = sum(measured)
    return {'known_subtotal': subtotal, 'measured_attempts': len(measured),
            'total': subtotal if len(measured) == len(values) and not authority_reasons else None}


def _resources(group: list[tuple[_Run, list[_Attempt]]]) -> dict[str, Any]:
    attempts = [(run, attempt) for run, records in group for attempt in records]
    reasons = sorted({reason for run, _ in group for reason in run.authority_reasons})
    costs = []
    for run, attempt in attempts:
        if run.plan.execution_mode == 'live':
            pricing = run.plan.pricing
            costs.append(AttemptCost(attempt_id=f'{run.plan.run_id}/{attempt.attempt_id}',
                                    cost=estimate_cost(attempt.response.usage, pricing),
                                    currency=pricing.currency if pricing else None))
    cost = incurred_cost(costs)
    if reasons:
        cost.total = None
        cost.reasons.extend(reasons)
    return {
        'retained_attempts': len(attempts),
        'authority_reasons': reasons,
        'tokens': {name: _measurement([getattr(attempt.response.usage, name) for _, attempt in attempts], reasons)
                   for name in ('input_tokens', 'output_tokens', 'cached_tokens')},
        'provider_seconds': _measurement([attempt.provider_seconds for _, attempt in attempts], reasons),
        'cost': cost.model_dump(),
        'attempts': [{
            'run_id': run.plan.run_id, 'id': attempt.attempt_id, 'status': attempt.status,
            'returned_model': attempt.response.returned_model,
            'system_fingerprint': attempt.response.raw_response.get('response_metadata', {}).get('system_fingerprint'),
        } for run, attempt in attempts],
    }


def _development_manifest(labels_path: Path, commitments_path: Path) -> ReportManifest:
    commitments = json.loads(commitments_path.read_text())
    labels = json.loads(labels_path.read_text())
    expected = [f'D{index}' for index in range(1, 15)]
    schedule = expected[:7] + ['D8', 'D9'] * 3 + expected[9:]
    if [row['condition'] for row in labels] != expected or commitments['baseline_schedule'] != schedule:
        raise ValueError('Development reporting requires the frozen D1–D14 roster and 18-slot schedule')
    counts = Counter(schedule)
    rows = {row['condition']: row for row in commitments['conditions']}
    fields = ('matter_family', 'case_id', 'source_digest', 'truth_digest', 'extraction_digest', 'annotation_digest')
    conditions = []
    for label in labels:
        key = label['condition']
        row = rows[key]
        if row['input_id'] != label['input_id']:
            raise ValueError(f'Committed input ID differs for {key}')
        conditions.append({**label, **{key: row[key] for key in fields}, 'observations': counts[key]})
    return ReportManifest.model_validate({'evaluator_version': 'semantic_edges_v1', 'conditions': conditions})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='phase', required=True)
    development = commands.add_parser('development', help='Report the 18-slot development baseline')
    development.add_argument('--commitments', required=True, type=Path, help='Retained preflight.json')
    development.add_argument('--labels', default=Path(__file__).with_name('development.json'), type=Path)
    final = commands.add_parser('final', help='Report the four held-out pairs after unsealing')
    final.add_argument('--commitments', required=True, type=Path, help='Private frozen final report manifest')
    final.add_argument('--final-run', action='append', type=Path, default=[])
    for command in (development, final):
        command.add_argument('--baseline-run', action='append', type=Path, default=[],
                             help='Frozen Workbench Run directory. Repeat for multiple Runs.')
    options = parser.parse_args()
    if options.phase == 'development':
        manifest = _development_manifest(options.labels, options.commitments)
        report = development_report(manifest, options.baseline_run)
    else:
        manifest = ReportManifest.model_validate_json(options.commitments.read_bytes())
        if len(manifest.conditions) != 4 or manifest.execution_mode != 'live':
            parser.error('The final protocol requires four conditions and live execution mode')
        report = final_report(manifest, options.baseline_run, options.final_run)
    print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
