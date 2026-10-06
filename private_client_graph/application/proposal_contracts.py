"""Matter Proposal contracts and opaque practitioner-supplied metadata."""

import unicodedata
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field, field_validator, model_validator

from private_client_graph.canonical_state import single_source_state
from private_client_graph.models import CanonicalGraph
from private_client_graph.models.source import Source

from .matters import AuthoritativeSource


def _opaque_text(value: str, *, limit: int) -> str:
    if any(unicodedata.category(character) in {"Cc", "Zl", "Zp"} for character in value):
        raise ValueError("Control characters and line breaks are not permitted")
    value = value.strip()
    if not value or len(value) > limit:
        raise ValueError(f"A non-empty value of at most {limit} characters is required")
    return value


class ProposalMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_reference: str
    matter_title: str
    source_title: str

    @field_validator("external_reference")
    @classmethod
    def reference_text(cls, value: str) -> str:
        return _opaque_text(value, limit=100)

    @field_validator("matter_title", "source_title")
    @classmethod
    def title_text(cls, value: str) -> str:
        return _opaque_text(value, limit=200)


class MatterProposalSummary(BaseModel):
    id: UUID
    external_reference: str
    matter_title: str


class MatterProposalDetail(MatterProposalSummary):
    authoritative_source: AuthoritativeSource
    proposed_graph: CanonicalGraph

    @model_validator(mode="after")
    def valid_source_and_graph(self) -> Self:
        ProposalMetadata(
            external_reference=self.external_reference,
            matter_title=self.matter_title,
            source_title=self.authoritative_source.title,
        )
        if not self.authoritative_source.text.strip():
            raise ValueError("The Authoritative Source must contain text")
        single_source_state(
            Source(
                id="source_001",
                title=self.authoritative_source.title,
                text=self.authoritative_source.text,
            ),
            self.proposed_graph,
        )
        return self


class ReferenceOwner(BaseModel):
    resource_kind: Literal["matter_proposal", "matter"]
    resource_id: UUID

    @computed_field  # type: ignore[prop-decorator]
    @property
    def location(self) -> str:
        collection = (
            "matter-proposals" if self.resource_kind == "matter_proposal" else "matters"
        )
        return f"/api/{collection}/{self.resource_id}"
