from typing import Literal

from pydantic import BaseModel, Field


RelationshipType = Literal[
    "parent_of",
    "sibling_of",
    "spouse_of",
    "settlor_of",
    "trustee_of",
    "beneficiary_of",
]


class RelationshipCandidate(BaseModel):
    source_name: str = Field(min_length=1)
    relationship_type: RelationshipType
    target_name: str = Field(min_length=1)
    supporting_text: str = Field(min_length=1)


class ExtractionResult(BaseModel):
    relationships: list[RelationshipCandidate]
