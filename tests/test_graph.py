from pathlib import Path
from typing import get_args

import pytest

from private_client_graph.graph import ENDPOINT_TYPES, build_graph
from private_client_graph.models import ExtractionResult, RelationshipCandidate, RelationshipType


QUOTE = "Alice and David are the parents of Bob."


def candidate(source="Alice", target="Bob", kind="parent_of", quote=QUOTE):
    return RelationshipCandidate(
        source_name=source, relationship_type=kind,
        target_name=target, supporting_text=quote,
    )


def build(*candidates, source_text=QUOTE):
    return build_graph(candidates, document="source.txt", source_text=source_text)


def test_verbatim_evidence_is_accepted_and_document_is_preserved():
    graph = build(candidate(), source_text=f"Introduction. {QUOTE} Conclusion.")
    assert graph.evidence[0].supporting_text == QUOTE
    assert graph.evidence[0].document == "source.txt"


@pytest.mark.parametrize("field", ["source_name", "target_name", "supporting_text"])
@pytest.mark.parametrize("value", [" ", "\t\n\r", "\u00a0"])
def test_whitespace_only_fields_are_rejected(field, value):
    fields = candidate().model_dump()
    fields[field] = value
    item = RelationshipCandidate(**fields)
    with pytest.raises(ValueError, match=f"{field} must not be empty or whitespace-only"):
        build(item, source_text=QUOTE + value)


@pytest.mark.parametrize("field", ["source_name", "target_name", "supporting_text"])
def test_empty_fields_are_rejected_if_schema_validation_was_bypassed(field):
    item = candidate().model_copy(update={field: ""})
    with pytest.raises(ValueError, match=f"{field} must not be empty or whitespace-only"):
        build(item)


def test_nonblank_values_are_preserved_without_trimming():
    quote = f"  {QUOTE}\n"
    item = candidate(source=" Alice ", target=" Bob ", quote=quote)
    graph = build(item, source_text=quote)
    assert {entity.name for entity in graph.entities} == {" Alice ", " Bob "}
    assert graph.evidence[0].supporting_text == quote
    assert item.source_name == " Alice "
    assert item.target_name == " Bob "
    assert item.supporting_text == quote


@pytest.mark.parametrize("quote", ["Alice is Bob's parent.", QUOTE.lower()])
def test_non_verbatim_evidence_is_rejected(quote):
    with pytest.raises(ValueError, match="verbatim"):
        build(candidate(quote=quote))


@pytest.mark.parametrize("kind", get_args(RelationshipType))
def test_self_relationship_is_rejected(kind):
    with pytest.raises(ValueError, match="self-relationship"):
        build(candidate(target="Alice", kind=kind))


@pytest.mark.parametrize("kind", ["parent_of", "sibling_of", "spouse_of"])
def test_family_relationships_imply_person_endpoints(kind):
    graph = build(candidate(kind=kind))
    assert {entity.name: entity.type for entity in graph.entities} == {
        "Alice": "person", "Bob": "person",
    }


@pytest.mark.parametrize("kind", ["settlor_of", "trustee_of", "beneficiary_of"])
def test_trust_roles_imply_person_to_trust(kind):
    graph = build(candidate(target="Evergreen", kind=kind))
    assert {entity.name: entity.type for entity in graph.entities} == {
        "Alice": "person", "Evergreen": "trust",
    }


def test_repeated_names_reuse_one_entity():
    graph = build(candidate(), candidate(target="David", kind="spouse_of"))
    assert len(graph.entities) == 3
    assert len({edge.source for edge in graph.relationships}) == 1


@pytest.mark.parametrize("reverse", [False, True])
def test_conflicting_types_are_rejected_regardless_of_order(reverse):
    candidates = [candidate(), candidate(source="David", target="Bob", kind="settlor_of")]
    if reverse:
        candidates.reverse()
    with pytest.raises(ValueError, match="conflicting entity types.*Bob"):
        build(*candidates)


def test_unsupported_type_is_rejected_even_if_schema_validation_was_bypassed():
    invalid = candidate().model_copy(update={"relationship_type": "cousin_of"})
    with pytest.raises(ValueError, match="unsupported relationship type"):
        build(invalid)


def test_semantics_cover_exactly_the_existing_relationship_vocabulary():
    assert set(ENDPOINT_TYPES) == set(get_args(RelationshipType))


def test_entity_ids_are_nonempty_and_unique():
    graph = build(candidate(), candidate(source="David"))
    ids = [entity.id for entity in graph.entities]
    assert all(ids)
    assert len(set(ids)) == len(ids) == 3


