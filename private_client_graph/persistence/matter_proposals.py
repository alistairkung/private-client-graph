"""Concrete atomic persistence of pending proposals and reference reservations."""

from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, Column, MetaData, Table, Text, Uuid, select
from sqlalchemy.dialects.postgresql import JSONB, insert
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
from private_client_graph.canonical_state import single_source_state

from .database import database_engine
from .matter_state import insert_matter
from .proposal_errors import DuplicateReference, ProposalPersistenceFailure

metadata = MetaData()
proposals = Table(
    "matter_proposals",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("external_reference", Text, nullable=False),
    Column("matter_title", Text, nullable=False),
    Column("source_title", Text, nullable=False),
    Column("source_text", Text, nullable=False),
    Column("proposed_graph", JSONB, nullable=False),
)
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
    with database_engine().connect() as connection:
        row = connection.execute(
            select(proposals).where(proposals.c.id == proposal_id)
        ).mappings().one_or_none()
    return _detail(row) if row is not None else None


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

        proposal = _detail(row)
        matter_id = uuid4()
        inserted = insert_matter(
            connection, matter_id=matter_id,
            external_reference=proposal.external_reference,
            title=proposal.matter_title,
            state=single_source_state(Source(
                id="source_001", title=proposal.authoritative_source.title,
                text=proposal.authoritative_source.text,
            ), proposal.proposed_graph),
        )
        if not inserted:
            raise ProposalPersistenceFailure(ambiguous=False)
        transferred = connection.execute(
            reference_claims.update().where(
                reference_claims.c.canonical_reference
                == proposal.external_reference.casefold(),
                reference_claims.c.resource_kind == "matter_proposal",
                reference_claims.c.resource_id == proposal_id,
            ).values(resource_kind="matter", resource_id=matter_id)
        )
        if transferred.rowcount != 1:
            raise ProposalPersistenceFailure(ambiguous=False)
        consumed = connection.execute(
            proposals.delete().where(proposals.c.id == proposal_id)
        )
        if consumed.rowcount != 1:
            raise ProposalPersistenceFailure(ambiguous=False)

    return MatterDetail(
        id=matter_id,
        external_reference=proposal.external_reference,
        title=proposal.matter_title,
        authoritative_source=proposal.authoritative_source,
        current_graph=proposal.proposed_graph,
    )


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
    connection.execute(proposals.insert().values(
        id=snapshot.id,
        external_reference=snapshot.external_reference,
        matter_title=snapshot.matter_title,
        source_title=snapshot.authoritative_source.title,
        source_text=snapshot.authoritative_source.text,
        proposed_graph=snapshot.proposed_graph.model_dump(mode="json"),
    ))


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


def _detail(row: RowMapping) -> MatterProposalDetail:
    return MatterProposalDetail.model_validate({
        "id": row["id"],
        "external_reference": row["external_reference"],
        "matter_title": row["matter_title"],
        "authoritative_source": {"title": row["source_title"], "text": row["source_text"]},
        "proposed_graph": row["proposed_graph"],
    })
