"""Batch authorisation, scientific outputs and local ledger values."""

from datetime import date
from typing import Annotated, Literal, Self

from pydantic import Field, model_validator

from benchmark_v3.portfolio import Count, Portfolio, PortfolioDecision
from benchmark_v3.replay_manifest import LiteralEdit, SavedIdeal
from benchmark_v3.research_contracts import (
    Contract, Digest, FamilyId, HypothesisRef, NonemptyNotes, Slug, Text,
)
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.models.evaluation_result import SemanticEdge

Stage = Literal[
    "design", "author", "realism", "freeze", "blind", "adjudicate", "audit",
    "masks", "technical", "admission_ready", "admitted", "returned", "quarantined",
]
Code = Literal[
    "budget", "isolation", "input_integrity", "uncertain_dispatch", "failed_dispatch",
    "documentary_realism", "scientific_review", "technical_validation",
]
Role = Literal["designer", "author", "realism", "annotation", "adjudication", "audit", "masked"]
ROLES = frozenset(("designer", "author", "realism", "annotation", "adjudication", "audit", "masked"))
SourceId = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,39}$")]
Commit = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
Risk = Literal[
    "joint_proof", "reader_disagreement", "ambiguous_identity_or_dates", "contradiction",
    "shortcut", "uncertain_provenance", "multiple_material_changes", "large_or_complex",
]


class Allocation(Contract):
    model: Text
    effort: Literal["low", "medium", "high", "xhigh"]
    rationale: Text


class IsolationScope(Contract):
    profile: Literal["benchmark_packet"]
    packet_implementation_sha256: Digest
    os_boundary_evidence_sha256: Digest
    custodian: Text
    scope_reference: Text


class FamilyAllocation(Contract):
    family_id: FamilyId
    hypothesis: HypothesisRef
    sessions: Count


class BatchManifest(Contract):
    schema_version: Literal[1]
    task_id: Slug
    batch_id: Slug
    namespace: Literal["development"]
    phase: Literal["pilot", "expansion"]
    portfolio_sha256: Digest
    previous_portfolio: Portfolio | None = None
    families: Annotated[list[FamilyAllocation], Field(min_length=1, max_length=20)]
    task_session_ceiling: Count
    max_parallel_families: Annotated[int, Field(strict=True, ge=1, le=20)] = 2
    repair_cycles: Literal[0, 1] = 1
    scope: IsolationScope
    models: dict[Role, Allocation]
    stop_conditions: NonemptyNotes

    @model_validator(mode="after")
    def verify_allocations(self) -> Self:
        families = [row.family_id for row in self.families]
        if len(set(families)) != len(families) or self.models.keys() != ROLES:
            raise ValueError("Allocate distinct families and specify all seven scientific roles.")
        if self.phase == "pilot" and len(families) != 3:
            raise ValueError("An efficiency pilot requires exactly three distinct families.")
        if sum(row.sessions for row in self.families) > self.task_session_ceiling:
            raise ValueError("Batch allocations exceed the task-wide session ceiling.")
        return self


class BatchDecision(Contract):
    schema_version: Literal[1]
    manifest_sha256: Digest
    portfolio: PortfolioDecision
    owner: Text
    decided_on: date
    decision_reference: Text


class PilotDecision(Contract):
    schema_version: Literal[1]
    pilot_batch_id: Slug
    summary_sha256: Digest
    status: Literal["continue", "stop"]
    owner: Text
    decision_reference: Text
    decided_on: date


class AuthorBrief(Contract):
    source_id: SourceId
    author: Text
    created_on: date
    provenance: Text
    participant_brief: Text
    received: list[SourceId]


class MatchedCondition(Contract):
    kind: Literal["literal_edit", "order_only"]
    edit: LiteralEdit | None = None
    order: list[SourceId] | None = None

    @model_validator(mode="after")
    def verify_control(self) -> Self:
        if self.kind == "literal_edit" and self.edit is not None and self.order is None:
            return self
        if self.kind == "order_only" and self.order and self.edit is None:
            return self
        raise ValueError("Declare one exact body edit or one Source order.")


class DesignOutput(Contract):
    neutral_brief: Text
    cutoff: date
    documentary_references: list[Text]
    private_history: Text
    inventory: Annotated[list[AuthorBrief], Field(min_length=1)]
    matched: list[MatchedCondition]
    candidates: list[SemanticEdge]
    required: dict[SourceId, list[SemanticEdge]]
    sections: dict[SourceId, list[SourceId]] = Field(default_factory=dict)
    scaling_snapshots: list[Count] = Field(default_factory=list)


class AuthoredSource(Contract):
    title: Text
    text: Text


class RealismReview(Contract):
    verdict: Literal["pass", "repair", "return"]
    summary: Text
    source_findings: dict[SourceId, Text]
    objections: list[Text] = Field(default_factory=list)
    repair_tickets: dict[SourceId, Text] = Field(default_factory=dict)


class Reading(Contract):
    candidates: SourcedExtractionResult
    reviewed_sources: Annotated[list[SourceId], Field(min_length=1)]
    open_questions: list[Text]


class Adjudication(Contract):
    key: SavedIdeal
    disagreement_resolutions: dict[Text, Text]
    source_audit: dict[SourceId, Text]
    unresolved: list[Text]


class MaskAssignment(Contract):
    condition: SourceId
    risk: Risk
    reason: Text
    question: Text
    included: Annotated[list[SourceId], Field(min_length=1)]
    remove_quotes: dict[SourceId, Text] = Field(default_factory=dict)
    present: list[SemanticEdge]
    absent: list[SemanticEdge]


class AuditReview(Contract):
    verdict: Literal["accept", "repair", "return", "quarantine"]
    summary: Text
    completeness: dict[SourceId, dict[SourceId, Text]]
    sufficiency: dict[SourceId, dict[Text, Text]]
    negative_controls: dict[SourceId, Text]
    shortcuts: dict[SourceId, Text]
    matched_controls: dict[SourceId, Text]
    risks: list[Risk]
    masks: list[MaskAssignment]
    objections: list[Text]
    limitations: list[Text]


class ExceptionRecord(Contract):
    stage: Stage
    family_id: FamilyId
    job: Text | None = None
    code: Code
    evidence: Text
    repair_permitted: bool
    human_action: Text | None
    remaining_work: Literal["family_halted", "task_halted"]


class FamilyDecision(Contract):
    family_id: FamilyId
    family_sha256: Digest
    disposition: Literal["accept", "return"]
    reason: Text


class AdmissionDecisions(Contract):
    schema_version: Literal[1]
    batch_id: Slug
    owner: Text
    decided_on: date
    source: Text
    reviewed_commit: Commit
    decisions: Annotated[list[FamilyDecision], Field(min_length=1)]

    @model_validator(mode="after")
    def verify_unique_families(self) -> Self:
        if len({item.family_id for item in self.decisions}) != len(self.decisions):
            raise ValueError("Supply one explicit decision per family.")
        return self
