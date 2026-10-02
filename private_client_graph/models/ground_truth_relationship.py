from pydantic import BaseModel

from .types import RelationshipType


class GroundTruthRelationship(BaseModel):
    source: str
    type: RelationshipType
    target: str
    approved_evidence: list[str]
