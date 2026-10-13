from pathlib import Path

import pytest

from private_client_graph.canonical_state import reconstruct_graph, single_source_state
from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import build_graph
from private_client_graph.models import ExtractionResult, GroundTruth
from private_client_graph.models.source import Source
from private_client_graph.models.canonical_state import CanonicalState


CASE = Path(__file__).resolve().parents[1] / "cases" / "case_01"


@pytest.fixture
def source_aware_state():
    return CanonicalState.model_validate_json(
        (Path(__file__).parent / "fixtures" / "canonical-state.json").read_text(encoding="utf-8")
    )


def test_case_01_state_round_trip_preserves_graph_and_evaluation():
    source_text = (CASE / "source.txt").read_text(encoding="utf-8")
    extraction = ExtractionResult.model_validate_json(
        (CASE / "expected_extraction.json").read_text(encoding="utf-8")
    )
    truth = GroundTruth.model_validate_json(
        (CASE / "ground_truth.json").read_text(encoding="utf-8")
    )
    graph = build_graph(extraction.relationships, document="source.txt", source_text=source_text)
    source = Source(id="note", title="Attendance note", text=source_text)

    state = single_source_state(source, graph)
    reconstructed = reconstruct_graph(state)

    assert reconstructed.model_dump() == graph.model_dump()
    assert state.sources == [source]
    assert {item.source_id for item in state.evidence} == {"note"}
    assert {item.document for item in reconstructed.evidence} == {"source.txt"}
    assert evaluate_graph(reconstructed, truth) == evaluate_graph(graph, truth)
    assert evaluate_graph(reconstructed, truth).tp == 6


@pytest.mark.parametrize("source_id,quote,message", [
    ("missing", "Alex Lee is a beneficiary of Cedar Trust.", "Source reference"),
    ("note_b", "An invented quote", "verbatim"),
    ("note_b", "", "non-empty"),
])
def test_reconstruction_rejects_invalid_source_provenance(source_aware_state, source_id, quote, message):
    source_aware_state.evidence[0].source_id = source_id
    source_aware_state.evidence[0].supporting_text = quote
    with pytest.raises(ValueError, match=message):
        reconstruct_graph(source_aware_state)


@pytest.mark.parametrize("collection", ["sources", "entities", "evidence"])
@pytest.mark.parametrize("invalid_id", [None, "", "  "])
def test_reconstruction_rejects_duplicate_or_blank_identity(source_aware_state, collection, invalid_id):
    items = getattr(source_aware_state, collection)
    items[1].id = items[0].id if invalid_id is None else invalid_id
    with pytest.raises(ValueError, match="ID"):
        reconstruct_graph(source_aware_state)


@pytest.mark.parametrize("changes,message", [
    ({"source": "another-matters-entity"}, "Entity reference"),
    ({"target": "missing"}, "Entity reference"),
    ({"source": "trust"}, "Self-relationship"),
    ({"target": "other_alex"}, "endpoint types"),
    ({"type": "unrecognised"}, "relationship type"),
    ({"evidence_ids": []}, "at least one Evidence"),
    ({"evidence_ids": ["another-matters-evidence"]}, "Evidence reference"),
    ({"evidence_ids": ["quote_a", "quote_a"]}, "Duplicate.*association"),
])
def test_reconstruction_rejects_invalid_relationship(source_aware_state, changes, message):
    source_aware_state.relationships[0] = source_aware_state.relationships[0].model_copy(update=changes)
    with pytest.raises(ValueError, match=message):
        reconstruct_graph(source_aware_state)


@pytest.mark.parametrize("index,reverse", [(0, False), (2, False), (2, True)])
def test_reconstruction_rejects_duplicate_canonical_edges(source_aware_state, index, reverse):
    duplicate = source_aware_state.relationships[index].model_copy(deep=True)
    if reverse:
        duplicate.source, duplicate.target = duplicate.target, duplicate.source
    source_aware_state.relationships.append(duplicate)
    with pytest.raises(ValueError, match="Duplicate canonical Relationship"):
        reconstruct_graph(source_aware_state)


def test_reconstruction_rejects_two_evidence_ids_for_same_source_quote(source_aware_state):
    duplicate = source_aware_state.evidence[0].model_copy(update={"id": "another-occurrence"})
    source_aware_state.evidence.append(duplicate)
    with pytest.raises(ValueError, match="Duplicate Source.*quote"):
        reconstruct_graph(source_aware_state)


