from pydantic import BaseModel, Field

from .types import RelationshipType


class RelationshipCandidate(BaseModel):
    source_name: str = Field(min_length=1)
    relationship_type: RelationshipType
    target_name: str = Field(min_length=1)
    supporting_text: str = Field(min_length=1)
