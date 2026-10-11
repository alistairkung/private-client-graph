"""One fixed semantic workflow for live analysis and explicit extraction replay."""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict

from private_client_graph.graph import build_graph
from private_client_graph.models import CanonicalGraph, ExtractionResult, RelationshipCandidate
from private_client_graph.resolution import ResolutionProvider, resolve_generative, no_resolution


@dataclass(frozen=True)
class PipelineInput:
    source_text: str
    document: str


class PipelineConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')

    resolver: Literal['none', 'generative'] = 'none'


@dataclass(frozen=True)
class PipelineResult:
    extracted: ExtractionResult
    resolved: ExtractionResult
    graph: CanonicalGraph


class GraphBuilder(Protocol):
    def __call__(self, candidates: list[RelationshipCandidate], *, document: str,
                 source_text: str) -> CanonicalGraph: ...


class PipelineExecutionError(Exception):
    """Only completed domain outputs cross this semantic failure boundary."""

    def __init__(self, stage: Literal['extraction', 'resolution', 'graph'], *,
                 extracted: ExtractionResult | None = None,
                 resolved: ExtractionResult | None = None):
        super().__init__(f'Analysis failed during {stage}')
        self.stage = stage
        self.extracted = extracted.model_copy(deep=True) if extracted is not None else None
        self.resolved = resolved.model_copy(deep=True) if resolved is not None else None


@dataclass(frozen=True)
class Pipeline:
    config: PipelineConfig
    extractor: Callable[[str], ExtractionResult]
    resolution_provider: ResolutionProvider | None = None
    graph_builder: GraphBuilder = build_graph

    def __post_init__(self) -> None:
        if self.config.resolver == 'generative' and self.resolution_provider is None:
            raise ValueError('Generative resolution requires a provider')

    def run(self, input: PipelineInput) -> PipelineResult:
        try:
            extracted = self.extractor(input.source_text)
        except Exception as error:
            raise PipelineExecutionError('extraction') from error
        return self.run_from_extraction(input, extracted)

    def run_from_extraction(self, input: PipelineInput,
                            extraction: ExtractionResult) -> PipelineResult:
        extracted = extraction.model_copy(deep=True)
        try:
            if self.config.resolver == 'generative':
                assert self.resolution_provider is not None
                resolved = resolve_generative(extracted, input.source_text, self.resolution_provider)
            else:
                resolved = no_resolution(extracted)
        except Exception as error:
            raise PipelineExecutionError('resolution', extracted=extracted) from error
        try:
            graph = self.graph_builder(resolved.model_copy(deep=True).relationships,
                                       document=input.document, source_text=input.source_text)
        except Exception as error:
            raise PipelineExecutionError('graph', extracted=extracted, resolved=resolved) from error
        return PipelineResult(extracted.model_copy(deep=True), resolved.model_copy(deep=True),
                              graph.model_copy(deep=True))
