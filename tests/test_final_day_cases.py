"""Authoring checks for frozen truth, ordered Sources and attributed ideals.

These checks establish mechanical integrity, not semantic completeness or model
quality. Independent source/answer-key review remains an explicit benchmark gate.
"""
import json
from pathlib import Path

import pytest

from private_client_graph.canonical_state import reconstruct_graph, validate_canonical_state
from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import SYMMETRIC_TYPES, build_graph
from private_client_graph.models import ExtractionResult, GroundTruth, RelationshipCandidate
from private_client_graph.models.canonical_state import CanonicalState

ROOT = Path(__file__).resolve().parents[1]
HELDOUT = ROOT / 'evaluation_cases'
DIRECTORIES = [ROOT / 'cases' / 'case_04', ROOT / 'cases' / 'case_05'] + sorted(HELDOUT.glob('heldout_*'))


def _read(directory, filename):
    return json.loads((directory / filename).read_text())


def _edge(source, kind, target):
    if kind in SYMMETRIC_TYPES:
        source, target = sorted((source, target))
    return source, kind, target


def _approved_pairs(directory, truth):
    sidecar = _read(directory, 'source_evidence.json')
    assert set(sidecar) == {'schema_version', 'relationships'}
    assert sidecar['schema_version'] == 1
    approvals = {}
    for edge in sidecar['relationships']:
        assert set(edge) == {'source', 'type', 'target', 'approved_evidence'}
        key = _edge(edge['source'], edge['type'], edge['target'])
        assert key not in approvals
        assert edge['approved_evidence']
        assert all(set(item) == {'source_id', 'supporting_text'} for item in edge['approved_evidence'])
        pairs = [(item['source_id'], item['supporting_text']) for item in edge['approved_evidence']]
        assert len(set(pairs)) == len(pairs)
        approvals[key] = set(pairs)
    truth_edges = {_edge(edge.source, edge.type, edge.target): edge for edge in truth.relationships}
    assert len(truth_edges) == len(truth.relationships)
    assert approvals.keys() == truth_edges.keys()
    for key, edge in truth_edges.items():
        assert {quote for _, quote in approvals[key]} == set(edge.approved_evidence)
    return approvals


@pytest.mark.parametrize('directory', DIRECTORIES, ids=lambda p: p.name)
def test_ordered_source_manifest_and_approvals_agree_with_existing_truth(directory):
    truth = GroundTruth.model_validate(_read(directory, 'ground_truth.json'))
    state = CanonicalState.model_validate(_read(directory, 'expected_state.json'))
    validate_canonical_state(state)
    assert state.entities == truth.entities
    manifest = _read(directory, 'sources.json')
    assert all(set(item) == {'id', 'title', 'path'} for item in manifest)
    assert [item['id'] for item in manifest] == [source.id for source in state.sources]
    assert [item['title'] for item in manifest] == [source.title for source in state.sources]
    for item, source in zip(manifest, state.sources, strict=True):
        path = directory / item['path']
        assert path.resolve().is_relative_to(directory.resolve())
        assert path.is_file()
        assert path.read_text() == source.text
    assert (directory / 'source.txt').read_text() == '\n\n'.join(
        source.text.rstrip() for source in state.sources) + '\n'
    approvals = _approved_pairs(directory, truth)
    sources = {source.id: source for source in state.sources}
    for pairs in approvals.values():
        for source_id, quote in pairs:
            assert source_id in sources
            assert quote.strip() and quote in sources[source_id].text
    expected_count = len(truth.relationships)
    score = evaluate_graph(reconstruct_graph(state), truth)
    assert (score.tp, score.fp, score.fn) == (expected_count, 0, 0)
    assert score.provenance_passed == expected_count
    evidence = {item.id: item for item in state.evidence}
    assert {_edge(edge.source, edge.type, edge.target) for edge in state.relationships} == approvals.keys()
    for edge in state.relationships:
        approved = approvals[_edge(edge.source, edge.type, edge.target)]
        assert {(evidence[eid].source_id, evidence[eid].supporting_text)
                for eid in edge.evidence_ids} <= approved


@pytest.mark.parametrize('directory', DIRECTORIES, ids=lambda p: p.name)
def test_source_attributed_ideal_matches_selected_state_support(directory):
    state = CanonicalState.model_validate(_read(directory, 'expected_state.json'))
    truth = GroundTruth.model_validate(_read(directory, 'ground_truth.json'))
    raw = _read(directory, 'expected_source_extraction.json')
    assert set(raw) == {'relationships'}
    names = {entity.id: entity.name for entity in state.entities}
    sources = {source.id: source for source in state.sources}
    actual = set()
    legacy = []
    for candidate in raw['relationships']:
        assert set(candidate) == {'source_name', 'relationship_type', 'target_name', 'supporting_text', 'source_id'}
        value = {key: item for key, item in candidate.items() if key != 'source_id'}
        parsed = RelationshipCandidate.model_validate(value)
        assert candidate['source_id'] in sources
        assert parsed.supporting_text in sources[candidate['source_id']].text
        actual.add((_edge(parsed.source_name, parsed.relationship_type, parsed.target_name),
                    candidate['source_id'], parsed.supporting_text))
        legacy.append(parsed)
    assert len(actual) == len(raw['relationships'])
    evidence = {item.id: item for item in state.evidence}
    expected = {(_edge(names[edge.source], edge.type, names[edge.target]),
                 evidence[eid].source_id, evidence[eid].supporting_text)
                for edge in state.relationships for eid in edge.evidence_ids}
    assert actual == expected
    graph = build_graph(legacy, document='source.txt', source_text=(directory / 'source.txt').read_text())
    score = evaluate_graph(graph, truth)
    assert (score.tp, score.fp, score.fn) == (len(truth.relationships), 0, 0)
    assert score.provenance_passed == score.tp
    legacy_extraction = ExtractionResult.model_validate(_read(directory, 'expected_extraction.json'))
    legacy_score = evaluate_graph(build_graph(legacy_extraction.relationships,
        document='source.txt', source_text=(directory / 'source.txt').read_text()), truth)
    assert (legacy_score.tp, legacy_score.fp, legacy_score.fn) == (len(truth.relationships), 0, 0)
    assert legacy_score.provenance_passed == legacy_score.tp


@pytest.mark.parametrize('directory', sorted(HELDOUT.glob('heldout_*')), ids=lambda p: p.name)
def test_heldout_identity_notes_and_no_answer_key_ids_in_sources(directory):
    metadata = _read(directory, 'metadata.json')
    assert metadata['id'] == directory.name
    assert metadata['name'].strip() and metadata['description'].strip()
    notes = (directory / 'README.md').read_text()
    assert 'held-out' in notes and 'Bidirectional semantic audit' in notes
    assert 'Independent validator' in notes
    truth = GroundTruth.model_validate(_read(directory, 'ground_truth.json'))
    assert len({entity.id for entity in truth.entities}) == len(truth.entities)
    text = (directory / 'source.txt').read_text()
    assert all(entity.id not in text for entity in truth.entities)


def test_heldout_dataset_is_separate_from_development_cases():
    assert HELDOUT.is_dir()
    assert not (ROOT / 'cases' / 'heldout_01').exists()
    assert [p.name for p in sorted(HELDOUT.glob('heldout_*'))] == [
        f'heldout_{i:02d}' for i in range(1, 11)]
