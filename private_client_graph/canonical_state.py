"""Identity-preserving adaptation of canonical facts, independent of extraction."""

from collections.abc import Iterable

from private_client_graph.graph import ENDPOINT_TYPES, SYMMETRIC_TYPES
from private_client_graph.models import CanonicalGraph, Evidence
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.source import Source
from private_client_graph.models.sourced_evidence import SourcedEvidence


def single_source_state(source: Source, graph: CanonicalGraph) -> CanonicalState:
    """Bind a legacy single-source graph explicitly, never by document label."""
    state = CanonicalState(
        sources=[source.model_copy(deep=True)],
        entities=[entity.model_copy(deep=True) for entity in graph.entities],
        relationships=[edge.model_copy(deep=True) for edge in graph.relationships],
        evidence=[
            SourcedEvidence(**item.model_dump(), source_id=source.id)
            for item in graph.evidence
        ],
    )
    validate_canonical_state(state)
    return state


def reconstruct_graph(state: CanonicalState) -> CanonicalGraph:
    """Project facts without renaming, regrouping, sorting, or changing evidence."""
    validate_canonical_state(state)
    return CanonicalGraph(
        entities=[entity.model_copy(deep=True) for entity in state.entities],
        relationships=[edge.model_copy(deep=True) for edge in state.relationships],
        evidence=[
            Evidence(id=item.id, document=item.document, supporting_text=item.supporting_text)
            for item in state.evidence
        ],
    )


def validate_canonical_state(state: CanonicalState) -> None:
    """Reject invalid facts, without repairing or mutating reviewed state."""
    _require_unique_ids((source.id for source in state.sources), "Source")
    _require_unique_ids((entity.id for entity in state.entities), "Entity")
    _require_unique_ids((item.id for item in state.evidence), "Evidence")
    for entity in state.entities:
        if not entity.name.strip():
            raise ValueError("Entity name must be non-empty")
    sources = {source.id: source for source in state.sources}
    quotes: set[tuple[str, str]] = set()
    for item in state.evidence:
        if item.source_id not in sources:
            raise ValueError(f"Unresolved Evidence Source reference: {item.source_id!r}")
        if not item.supporting_text.strip():
            raise ValueError("Evidence supporting text must be non-empty")
        if item.supporting_text not in sources[item.source_id].text:
            raise ValueError("Evidence must occur verbatim in its Source")
        key = (item.source_id, item.supporting_text)
        if key in quotes:
            raise ValueError("Duplicate Source and Evidence quote")
        quotes.add(key)
    _validate_relationships(state)


def _validate_relationships(state: CanonicalState) -> None:
    entities = {entity.id: entity for entity in state.entities}
    evidence_ids = {item.id for item in state.evidence}
    edges: set[tuple[str, str, str]] = set()
    for edge in state.relationships:
        if edge.source not in entities or edge.target not in entities:
            raise ValueError("Unresolved Relationship Entity reference")
        if edge.source == edge.target:
            raise ValueError("Self-relationship is not permitted")
        if edge.type not in ENDPOINT_TYPES:
            raise ValueError(f"Unsupported relationship type: {edge.type!r}")
        actual_types = (entities[edge.source].type, entities[edge.target].type)
        if actual_types != ENDPOINT_TYPES[edge.type]:
            raise ValueError("Invalid Relationship endpoint types")
        if not edge.evidence_ids:
            raise ValueError("Relationship must have at least one Evidence association")
        if len(set(edge.evidence_ids)) != len(edge.evidence_ids):
            raise ValueError("Duplicate Relationship–Evidence association")
        if not set(edge.evidence_ids) <= evidence_ids:
            raise ValueError("Unresolved Relationship Evidence reference")
        source, target = edge.source, edge.target
        if edge.type in SYMMETRIC_TYPES:
            source, target = sorted((source, target))
        key = (source, edge.type, target)
        if key in edges:
            raise ValueError("Duplicate canonical Relationship")
        edges.add(key)


def _require_unique_ids(ids: Iterable[str], kind: str) -> None:
    seen: set[str] = set()
    for identifier in ids:
        if not identifier.strip():
            raise ValueError(f"{kind} ID must be non-empty")
        if identifier in seen:
            raise ValueError(f"Duplicate {kind} ID: {identifier!r}")
        seen.add(identifier)
