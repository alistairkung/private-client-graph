"""Store/reconstruct one Matter Proposal inside the caller's transaction."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection

from private_client_graph.canonical_state import validate_canonical_state
from private_client_graph.models.canonical_state import CanonicalState

from . import proposal_records as records
from .proposal_records import proposals


def insert_proposal(
    connection: Connection, *, proposal_id: UUID, external_reference: str,
    title: str, state: CanonicalState,
) -> bool:
    """Insert a complete Matter Proposal, or leave an existing ID wholly unchanged.

    The caller owns commit/rollback and external-reference claim management.
    """
    validate_canonical_state(state)
    if not state.sources:
        raise ValueError("A Matter Proposal must retain its Source")
    inserted = connection.scalar(insert(proposals).values(
        id=proposal_id, external_reference=external_reference, matter_title=title,
    ).on_conflict_do_nothing(index_elements=[proposals.c.id]).returning(proposals.c.id))
    if inserted is None:
        return False
    _insert_facts(connection, proposal_id, state)
    return True


def load_proposal_state(connection: Connection, proposal_id: UUID) -> CanonicalState:
    """Read all facts in one statement snapshot, including at Read Committed."""
    row = connection.execute(text("""
        SELECT
          (SELECT jsonb_agg(to_jsonb(s) ORDER BY position) FROM proposal_sources s
             WHERE proposal_id=:owner) AS sources,
          (SELECT jsonb_agg(to_jsonb(e) ORDER BY position) FROM proposal_entities e
             WHERE proposal_id=:owner) AS entities,
          (SELECT jsonb_agg(to_jsonb(e) ORDER BY position) FROM proposal_evidence e
             WHERE proposal_id=:owner) AS evidence,
          (SELECT jsonb_agg(jsonb_build_object(
             'source', r.source_id, 'type', r.type, 'target', r.target_id,
             'evidence_ids', (SELECT jsonb_agg(evidence_id ORDER BY position)
                FROM proposal_relationship_evidence a
                WHERE a.proposal_id=r.proposal_id AND a.relationship_id=r.id)
           ) ORDER BY r.id) FROM proposal_relationships r
             WHERE proposal_id=:owner) AS relationships
    """), {"owner": proposal_id}).mappings().one()
    state = CanonicalState.model_validate({key: value or [] for key, value in row.items()})
    validate_canonical_state(state)
    return state


def _insert_facts(connection: Connection, proposal_id: UUID, state: CanonicalState) -> None:
    for table, items in (
        (records.sources, state.sources), (records.entities, state.entities),
        (records.evidence, state.evidence),
    ):
        if items:
            connection.execute(table.insert(), [
                {"proposal_id": proposal_id, "position": position, **item.model_dump()}
                for position, item in enumerate(items)
            ])
    entity_types = {entity.id: entity.type for entity in state.entities}
    for position, edge in enumerate(state.relationships):
        connection.execute(records.relationships.insert().values(
            proposal_id=proposal_id, id=position, source_id=edge.source,
            source_type=entity_types[edge.source], target_id=edge.target,
            target_type=entity_types[edge.target], type=edge.type,
            support_id=edge.evidence_ids[0],
        ))
        connection.execute(records.support.insert(), [
            {"proposal_id": proposal_id, "relationship_id": position,
             "evidence_id": evidence_id, "position": index}
            for index, evidence_id in enumerate(edge.evidence_ids)
        ])
