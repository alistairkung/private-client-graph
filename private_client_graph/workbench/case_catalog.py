"""Repository-owned display metadata, separate from evaluation ground truth."""
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
from typing import Literal

from private_client_graph.graph import build_canonical_state
from private_client_graph.research.fixtures import ROOT, load_inputs
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.case_metadata import CaseMetadata
from private_client_graph.models import ExtractionResult, source_extraction_from_legacy, SourcedExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.research.source_attribution import (
    ApprovedSourceEvidence, SourceEvidenceApproval, SourceEvidenceRelationship,
)


def default_input_ids(root: Path = ROOT) -> list[str]:
    """Select all benchmark cases, excluding optional diagnostic/alternate inputs."""
    return [f'{directory.name}_fixture' for directory in _case_directories(root)]


@dataclass(frozen=True)
class _CasePackage:
    directory: Path
    kind: Literal['benchmark', 'diagnostic', 'heldout']
    axis: str | None = None
    split: Literal['dev', 'held_out'] | None = None
    matter_family: str | None = None


def repository_inputs(root: Path = ROOT) -> list[ResearchInput]:
    """Load the original research controls and the catalogued case packages."""
    samples = {sample.sample_id: sample for sample in load_inputs(root)}
    for case_id, package in _case_packages(root).items():
        fixture_id = f'{case_id}_fixture'
        if fixture_id not in samples:
            samples[fixture_id] = _read_fixture(package.directory, case_id, fixture_id)
        _freeze_sources(samples[fixture_id], package)
    return list(samples.values())


def _read_fixture(directory: Path, case_id: str, fixture_id: str) -> ResearchInput:
    paths = {'source.txt': directory / 'source.txt',
             'ground_truth.json': directory / 'ground_truth.json',
             'extraction.json': directory / 'expected_extraction.json'}
    raw = {name: path.read_bytes() for name, path in paths.items()}
    return ResearchInput(sample_id=fixture_id, case_id=case_id,
        cohort='authored', source=raw['source.txt'].decode(),
        truth=json.loads(raw['ground_truth.json']), extraction=json.loads(raw['extraction.json']),
        origin_hashes={name: hashlib.sha256(value).hexdigest() for name, value in raw.items()})


def load_case_catalog(root: Path = ROOT) -> list[CaseMetadata]:
    return list(frozen_case_metadata(repository_inputs(root), root).values())


def frozen_case_metadata(inputs: list[ResearchInput], root: Path = ROOT) -> dict[str, CaseMetadata]:
    """Copy labels now; historical readers use only the retained copy."""
    packages = _case_packages(root)
    return {sample.sample_id: _metadata(sample, packages.get(sample.case_id), root) for sample in inputs}


def _case_directories(root: Path) -> list[Path]:
    return sorted(path for path in (root / 'cases').iterdir()
                  if path.is_dir() and (path / 'ground_truth.json').is_file())


def _case_packages(root: Path) -> dict[str, _CasePackage]:
    packages = {path.name: _CasePackage(path, 'benchmark') for path in _case_directories(root)}
    for path in sorted((root / 'evaluation_cases').glob('heldout_*')):
        if path.is_dir() and (path / 'ground_truth.json').is_file():
            if path.name in packages:
                raise ValueError(f'Duplicate case identity: {path.name}')
            packages[path.name] = _CasePackage(path, 'heldout')

    for directory in sorted((root / 'benchmark_v1').glob('*/*/case_*')):
        if not directory.is_dir():
            continue
        case_id, package = _diagnostic_package(directory)
        if case_id in packages:
            raise ValueError(f'Duplicate case identity: {case_id}')
        packages[case_id] = package
    return packages


def _diagnostic_package(directory: Path) -> tuple[str, _CasePackage]:
    metadata = json.loads((directory / 'metadata.json').read_bytes())
    axis = directory.parent.parent.name
    split = metadata.get('split')
    if split not in ('dev', 'held_out') or directory.parent.name != split or metadata.get('axis') != axis:
        raise ValueError(f'Axis or split mismatch in {directory}')
    ordinal = directory.name.removeprefix('case_')
    case_id = f'benchmark_v1_{axis}_{split}_{ordinal}'
    if not re.fullmatch(r'[1-9][0-9]*', ordinal) or metadata.get('id') != case_id:
        raise ValueError(f'Invalid benchmark_v1 case identity in {directory}, expected {case_id}')
    family = metadata.get('matter_family')
    if not isinstance(family, str) or not family.strip():
        raise ValueError(f'Missing matter family in {directory}')
    kind: Literal['heldout', 'diagnostic'] = 'heldout' if split == 'held_out' else 'diagnostic'
    return case_id, _CasePackage(directory, kind, axis, split, family)


def _metadata(sample: ResearchInput, package: _CasePackage | None, root: Path) -> CaseMetadata:
    if package is not None and (package.directory / 'metadata.json').is_file():
        metadata = json.loads((package.directory / 'metadata.json').read_text())
        if metadata['id'] != sample.case_id:
            raise ValueError('Case metadata identity mismatch')
        historical = sample.cohort == 'historical'
        return CaseMetadata(id=sample.sample_id, case_id=sample.case_id,
            name=metadata['name'], description=metadata['description'],
            fixture_name='Historical saved extraction' if historical else 'Authored extraction',
            fixture_description='Retained alternate extraction of this benchmark source.' if historical
                else 'Repository-authored extraction for deterministic pipeline inspection.',
            kind='historical' if historical else package.kind, metadata_available=True,
            axis=package.axis, split=package.split, matter_family=package.matter_family)
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


def _freeze_sources(sample: ResearchInput, package: _CasePackage) -> None:
    """Freeze original ordered files; compatibility text never establishes attribution."""
    directory = package.directory
    manifest = directory / 'sources.json'
    if not manifest.exists() and (package.split or (directory / 'source_evidence.json').exists()
                                  or (directory / 'expected_source_extraction.json').exists()):
        raise ValueError(f'Missing sources.json for source-aware fixture {directory}')
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
        sample.source_evidence = SourceEvidenceApproval(relationships=[SourceEvidenceRelationship(
            source=edge.source, type=edge.type, target=edge.target,
            approved_evidence=[ApprovedSourceEvidence(source_id=source.id, supporting_text=quote)
                               for quote in edge.approved_evidence])
            for edge in sample.truth.relationships])
    # Revalidate after filling optional fields so malformed frozen sidecars fail discovery.
    ResearchInput.model_validate(sample.model_dump())
    if package.split is not None:
        _validate_diagnostic_ideal(sample)


def _validate_diagnostic_ideal(sample: ResearchInput) -> None:
    """Both ideal fixtures describe the same candidates with explicit attribution."""
    assert sample.sourced_extraction is not None and sample.sources is not None
    candidates = sample.sourced_extraction.relationships
    projection = ExtractionResult.model_validate({'relationships': [
        item.model_dump(exclude={'source_id'}) for item in candidates
    ]})
    if projection != sample.extraction:
        raise ValueError(f'Legacy and attributed ideals disagree for {sample.case_id}')
    build_canonical_state(candidates, sources=sample.sources)
