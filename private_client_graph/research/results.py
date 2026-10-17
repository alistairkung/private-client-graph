"""Typed persisted result contract for one research configuration run."""
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from private_client_graph.models import CanonicalGraph, EvaluationResult, ExtractionResult, SourcedExtractionResult
from private_client_graph.models.canonical_state import CanonicalState
from .source_attribution import SourceAttributionDiagnostic

from .metrics import IdentityDiagnostics
from .provider import TokenUsage


class ResearchResult(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)

    sample_id: str
    case_id: str
    cohort: Literal["authored", "historical", "fresh"]
    status: Literal[
        "completed",
        "provider_error",
        "parse_error",
        "edit_error",
        "graph_error",
        "evaluation_error",
        "uncertain",
        "unavailable",
    ] = "completed"
    stage: Literal["provider", "parse", "edits", "graph", "evaluation", "extraction"] | None = None
    graph: CanonicalGraph | None = None
    state: CanonicalState | None = None
    sourced_extraction: SourcedExtractionResult | None = None
    source_attribution: SourceAttributionDiagnostic | None = None
    evaluation: EvaluationResult | None = None
    identity: IdentityDiagnostics | None = None
    extraction: ExtractionResult | None = None
    edits: list[dict[str, Any]] | None = None
    configuration: Literal["noop", "generative_full_source"] | None = None
    repetition: int | None = None
    attempt_id: str | None = None
    error_type: str | None = None
    usage: TokenUsage | None = None
    incremental_cost: float | None = None
    provider_seconds: float | None = None
    resolution_seconds: float | None = None
    edit_seconds: float | None = None
    graph_seconds: float | None = None
    evaluation_seconds: float | None = None
    downstream_seconds: float | None = None
