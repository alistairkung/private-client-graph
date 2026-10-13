"""Read complete persisted Matter state for professional review."""

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select

from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.models import CanonicalGraph
from private_client_graph.persistence.database import database_engine
from private_client_graph.persistence.matters import matters
from private_client_graph.persistence.matter_state import load_matter_state


class MatterSummary(BaseModel):
    id: UUID
    external_reference: str
    title: str


def list_matters() -> list[MatterSummary]:
    statement = select(
        matters.c.id, matters.c.external_reference, matters.c.title
    ).order_by(matters.c.title, matters.c.id)
    with database_engine().connect() as connection:
        return [MatterSummary.model_validate(row) for row in connection.execute(statement).mappings()]


class AuthoritativeSource(BaseModel):
    title: str
    text: str


class MatterDetail(MatterSummary):
    authoritative_source: AuthoritativeSource
    current_graph: CanonicalGraph


def get_matter(internal_id: UUID) -> MatterDetail | None:
    with database_engine().connect().execution_options(isolation_level="REPEATABLE READ") as connection:
        row = connection.execute(
            select(matters).where(matters.c.id == internal_id)
        ).mappings().one_or_none()
        if row is None:
            return None
        state = load_matter_state(connection, internal_id)
    # The current practitioner contract is deliberately single-source. Never
    # display a multi-source graph against one arbitrarily chosen source panel.
    if len(state.sources) != 1:
        raise ValueError("The practitioner workspace requires exactly one Source")
    source = state.sources[0]
    return MatterDetail(
        id=row["id"], external_reference=row["external_reference"], title=row["title"],
        authoritative_source=AuthoritativeSource(title=source.title, text=source.text),
        current_graph=reconstruct_graph(state),
    )
