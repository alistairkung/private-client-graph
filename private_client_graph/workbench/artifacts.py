"""Read historical schema-1 bundles without locks, writes, or ledger relocation."""
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.plan import FiniteExperimentPlan
from private_client_graph.research.summary import summarize

from .execution_contracts import FrozenPlan, Preview
from .contracts import CohortMetric, CohortSummary, ExperimentDetail, HistoryItem, Observation, Sample
from .evidence import digest_text, relationship_outcomes


def artifact_digest(path: Path) -> str:
    """Fingerprint all retained files, excluding transient hidden lock files."""
    entries = []
    for file in sorted(path.rglob('*')):
        relative = file.relative_to(path)
        if any(part.startswith('.') for part in relative.parts):
            continue
        if file.is_symlink():
            raise ValueError('Symlinks are not supported in research artifacts')
        if file.is_file():
            entries.append((relative.as_posix(), hashlib.sha256(file.read_bytes()).hexdigest()))
    return digest_text(json.dumps(entries))


def read_artifact(path: Path, relative_path: str) -> ExperimentDetail:
    history = HistoryItem(id=digest_text(relative_path), artifact_path=relative_path, digest="")
    try:
        if path.is_symlink():
            raise ValueError('Symlink artifact directories are not supported')
        history.digest = artifact_digest(path)
        manifest = json.loads((path / 'manifest.json').read_text())
        if not isinstance(manifest, dict):
            raise ValueError('Manifest must be a JSON object')
        history.experiment_id = str(manifest.get('experiment_id', '')) or None
        version = manifest.get('schema_version')
        history.artifact_version = version if type(version) is int else None
        history.created_at = manifest.get('created_at') if isinstance(manifest.get('created_at'), str) else None
        if history.artifact_version not in (1, 2, 3):
            history.integrity = 'unsupported'
            history.integrity_reason = f'Unsupported artifact version: {history.artifact_version}'
            return ExperimentDetail(history=history)
        _verify_export_checksums(path)
        bundle = Bundle.open(path)
        if history.artifact_version in (2, 3):
            _verify_execution_binding(path)
        detail = _project_bundle(bundle, history)
        if artifact_digest(path) != history.digest:
            raise ValueError('Artifacts changed during indexing; rerun after writes finish')
        return detail
    except (ValueError, OSError, KeyError, TypeError) as error:
        history.integrity = 'missing' if isinstance(error, FileNotFoundError) else 'corrupt'
        history.integrity_reason = str(error)
        return ExperimentDetail(history=history)


