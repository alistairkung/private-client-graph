"""Read complete persisted Matter state for professional review."""

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select

from private_client_graph.canonical_state import reconstruct_graph, single_source_state
from private_client_graph.models import CanonicalGraph
from private_client_graph.models.source import Source
from private_client_graph.persistence.database import database_engine
from private_client_graph.persistence.matters import matters


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
    with database_engine().connect() as connection:
        row = connection.execute(
            select(matters).where(matters.c.id == internal_id)
        ).mappings().one_or_none()
    if row is None:
        return None
    graph = CanonicalGraph.model_validate(row["current_graph"])
    state = single_source_state(
        Source(id="source_001", title=row["source_title"], text=row["source_text"]), graph,
    )
    return MatterDetail(
        id=row["id"], external_reference=row["external_reference"], title=row["title"],
        authoritative_source=AuthoritativeSource(title=row["source_title"], text=row["source_text"]),
        current_graph=reconstruct_graph(state),
    )
