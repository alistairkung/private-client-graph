"""Read only the fields needed to identify persisted Matters."""

from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import select

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
