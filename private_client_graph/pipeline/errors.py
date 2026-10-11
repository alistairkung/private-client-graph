"""Stage failures expose completed domain snapshots and preserve the chained cause."""
from typing import Literal

from private_client_graph.models import ExtractionResult


class PipelineExecutionError(Exception):
    """Only completed domain outputs cross this semantic failure boundary."""

    def __init__(self, stage: Literal['extraction', 'resolution', 'graph'], *,
                 extracted: ExtractionResult | None = None,
                 resolved: ExtractionResult | None = None):
        super().__init__(f'Analysis failed during {stage}')
        self.stage = stage
        self.extracted = extracted.model_copy(deep=True) if extracted is not None else None
        self.resolved = resolved.model_copy(deep=True) if resolved is not None else None
