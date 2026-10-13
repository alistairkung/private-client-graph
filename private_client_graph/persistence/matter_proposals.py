"""Concrete atomic persistence of pending proposals and reference reservations."""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, MetaData, Table, Text, Uuid, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection, RowMapping
from sqlalchemy.exc import DBAPIError, SQLAlchemyError

from private_client_graph.application.matters import MatterDetail
from private_client_graph.application.proposal_contracts import (
    MatterProposalDetail,
    MatterProposalSummary,
    ProposalMetadata,
    ReferenceOwner,
)
from private_client_graph.models import CanonicalGraph
from private_client_graph.models.source import Source
from private_client_graph.canonical_state import reconstruct_graph, single_source_state
from private_client_graph.models.canonical_state import CanonicalState

from .database import database_engine
from .matter_state import insert_matter
from .proposal_records import proposals
from .proposal_state import insert_proposal, load_proposal_state
from .proposal_errors import DuplicateReference, ProposalPersistenceFailure

metadata = MetaData()
reference_claims = Table(
    "external_matter_reference_claims",
    metadata,
    Column("canonical_reference", Text, primary_key=True),
    Column("resource_kind", Text, nullable=False),
    Column("resource_id", Uuid, nullable=False),
    CheckConstraint(
        "resource_kind IN ('matter_proposal', 'matter')",
        name="reference_claim_resource_kind",
    ),
)


def list_proposals() -> list[MatterProposalSummary]:
    statement = select(
        proposals.c.id,
        proposals.c.external_reference,
        proposals.c.matter_title,
    ).order_by(
        proposals.c.matter_title,
        proposals.c.id,
    )
    with database_engine().connect() as connection:
        return [
            MatterProposalSummary.model_validate(row)
            for row in connection.execute(statement).mappings()
        ]


def get_proposal(proposal_id: UUID) -> MatterProposalDetail | None:
    with database_engine().connect().execution_options(isolation_level="REPEATABLE READ") as connection:
        row = connection.execute(
            select(proposals).where(proposals.c.id == proposal_id)
        ).mappings().one_or_none()
        return _detail(row, load_proposal_state(connection, proposal_id)) if row is not None else None


def find_reference(external_reference: str) -> ReferenceOwner | None:
    with database_engine().connect() as connection:
        return _find_reference(connection, external_reference)


def save_proposal(
    metadata: ProposalMetadata,
    source_text: str,
    proposed_graph: CanonicalGraph,
) -> MatterProposalDetail:
    snapshot = MatterProposalDetail.model_validate({
        "id": uuid4(),
        **metadata.model_dump(exclude={"source_title"}),
        "authoritative_source": {"title": metadata.source_title, "text": source_text},
        "proposed_graph": proposed_graph.model_dump(),
    })
    with _proposal_transaction() as connection:
        _claim_reference(connection, snapshot)
        _insert_proposal(connection, snapshot)
    return snapshot


def discard_proposal(proposal_id: UUID) -> bool:
    with _proposal_transaction() as connection:
        existing = connection.scalar(
            select(proposals.c.id).where(proposals.c.id == proposal_id).with_for_update()
        )
        if existing is None:
            return False
        connection.execute(reference_claims.delete().where(
            reference_claims.c.resource_kind == "matter_proposal",
            reference_claims.c.resource_id == proposal_id,
        ))
        connection.execute(proposals.delete().where(proposals.c.id == proposal_id))
    return True


def confirm_proposal(proposal_id: UUID) -> MatterDetail | None:
    with _proposal_transaction() as connection:
        row = connection.execute(
            select(proposals).where(proposals.c.id == proposal_id).with_for_update()
        ).mappings().one_or_none()
        if row is None:
            return None
        # Validate the single-source presentation contract before consuming state.
        state = load_proposal_state(connection, proposal_id)
        proposal = _detail(row, state)
        matter_id = _promote_locked_proposal(connection, row, state)
        return MatterDetail(
            id=matter_id, external_reference=proposal.external_reference,
            title=proposal.matter_title, authoritative_source=proposal.authoritative_source,
            current_graph=proposal.proposed_graph,
        )


