"""One fixed semantic workflow for live analysis and explicit extraction replay."""
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

from private_client_graph.graph import build_graph, build_canonical_state
from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.models.source import Source
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.models.sourced_extraction import SourcedRelationshipCandidate
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models import CanonicalGraph, ExtractionResult, RelationshipCandidate
from private_client_graph.resolution import ResolutionProvider, resolve_generative, resolve_sourced_generative, no_resolution

from .config import PipelineConfig
from .errors import PipelineExecutionError
from .models import PipelineInput, PipelineResult, SourcedPipelineResult


class GraphBuilder(Protocol):
    def __call__(self, candidates: list[RelationshipCandidate], *, document: str,
                 source_text: str) -> CanonicalGraph: ...


class StateBuilder(Protocol):
    def __call__(self, candidates: list[SourcedRelationshipCandidate], *,
                 sources: list[Source]) -> CanonicalState: ...


@dataclass(frozen=True)
class Pipeline:
    config: PipelineConfig
    extractor: Callable[[str], ExtractionResult] | None = None
    resolution_provider: ResolutionProvider | None = None
    graph_builder: GraphBuilder = build_graph
    source_extractor: Callable[[list[Source]], SourcedExtractionResult] | None = None
    state_builder: StateBuilder = build_canonical_state

    def __post_init__(self) -> None:
        if self.config.resolver == 'generative' and self.resolution_provider is None:
            raise ValueError('Generative resolution requires a provider')

    def run(self, input: PipelineInput) -> PipelineResult:
        try:
            if self.extractor is None:
                raise ValueError('Legacy execution requires an extractor')
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

    def run_sources(self, sources: list[Source]) -> SourcedPipelineResult:
        """Extract one final current snapshot from the complete ordered Source bundle."""
        if self.source_extractor is None:
            raise ValueError('Source-aware execution requires a source_extractor')
        # Reject ambiguous Source identity before invoking a paid provider.
        build_canonical_state([], sources=sources)
        try:
            extracted = self.source_extractor([source.model_copy(deep=True) for source in sources])
        except Exception as error:
            raise PipelineExecutionError('extraction') from error
        return self.run_from_sourced_extraction(sources, extracted)

    def run_from_sourced_extraction(self, sources: list[Source],
                                    extraction: SourcedExtractionResult) -> SourcedPipelineResult:
        """Replay explicitly attributed claims without guessing legacy attribution."""
        if not isinstance(extraction, SourcedExtractionResult):
            raise TypeError('Source-aware replay requires SourcedExtractionResult')
        extracted = extraction.model_copy(deep=True)
        try:
            if self.config.resolver == 'generative':
                assert self.resolution_provider is not None
                resolved = resolve_sourced_generative(extracted, sources, self.resolution_provider)
            else:
                resolved = extracted.model_copy(deep=True)
        except Exception as error:
            raise PipelineExecutionError('resolution', extracted=extracted) from error
        try:
            state = self.state_builder(resolved.relationships, sources=sources)
            graph = reconstruct_graph(state)
        except Exception as error:
            raise PipelineExecutionError('graph', extracted=extracted, resolved=resolved) from error
        return SourcedPipelineResult(extracted, resolved, state, graph)
