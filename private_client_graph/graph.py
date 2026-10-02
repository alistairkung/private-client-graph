"""Deterministic construction of a single-document relationship graph."""

from collections.abc import Sequence
from typing import Literal

from pydantic import BaseModel

from private_client_graph.models import RelationshipCandidate, RelationshipType


EntityType = Literal["person", "trust"]

ENDPOINT_TYPES: dict[RelationshipType, tuple[EntityType, EntityType]] = {
    "parent_of": ("person", "person"),
    "sibling_of": ("person", "person"),
    "spouse_of": ("person", "person"),
    "settlor_of": ("person", "trust"),
    "trustee_of": ("person", "trust"),
    "beneficiary_of": ("person", "trust"),
}
SYMMETRIC_TYPES = {"spouse_of", "sibling_of"}


class Entity(BaseModel):
    id: str
    type: EntityType
    name: str


class Relationship(BaseModel):
    source: str
    type: RelationshipType
    target: str
    evidence_ids: list[str]


class Evidence(BaseModel):
    id: str
    document: str
    supporting_text: str


class CanonicalGraph(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]
    evidence: list[Evidence]


def build_graph(
    candidates: Sequence[RelationshipCandidate], *, document: str, source_text: str
) -> CanonicalGraph:
    """Validate all candidates, then normalize them without modifying the input.

    Names are exact, case-sensitive identity keys for Case 01 only. IDs are local
    to this graph, assigned in sorted order for reproducible output. Any invalid
    candidate raises ValueError; no partial graph is returned. Verbatim matching
    checks quote occurrence, not whether the quote semantically supports an edge.
    """
    # Validation: reject invalid claims and collect consistent endpoint types.
    entity_types: dict[str, EntityType] = {}
    for index, candidate in enumerate(candidates):
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

    # Normalization: construct unique entities and evidence in a stable order.
    entities = {
        name: Entity(id=f"entity_{index:03d}", type=entity_types[name], name=name)
        for index, name in enumerate(sorted(entity_types), start=1)
    }
    evidence = {
        quote: Evidence(id=f"evidence_{index:03d}", document=document, supporting_text=quote)
        for index, quote in enumerate(
            sorted({candidate.supporting_text for candidate in candidates}), start=1
        )
    }
    edges: dict[tuple[str, RelationshipType, str], set[str]] = {}
    for candidate in candidates:
        source, target = candidate.source_name, candidate.target_name
        if candidate.relationship_type in SYMMETRIC_TYPES:
            source, target = sorted((source, target))
        key = (source, candidate.relationship_type, target)
        edges.setdefault(key, set()).add(evidence[candidate.supporting_text].id)

    relationships = [
        Relationship(
            source=entities[source].id,
            type=relationship_type,
            target=entities[target].id,
            evidence_ids=sorted(edges[(source, relationship_type, target)]),
        )
        for source, relationship_type, target in sorted(edges)
    ]
    return CanonicalGraph(
        entities=list(entities.values()),
        relationships=relationships,
        evidence=list(evidence.values()),
    )
