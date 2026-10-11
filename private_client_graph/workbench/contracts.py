"""Version 1 read contracts, independent of HTTP and the research runner."""
from typing import Any, Literal

from pydantic import BaseModel, Field

from private_client_graph.models import EvaluationResult
from private_client_graph.models.evaluation_result import SemanticEdge


class HistoryItem(BaseModel):
    id: str
    artifact_path: str
    experiment_id: str | None = None
    created_at: str | None = None
    artifact_version: int | None = None
    digest: str
    indexed_at: str = ""
    integrity: Literal["verified", "corrupt", "unsupported", "missing"] = "verified"
    integrity_reason: str | None = None
    freshness: Literal["current", "changed", "missing"] = "current"
    lifecycle: Literal["complete", "incomplete", "failed", "unavailable", "frozen", "running", "stopping", "stopped", "interrupted"] = "unavailable"
    kind: str | None = None
    model: str | None = None
    cases: list[str] = Field(default_factory=list)
    configurations: list[str] = Field(default_factory=list)
    cohorts: list[str] = Field(default_factory=list)
    scored: int | None = None
    planned: int | None = None


class HistoryPage(BaseModel):
    api_version: Literal["1"] = "1"
    items: list[HistoryItem]
    total: int
    offset: int
    limit: int


class EvidenceQuote(BaseModel):
    id: str
    source_id: str
    text: str
    # Unicode code-point offsets in the frozen Source, not browser UTF-16 offsets.
    occurrences: list[tuple[int, int]]


class RelationshipOutcome(BaseModel):
    id: str
    edge: SemanticEdge
    outcome: Literal["matched", "missing", "extra", "provenance_failure"]
    expected: list[EvidenceQuote]
    predicted: list[EvidenceQuote]


class Observation(BaseModel):
    id: str
    configuration: str
    repetition: int | None = None
    status: str
    stage: str | None = None
    error_type: str | None = None
    evaluation: EvaluationResult | None = None
    delta_f1: float | None = None
    identity: dict[str, Any] | None = None
    identity_reason: str | None = None
    relationships: list[RelationshipOutcome] = Field(default_factory=list)
    execution: dict[str, Any] = Field(default_factory=dict)


class Sample(BaseModel):
    id: str
    case_id: str
    cohort: str
    source: str | None
    source_digest: str | None
    truth_digest: str | None
    extraction_digest: str | None
    unavailable_reason: str | None = None
    observations: list[Observation]
    resolver_mean_f1: float | None = None
    mean_delta_f1: float | None = None
    scored: int
    planned: int
    outcome_filters: list[str] = Field(default_factory=list)


class CohortMetric(BaseModel):
    name: str
    baseline_mean: float | None
    treatment_mean: float | None
    baseline_scored: int
    treatment_scored: int


class CohortSummary(BaseModel):
    cohort: str
    samples: int
    scored_repetitions: int
    failed_repetitions: int
    not_attempted_repetitions: int
    metrics: list[CohortMetric]


class ExperimentDetail(BaseModel):
    api_version: Literal["1"] = "1"
    history: HistoryItem
    configuration: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    operations: dict[str, Any] = Field(default_factory=dict)
    cohorts: dict[str, Any] = Field(default_factory=dict)
    cohort_summaries: list[CohortSummary] = Field(default_factory=list)
    sessions: list[dict[str, Any]] = Field(default_factory=list)
    samples: list[Sample] = Field(default_factory=list)


class ComparedObservation(BaseModel):
    left_sample: str
    right_sample: str
    configuration: str
    repetition: int | None
    left_f1: float | None
    right_f1: float | None
    delta_f1: float | None
    reason: str | None = None


class Exclusion(BaseModel):
    side: Literal["left", "right"]
    sample_id: str
    reason: str


class Comparison(BaseModel):
    api_version: Literal["1"] = "1"
    left: HistoryItem
    right: HistoryItem
    differences: list[str]
    observations: list[ComparedObservation]
    exclusions: list[Exclusion]
    matched_inputs: int
    scored_pairs: int