def promote_proposal(connection: Connection, proposal_id: UUID) -> UUID | None:
    """Copy and consume a complete source-aware proposal in the caller's transaction.

    The root lock serializes supported confirmation/discard operations. Facts
    are loaded in one statement snapshot.
    No Matter identity is allocated before locked state has been validated.
    """
    row = connection.execute(
        select(proposals).where(proposals.c.id == proposal_id).with_for_update()
    ).mappings().one_or_none()
    if row is None:
        return None
    state = load_proposal_state(connection, proposal_id)
    return _promote_locked_proposal(connection, row, state)


def _promote_locked_proposal(connection: Connection, row: RowMapping, state: CanonicalState) -> UUID:
    proposal_id = row["id"]
    matter_id = uuid4()
    if not insert_matter(
        connection, matter_id=matter_id, external_reference=row["external_reference"],
        title=row["matter_title"], state=state,
    ):
        raise ProposalPersistenceFailure(ambiguous=False)
    transferred = connection.execute(reference_claims.update().where(
        reference_claims.c.canonical_reference == row["external_reference"].casefold(),
        reference_claims.c.resource_kind == "matter_proposal",
        reference_claims.c.resource_id == proposal_id,
    ).values(resource_kind="matter", resource_id=matter_id))
    if transferred.rowcount != 1:
        raise ProposalPersistenceFailure(ambiguous=False)
    consumed = connection.execute(proposals.delete().where(proposals.c.id == proposal_id))
    if consumed.rowcount != 1:
        raise ProposalPersistenceFailure(ambiguous=False)
    return matter_id


def _claim_reference(connection: Connection, snapshot: MatterProposalDetail) -> None:
    statement = (
        insert(reference_claims)
        .values(
            canonical_reference=snapshot.external_reference.casefold(),
            resource_kind="matter_proposal",
            resource_id=snapshot.id,
        )
        .on_conflict_do_nothing(index_elements=[reference_claims.c.canonical_reference])
        .returning(reference_claims.c.canonical_reference)
    )
    claimed = connection.scalar(statement)
    if claimed is not None:
        return
    owner = _find_reference(connection, snapshot.external_reference)
    if owner is None:
        raise ProposalPersistenceFailure(ambiguous=False)
    raise DuplicateReference(owner)


def _insert_proposal(connection: Connection, snapshot: MatterProposalDetail) -> None:
    state = single_source_state(Source(
        id="source_001", title=snapshot.authoritative_source.title,
        text=snapshot.authoritative_source.text,
    ), snapshot.proposed_graph)
    if not insert_proposal(
        connection, proposal_id=snapshot.id, external_reference=snapshot.external_reference,
        title=snapshot.matter_title, state=state,
    ):
        raise ProposalPersistenceFailure(ambiguous=False)


@contextmanager
def _proposal_transaction() -> Iterator[Connection]:
    commit_started = False
    try:
        with database_engine().begin() as connection:
            yield connection
            commit_started = True
    except SQLAlchemyError as error:
        # Server constraint/transaction rejection proves rollback, unlike a lost
        # connection while COMMIT is being acknowledged.
        sqlstate = getattr(error.orig, "sqlstate", "") if isinstance(error, DBAPIError) else ""
        known_rejection = isinstance(sqlstate, str) and (
            sqlstate.startswith("23") or sqlstate in {"40001", "40P01"}
        )
        raise ProposalPersistenceFailure(
            ambiguous=commit_started and not known_rejection,
        ) from error


def _find_reference(connection: Connection, external_reference: str) -> ReferenceOwner | None:
    statement = select(
        reference_claims.c.resource_kind,
        reference_claims.c.resource_id,
    ).where(
        reference_claims.c.canonical_reference == external_reference.strip().casefold(),
    )
    row = connection.execute(statement).mappings().one_or_none()
    return ReferenceOwner.model_validate(row) if row is not None else None


def _detail(row: RowMapping, state: CanonicalState) -> MatterProposalDetail:
    if len(state.sources) != 1:
        raise ValueError("The practitioner workspace requires exactly one Source")
    source = state.sources[0]
    return MatterProposalDetail.model_validate({
        "id": row["id"],
        "external_reference": row["external_reference"],
        "matter_title": row["matter_title"],
        "authoritative_source": {"title": source.title, "text": source.text},
        "proposed_graph": reconstruct_graph(state),
    })
