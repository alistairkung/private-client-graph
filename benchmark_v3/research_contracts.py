"""Version 1 contracts for portfolio research, commissioning and reconciliation."""

from datetime import date, datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, StringConstraints, model_validator

Text = Annotated[str, StringConstraints(pattern=r"\S")]
Slug = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9-]{1,63}$")]
FamilyId = Annotated[str, StringConstraints(pattern=r"^[A-Z][A-Z0-9-]{0,23}$")]
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Revision = Annotated[int, Field(strict=True, ge=1)]
NonemptyNotes = Annotated[list[Text], Field(min_length=1)]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PublicReference(Contract):
    title: Text
    url: HttpUrl
    relevance: Text


class Grounding(Contract):
    legal_workflow: Text
    retainer: Text
    meeting_purpose: Text
    documentary_situation: Text
    confidence: Literal["documented", "provisional"]
    references: list[PublicReference]
    assumptions: list[Text]
    practitioner_unknowns: NonemptyNotes

    @model_validator(mode="after")
    def require_grounding(self) -> Self:
        if self.confidence == "documented" and not self.references:
            raise ValueError("Documented grounding requires public references.")
        if self.confidence == "provisional" and not self.assumptions:
            raise ValueError("Provisional grounding requires explicit assumptions.")
        return self


class Objective(Contract):
    primary_axis: Slug
    secondary_axes: list[Slug]
    failure_mechanism: Text
    falsifiable_hypothesis: Text
    coverage_gap: Text

    @model_validator(mode="after")
    def require_distinct_axes(self) -> Self:
        axes = [self.primary_axis, *self.secondary_axes]
        if len(set(axes)) != len(axes):
            raise ValueError("Primary and secondary difficulty axes must be distinct.")
        return self


class Design(Contract):
    scenario: Text
    genres_and_provenance: NonemptyNotes
    intervention: Text
    invariants: NonemptyNotes
    expected_sensitivity_or_invariance: Text
    negative_controls: NonemptyNotes
    evidence_dependencies: NonemptyNotes
    shortcut_heuristics: NonemptyNotes
    success_criteria: NonemptyNotes


class Feasibility(Contract):
    conditions: Annotated[int, Field(strict=True, ge=1)]
    documentary_complexity: Text
    authoring_and_review_effort: Text
    ontology_compatibility: Text
    infrastructure_reuse: Text
    risks_and_limits: NonemptyNotes


class Hypothesis(Contract):
    schema_version: Literal[1, 2]
    hypothesis_id: Slug
    revision: Revision
    previous_revision_sha256: Digest | None
    family_id: FamilyId
    title: Text
    status: Literal["proposed"]
    grounding: Grounding
    objective: Objective
    design: Design
    feasibility: Feasibility

    @model_validator(mode="after")
    def require_revision_lineage(self) -> Self:
        if (self.revision == 1) != (self.previous_revision_sha256 is None):
            raise ValueError("Only revision 1 has no previous revision digest.")
        if self.schema_version == 1 and self.feasibility.conditions < 2:
            raise ValueError("Version 1 hypotheses require a matched condition.")
        return self


class HypothesisRef(Contract):
    hypothesis_id: Slug
    revision: Revision
    hypothesis_sha256: Digest


class OwnerDecision(HypothesisRef):
    schema_version: Literal[1]
    status: Literal["approved", "returned", "rejected"]
    owner: Text
    decided_on: date
    decision_reference: Text


class Gap(Contract):
    axes: Annotated[list[Slug], Field(min_length=1)]
    finding: Text


class FamilyAssessment(Contract):
    family_id: FamilyId
    assessment: Text
    overlap: Text


class PlanningResult(Contract):
    schema_version: Literal[1]
    portfolio_summary: Text
    family_assessments: list[FamilyAssessment]
    gaps: list[Gap]
    proposals: list[Hypothesis]
    stopping_criteria: NonemptyNotes


class SessionProvenance(Contract):
    session: Text
    packet_sha256: Digest
    prompt_sha256: Digest
    output_sha256: Digest
    model: Text
    effort: Text
    completed_at: datetime


class PlanningRecord(Contract):
    schema_version: Literal[1]
    provenance: SessionProvenance
    result: PlanningResult


class VerifiedFinding(Contract):
    axis: Slug
    finding: Text
    evidence: NonemptyNotes


class ReconciliationResult(Contract):
    schema_version: Literal[1]
    operationalisation: Literal[
        "adequate", "partial", "not_operationalised", "invalidated_by_shortcut", "unassessable",
    ]
    achieved_vs_intended: Text
    verified_findings: list[VerifiedFinding]
    additional_coverage: Text
    redundancy: Text
    remaining_gaps: list[Gap]
    recommendation: Literal["retain", "refine_future_designs", "stop_expanding"]
    rationale: Text

    @model_validator(mode="after")
    def require_adequate_evidence(self) -> Self:
        if self.operationalisation == "adequate" and not self.verified_findings:
            raise ValueError("Adequate operationalisation requires verified findings.")
        return self


class ReconciliationContext(Contract):
    family_id: FamilyId
    hypothesis: HypothesisRef
    admission_sha256: Digest


class ReconciliationRecord(Contract):
    schema_version: Literal[1]
    provenance: SessionProvenance
    context: ReconciliationContext
    result: ReconciliationResult


class Axis(Contract):
    id: Slug
    category: Literal["reasoning", "documentary", "workflow_discovery"]
    description: Text
    scope: Literal["in_scope", "conditional", "deferred"]


class AdmittedFamily(Contract):
    family_id: FamilyId
    name: Text
    protocol: Literal["historical", "architect_v1"]
    admission_sha256: Digest
    hypothesis: HypothesisRef | None
    title: Text
    primary_axis: Slug
    secondary_axes: list[Slug]
    intended_difficulty: Text
    verified_findings: list[VerifiedFinding]
    incidental_challenges: NonemptyNotes
    matched_controls: NonemptyNotes
    known_shortcuts_and_limits: NonemptyNotes
    documentary_genres: NonemptyNotes
    overlap: Text

    @model_validator(mode="after")
    def verify_historical_lineage(self) -> Self:
        if (self.protocol == "historical") != (self.hypothesis is None):
            raise ValueError("Only historical families have no approved hypothesis lineage.")
        if self.protocol == "architect_v1" and self.verified_findings:
            raise ValueError("New verified findings belong in the reconciliation record.")
        return self


class CoverageRegister(Contract):
    schema_version: Literal[1]
    taxonomy: Annotated[list[Axis], Field(min_length=1)]
    families: list[AdmittedFamily]
    gaps: list[Gap]
