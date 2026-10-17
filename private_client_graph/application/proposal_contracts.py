"""Matter Proposal contracts and opaque practitioner-supplied metadata."""

import unicodedata
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, computed_field, field_validator, model_validator

from private_client_graph.canonical_state import reconstruct_graph, single_source_state, validate_canonical_state
from private_client_graph.models.canonical_state import CanonicalState
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


class MatterIntakeMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_reference: str
    matter_title: str

    @field_validator("external_reference")
    @classmethod
    def reference_text(cls, value: str) -> str:
        return _opaque_text(value, limit=100)

    @field_validator("matter_title")
    @classmethod
    def title_text(cls, value: str) -> str:
        return _opaque_text(value, limit=200)


class ProposalMetadata(MatterIntakeMetadata):
    """Legacy single-PDF metadata, retained for existing callers."""
    source_title: str

    @field_validator("source_title")
    @classmethod
    def source_title_text(cls, value: str) -> str:
        return _opaque_text(value, limit=200)


class ProposalSourceMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    title: str

    @field_validator("id")
    @classmethod
    def source_identity(cls, value: str) -> str:
        if not value or len(value) > 80 or not value.isascii() or not all(
            character.isalnum() or character in "_-" for character in value
        ):
            raise ValueError("Use a Source ID of 1–80 ASCII letters, digits, underscores or hyphens")
        return value

    @field_validator("title")
    @classmethod
    def source_title_text(cls, value: str) -> str:
        return _opaque_text(value, limit=200)


class MatterProposalSummary(BaseModel):
    id: UUID
    external_reference: str
    matter_title: str


class MatterProposalDetail(MatterProposalSummary):
    authoritative_source: AuthoritativeSource | None
    proposed_graph: CanonicalGraph
    state: CanonicalState | None = None

    @model_validator(mode="after")
    def valid_source_and_graph(self) -> Self:
        MatterIntakeMetadata(external_reference=self.external_reference, matter_title=self.matter_title)
        if self.state is not None:
            validate_canonical_state(self.state)
            if not self.state.sources:
                raise ValueError("A proposal must retain at least one Source")
            for item in self.state.sources:
                _opaque_text(item.title, limit=200)
                if not item.text.strip():
                    raise ValueError("Each Authoritative Source must contain text")
            if reconstruct_graph(self.state) != self.proposed_graph:
                raise ValueError("Proposal graph must project its complete canonical state")
            source = self.state.sources[0] if len(self.state.sources) == 1 else None
            expected = AuthoritativeSource(title=source.title, text=source.text) if source else None
            if self.authoritative_source != expected:
                raise ValueError("The legacy Source view is available only for single-Source state")
            return self
        if self.authoritative_source is None:
            raise ValueError("Source-aware state is required for multiple Sources")
        ProposalMetadata(external_reference=self.external_reference, matter_title=self.matter_title,
                         source_title=self.authoritative_source.title)
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
