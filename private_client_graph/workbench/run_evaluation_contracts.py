"""Versioned, backend-owned Run metrics and scientific comparison contracts."""
from typing import Literal

from pydantic import BaseModel, Field


# Compatibility name for the same research-owned frozen observation contract.
from private_client_graph.research.run_plan import ObservationSlot as PlannedObservation


class Coverage(BaseModel):
    planned: int = 0
    scored: int = 0
    pending: int = 0
    failed: int = 0
    uncertain: int = 0
    unavailable: int = 0


class ObservationCoverage(BaseModel):
    observation_id: str
    case_id: str
    state: Literal['scored', 'pending', 'failed', 'uncertain', 'unavailable']
    status: str
    reason: str | None = None


class CaseAggregate(BaseModel):
    case_id: str
    tp: int = 0
    fp: int = 0
    fn: int = 0
    f1: float | None = None
    coverage: Coverage = Field(default_factory=Coverage)


class RunAggregate(BaseModel):
    version: Literal['observation_micro_f1_v1'] = 'observation_micro_f1_v1'
    tp: int = 0
    fp: int = 0
    fn: int = 0
    f1: float | None = None
    coverage: Coverage = Field(default_factory=Coverage)
    cases: list[CaseAggregate] = Field(default_factory=list)
    state: Literal['complete', 'provisional', 'unavailable'] = 'unavailable'
    observations: list[ObservationCoverage] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


class AttemptCost(BaseModel):
    attempt_id: str
    incurred: bool = True
    cost: float | None = Field(default=None, ge=0, allow_inf_nan=False)
    currency: str | None = 'USD'
    reason: str | None = None


class RunCost(BaseModel):
    total: float | None = None
    known_subtotal: float | None = 0
    currency: str | None = 'USD'
    attempts: int = 0
    unpriced_attempts: int = 0
    reasons: list[str] = Field(default_factory=list)


class ScopeInput(BaseModel):
    input_id: str
    case_id: str
    cohort: str
    source_digest: str
    truth_digest: str
    samples: int
    repetitions: int


class BenchmarkScope(BaseModel):
    identity: str
    inputs: list[ScopeInput]
    input_mode: str
    evaluator_version: str
    aggregate_version: str
    unequal_allocation: bool = False


class ChartEligibility(BaseModel):
    f1_by_run: bool = False
    f1_vs_cost: bool = False
    f1_reasons: list[str] = Field(default_factory=list)
    cost_reasons: list[str] = Field(default_factory=list)


class RunEvaluation(BaseModel):
    api_version: Literal['2'] = '2'
    run_id: str
    aggregate: RunAggregate
    cost: RunCost
    scope: BenchmarkScope | None = None
    eligibility: ChartEligibility = Field(default_factory=ChartEligibility)
    artifact_digest: str | None = None
    full_pipeline_cost: float | None = None
    full_pipeline_cost_reason: str = 'Run-wide reconstruction is undefined; retained individual pipeline estimates remain separate.'
    reasons: list[str] = Field(default_factory=list)


class ObservationPair(BaseModel):
    left_observation: str
    right_observation: str
    left_sample: str
    right_sample: str


class PairingExclusion(BaseModel):
    side: Literal['left', 'right']
    observation_id: str
    reason: str


class RunComparison(BaseModel):
    api_version: Literal['2'] = '2'
    left_run_id: str
    right_run_id: str
    comparable_scope: bool = False
    scope_differences: list[str] = Field(default_factory=list)
    provenance_differences: list[str] = Field(default_factory=list)
    pairs: list[ObservationPair] = Field(default_factory=list)
    exclusions: list[PairingExclusion] = Field(default_factory=list)
    matched_inputs: int = 0
    unqualified_improvement_allowed: bool = False
    reasons: list[str] = Field(default_factory=list)
