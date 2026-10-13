"""Request-local execution values, separate from persisted domain aggregates."""
from dataclasses import dataclass

from private_client_graph.models import CanonicalGraph, ExtractionResult


@dataclass(frozen=True)
class PipelineInput:
    source_text: str
    document: str


@dataclass(frozen=True)
class PipelineResult:
    extracted: ExtractionResult
    resolved: ExtractionResult
    graph: CanonicalGraph
