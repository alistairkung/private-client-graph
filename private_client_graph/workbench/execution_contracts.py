"""Finite command contracts, separate from the read-only composition."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Proposal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    input_ids: list[str] = Field(min_length=1, max_length=6)
    input_mode: Literal['saved', 'fresh'] = 'saved'
    execution_mode: Literal['replay', 'recorded', 'live'] = 'replay'
    resolver: Literal['none', 'generative'] = 'none'
    extraction_samples: int = Field(default=1, ge=1, le=5)
    resolver_repetitions: int = Field(default=1, ge=1, le=3)
    invocation_cap: int = Field(default=0, ge=0, le=38)
    temperature: float | None = Field(default=None, ge=0, le=2)
    timeout_seconds: float = Field(default=90, gt=0, le=300)
    task_call_cap: int = Field(default=0, ge=0, le=10000)
    model: Literal['deepseek-flash'] = 'deepseek-flash'


class InputChoice(BaseModel):
    id: str
    case_id: str
    cohort: str
    hashes: dict[str, str]


class TaskBudget(BaseModel):
    task_id: str
    label: str
    used: int
    cap: int
    remaining: int


class Capabilities(BaseModel):
    api_version: Literal['1'] = '1'
    live_enabled: bool = False
    live_reason: str = "Live execution is disabled"
    live_task: TaskBudget | None = None
    inputs: list[InputChoice]
    models: list[str] = ['deepseek-flash']
    provider: str = 'DeepSeek settings; recorded responses only'
    fresh_input_id: str = 'case_03_fixture'
    maximum_extraction_samples: int = 5
    maximum_resolver_repetitions: int = 3


class Preview(BaseModel):
    proposal: Proposal
    inputs: list[InputChoice]
    extraction_call_maximum: int
    resolution_call_maximum: int
    matrix_call_maximum: int
    planned_observations: int
    invocation_cap: int
    task_paid_usage: int = 0
    task_paid_allowance: int = 0
    task_paid_remaining: int = 0
    task_id: str | None = None
    task_label: str | None = None
    cost_reason: str = 'Offline only. No paid calls authorized. Recorded responses do not measure live quality or cost.'


class FrozenPlan(BaseModel):
    id: str
    digest: str
    task_id: str
    preview: Preview
    created_at: str


class Command(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,80}$')
    plan_digest: str = Field(pattern=r'^[a-f0-9]{64}$')


class LiveApproval(Command):
    approved: Literal[True]
    task_id: str
    expected_task_usage: int = Field(ge=0)
    expected_task_cap: int = Field(ge=0)
    task_cap: int = Field(ge=1, le=10000)
    continuation: bool = False


class RunStatus(BaseModel):
    plan: FrozenPlan
    state: Literal['frozen', 'running', 'stopping', 'stopped', 'interrupted', 'complete', 'failed']
    message: str
    completed_observations: int
    planned_observations: int
    attempts: int
    uncertain_attempts: int
    remaining_attempts: int
    result_id: str
    active_plan_id: str | None = None
    current_work: str | None = None
    task_budget: TaskBudget | None = None
