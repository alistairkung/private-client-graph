"""The finite experiment matrix; no executable topology or plugin registry."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .inputs import ResearchInput
from .provider import ModelSettings


class Pricing(BaseModel):
    model_config = ConfigDict(extra="forbid")
    currency: str = "USD"
    input_per_million: float = Field(ge=0)
    output_per_million: float = Field(ge=0)
    cached_input_per_million: float | None = Field(default=None, ge=0)
    source_url: str
    retrieved_at: str
    model: str


class ExperimentPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["demonstration", "task_a_diagnostic", "task_b_pilot"] = "demonstration"
    task_id: str = "91"
    inputs: list[ResearchInput]
    settings: ModelSettings = Field(default_factory=ModelSettings)
    repetitions: int = Field(default=3, ge=1, le=3)
    fresh_extractions: int = Field(default=0, ge=0, le=5)
    max_calls: int = Field(default=5, ge=0, le=38)
    pricing: Pricing | None = None
    authorization_reference: str | None = None
    reviewed_commit: str | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "ExperimentPlan":
        if self.kind != 'demonstration' and self.task_id != ('91' if self.kind == 'task_a_diagnostic' else '92'):
            raise ValueError('Task ID must match the authorized work item')
        if self.kind == "task_a_diagnostic" and self.max_calls > 5:
            raise ValueError("Task A has at most five attempts")
        if len({s.sample_id for s in self.inputs}) != len(self.inputs):
            raise ValueError("Duplicate sample IDs")
        if any(s.extraction is None or s.cohort == 'fresh' for s in self.inputs):
            raise ValueError("Frozen inputs require extractions and a non-fresh cohort")
        if self.fresh_extractions and not any(s.case_id == 'case_03' for s in self.inputs):
            raise ValueError("Fresh extractions require a frozen Case 03 Source/truth")
        if self.pricing is not None and self.pricing.model != self.settings.model:
            raise ValueError("Pricing must identify the configured model")
        return self
