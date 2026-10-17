"""Single-configuration execution matrices, additive to historical study plans."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .plan import FiniteExperimentPlan
from .case_metadata import CaseMetadata


class ObservationSlot(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    observation_id: str
    sample_id: str
    case_id: str
    configuration: Literal['noop', 'generative_full_source']
    repetition: int
    extraction_attempt_id: str | None = None


class RunPlan(FiniteExperimentPlan):
    """Freeze planned membership before execution, including extraction failures."""
    plan_version: Literal[2, 3, 4] = 4
    experiment_id: str | None = None
    run_id: str | None = None
    draft_revision: int | None = None
    max_calls: int = Field(default=0, ge=0, le=10000)
    repetitions: int = Field(default=1, ge=1, le=3)
    planned_slots: list[ObservationSlot] = Field(default_factory=list)
    case_metadata: dict[str, CaseMetadata] = Field(default_factory=dict)
    evaluator_version: str = 'semantic_edges_v1'
    aggregate_version: Literal['observation_micro_f1_v1'] = 'observation_micro_f1_v1'

    @model_validator(mode='after')
    def validate_scope(self) -> 'RunPlan':
        if not self.inputs or len({sample.sample_id for sample in self.inputs}) != len(self.inputs):
            raise ValueError('Select distinct frozen inputs')
        if any(sample.extraction is None or sample.cohort == 'fresh' for sample in self.inputs):
            raise ValueError('Templates require repository-owned frozen inputs')
        if any(sample.sources is not None and len(sample.sources) > 1 for sample in self.inputs) and self.resolver != 'none':
            raise ValueError('Source-aware Runs support no resolution only')
        if self.experiment_id or self.case_metadata:
            self._validate_case_metadata()
        if self.pricing is not None and self.pricing.model != (self.effective_model or self.settings.model):
            raise ValueError('Pricing must identify the effective model')
        return self

    def _validate_case_metadata(self) -> None:
        if set(self.case_metadata) != {sample.sample_id for sample in self.inputs}:
            raise ValueError('Runs require frozen case metadata for every input')
        for sample in self.inputs:
            metadata = self.case_metadata[sample.sample_id]
            if metadata.id != sample.sample_id or metadata.case_id != sample.case_id:
                raise ValueError('Frozen case metadata must match input identities')

    @model_validator(mode='after')
    def validate_finite_matrix(self) -> 'RunPlan':
        if self.plan_version != 4:
            raise ValueError('Single-configuration Runs require plan version 4')
        live = self.execution_mode == 'live'
        if live != (self.kind == 'live_experiment'):
            raise ValueError('Live execution requires an explicit live plan')
        if live and (not self.maximum_attempts or not self.task_call_cap):
            raise ValueError('Live execution requires a paid matrix and explicit task cap')
        if not live and self.task_call_cap:
            raise ValueError('Offline plans cannot authorize paid calls')
        if self.input_mode == 'fresh':
            if not self.fresh_extractions or any(sample.cohort != 'authored' for sample in self.inputs):
                raise ValueError('Fresh extraction requires authored source templates and a sample count')
        elif self.fresh_extractions:
            raise ValueError('Saved inputs cannot request fresh extractions')
        if self.execution_mode == 'replay' and (self.resolver != 'none' or self.input_mode != 'saved'):
            raise ValueError('Replay requires saved extractions and no resolution')
        if self.resolver == 'none' and self.repetitions != 1:
            raise ValueError('No resolution has one deterministic observation per input')
        if self.invocation_cap > self.maximum_attempts or (self.maximum_attempts and not self.invocation_cap):
            raise ValueError('Invocation bound must fit the frozen matrix')
        if self.max_calls != self.maximum_attempts:
            raise ValueError('The frozen call maximum must match the finite matrix')
        slots = self.observation_matrix()
        if 'planned_slots' in self.model_fields_set and self.planned_slots != slots:
            raise ValueError('Frozen observation slots do not match the selected configuration')
        self.planned_slots = slots
        return self

    @property
    def maximum_attempts(self) -> int:
        extractions = len(self.inputs) * self.fresh_extractions if self.input_mode == 'fresh' else 0
        samples = extractions if self.input_mode == 'fresh' else len(self.inputs)
        return extractions + samples * self.resolution_repetitions

    def observation_matrix(self) -> list[ObservationSlot]:
        slots = []
        for template in self.inputs:
            sample_ids = ([f'{template.sample_id}_fresh_{index:02d}'
                for index in range(1, self.fresh_extractions + 1)]
                if self.input_mode == 'fresh' else [template.sample_id])
            for sample_id in sample_ids:
                repetitions = range(1, self.repetitions + 1) if self.resolver == 'generative' else [0]
                for repetition in repetitions:
                    suffix = f'resolve-{repetition}' if self.resolver == 'generative' else 'noop'
                    slots.append(ObservationSlot(observation_id=f'{sample_id}-{suffix}',
                        sample_id=sample_id, case_id=template.case_id,
                        configuration='generative_full_source' if self.resolver == 'generative' else 'noop',
                        repetition=repetition,
                        extraction_attempt_id=f'{sample_id}-extraction' if self.input_mode == 'fresh' else None))
        return slots
