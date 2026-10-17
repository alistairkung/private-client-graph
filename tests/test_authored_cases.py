"""Validate authored answers independently of probabilistic extraction."""
import json
from pathlib import Path

import pytest

from private_client_graph.canonical_state import reconstruct_graph, validate_canonical_state
from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import ENDPOINT_TYPES, SYMMETRIC_TYPES, build_graph
from private_client_graph.models import ExtractionResult, GroundTruth
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.workbench.case_catalog import repository_inputs, load_case_catalog

CASES = Path(__file__).resolve().parents[1] / 'cases'


def _read_model(directory, filename, model):
    return model.model_validate_json((directory / filename).read_text())


def _edge(source, kind, target):
    if kind in SYMMETRIC_TYPES:
        source, target = sorted((source, target))
    return source, kind, target


def _state_evidence(state):
    names = {entity.id: entity.name for entity in state.entities}
    evidence = {item.id: (item.source_id, item.supporting_text) for item in state.evidence}
    return {
        _edge(names[edge.source], edge.type, names[edge.target]):
            {evidence[identifier] for identifier in edge.evidence_ids}
        for edge in state.relationships
    }


def _assert_perfect_score(graph, truth, count):
    score = evaluate_graph(graph, truth)
    assert (score.tp, score.fp, score.fn) == (count, 0, 0)
    assert score.precision == score.recall == score.f1 == 1.0
    assert score.provenance_passed == count
    assert score.provenance_failed == 0
    assert score.provenance_accuracy == 1.0


@pytest.mark.parametrize(('case_id', 'edge_count'), [('case_04', 7), ('case_05', 6)])
def test_complete_authored_cases_have_valid_answers_evidence_and_loader_inputs(case_id, edge_count):
    directory = CASES / case_id
    truth = _read_model(directory, 'ground_truth.json', GroundTruth)
    extraction = _read_model(directory, 'expected_extraction.json', ExtractionResult)
    state = _read_model(directory, 'expected_state.json', CanonicalState)
    texts = {note: (directory / f'sources/{note}.txt').read_text() for note in ('note_01', 'note_02')}
    combined = (directory / 'source.txt').read_text()
    assert combined == '\n\n'.join(text.rstrip() for text in texts.values()) + '\n'
    assert [(source.id, source.title, source.text) for source in state.sources] == [
        (note, f'sources/{note}.txt', text) for note, text in texts.items()]

    entities = {entity.id: entity for entity in truth.entities}
    assert len(entities) == len(truth.entities)
    truth_edges = set()
    for relationship in truth.relationships:
        source, target = entities[relationship.source], entities[relationship.target]
        assert (source.type, target.type) == ENDPOINT_TYPES[relationship.type]
        assert source.id != target.id
        edge = _edge(source.name, relationship.type, target.name)
        assert edge not in truth_edges
        truth_edges.add(edge)
        assert relationship.approved_evidence
        assert len(set(relationship.approved_evidence)) == len(relationship.approved_evidence)
        assert all(quote.strip() and any(quote in text for text in texts.values())
                   for quote in relationship.approved_evidence)
    assert len(truth_edges) == edge_count
    # Answer-key IDs and graph/evidence objects cannot leak into raw extraction.
    raw = json.loads((directory / 'expected_extraction.json').read_text())
    assert set(raw) == {'relationships'}
    assert all(set(candidate) == {'source_name', 'relationship_type', 'target_name', 'supporting_text'}
               for candidate in raw['relationships'])
    assert all(entity.id not in combined for entity in truth.entities)

    graph = build_graph(extraction.relationships, document='source.txt', source_text=combined)
    _assert_perfect_score(graph, truth, edge_count)
    validate_canonical_state(state)
    _assert_perfect_score(reconstruct_graph(state), truth, edge_count)
    assert state.entities == truth.entities
    assert set(_state_evidence(state)) == truth_edges
    # Check every association, not just the evaluator's at-least-one-approved rule.
    names = {entity.id: entity.name for entity in truth.entities}
    approved = {
        _edge(names[edge.source], edge.type, names[edge.target]): set(edge.approved_evidence)
        for edge in truth.relationships}
    for edge, evidence in _state_evidence(state).items():
        assert all(quote in approved[edge] for source_id, quote in evidence)
    assert all(item.document == f'sources/{item.source_id}.txt' for item in state.evidence)

    loaded = next(sample for sample in repository_inputs() if sample.case_id == case_id)
    assert loaded.source == combined
    assert loaded.truth == truth
    assert loaded.extraction == extraction
    metadata = next(entry for entry in load_case_catalog() if entry.id == loaded.sample_id)
    assert metadata.metadata_available and metadata.kind == 'benchmark'
    assert metadata.description and metadata.name


@pytest.mark.parametrize('case_id', ['case_04', 'case_05'])
def test_per_document_candidates_validate_and_match_selected_state_attribution(case_id):
    directory = CASES / case_id
    state = _read_model(directory, 'expected_state.json', CanonicalState)
    candidates_by_note = {}
    for note in ('note_01', 'note_02'):
        source = (directory / f'sources/{note}.txt').read_text()
        extraction = _read_model(directory, f'expected_extraction_{note}.json', ExtractionResult)
        graph = build_graph(extraction.relationships, document=f'sources/{note}.txt', source_text=source)
        assert all(item.document == f'sources/{note}.txt' for item in graph.evidence)
        candidates_by_note[note] = {
            (_edge(candidate.source_name, candidate.relationship_type, candidate.target_name),
             candidate.supporting_text) for candidate in extraction.relationships}
    for edge, evidence in _state_evidence(state).items():
        for source_id, quote in evidence:
            assert (edge, quote) in candidates_by_note[source_id]