def test_identical_evidence_is_shared_by_two_relationships():
    graph = build(candidate(), candidate(source="David"))
    assert len(graph.relationships) == 2
    assert len(graph.evidence) == 1
    assert all(edge.evidence_ids == [graph.evidence[0].id] for edge in graph.relationships)


def test_distinct_evidence_gets_unique_nonempty_ids():
    second_quote = "Alice is Bob's parent."
    graph = build(candidate(), candidate(quote=second_quote), source_text=QUOTE + second_quote)
    ids = [item.id for item in graph.evidence]
    assert all(ids)
    assert len(set(ids)) == len(ids) == 2


def test_duplicate_directed_edges_and_evidence_references_collapse():
    graph = build(candidate(), candidate())
    assert len(graph.relationships) == 1
    assert graph.relationships[0].evidence_ids == [graph.evidence[0].id]


def test_duplicate_edges_retain_all_distinct_evidence():
    second_quote = "Alice is Bob's parent."
    graph = build(candidate(), candidate(quote=second_quote), source_text=QUOTE + second_quote)
    assert len(graph.relationships) == 1
    assert set(graph.relationships[0].evidence_ids) == {item.id for item in graph.evidence}


@pytest.mark.parametrize("kind", ["spouse_of", "sibling_of"])
def test_reversed_symmetric_edges_collapse_in_name_order(kind):
    graph = build(candidate(source="Bob", target="Alice", kind=kind), candidate(kind=kind))
    assert len(graph.relationships) == 1
    names = {entity.id: entity.name for entity in graph.entities}
    edge = graph.relationships[0]
    assert (names[edge.source], names[edge.target]) == ("Alice", "Bob")


def test_parent_edges_keep_direction_and_do_not_collapse_when_reversed():
    graph = build(candidate(), candidate(source="Bob", target="Alice"))
    names = {entity.id: entity.name for entity in graph.entities}
    assert {(names[edge.source], names[edge.target]) for edge in graph.relationships} == {
        ("Alice", "Bob"), ("Bob", "Alice"),
    }


def test_relationship_types_between_same_endpoints_remain_distinct():
    graph = build(candidate(), candidate(kind="spouse_of"))
    assert {edge.type for edge in graph.relationships} == {"parent_of", "spouse_of"}


def test_all_entity_references_resolve():
    graph = build(candidate(), candidate(source="David"))
    entity_ids = {entity.id for entity in graph.entities}
    assert all(edge.source in entity_ids and edge.target in entity_ids for edge in graph.relationships)


def test_all_evidence_references_resolve():
    graph = build(candidate(), candidate(source="David"))
    evidence_ids = {item.id for item in graph.evidence}
    assert all(edge.evidence_ids and set(edge.evidence_ids) <= evidence_ids for edge in graph.relationships)


def test_output_is_independent_of_candidate_order_and_input_is_not_modified():
    candidates = [candidate(source="David"), candidate(), candidate(kind="spouse_of")]
    before = [item.model_dump() for item in candidates]
    assert build(*candidates) == build(*reversed(candidates))
    assert [item.model_dump() for item in candidates] == before


def test_empty_candidates_produce_empty_graph():
    assert build().model_dump() == {"entities": [], "relationships": [], "evidence": []}


def test_case_01_expected_candidates_build_canonical_graph():
    case_dir = Path(__file__).resolve().parents[1] / "cases" / "case_01"
    result = ExtractionResult.model_validate_json(
        (case_dir / "expected_extraction.json").read_text(encoding="utf-8")
    )
    graph = build_graph(
        result.relationships, document="cases/case_01/source.txt",
        source_text=(case_dir / "source.txt").read_text(encoding="utf-8"),
    )
    assert len(graph.entities) == 5
    assert len(graph.relationships) == 6
    assert len(graph.evidence) == 5
    names = {entity.id: entity.name for entity in graph.entities}
    assert {(names[edge.source], edge.type, names[edge.target]) for edge in graph.relationships} == {
        ("Alice Chen", "settlor_of", "Evergreen Family Trust"),
        ("Alice Chen", "spouse_of", "David Chen"),
        ("Alice Chen", "parent_of", "Bob Chen"),
        ("David Chen", "parent_of", "Bob Chen"),
        ("Bob Chen", "beneficiary_of", "Evergreen Family Trust"),
        ("Carol Wong", "beneficiary_of", "Evergreen Family Trust"),
    }
    parents = [edge for edge in graph.relationships if edge.type == "parent_of"]
    assert parents[0].evidence_ids == parents[1].evidence_ids
    assert len(parents[0].evidence_ids) == 1
