"""Deterministic single-document graphs and explicitly sourced canonical state."""

from collections.abc import Sequence
from private_client_graph.models import (
    CanonicalGraph,
    Entity,
    EntityType,
    Evidence,
    Relationship,
    RelationshipCandidate,
    RelationshipType,
    SourcedRelationshipCandidate,
)

from private_client_graph.models.source import Source
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.sourced_evidence import SourcedEvidence

ENDPOINT_TYPES: dict[RelationshipType, tuple[EntityType, EntityType]] = {
    "parent_of": ("person", "person"),
    "sibling_of": ("person", "person"),
    "spouse_of": ("person", "person"),
    "settlor_of": ("person", "trust"),
    "trustee_of": ("person", "trust"),
    "beneficiary_of": ("person", "trust"),
}
SYMMETRIC_TYPES = {"spouse_of", "sibling_of"}


def build_graph(
    candidates: Sequence[RelationshipCandidate], *, document: str, source_text: str
) -> CanonicalGraph:
    """Validate all candidates, then normalize them without modifying the input.

    Names are exact, case-sensitive identity keys for Case 01 only. IDs are local
    to this graph, assigned in sorted order for reproducible output. Any invalid
    candidate raises ValueError; no partial graph is returned. Verbatim matching
    checks quote occurrence, not whether the quote semantically supports an edge.
    """
    entity_types = _validate_candidates(candidates, source_text)
    entities = _build_entities(entity_types)
    evidence = _build_evidence(candidates, document)
    relationships = _build_relationships(
        candidates, entities, [evidence[item.supporting_text].id for item in candidates])

    return CanonicalGraph(
        entities=list(entities.values()),
        relationships=relationships,
        evidence=list(evidence.values()),
    )


def _validate_candidates(
    candidates: Sequence[RelationshipCandidate], source_text: str
) -> dict[str, EntityType]:
    entity_types: dict[str, EntityType] = {}
    for index, candidate in enumerate(candidates):
        for field in ("source_name", "target_name", "supporting_text"):
            if not getattr(candidate, field).strip():
                raise ValueError(f"Candidate {index}: {field} must not be empty or whitespace-only")
        relationship_type = candidate.relationship_type
        if relationship_type not in ENDPOINT_TYPES:
            raise ValueError(f"Candidate {index}: unsupported relationship type {relationship_type!r}")
        if candidate.supporting_text not in source_text:
            raise ValueError(f"Candidate {index}: supporting_text does not occur verbatim in source")
        if candidate.source_name == candidate.target_name:
            raise ValueError(f"Candidate {index}: self-relationship for {candidate.source_name!r}")
        names = (candidate.source_name, candidate.target_name)
        for name, entity_type in zip(names, ENDPOINT_TYPES[relationship_type]):
            if name in entity_types and entity_types[name] != entity_type:
                raise ValueError(f"Candidate {index}: conflicting entity types for {name!r}")
            entity_types[name] = entity_type

    return entity_types


def _build_entities(entity_types: dict[str, EntityType]) -> dict[str, Entity]:
    return {
        name: Entity(id=f"entity_{index:03d}", type=entity_types[name], name=name)
        for index, name in enumerate(sorted(entity_types), start=1)
    }


def _build_evidence(
    candidates: Sequence[RelationshipCandidate], document: str
) -> dict[str, Evidence]:
    return {
        quote: Evidence(id=f"evidence_{index:03d}", document=document, supporting_text=quote)
        for index, quote in enumerate(
            sorted({candidate.supporting_text for candidate in candidates}), start=1
        )
    }


def _build_relationships(
    candidates: Sequence[RelationshipCandidate],
    entities: dict[str, Entity],
    evidence_ids: Sequence[str],
) -> list[Relationship]:
    edges: dict[tuple[str, RelationshipType, str], set[str]] = {}
    for candidate, evidence_id in zip(candidates, evidence_ids, strict=True):
        source, target = candidate.source_name, candidate.target_name
        if candidate.relationship_type in SYMMETRIC_TYPES:
            source, target = sorted((source, target))
        key = (source, candidate.relationship_type, target)
        edges.setdefault(key, set()).add(evidence_id)

    return [
        Relationship(
            source=entities[source].id,
            type=relationship_type,
            target=entities[target].id,
            evidence_ids=sorted(edges[(source, relationship_type, target)]),
        )
        for source, relationship_type, target in sorted(edges)
    ]


def build_canonical_state(
    candidates: Sequence[SourcedRelationshipCandidate], *, sources: Sequence[Source]
) -> CanonicalState:
    """Validate attributed final-current claims and construct one deterministic state.

    Source order is retained. Temporal interpretation belongs to extraction; this
    boundary never drops claims or infers attribution from titles or quote matches.
    """
    from private_client_graph.canonical_state import validate_canonical_state

    sources = [source.model_copy(deep=True) for source in sources]
    source_lookup = _validated_sources(sources)
    entities = _build_entities(_sourced_entity_types(candidates, source_lookup))
    evidence = _build_sourced_evidence(candidates, source_lookup)
    relationships = _build_relationships(candidates, entities,
        [evidence[(item.source_id, item.supporting_text)].id for item in candidates])
    state = CanonicalState(sources=sources, entities=list(entities.values()),
                           relationships=relationships, evidence=list(evidence.values()))
    validate_canonical_state(state)
    return state


def _validated_sources(sources: Sequence[Source]) -> dict[str, Source]:
    source_lookup = {source.id: source for source in sources}
    if not sources or len(source_lookup) != len(sources) or any(not source.id.strip() for source in sources):
        raise ValueError('Sources require non-empty unique IDs and at least one Source')
    return source_lookup


def _sourced_entity_types(
    candidates: Sequence[SourcedRelationshipCandidate], sources: dict[str, Source]
) -> dict[str, EntityType]:
    entity_types: dict[str, EntityType] = {}
    for candidate in candidates:
        if candidate.source_id not in sources:
            raise ValueError(f'Unresolved candidate Source reference: {candidate.source_id!r}')
        types = _validate_candidates([candidate], sources[candidate.source_id].text)
        for name, entity_type in types.items():
            if name in entity_types and entity_types[name] != entity_type:
                raise ValueError(f'Conflicting entity types for {name!r}')
            entity_types[name] = entity_type
    return entity_types


def _build_sourced_evidence(
    candidates: Sequence[SourcedRelationshipCandidate], sources: dict[str, Source]
) -> dict[tuple[str, str], SourcedEvidence]:
    keys = sorted({(item.source_id, item.supporting_text) for item in candidates})
    return {
        key: SourcedEvidence(id=f'evidence_{index:03d}', source_id=key[0],
                            document=sources[key[0]].title, supporting_text=key[1])
        for index, key in enumerate(keys, start=1)
    }
