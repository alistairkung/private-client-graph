from pathlib import Path

import pytest

from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import build_graph
from private_client_graph.models import (
    CanonicalGraph, Entity, Evidence, ExtractionResult, GroundTruth,
    GroundTruthRelationship, Relationship,
)


PARENT = ("Alice", "parent_of", "Bob")
SPOUSE = ("Alice", "spouse_of", "David")
SIBLING = ("Bob", "sibling_of", "David")
QUOTE = "Alice is Bob's parent."


def prediction(edges=(PARENT,), quotes=(QUOTE,), prefix="pred"):
    names = sorted({name for source, _, target in edges for name in (source, target)})
    ids = {name: f"{prefix}-{index}" for index, name in enumerate(names)}
    evidence = [
        Evidence(id=f"quote-{index}", document="source.txt", supporting_text=quote)
        for index, quote in enumerate(quotes)
    ]
    return CanonicalGraph(
        entities=[Entity(id=ids[name], name=name, type="person") for name in names],
        relationships=[
            Relationship(source=ids[source], type=kind, target=ids[target],
                         evidence_ids=[item.id for item in evidence])
            for source, kind, target in edges
        ],
        evidence=evidence,
    )


def truth(edges=(PARENT,), quotes=(QUOTE,)):
    graph = prediction(edges, prefix="truth")
    return GroundTruth(
        entities=graph.entities,
        relationships=[
            GroundTruthRelationship(source=edge.source, type=edge.type,
                                    target=edge.target, approved_evidence=list(quotes))
            for edge in graph.relationships
        ],
    )


def test_identical_directed_edge_matches():
    result = evaluate_graph(prediction(), truth())
    assert (result.tp, result.fp, result.fn) == (1, 0, 0)
    assert result.true_positive_edges == [PARENT]


@pytest.mark.parametrize("kind", ["parent_of", "settlor_of", "trustee_of", "beneficiary_of"])
def test_reversed_directed_edges_do_not_match(kind):
    edge = ("Alice", kind, "Bob")
    reverse = ("Bob", kind, "Alice")
    result = evaluate_graph(prediction([reverse]), truth([edge]))
    assert (result.tp, result.fp, result.fn) == (0, 1, 1)
    assert result.false_positive_edges == [reverse]
    assert result.false_negative_edges == [edge]


@pytest.mark.parametrize("kind", ["spouse_of", "sibling_of"])
@pytest.mark.parametrize("reverse_truth", [False, True])
def test_symmetric_edges_normalized_on_both_sides(kind, reverse_truth):
    edge = ("Alice", kind, "Bob")
    reverse = ("Bob", kind, "Alice")
    predicted, expected = (edge, reverse) if reverse_truth else (reverse, edge)
    result = evaluate_graph(prediction([predicted]), truth([expected]))
    assert (result.tp, result.fp, result.fn) == (1, 0, 0)
    assert result.true_positive_edges == [edge]
    assert result.provenance_passes == [edge]


def test_generated_entity_ids_do_not_affect_scoring():
    assert evaluate_graph(prediction(prefix="random"), truth()) == evaluate_graph(prediction(), truth())


def test_perfect_prediction():
    result = evaluate_graph(prediction([PARENT, SPOUSE]), truth([PARENT, SPOUSE]))
    assert (result.tp, result.fp, result.fn) == (2, 0, 0)
    assert (result.precision, result.recall, result.f1) == (1.0, 1.0, 1.0)
    assert result.false_positive_edges == result.false_negative_edges == []


def test_one_false_positive():
    result = evaluate_graph(prediction([PARENT, SPOUSE]), truth())
    assert (result.tp, result.fp, result.fn) == (1, 1, 0)
    assert result.precision == 0.5
    assert result.recall == 1.0
    assert result.f1 == pytest.approx(2 / 3)
    assert result.false_positive_edges == [SPOUSE]


def test_one_false_negative():
    result = evaluate_graph(prediction(), truth([PARENT, SPOUSE]))
    assert (result.tp, result.fp, result.fn) == (1, 0, 1)
    assert result.precision == 1.0
    assert result.recall == 0.5
    assert result.f1 == pytest.approx(2 / 3)
    assert result.false_negative_edges == [SPOUSE]


def test_simultaneous_false_positive_and_false_negative():
    result = evaluate_graph(prediction([PARENT, SIBLING]), truth([PARENT, SPOUSE]))
    assert (result.tp, result.fp, result.fn) == (1, 1, 1)
    assert (result.precision, result.recall, result.f1) == (0.5, 0.5, 0.5)
    assert result.true_positive_edges == [PARENT]
    assert result.false_positive_edges == [SIBLING]
    assert result.false_negative_edges == [SPOUSE]


@pytest.mark.parametrize("predicted,expected", [([], []), ([], [PARENT]), ([PARENT], []), ([SPOUSE], [PARENT])])
def test_zero_denominators_and_no_true_positives(predicted, expected):
    result = evaluate_graph(prediction(predicted), truth(expected))
    assert (result.precision, result.recall, result.f1, result.provenance_accuracy) == (0.0, 0.0, 0.0, 0.0)
    assert result.tp == result.provenance_passed == result.provenance_failed == 0
    assert result.provenance_passes == result.provenance_failures == []


def test_approved_evidence_passes():
    result = evaluate_graph(prediction(), truth())
    assert result.provenance_passed == 1
    assert result.provenance_failed == 0
    assert result.provenance_accuracy == 1.0
    assert result.provenance_passes == [PARENT]


