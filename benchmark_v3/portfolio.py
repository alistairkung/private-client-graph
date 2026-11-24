"""Versioned Research Architect portfolio and explicit owner approval contracts."""

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from benchmark_v3.research_contracts import (
    Contract, Digest, FamilyId, Gap, HypothesisRef, NonemptyNotes, Revision, Slug, Text,
)

Count = Annotated[int, Field(strict=True, ge=1)]
Tier = Literal["routine", "moderate", "complex", "administrative", "giant"]


class ExistingFamily(Contract):
    family_id: FamilyId
    admission_sha256: Digest
    primary_axis: Slug
    secondary_axes: list[Slug]
    conditions: list[Text]


class FamilySlot(Contract):
    family_id: FamilyId
    hypothesis: HypothesisRef
    primary_axis: Slug
    secondary_axes: list[Slug]
    tier: Tier
    expected_sources: Count
    retainer: Text
    workflow: Text
    natural_condition: Text
    matched_conditions: list[Text]
    estimated_sessions: Count
    estimated_cost_usd: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None
    independent_authoring: NonemptyNotes

    @model_validator(mode="after")
    def verify_workload(self) -> Self:
        if self.tier == "giant" and not 100 <= self.expected_sources <= 200:
            raise ValueError("Plan 100 to 200 Sources for the giant Matter.")
        descriptions = [self.natural_condition, *self.matched_conditions]
        if len(set(descriptions)) != len(descriptions):
            raise ValueError("Condition descriptions must be distinct.")
        return self


class PortfolioProposal(Contract):
    schema_version: Literal[1]
    portfolio_id: Slug
    revision: Revision
    previous_revision_sha256: Digest | None
    namespace: Literal["development"]
    target_families: Literal[20]
    coverage_sha256: Digest
    existing: list[ExistingFamily]
    slots: list[FamilySlot]
    admission_criteria: NonemptyNotes
    stopping_criteria: NonemptyNotes
    gaps: list[Gap]

    @model_validator(mode="after")
    def verify_family_counts(self) -> Self:
        families = [row.family_id for row in self.existing] + [row.family_id for row in self.slots]
        if len(set(families)) != len(families) or len(families) > self.target_families:
            raise ValueError("Count each independent family once, up to the portfolio target.")
        if sum(slot.tier == "giant" for slot in self.slots) > 1:
            raise ValueError("The portfolio may plan at most one giant Matter.")
        if (self.revision == 1) != (self.previous_revision_sha256 is None):
            raise ValueError("Revised portfolios must identify their previous digest.")
        return self


class Portfolio(PortfolioProposal):
    architect_session: Text


class PortfolioDecision(Contract):
    schema_version: Literal[1]
    portfolio_sha256: Digest
    status: Literal["approved", "returned", "rejected"]
    owner: Text
    decided_on: date
    decision_reference: Text
