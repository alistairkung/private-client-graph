"""Read-only projections for the private Benchmark v4 Workbench."""
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.research.provider import ModelSettings, TokenUsage
from private_client_graph.research.semantic_evidence.comparison import compare
from private_client_graph.research.semantic_evidence.inputs import Baseline, ExactOutcome
from private_client_graph.research.semantic_evidence.judging import Fact, FactStatus, Judgment, Quotation, Verdict
from private_client_graph.research.semantic_evidence.reporting import report
from private_client_graph.research.semantic_evidence.store import find

SemanticStatus = Literal['judged', 'invalid_judgment', 'deterministic_delivery_failure',
                         'unattempted', 'awaiting_receipt', 'interrupted', 'provider_failed']


class SemanticEvaluator(BaseModel):
    version: str
    prompt_sha256: str
    model: str
    settings: ModelSettings
    observation_origin: str


class SemanticOperations(BaseModel):
    planned_attempts: int
    reserved_attempts: int
    reused_judgments: int
    known_estimated_peak_usd: float | None
    reserved_attempts_without_usage: int
    mean_latency_seconds: float | None


class PotentialSupport(BaseModel):
    count: int | None
    formal_target_denominator: int
    recovered_exact_incomplete_denominator: int
    recovered_exact_incomplete_judged: int


class SemanticSummary(BaseModel):
    formal_targets: int
    recovered_targets: int
    semantic_outcomes: dict[SemanticStatus, int]
    verdicts: dict[Verdict, int]
    flags: dict[str, int]
    potentially_sufficient_overlooked_by_exact_matching: PotentialSupport


class SemanticReuse(BaseModel):
    origin_run: str
    origin_plan_sha256: str
    origin_request_sha256: str
    origin_receipt_sha256: str


class SemanticProvider(BaseModel):
    latency_seconds: float
    estimated_peak_usd: float | None
    usage: TokenUsage | None = None
    returned_model: str | None = None
    finish_reason: str | None = None
    status_code: int | None = None


class SemanticQuotation(Quotation):
    source_id: str


class SemanticTarget(BaseModel):
    id: str
    condition: str | None
    edge: SemanticEdge
    control: str | None
    deterministic: Baseline | None
    status: SemanticStatus
    flags: list[str]
    quotations: list[SemanticQuotation] = []
    judgment: Judgment | None = None
    error: str | None = None
    invalid_response: str | None = None
    provider: SemanticProvider | None = None
    reuse: SemanticReuse | None = None


class SemanticRunSummary(BaseModel):
    run_id: str
    plan_sha256: str
    target_summary: SemanticSummary
    operations: SemanticOperations


class SemanticEvidenceReport(SemanticRunSummary):
    status: Literal['Exploratory and unverified']
    evaluator: SemanticEvaluator
    targets: list[SemanticTarget]
    controls: list[SemanticTarget]


class SemanticOutcome(BaseModel):
    status: SemanticStatus
    verdict: Verdict | None
    exact_outcome: ExactOutcome
    potentially_sufficient: bool
    reused: bool


class SemanticFactChange(BaseModel):
    fact: Fact
    left: FactStatus
    right: FactStatus


class SemanticTransition(BaseModel):
    id: str
    condition: str
    edge: SemanticEdge
    left: SemanticOutcome
    right: SemanticOutcome
    facts_comparable: bool
    changed_facts: list[SemanticFactChange]


class SemanticComparison(BaseModel):
    status: Literal['Exploratory and unverified']
    evaluator: SemanticEvaluator
    formal_targets: int
    paired_valid_targets: int
    left: SemanticRunSummary
    right: SemanticRunSummary
    transitions: list[SemanticTransition]


def mount_semantic_evidence(app: FastAPI, root: Path, prefix: str) -> None:
    """Mount only behind the Benchmark v4 owner middleware."""
    @app.get(f'{prefix}/semantic-evidence/runs/{{run_id}}', response_model=SemanticEvidenceReport | None)
    def assessment(run_id: str) -> SemanticEvidenceReport | None:
        try:
            path = find(root, run_id)
            return SemanticEvidenceReport.model_validate(report(path)) if path else None
        except (ValueError, OSError, KeyError):
            raise HTTPException(409, 'The retained Semantic Evidence assessment could not be verified.') from None

    @app.get(f'{prefix}/semantic-evidence/comparison', response_model=SemanticComparison | None)
    def comparison(left: str, right: str) -> SemanticComparison | None:
        if left == right:
            raise HTTPException(422, 'Select two distinct Benchmark v4 Runs.')
        try:
            first, second = find(root, left), find(root, right)
            return SemanticComparison.model_validate(compare(first, second)) if first and second else None
        except (ValueError, OSError, KeyError):
            raise HTTPException(409, 'Semantic Evidence comparison requires verified assessments with the same target scope.') from None