@pytest.mark.parametrize("quote", ["Unrelated sentence.", QUOTE.lower(), QUOTE + " ", QUOTE[:-1]])
def test_evidence_requires_exact_match(quote):
    result = evaluate_graph(prediction(quotes=[quote]), truth())
    assert result.tp == 1
    assert result.provenance_failed == 1
    assert result.provenance_accuracy == 0.0
    assert result.provenance_failures == [PARENT]


def test_any_predicted_evidence_can_match():
    result = evaluate_graph(prediction(quotes=["Unapproved.", QUOTE]), truth())
    assert result.provenance_passed == 1
    assert result.provenance_accuracy == 1.0


def test_any_approved_alternative_can_match():
    result = evaluate_graph(prediction(quotes=["Alternative."]), truth(quotes=[QUOTE, "Alternative."]))
    assert result.provenance_passed == 1


def test_no_attached_evidence_fails_provenance():
    result = evaluate_graph(prediction(quotes=[]), truth())
    assert result.tp == result.provenance_failed == 1


def test_provenance_excludes_false_positives_and_false_negatives():
    result = evaluate_graph(prediction([PARENT, SIBLING]), truth([PARENT, SPOUSE]))
    assert result.provenance_passes == [PARENT]
    assert result.provenance_failures == []
    assert result.provenance_accuracy == 1.0


def test_provenance_accuracy_denominator_is_true_positives_only():
    graph = prediction([PARENT, SPOUSE, SIBLING])
    graph.relationships[1].evidence_ids = []
    result = evaluate_graph(graph, truth([PARENT, SPOUSE]))
    assert result.tp == 2
    assert result.fp == 1
    assert result.provenance_passed == result.provenance_failed == 1
    assert result.provenance_accuracy == 0.5
    assert result.provenance_passes == [PARENT]
    assert result.provenance_failures == [SPOUSE]


@pytest.mark.parametrize("field", ["source", "target"])
@pytest.mark.parametrize("side", ["prediction", "truth"])
def test_unresolved_entity_references_fail_clearly(field, side):
    graph, expected = prediction(), truth()
    item = graph if side == "prediction" else expected
    setattr(item.relationships[0], field, "missing")
    with pytest.raises(ValueError, match="Unresolved .*entity reference: 'missing'"):
        evaluate_graph(graph, expected)


@pytest.mark.parametrize("edges", [[PARENT], [SPOUSE]])
def test_unresolved_evidence_fails_even_on_false_positive(edges):
    graph = prediction(edges)
    graph.relationships[0].evidence_ids.append("missing")
    with pytest.raises(ValueError, match="Unresolved predicted evidence reference: 'missing'"):
        evaluate_graph(graph, truth())


@pytest.mark.parametrize("side,collection", [("prediction", "entities"), ("prediction", "evidence"), ("truth", "entities")])
def test_duplicate_reference_ids_are_rejected(side, collection):
    graph, expected = prediction(), truth()
    items = getattr(graph if side == "prediction" else expected, collection)
    items.append(items[0])
    with pytest.raises(ValueError, match="Duplicate .* ID"):
        evaluate_graph(graph, expected)


def test_repeated_semantic_edges_count_once_and_pool_evidence():
    graph = prediction([PARENT, PARENT], quotes=["Unapproved.", QUOTE])
    graph.relationships[0].evidence_ids = ["quote-0"]
    graph.relationships[1].evidence_ids = ["quote-1"]
    expected = truth([PARENT, PARENT])
    expected.relationships[0].approved_evidence = ["Other."]
    result = evaluate_graph(graph, expected)
    assert result.tp == result.provenance_passed == 1


def test_diagnostics_are_sorted_and_input_is_unchanged():
    graph, expected = prediction([SIBLING, SPOUSE, PARENT]), truth([PARENT, SPOUSE])
    before = graph.model_dump(), expected.model_dump()
    result = evaluate_graph(graph, expected)
    assert result.true_positive_edges == sorted([PARENT, SPOUSE])
    graph.relationships.reverse()
    assert evaluate_graph(graph, expected) == result
    graph.relationships.reverse()
    assert (graph.model_dump(), expected.model_dump()) == before


CASE_01 = Path(__file__).resolve().parents[1] / "cases" / "case_01"


def test_case_01_perfect_semantic_and_provenance_scores():
    candidates = ExtractionResult.model_validate_json((CASE_01 / "expected_extraction.json").read_text())
    graph = build_graph(candidates.relationships, document="source.txt", source_text=(CASE_01 / "source.txt").read_text())
    expected = GroundTruth.model_validate_json((CASE_01 / "ground_truth.json").read_text())
    result = evaluate_graph(graph, expected)
    assert (result.tp, result.fp, result.fn) == (6, 0, 0)
    assert (result.precision, result.recall, result.f1) == (1.0, 1.0, 1.0)
    assert (result.provenance_passed, result.provenance_failed, result.provenance_accuracy) == (6, 0, 1.0)


def test_case_01_approved_spans_are_verbatim_and_include_alternatives():
    expected = GroundTruth.model_validate_json((CASE_01 / "ground_truth.json").read_text())
    source = (CASE_01 / "source.txt").read_text()
    for edge in expected.relationships:
        assert len(edge.approved_evidence) > 1
        assert all(quote and quote in source for quote in edge.approved_evidence)