def test_source_aware_state_preserves_explicit_identity_provenance_and_order(source_aware_state):
    before = source_aware_state.model_dump()
    # This boundary must remain usable after serialization by a future repository.
    restored = CanonicalState.model_validate_json(source_aware_state.model_dump_json())
    graph = reconstruct_graph(restored)
    assert graph.model_dump() == {
        "entities": [
            {"id": "other_alex", "type": "person", "name": "Alex Lee"},
            {"id": "trust", "type": "trust", "name": "Cedar Trust"},
            {"id": "shared_alex", "type": "person", "name": "Alex Lee"},
            {"id": "morgan", "type": "person", "name": "Morgan Lee"},
        ],
        "relationships": [
            {"source": "shared_alex", "type": "beneficiary_of", "target": "trust", "evidence_ids": ["quote_b", "quote_a"]},
            {"source": "other_alex", "type": "beneficiary_of", "target": "trust", "evidence_ids": ["quote_a"]},
            {"source": "shared_alex", "type": "sibling_of", "target": "morgan", "evidence_ids": ["siblings"]},
        ],
        "evidence": [
            {"id": "quote_b", "document": "legacy-b.txt", "supporting_text": "Alex Lee is a beneficiary of Cedar Trust."},
            {"id": "siblings", "document": "legacy-a.txt", "supporting_text": "Alex Lee and Morgan Lee are siblings."},
            {"id": "quote_a", "document": "legacy-a.txt", "supporting_text": "Alex Lee is a beneficiary of Cedar Trust."},
        ],
    }
    assert [(item.id, item.source_id) for item in restored.evidence] == [
        ("quote_b", "note_b"), ("siblings", "note_a"), ("quote_a", "note_a"),
    ]
    assert [source.id for source in restored.sources] == ["note_b", "note_a"]
    assert restored.sources[0].text == restored.sources[1].text
    assert source_aware_state.model_dump() == before
    graph.entities[0].name = "Changed in presentation"
    graph.relationships[0].evidence_ids.clear()
    graph.evidence[0].supporting_text = "Changed in presentation"
    assert restored.model_dump() == before


def test_empty_graph_keeps_its_source_and_single_source_adapter_does_not_alias_inputs():
    from private_client_graph.models import CanonicalGraph

    source = Source(id="note", title="No supported relationships", text="Unrelated text.")
    state = single_source_state(source, CanonicalGraph(entities=[], relationships=[], evidence=[]))
    source.title = "Changed by caller"
    assert state.sources[0].model_dump() == {
        "id": "note", "title": "No supported relationships", "text": "Unrelated text.",
    }
    assert reconstruct_graph(state).model_dump() == {
        "entities": [], "relationships": [], "evidence": [],
    }


@pytest.mark.parametrize("name", ["", " \n "])
def test_reconstruction_rejects_blank_entity_names(source_aware_state, name):
    source_aware_state.entities[0].name = name
    with pytest.raises(ValueError, match="Entity name"):
        reconstruct_graph(source_aware_state)


def test_quote_in_another_source_does_not_validate_attribution(source_aware_state):
    source_aware_state.sources[0].text = "This Source does not contain that quote."
    with pytest.raises(ValueError, match="verbatim"):
        reconstruct_graph(source_aware_state)


def test_distinct_same_name_entities_can_be_endpoints_of_directed_relationships(source_aware_state):
    from private_client_graph.models import Relationship

    source_aware_state.relationships = [
        Relationship(source="other_alex", type="parent_of", target="shared_alex", evidence_ids=["quote_a"]),
        Relationship(source="shared_alex", type="parent_of", target="other_alex", evidence_ids=["quote_b"]),
    ]
    # Structural validation does not claim these fixture quotes support parenthood.
    graph = reconstruct_graph(source_aware_state)
    assert [(edge.source, edge.target) for edge in graph.relationships] == [
        ("other_alex", "shared_alex"), ("shared_alex", "other_alex"),
    ]


def test_single_source_adaptation_rejects_invalid_state_before_returning(source_aware_state):
    graph = reconstruct_graph(source_aware_state)
    # Use one quote because this explicit legacy adapter binds everything to one Source.
    graph.evidence = [graph.evidence[0]]
    graph.relationships = [graph.relationships[0]]
    graph.relationships[0].evidence_ids = ["missing"]
    with pytest.raises(ValueError, match="Evidence reference"):
        single_source_state(source_aware_state.sources[0], graph)


def test_exact_names_quotes_and_overlapping_evidence_are_preserved(source_aware_state):
    source_aware_state.entities[0].name = "  alex LEE  "
    source_aware_state.evidence.append(source_aware_state.evidence[0].model_copy(update={
        "id": "longer-quote",
        "supporting_text": "Alex Lee is a beneficiary of Cedar Trust. Alex Lee is a beneficiary of Cedar Trust.",
    }))
    source_aware_state.relationships[0].evidence_ids.append("longer-quote")
    graph = reconstruct_graph(source_aware_state)
    assert graph.entities[0].name == "  alex LEE  "
    assert graph.evidence[-1].supporting_text == (
        "Alex Lee is a beneficiary of Cedar Trust. Alex Lee is a beneficiary of Cedar Trust."
    )
    assert graph.relationships[0].evidence_ids == ["quote_b", "quote_a", "longer-quote"]
