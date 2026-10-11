"""Repository-owned display metadata, separate from evaluation ground truth."""
import hashlib
import json
from pathlib import Path

from private_client_graph.research.fixtures import ROOT, load_inputs
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.case_metadata import CaseMetadata


def default_input_ids(root: Path = ROOT) -> list[str]:
    """Select all benchmark cases, excluding optional diagnostic/alternate inputs."""
    return [f'{directory.name}_fixture' for directory in _case_directories(root)]


def repository_inputs(root: Path = ROOT) -> list[ResearchInput]:
    """Retain legacy reviewed fixtures and discover additional authored cases."""
    samples = load_inputs(root)
    known = {sample.sample_id for sample in samples}
    for directory in _case_directories(root):
        sample_id = f'{directory.name}_fixture'
        if sample_id in known:
            continue
        paths = {'source.txt': directory / 'source.txt',
                 'ground_truth.json': directory / 'ground_truth.json',
                 'extraction.json': directory / 'expected_extraction.json'}
        raw = {name: path.read_bytes() for name, path in paths.items()}
        samples.append(ResearchInput(sample_id=sample_id, case_id=directory.name,
            cohort='authored', source=raw['source.txt'].decode(),
            truth=json.loads(raw['ground_truth.json']), extraction=json.loads(raw['extraction.json']),
            origin_hashes={name: hashlib.sha256(value).hexdigest() for name, value in raw.items()}))
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
    case_path = root / 'cases' / sample.case_id / 'metadata.json'
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
            kind='historical' if historical else 'benchmark', metadata_available=True)
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
