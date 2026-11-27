"""Read-only projections for the private Benchmark v4 Workbench."""
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.research.benchmark_v4_scoring import DeliveredGraphMetrics
from private_client_graph.research.provider import ModelSettings, TokenUsage
from private_client_graph.research.semantic_evidence.comparison import compare_reports
from private_client_graph.research.semantic_evidence.inputs import Baseline, ExactOutcome
from private_client_graph.research.semantic_evidence.judging import CandidatePair, PairDecision, Quotation, Verdict
from private_client_graph.research.semantic_evidence.reporting import EvaluationState, report_run

SemanticStatus = Literal['judged', 'invalid_judgment', 'deterministic_delivery_failure', 'no_eligible_comparison',
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


class SemanticTargetRate(BaseModel):
    count: int
    targets: int
    rate: float | None


class SemanticMultiSourceEvidenceCoverage(BaseModel):
    targets: int
    matched_target_equivalents: float
    mean: float | None


class SemanticSummary(BaseModel):
    formal_targets: int
    semantic_outcomes: dict[SemanticStatus, int]
    pair_verdicts: dict[Verdict, int]
    candidate_pairs: int
    evidence_support: SemanticTargetRate
    proof_completion: SemanticTargetRate
    multi_source_evidence_coverage: SemanticMultiSourceEvidenceCoverage
    exact_matched_members: int
    unmatched_required_members: int
    targets_with_added_matches: int
    additional_matched_members: int
    newly_completed_proofs: int


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


class SemanticRoute(BaseModel):
    members: list[str]
    matched_members: list[str]
    complete: bool


class SemanticTarget(BaseModel):
    id: str
    condition: str
    edge: SemanticEdge
    deterministic: Baseline
    status: SemanticStatus
    members: list[SemanticQuotation]
    quotations: list[SemanticQuotation]
    exact_matches: dict[str, str]
    semantic_members: list[str]
    routes: list[SemanticRoute]
    candidate_pairs: list[CandidatePair]
    decisions: list[PairDecision]
    error: str | None = None
    invalid_response: str | None = None
    provider: SemanticProvider | None = None
    reuse: SemanticReuse | None = None


class SemanticRunSummary(BaseModel):
    run_id: str
    plan_sha256: str | None
    state: EvaluationState
    graph_f1: DeliveredGraphMetrics | None
    target_summary: SemanticSummary
    operations: SemanticOperations | None


class SemanticEvidenceReport(SemanticRunSummary):
    methodology: str
    scope_note: str
    evaluator: SemanticEvaluator
    targets: list[SemanticTarget]


class SemanticOutcome(BaseModel):
    status: SemanticStatus
    exact_outcome: ExactOutcome
    complete: bool
    reused: bool


MemberMatch = Literal['exact', 'semantic', 'unmatched']


class SemanticMemberChange(BaseModel):
    member_id: str
    source_id: str
    quotation: str
    left: MemberMatch
    right: MemberMatch


class SemanticTransition(BaseModel):
    id: str
    condition: str
    edge: SemanticEdge
    left: SemanticOutcome
    right: SemanticOutcome
    changed_members: list[SemanticMemberChange]


class SemanticComparison(BaseModel):
    methodology: str
    scope_note: str
    evaluator: SemanticEvaluator
    formal_targets: int
    comparable: bool
    paired_valid_targets: int
    left: SemanticRunSummary
    right: SemanticRunSummary
    transitions: list[SemanticTransition]


def mount_semantic_evidence(app: FastAPI, root: Path, prefix: str) -> None:
    """Mount only behind the Benchmark v4 owner middleware."""
    @app.get(f'{prefix}/semantic-evidence/runs/{{run_id}}', response_model=SemanticEvidenceReport)
    def assessment(run_id: str) -> SemanticEvidenceReport:
        try:
            return SemanticEvidenceReport.model_validate(report_run(root, run_id))
        except (ValueError, OSError, KeyError):
            raise HTTPException(409, 'The retained PCG Evaluation could not be verified.') from None

    @app.get(f'{prefix}/semantic-evidence/comparison', response_model=SemanticComparison)
    def comparison(left: str, right: str) -> SemanticComparison:
        if left == right:
            raise HTTPException(422, 'Select two distinct Benchmark v4 Runs.')
        try:
            return SemanticComparison.model_validate(compare_reports(report_run(root, left), report_run(root, right)))
        except (ValueError, OSError, KeyError):
            raise HTTPException(409, 'PCG Evaluation comparison requires verified Runs with the same frozen scope and matching contract.') from None
