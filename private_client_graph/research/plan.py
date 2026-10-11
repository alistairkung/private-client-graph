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
    kind: Literal["demonstration", "task_a_diagnostic", "task_b_pilot", "live_experiment"] = "demonstration"
    task_id: str = "91"
    inputs: list[ResearchInput]
    settings: ModelSettings = Field(default_factory=ModelSettings)
    effective_model: str | None = None
    repetitions: int = Field(default=3, ge=1, le=3)
    fresh_extractions: int = Field(default=0, ge=0, le=5)
    max_calls: int = Field(default=5, ge=0, le=38)
    pricing: Pricing | None = None
    authorization_reference: str | None = None
    reviewed_commit: str | None = None

    @model_validator(mode="after")
    def validate_scope(self) -> "ExperimentPlan":
        if self.kind in ('task_a_diagnostic', 'task_b_pilot') and self.task_id != ('91' if self.kind == 'task_a_diagnostic' else '92'):
            raise ValueError('Task ID must match the authorized work item')
        if self.kind == "task_a_diagnostic" and self.max_calls > 5:
            raise ValueError("Task A has at most five attempts")
        if self.kind == "task_b_pilot":
            if not self.effective_model or not self.effective_model.strip():
                raise ValueError("Task B requires a preflighted effective model")
            if self.pricing is None:
                raise ValueError("Task B requires preflighted pricing metadata")
        if len({s.sample_id for s in self.inputs}) != len(self.inputs):
            raise ValueError("Duplicate sample IDs")
        if any(s.extraction is None or s.cohort == 'fresh' for s in self.inputs):
            raise ValueError("Frozen inputs require extractions and a non-fresh cohort")
        if self.fresh_extractions and not any(s.case_id == 'case_03' for s in self.inputs):
            raise ValueError("Fresh extractions require a frozen Case 03 Source/truth")
        priced_model = self.effective_model or self.settings.model
        if self.pricing is not None and self.pricing.model != priced_model:
            raise ValueError("Pricing must identify the effective model")
        return self


    @property
    def resolution_repetitions(self) -> int:
        return self.repetitions

    @property
    def maximum_attempts(self) -> int:
        return len(self.inputs) * self.repetitions + self.fresh_extractions * (1 + self.repetitions)


class FiniteExperimentPlan(ExperimentPlan):
    """Versioned finite matrix; legacy study plans retain their original rules."""
    plan_version: Literal[2, 3, 4] = 2
    task_call_cap: int = Field(default=0, ge=0, le=10000)
    invocation_cap: int = Field(default=0, ge=0, le=38)
    kind: Literal["demonstration", "live_experiment"] = "demonstration"
    input_mode: Literal["saved", "fresh"] = "saved"
    execution_mode: Literal["replay", "recorded", "live"] = "replay"
    resolver: Literal["none", "generative"] = "none"

    @model_validator(mode="after")
    def validate_finite_matrix(self) -> "FiniteExperimentPlan":
        if self.plan_version not in (2, 3):
            raise ValueError("Legacy finite matrices require version 2 or 3")
        live = self.execution_mode == 'live'
        if live != (self.plan_version == 3) or live != (self.kind == 'live_experiment'):
            raise ValueError('Live matrices require explicit version 3 plans')
        if live and (not self.maximum_attempts or not self.task_call_cap):
            raise ValueError('Live execution requires a paid matrix and explicit task cap')
        if not live and self.task_call_cap:
            raise ValueError('Offline plans cannot authorize paid calls')
        if not self.inputs:
            raise ValueError("Select at least one input")
        if self.input_mode == 'fresh':
            if len(self.inputs) != 1 or self.inputs[0].sample_id != 'case_03_fixture' or not self.fresh_extractions:
                raise ValueError("Fresh recorded extraction supports the Case 03 authored Source only")
        elif self.fresh_extractions:
            raise ValueError("Saved inputs cannot request fresh extractions")
        if self.execution_mode == 'replay' and (self.resolver != 'none' or self.input_mode != 'saved'):
            raise ValueError("Replay requires saved extractions and no resolution; generative replay is not free")
        if self.resolver == 'none' and self.repetitions != 1:
            raise ValueError("No resolution has one deterministic observation per input")
        if self.invocation_cap > self.maximum_attempts or (self.maximum_attempts and not self.invocation_cap):
            raise ValueError('Invocation bound must fit the frozen matrix')
        if self.max_calls != self.maximum_attempts:
            raise ValueError("The frozen call maximum must match the finite matrix")
        return self

    @property
    def resolution_repetitions(self) -> int:
        return self.repetitions if self.resolver == 'generative' else 0

    @property
    def maximum_attempts(self) -> int:
        samples = self.fresh_extractions if self.input_mode == 'fresh' else len(self.inputs)
        return self.fresh_extractions + samples * self.resolution_repetitions
