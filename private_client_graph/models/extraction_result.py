from pydantic import BaseModel

from .relationship_candidate import RelationshipCandidate


class ExtractionResult(BaseModel):
    relationships: list[RelationshipCandidate]