def test_case_04_pools_two_documents_on_one_shared_beneficiary_edge():
    directory = CASES / 'case_04'
    state = _read_model(directory, 'expected_state.json', CanonicalState)
    evidence = _state_evidence(state)
    shared = evidence[('Andrew Chan', 'beneficiary_of', 'Hillcrest Family Trust')]
    assert {source_id for source_id, quote in shared} == {'note_01', 'note_02'}
    assert len(shared) == 2
    assert {source_id for source_id, quote in evidence[
        ('Lucy Chan', 'beneficiary_of', 'Hillcrest Family Trust')]} == {'note_02'}
    assert {source_id for source_id, quote in evidence[
        ('Marcus Yip', 'beneficiary_of', 'Hillcrest Family Trust')]} == {'note_02'}
    combined = _read_model(directory, 'expected_extraction.json', ExtractionResult)
    parts = [_read_model(directory, f'expected_extraction_note_0{i}.json', ExtractionResult)
             for i in (1, 2)]
    assert [len(part.relationships) for part in parts] == [5, 3]
    assert combined.relationships == parts[0].relationships + parts[1].relationships
    assert len(state.relationships) == 7


def test_case_05_snapshots_replace_only_the_trustee_and_keep_earlier_provenance():
    directory = CASES / 'case_05'
    initial_truth = _read_model(directory, 'ground_truth_after_note_01.json', GroundTruth)
    initial = _read_model(directory, 'expected_state_after_note_01.json', CanonicalState)
    final_truth = _read_model(directory, 'ground_truth.json', GroundTruth)
    final = _read_model(directory, 'expected_state.json', CanonicalState)
    first = _read_model(directory, 'expected_extraction_note_01.json', ExtractionResult)
    graph = build_graph(first.relationships, document='sources/note_01.txt',
                        source_text=(directory / 'sources/note_01.txt').read_text())
    _assert_perfect_score(graph, initial_truth, 6)
    _assert_perfect_score(reconstruct_graph(initial), initial_truth, 6)
    assert initial.entities == initial_truth.entities
    assert [source.id for source in initial.sources] == ['note_01']
    assert initial.sources == final.sources[:1]
    assert all(item.source_id == 'note_01' for item in initial.evidence)

    before, after = _state_evidence(initial), _state_evidence(final)
    former = ('David Ng', 'trustee_of', 'Willow Family Trust')
    successor = ('Rachel Lim', 'trustee_of', 'Willow Family Trust')
    assert before.keys() - after.keys() == {former}
    assert after.keys() - before.keys() == {successor}
    assert {source_id for source_id, quote in after[successor]} == {'note_02'}
    for edge in before.keys() & after.keys():
        assert before[edge] == after[edge]
        assert {source_id for source_id, quote in after[edge]} == {'note_01'}
    final_entities = {entity.id: entity for entity in final.entities}
    final_evidence = {item.id: item for item in final.evidence}
    assert all(final_entities[entity.id] == entity for entity in initial.entities if entity.id in final_entities)
    assert all(final_evidence[item.id] == item for item in initial.evidence if item.id in final_evidence)
    assert len(before) == len(after) == 6
    _assert_perfect_score(reconstruct_graph(final), final_truth, 6)


def test_case_05_union_and_single_document_controls_expose_required_reconciliation():
    directory = CASES / 'case_05'
    truth = _read_model(directory, 'ground_truth.json', GroundTruth)
    parts = [_read_model(directory, f'expected_extraction_note_0{i}.json', ExtractionResult)
             for i in (1, 2)]
    union = build_graph(parts[0].relationships + parts[1].relationships, document='source.txt',
                        source_text=(directory / 'source.txt').read_text())
    score = evaluate_graph(union, truth)
    assert (score.tp, score.fp, score.fn) == (6, 1, 0)
    assert score.false_positive_edges == [('David Ng', 'trustee_of', 'Willow Family Trust')]
    assert score.provenance_accuracy == 1.0  # Quote scoring alone cannot detect supersession.
    for index, expected in [(0, (5, 1, 1)), (1, (1, 0, 5))]:
        graph = build_graph(parts[index].relationships, document=f'sources/note_0{index + 1}.txt',
                            source_text=(directory / f'sources/note_0{index + 1}.txt').read_text())
        result = evaluate_graph(graph, truth)
        assert (result.tp, result.fp, result.fn) == expected


@pytest.mark.parametrize('case_id', ['case_04', 'case_05'])
def test_source_aware_expectation_rejects_quotes_attributed_to_the_other_document(case_id):
    state = _read_model(CASES / case_id, 'expected_state.json', CanonicalState)
    # A settlor quote occurs only in the initial note; moving it must fail validation.
    quote = next(item for item in state.evidence if 'settlor' in item.supporting_text)
    quote.source_id = 'note_02'
    with pytest.raises(ValueError, match='verbatim'):
        validate_canonical_state(state)
