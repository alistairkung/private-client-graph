"""Frozen experimental inputs; evaluation annotations never enter model requests."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from private_client_graph.graph import ENDPOINT_TYPES
from private_client_graph.models import ExtractionResult, GroundTruth, SourcedExtractionResult
from private_client_graph.models.source import Source
from .source_attribution import SourceEvidenceApproval, validate_source_approval


class EndpointIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    candidate_index: int = Field(ge=0)
    endpoint: Literal["source_name", "target_name"]
    participant: str


class ResearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sample_id: str = Field(pattern=r"^[a-z0-9_]+$")
    case_id: str
    cohort: Literal["authored", "historical", "fresh"]
    source: str
    sources: list[Source] | None = None
    sourced_extraction: SourcedExtractionResult | None = None
    source_evidence: SourceEvidenceApproval | None = None
    truth: GroundTruth
    extraction: ExtractionResult | None = None
    annotations: list[EndpointIdentity] | None = None
    origin_hashes: dict[str, str] = Field(default_factory=dict)
    historical: dict[str, Any] | None = None

    @model_validator(mode="after")
    def validate_sources(self) -> "ResearchInput":
        if self.sources is not None:
            identifiers = [source.id for source in self.sources]
            if not identifiers or len(set(identifiers)) != len(identifiers) or any(not item.strip() for item in identifiers):
                raise ValueError('Source bundles require non-empty unique explicit identities')
        if self.sourced_extraction is not None and self.sources is None:
            raise ValueError('Attributed extraction requires explicit Sources')
        if self.source_evidence is not None:
            if self.sources is None:
                raise ValueError('Source approvals require explicit Sources')
            validate_source_approval(self.source_evidence, self.truth, self.sources)
        return self

    @model_validator(mode="after")
    def validate_annotations(self) -> "ResearchInput":
        if self.annotations is None:
            return self
        if self.extraction is None:
            raise ValueError("Endpoint annotations require a frozen extraction")
        expected = {(i, side) for i in range(len(self.extraction.relationships))
                    for side in ("source_name", "target_name")}
        actual = {(a.candidate_index, a.endpoint) for a in self.annotations}
        if actual != expected or len(actual) != len(self.annotations):
            raise ValueError("Annotations must cover every endpoint exactly once")
        people = {entity.id: entity.type for entity in self.truth.entities}
        for annotation in self.annotations:
            candidate = self.extraction.relationships[annotation.candidate_index]
            position = 0 if annotation.endpoint == "source_name" else 1
            if people.get(annotation.participant) != ENDPOINT_TYPES[candidate.relationship_type][position]:
                raise ValueError("Annotation participant or endpoint type is invalid")
        return self
