"""Dated human admission for exact development packages and diagnostic annotations."""
import hashlib
import json
from pathlib import Path

from private_client_graph.research.benchmark_decisions import DecisionTargets
from private_client_graph.research.retained_inputs import value_digest
from private_client_graph.research.inputs import ResearchInput

D13_CASE = 'benchmark_v1_cross_source_dev_3'
D13_PACKAGE = '915338fcafc4262fba5c90942184cffa96b48c8aaebda780b894e98e640e619e'
D13_ANNOTATION = 'dd0dfe33636bddd2868e7c3e691a785213e0cd3bee491d6804192db1d52f1a7d'
D13_REVIEW = '563a8c5840d7bbdccd99383f1a0998564461df991467299e0af43a9ebd0ae78f'

DEVELOPMENT_REVIEW = 'fe81109afffe5bbd36b8ab272b5552191913a9496d6b5427169f01f84dfc2f1a'
REVIEWED_CASES = frozenset({
    'benchmark_v1_temporal_dev_7',
    'benchmark_v1_authority_dev_2',
    'benchmark_v1_authority_dev_3',
    'benchmark_v1_cross_source_dev_2',
    'benchmark_v1_composite_dev_1',
})


def package_hashes(directory: Path) -> dict[str, str]:
    return {p.relative_to(directory).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in directory.rglob('*') if p.is_file()}


def pending_semantic_review(sample: ResearchInput) -> bool:
    if 'pending_semantic_review.md' not in sample.origin_hashes:
        return False
    return sample.case_id not in REVIEWED_CASES or sample.origin_hashes.get('human_review') != DEVELOPMENT_REVIEW


def reviewed_snapshot(study: Path, directory: Path, case_id: str) -> tuple[dict[Path, bytes], dict[str, str]]:
    """Construct the model-facing input from the same bytes bound to its signed approval."""
    if case_id == D13_CASE:
        review = (study / 'reviews/D13.md').read_bytes()
        if hashlib.sha256(review).hexdigest() != D13_REVIEW:
            raise ValueError('D13 signed review commitment mismatch')
        condition, expected_package, expected_annotation, signature = 'D13', D13_PACKAGE, D13_ANNOTATION, D13_REVIEW
    else:
        review = (study / 'reviews/development-2026-11-22.json').read_bytes()
        if hashlib.sha256(review).hexdigest() != DEVELOPMENT_REVIEW:
            raise ValueError('Development signed review commitment mismatch')
        admission, = [r for r in json.loads(review)['conditions'] if r['input_id'] == f'{case_id}_fixture']
        condition, expected_package = admission['condition'], admission['package_sha256']
        expected_annotation, signature = admission['annotation_sha256'], DEVELOPMENT_REVIEW

    contents = {p: p.read_bytes() for p in directory.rglob('*') if p.is_file()}
    hashes = {p.relative_to(directory).as_posix(): hashlib.sha256(raw).hexdigest()
              for p, raw in contents.items()}
    if value_digest(hashes) != expected_package:
        raise ValueError(f'{condition} package differs from the human-approved revision')
    rows = [r for r in json.loads((study / 'development.json').read_bytes()) if r['condition'] == condition]
    if len(rows) != 1:
        raise ValueError(f'Expected one reviewed {condition} annotation')
    row = rows[0]
    labels = DecisionTargets.model_validate(row['targets'])
    annotation = value_digest({**row, 'targets': labels.model_dump(mode='json')})
    if annotation != expected_annotation:
        raise ValueError(f'{condition} annotation differs from the human-approved revision')
    return contents, {**hashes, 'decision_annotation': annotation, 'human_review': signature}
