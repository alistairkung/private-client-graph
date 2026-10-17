"""Explicit Source attribution for full-context extraction; legacy fixtures stay distinct."""
from pydantic import BaseModel, ConfigDict, Field

from .extraction_result import ExtractionResult
from .relationship_candidate import RelationshipCandidate


class SourcedRelationshipCandidate(RelationshipCandidate):
    model_config = ConfigDict(extra='forbid')
    source_id: str = Field(min_length=1)


class SourcedExtractionResult(BaseModel):
    model_config = ConfigDict(extra='forbid')
    relationships: list[SourcedRelationshipCandidate]


def source_extraction_from_legacy(extraction: ExtractionResult, *, source_id: str) -> SourcedExtractionResult:
    """Bind a known single Source explicitly, never infer it from quotes or titles."""
    return SourcedExtractionResult(relationships=[
        SourcedRelationshipCandidate(**candidate.model_dump(), source_id=source_id)
        for candidate in extraction.relationships
    ])
