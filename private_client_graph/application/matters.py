"""Read complete persisted Matter state for professional review."""

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select

from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.models import CanonicalGraph
from private_client_graph.models.canonical_state import CanonicalState
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
    authoritative_source: AuthoritativeSource | None
    current_graph: CanonicalGraph
    state: CanonicalState | None = None


def get_matter(internal_id: UUID) -> MatterDetail | None:
    with database_engine().connect().execution_options(isolation_level="REPEATABLE READ") as connection:
        row = connection.execute(
            select(matters).where(matters.c.id == internal_id)
        ).mappings().one_or_none()
        if row is None:
            return None
        state = load_matter_state(connection, internal_id)
    if not state.sources:
        raise ValueError("A Matter must retain at least one Source")
    source = state.sources[0] if len(state.sources) == 1 else None
    return MatterDetail(
        id=row["id"], external_reference=row["external_reference"], title=row["title"],
        authoritative_source=AuthoritativeSource(title=source.title, text=source.text) if source else None,
        current_graph=reconstruct_graph(state), state=state,
    )
