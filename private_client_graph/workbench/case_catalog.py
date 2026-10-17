"""Repository-owned display metadata, separate from evaluation ground truth."""
import hashlib
import json
from pathlib import Path

from private_client_graph.research.fixtures import ROOT, load_inputs
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.case_metadata import CaseMetadata
from private_client_graph.models import source_extraction_from_legacy, SourcedExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.research.source_attribution import SourceEvidenceApproval


def default_input_ids(root: Path = ROOT) -> list[str]:
    """Select all benchmark cases, excluding optional diagnostic/alternate inputs."""
    return [f'{directory.name}_fixture' for directory in _case_directories(root)]


def repository_inputs(root: Path = ROOT) -> list[ResearchInput]:
    """Retain legacy reviewed fixtures and discover additional authored cases."""
    samples = load_inputs(root)
    known = {sample.sample_id for sample in samples}
    directories = _case_directories(root) + sorted(
        path for path in (root / 'evaluation_cases').glob('heldout_*')
        if path.is_dir() and (path / 'ground_truth.json').is_file())
    for directory in directories:
        sample_id = f'{directory.name}_fixture'
        if sample_id not in known:
            paths = {'source.txt': directory / 'source.txt',
                     'ground_truth.json': directory / 'ground_truth.json',
                     'extraction.json': directory / 'expected_extraction.json'}
            raw = {name: path.read_bytes() for name, path in paths.items()}
            samples.append(ResearchInput(sample_id=sample_id, case_id=directory.name,
                cohort='authored', source=raw['source.txt'].decode(),
                truth=json.loads(raw['ground_truth.json']), extraction=json.loads(raw['extraction.json']),
                origin_hashes={name: hashlib.sha256(value).hexdigest() for name, value in raw.items()}))
        sample = next(item for item in samples if item.sample_id == sample_id)
        _freeze_sources(sample, directory)
    return samples


def load_case_catalog(root: Path = ROOT) -> list[CaseMetadata]:
    return [_metadata(sample, root) for sample in repository_inputs(root)]


def frozen_case_metadata(inputs: list[ResearchInput], root: Path = ROOT) -> dict[str, CaseMetadata]:
    """Copy labels now; historical readers use only the retained copy."""
    return {sample.sample_id: _metadata(sample, root) for sample in inputs}


def _case_directories(root: Path) -> list[Path]:
    return sorted(path for path in (root / 'cases').iterdir()
                  if path.is_dir() and (path / 'ground_truth.json').is_file())


def _metadata(sample: ResearchInput, root: Path) -> CaseMetadata:
    heldout = sample.case_id.startswith('heldout_')
    case_path = root / ('evaluation_cases' if heldout else 'cases') / sample.case_id / 'metadata.json'
    if case_path.is_file():
        metadata = json.loads(case_path.read_text())
        if metadata['id'] != sample.case_id:
            raise ValueError('Case metadata identity mismatch')
        historical = sample.cohort == 'historical'
        return CaseMetadata(id=sample.sample_id, case_id=sample.case_id,
            name=metadata['name'], description=metadata['description'],
            fixture_name='Historical saved extraction' if historical else 'Authored extraction',
            fixture_description='Retained alternate extraction of this benchmark source.' if historical
                else 'Repository-authored extraction for deterministic pipeline inspection.',
            kind='historical' if historical else 'heldout' if heldout else 'benchmark', metadata_available=True)
    diagnostic_path = root / 'research' / 'fixtures' / sample.sample_id / 'metadata.json'
    if diagnostic_path.is_file():
        metadata = json.loads(diagnostic_path.read_text())
        if metadata['id'] != sample.sample_id:
            raise ValueError('Diagnostic metadata identity mismatch')
        return CaseMetadata(id=sample.sample_id, case_id=sample.case_id,
            name=metadata['case_name'], description=metadata['case_description'],
            fixture_name=metadata['name'], fixture_description=metadata['description'],
            kind='diagnostic', metadata_available=True)
    return CaseMetadata(id=sample.sample_id, case_id=sample.case_id,
        name=f'Benchmark case {sample.case_id} (name unavailable)', description=None,
        fixture_name=f'Input {sample.sample_id} (name unavailable)', fixture_description=None,
        kind='historical' if sample.cohort == 'historical' else 'benchmark', metadata_available=False)


def _freeze_sources(sample: ResearchInput, directory: Path) -> None:
    """Freeze original ordered files; compatibility text never establishes attribution."""
    manifest = directory / 'sources.json'
    if manifest.exists():
        records = json.loads(manifest.read_text())
        sources = []
        for record in records:
            path = (directory / record['path']).resolve()
            if not path.is_relative_to(directory.resolve()):
                raise ValueError('Source manifest path escapes its case directory')
            raw = path.read_bytes()
            sources.append(Source(id=record['id'], title=record['title'], text=raw.decode()))
            sample.origin_hashes[record['path']] = hashlib.sha256(raw).hexdigest()
        extraction_path = directory / 'expected_source_extraction.json'
        approval_path = directory / 'source_evidence.json'
        sample.sources = sources
        sample.sourced_extraction = SourcedExtractionResult.model_validate_json(extraction_path.read_text())
        sample.source_evidence = SourceEvidenceApproval.model_validate_json(approval_path.read_text())
        for path in (manifest, extraction_path, approval_path):
            sample.origin_hashes[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    else:
        # Legacy authored single-document cases have one explicitly known Source.
        source = Source(id='source_01', title='source.txt', text=sample.source)
        sample.sources = [source]
        assert sample.extraction is not None
        sample.sourced_extraction = source_extraction_from_legacy(sample.extraction, source_id=source.id)
        sample.source_evidence = SourceEvidenceApproval(relationships=[dict(
            source=edge.source, type=edge.type, target=edge.target,
            approved_evidence=[dict(source_id=source.id, supporting_text=quote)
                               for quote in edge.approved_evidence])
            for edge in sample.truth.relationships])
    # Revalidate after filling optional fields so malformed frozen sidecars fail discovery.
    ResearchInput.model_validate(sample.model_dump())
