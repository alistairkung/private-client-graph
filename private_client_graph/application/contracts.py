"""Professional-review contracts; raw extraction stays inside the pipeline."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from private_client_graph.models import CanonicalGraph

AnalysisMode = Literal["live", "sample"]


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: AnalysisMode


class LiveAvailability(BaseModel):
    state: Literal["disabled", "available", "exhausted", "unavailable"]
    resets_at: datetime | None = None


class CaseDetail(BaseModel):
    title: str
    notice: str
    source_text: str
    live_analysis: LiveAvailability = LiveAvailability(state="disabled")


class Execution(BaseModel):
    mode: AnalysisMode
    run_artifact_id: str | None = None


class CaseAnalysis(BaseModel):
    execution: Execution
    graph: CanonicalGraph


class AnalysisError(BaseModel):
    stage: Literal["source", "provider", "sample", "persistence", "graph", "request", "availability"]
    message: str
    retryable: bool = False
    live_analysis: LiveAvailability | None = None
    run_artifact_id: str | None = None
