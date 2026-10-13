"""Store/reconstruct one accepted Matter inside the caller's transaction."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from private_client_graph.canonical_state import validate_canonical_state
from private_client_graph.models.canonical_state import CanonicalState

from . import matter_records as records
from .matters import matters


def insert_matter(
    connection: Connection, *, matter_id: UUID, external_reference: str,
    title: str, state: CanonicalState,
) -> bool:
    """Insert a complete Matter, or leave an existing ID wholly unchanged.

    The caller owns commit/rollback and external-reference claim management.
    """
    validate_canonical_state(state)
    if not state.sources:
        raise ValueError("A Matter must retain its Source")
    inserted = connection.scalar(insert(matters).values(
        id=matter_id, external_reference=external_reference, title=title,
    ).on_conflict_do_nothing(index_elements=[matters.c.id]).returning(matters.c.id))
    if inserted is None:
        return False
    _insert_facts(connection, matter_id, state)
    return True


def load_matter_state(connection: Connection, matter_id: UUID) -> CanonicalState:
    """Read within one transaction snapshot; never infer identity from names."""
    sources = connection.execute(select(records.sources).where(
        records.sources.c.matter_id == matter_id,
    ).order_by(records.sources.c.position)).mappings().all()
    entities = connection.execute(select(records.entities).where(
        records.entities.c.matter_id == matter_id,
    ).order_by(records.entities.c.position)).mappings().all()
    evidence = connection.execute(select(records.evidence).where(
        records.evidence.c.matter_id == matter_id,
    ).order_by(records.evidence.c.position)).mappings().all()
    edges = connection.execute(select(records.relationships).where(
        records.relationships.c.matter_id == matter_id,
    ).order_by(records.relationships.c.id)).mappings().all()
    associations = connection.execute(select(records.support).where(
        records.support.c.matter_id == matter_id,
    ).order_by(records.support.c.relationship_id, records.support.c.position)).mappings()
    evidence_ids: dict[int, list[str]] = {}
    for association in associations:
        evidence_ids.setdefault(association["relationship_id"], []).append(association["evidence_id"])
    state = CanonicalState.model_validate({
        "sources": sources, "entities": entities, "evidence": evidence,
        "relationships": [
            {"source": edge["source_id"], "type": edge["type"], "target": edge["target_id"],
             "evidence_ids": evidence_ids.get(edge["id"], [])}
            for edge in edges
        ],
    })
    validate_canonical_state(state)
    return state


def _insert_facts(connection: Connection, matter_id: UUID, state: CanonicalState) -> None:
    for table, items in (
        (records.sources, state.sources), (records.entities, state.entities),
        (records.evidence, state.evidence),
    ):
        if items:
            connection.execute(table.insert(), [
                {"matter_id": matter_id, "position": position, **item.model_dump()}
                for position, item in enumerate(items)
            ])
    entity_types = {entity.id: entity.type for entity in state.entities}
    for position, edge in enumerate(state.relationships):
        connection.execute(records.relationships.insert().values(
            matter_id=matter_id, id=position, source_id=edge.source,
            source_type=entity_types[edge.source], target_id=edge.target,
            target_type=entity_types[edge.target], type=edge.type,
            support_id=edge.evidence_ids[0],
        ))
        connection.execute(records.support.insert(), [
            {"matter_id": matter_id, "relationship_id": position,
             "evidence_id": evidence_id, "position": index}
            for index, evidence_id in enumerate(edge.evidence_ids)
        ])
