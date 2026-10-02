from pydantic import BaseModel

from .types import RelationshipType


class Relationship(BaseModel):
    source: str
    type: RelationshipType
    target: str
    evidence_ids: list[str]