def _verify_export_checksums(path: Path) -> None:
    checksum_file = path / 'CHECKSUMS.json'
    if not checksum_file.exists():
        return
    hashes = json.loads(checksum_file.read_text())
    if not isinstance(hashes, dict):
        raise ValueError('Checksum inventory must be a JSON object')
    actual = {p.relative_to(path).as_posix() for p in path.rglob('*') if p.is_file()
              and not any(part.startswith('.') for part in p.relative_to(path).parts)}
    if actual != set(hashes) | {'CHECKSUMS.json'}:
        raise ValueError('Export file inventory differs from CHECKSUMS.json')
    for name, digest in hashes.items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('Unsafe checksum path')
        if hashlib.sha256((path / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f'Artifact checksum mismatch: {name}')


def _project_bundle(bundle: Bundle, history: HistoryItem) -> ExperimentDetail:
    summary = summarize(bundle)
    inputs = _frozen_inputs(bundle)
    _validate_result_identities(bundle, summary)
    attempts = {attempt['attempt_id']: attempt for attempt in summary['operations']['attempts']}
    samples = [_sample_projection(item, inputs.get(item['sample_id']), attempts)
               for item in summary['samples']]
    observations = [observation for sample in samples for observation in sample.observations]
    history.kind = 'replay' if isinstance(bundle.plan, FiniteExperimentPlan) and bundle.plan.execution_mode == 'replay' else bundle.plan.kind
    history.model = bundle.plan.effective_model or bundle.plan.settings.model
    history.cases = sorted({sample.case_id for sample in samples})
    history.cohorts = sorted({sample.cohort for sample in samples})
    history.configurations = sorted({observation.configuration for observation in observations})
    history.scored = sum(observation.evaluation is not None for observation in observations)
    history.planned = len(observations)
    history.lifecycle = _lifecycle(observations)
    if isinstance(bundle.plan, FiniteExperimentPlan):
        records = [json.loads(p.read_text()) for p in (bundle.path / 'lifecycle').glob('*.json')]
        history.lifecycle = max(records, key=lambda record: record['at'])['state'] if records else 'frozen'
        # Failed scientific observations remain explicit even when execution completed.
        if history.lifecycle == 'complete' and _lifecycle(observations) == 'failed':
            history.lifecycle = 'failed'

    return ExperimentDetail(
        history=HistoryItem.model_validate(history.model_dump()), configuration=summary['configuration'],
        provenance={**{key: value for key, value in summary['provenance'].items() if key != 'code'},
                    'code_digest': _value_digest(summary['provenance'].get('code'))},
        operations={**summary['operations'],
            'authorizations': [json.loads(p.read_text()) for p in sorted((bundle.path / 'authorizations').glob('*.json'))]},
        cohorts=summary['cohorts'],
        sessions=summary['sessions'], samples=samples,
        cohort_summaries=_cohort_summaries(summary['cohorts']),
    )


def _lifecycle(observations: list[Observation]) -> Literal["complete", "incomplete", "failed"]:
    if any(row.status in {'not_attempted', 'uncertain', 'result_missing'} for row in observations):
        return 'incomplete'
    if any(row.status != 'completed' for row in observations):
        return 'failed'
    return 'complete'


def _value_digest(value: Any) -> str:
    return digest_text(json.dumps(value, sort_keys=True, ensure_ascii=False))


def _sample_projection(summary: dict[str, Any], sample: ResearchInput | None,
                       attempts: dict[str, dict[str, Any]]) -> Sample:
    rows = [summary['baseline'], *summary['repetitions']]
    baseline_f1 = (summary['baseline'].get('evaluation') or {}).get('f1')
    observations = [_observation(row, sample, index, baseline_f1,
        attempts.get(f"{summary['sample_id']}-resolve-{index}")) for index, row in enumerate(rows)]
    return Sample(
        id=summary['sample_id'], case_id=summary['case_id'], cohort=summary['cohort'],
        source=sample.source if sample else None,
        source_digest=digest_text(sample.source) if sample else None,
        truth_digest=_value_digest(sample.truth.model_dump(mode='json')) if sample else None,
        extraction_digest=_value_digest(sample.extraction.model_dump(mode='json'))
            if sample and sample.extraction else None,
        unavailable_reason=None if sample else 'Frozen extraction sample is unavailable.',
        observations=observations, resolver_mean_f1=summary['resolver_metrics']['f1']['mean'],
        mean_delta_f1=summary['paired_deltas']['mean'], scored=summary['scored_repetitions'],
        planned=len(summary['repetitions']),
        outcome_filters=sorted({relationship.outcome for observation in observations
                                for relationship in observation.relationships}),
    )


def _observation(row: dict[str, Any], sample: ResearchInput | None,
                 index: int, baseline_f1: float | None,
                 attempt: dict[str, Any] | None) -> Observation:
    configuration = 'noop' if index == 0 else 'generative_full_source'
    base = dict(id=f'{configuration}-{index}', configuration=configuration,
                repetition=None if index == 0 else index, status=row['status'])
    if row['status'] == 'not_attempted':
        if attempt:
            base['status'] = 'uncertain' if attempt['status'] == 'uncertain' else 'result_missing'
            return Observation(**base, identity_reason='No result artifact was recorded for this attempt.',
                               execution=attempt)
        return Observation(**base, identity_reason='Observation not attempted.')
    result = ResearchResult.model_validate(row)
    if result.evaluation is not None and (sample is None or result.graph is None):
        raise ValueError('Scored result lacks its frozen input or graph')
    return Observation(
        **base, stage=result.stage, error_type=result.error_type, evaluation=result.evaluation,
        delta_f1=result.evaluation.f1 - baseline_f1
            if result.evaluation is not None and baseline_f1 is not None else None,
        identity=result.identity.model_dump() if result.identity else None,
        identity_reason=None if result.identity else 'Annotations or identity diagnostics were not recorded.',
        relationships=relationship_outcomes(sample, result) if sample else [],
        execution={key: value for key, value in row.items()
                   if key not in {'graph', 'extraction', 'evaluation', 'identity'}},
    )


def _cohort_summaries(cohorts: dict[str, Any]) -> list[CohortSummary]:
    return [CohortSummary(
        cohort=name, samples=summary['samples'],
        scored_repetitions=summary['scored_repetitions'],
        failed_repetitions=summary['failed_repetitions'],
        not_attempted_repetitions=summary['not_attempted_repetitions'],
        metrics=[CohortMetric(
            name=metric, baseline_mean=baseline['mean'],
            treatment_mean=summary['resolver_per_input_means'][metric]['mean'],
            baseline_scored=baseline['n'],
            treatment_scored=summary['resolver_per_input_means'][metric]['n'],
        ) for metric, baseline in summary['baseline_metrics'].items()],
    ) for name, summary in cohorts.items()]


def _frozen_inputs(bundle: Bundle) -> dict[str, ResearchInput]:
    inputs = {sample.sample_id: sample for sample in bundle.plan.inputs}
    for path in sorted((bundle.path / 'fresh_inputs').glob('*.json')):
        sample = ResearchInput.model_validate_json(path.read_text())
        if sample.sample_id in inputs:
            raise ValueError('Duplicate frozen sample identity')
        inputs[sample.sample_id] = sample
    return inputs


def _validate_result_identities(bundle: Bundle, summary: dict[str, Any]) -> None:
    rows = bundle.results()
    identities = [(row['sample_id'], row['configuration'], row['repetition']) for row in rows]
    if len(identities) != len(set(identities)):
        raise ValueError('Duplicate result identity')
    planned_ids = {sample['sample_id'] for sample in summary['samples']}
    if any(row['sample_id'] not in planned_ids for row in rows):
        raise ValueError('Result references an unplanned sample')

    for row in rows:
        valid_baseline = row['configuration'] == 'noop' and row['repetition'] in (None, 0)
        valid_treatment = (row['configuration'] == 'generative_full_source'
                           and row['repetition'] in range(1, bundle.plan.resolution_repetitions + 1))
        if not (valid_baseline or valid_treatment):
            raise ValueError('Result configuration or repetition is outside the frozen plan')


def _verify_execution_binding(path: Path) -> None:
    """Verify frozen offline provenance without requiring current execution authority."""
    plan = FrozenPlan.model_validate_json((path / 'execution.json').read_text())
    binding_bytes = (path / 'execution-binding.json').read_bytes()
    digest = hashlib.sha256((path / 'manifest.json').read_bytes() + binding_bytes).hexdigest()
    if plan.digest != digest:
        raise ValueError('Frozen execution binding checksum mismatch')
    binding = json.loads(binding_bytes)
    if Preview.model_validate(binding['preview']) != plan.preview:
        raise ValueError('Frozen execution preview mismatch')
    if binding['recordings_digest'] != hashlib.sha256((path / 'recorded-responses.json').read_bytes()).hexdigest():
        raise ValueError('Frozen recordings checksum mismatch')
