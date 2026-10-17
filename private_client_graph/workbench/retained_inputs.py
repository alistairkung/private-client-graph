"""Verify actual fresh provider outputs before admitting them as saved inputs."""
import json
from pathlib import Path

from private_client_graph.models import ExtractionResult
from private_client_graph.research.artifacts import Bundle, checksum
from private_client_graph.research.case_metadata import CaseMetadata
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.research.retained_inputs import RetainedInputLineage, RetainedSampleLineage, input_digests
from .artifacts import artifact_digest
from .run_inspection import read_run


def load_retained_inputs(root: Path, experiment_id: str, run_id: str
) -> tuple[list[ResearchInput], dict[str, CaseMetadata], RetainedInputLineage]:
    detail = read_run(root, experiment_id, run_id)
    path = root / run_id
    if path.is_symlink():
        raise ValueError('Retained artifacts cannot be symlinks')
    bundle = Bundle.open(path)
    if not isinstance(bundle.plan, RunPlan):
        raise ValueError('Retained inputs require a single-configuration Run')
    if detail.lifecycle != 'complete' or bundle.plan.input_mode != 'fresh' or bundle.plan.resolver != 'none':
        raise ValueError('Retained inputs require a completed fresh no-resolution Run')
    samples, metadata, lineage = [], {}, {}
    templates = {sample.sample_id: sample for sample in bundle.plan.inputs}
    for slot in bundle.plan.planned_slots:
        if slot.sample_id in lineage or slot.extraction_attempt_id is None:
            raise ValueError('Retained inputs require distinct completed extraction identities')
        sample_path = path / 'fresh_inputs' / f'{slot.sample_id}.json'
        if sample_path.is_symlink() or sample_path.parent.is_symlink():
            raise ValueError('Retained extraction snapshots cannot be symlinks')
        sample = ResearchInput.model_validate_json(sample_path.read_text())
        if sample.sample_id != slot.sample_id:
            raise ValueError('Retained snapshot identity does not match its planned extraction')
        template_id = slot.sample_id.rsplit('_fresh_', 1)[0]
        template = templates[template_id]
        _verify_sample(path, sample, template, slot.extraction_attempt_id)
        digests = input_digests(sample)
        lineage[sample.sample_id] = RetainedSampleLineage(original_sample_id=sample.sample_id,
            extraction_attempt_id=slot.extraction_attempt_id, snapshot_digest=checksum(sample_path.read_bytes()),
            source_digest=digests['source_digest'], truth_digest=digests['truth_digest'],
            extraction_digest=digests['extraction_digest'])
        samples.append(sample.model_copy(deep=True, update={'cohort': 'historical'}))
        metadata[sample.sample_id] = bundle.plan.case_metadata[template_id].model_copy(update={'id': sample.sample_id})
    if artifact_digest(path) != detail.artifact_digest:
        raise ValueError('Original Run changed while selecting retained inputs')
    return samples, metadata, RetainedInputLineage(experiment_id=experiment_id, run_id=run_id,
        plan_digest=detail.plan.digest, artifact_digest=detail.artifact_digest, samples=lineage)


def _verify_sample(path: Path, sample: ResearchInput, template: ResearchInput, attempt_id: str) -> None:
    if sample.cohort != 'fresh' or sample.case_id != template.case_id:
        raise ValueError('Retained snapshot identity does not match its planned extraction')
    digests, expected = input_digests(sample), input_digests(template)
    if any(digests[key] != expected[key] for key in ('source_digest', 'truth_digest')):
        raise ValueError('Retained Source or ground truth differs from its frozen template')
    started_path = path / 'attempts' / f'{attempt_id}.started.json'
    finished_path = path / 'attempts' / f'{attempt_id}.finished.json'
    if any(item.is_symlink() for item in (started_path.parent, started_path, finished_path)):
        raise ValueError('Retained extraction attempts cannot be symlinks')
    started = json.loads(started_path.read_text())
    finished = json.loads(finished_path.read_text())
    request = started['request']
    expected_sources = [source.model_dump(mode='json') for source in sample.sources] if sample.sources is not None else None
    if (started['attempt_id'] != attempt_id or finished['attempt_id'] != attempt_id
            or request['stage'] != 'extraction' or request['source'] != sample.source
            or request.get('sources') != expected_sources or finished['status'] != 'completed'
            or finished['response'].get('error_type') is not None):
        raise ValueError('Retained extraction attempt is missing or inconsistent')
    extraction = sample.sourced_extraction if sample.sources is not None else sample.extraction
    if extraction is None or finished['response']['payload'] != extraction.model_dump(mode='json'):
        raise ValueError('Retained extraction does not match the actual provider output')
    if sample.sourced_extraction is not None:
        projection = ExtractionResult.model_validate({'relationships': [candidate.model_dump(exclude={'source_id'})
            for candidate in sample.sourced_extraction.relationships]})
        if projection != sample.extraction:
            raise ValueError('Retained legacy projection differs from the sourced provider output')
