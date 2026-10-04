"""Professional-review contracts; raw extraction stays inside the pipeline."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from private_client_graph.models import CanonicalGraph

AnalysisMode = Literal["live", "sample"]


class AnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: AnalysisMode


class CaseDetail(BaseModel):
    title: str
    notice: str
    source_text: str


class Execution(BaseModel):
    mode: AnalysisMode
    run_artifact_id: str | None = None


class CaseAnalysis(BaseModel):
    execution: Execution
    graph: CanonicalGraph


class AnalysisError(BaseModel):
    stage: Literal["source", "provider", "sample", "persistence", "graph", "request"]
    message: str
    retryable: bool = False
    run_artifact_id: str | None = None
