"""Version 2 persistent Experiment and editable Run Draft contracts."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .execution_contracts import Proposal
from .case_catalog import default_input_ids


class RunConfiguration(Proposal):
    input_ids: list[str] = Field(default_factory=default_input_ids, min_length=1, max_length=100)


class WorkspaceCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')
    request_id: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,80}$')


class CreateExperiment(WorkspaceCommand):
    name: str = Field(min_length=1, max_length=200)
    hypothesis: str | None = Field(default=None, max_length=4000)
    description: str | None = Field(default=None, max_length=4000)

    @field_validator('name')
    @classmethod
    def require_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Experiment name must not be blank')
        return value.strip()


class RunDraft(BaseModel):
    revision: int = 0
    configuration: RunConfiguration = Field(default_factory=RunConfiguration)
    copied_from_run: str | None = None


class DraftUpdate(WorkspaceCommand):
    expected_revision: int = Field(ge=0)
    configuration: RunConfiguration


class CopyRunDraft(WorkspaceCommand):
    expected_revision: int = Field(ge=0)
    run_id: str = Field(pattern=r'^[a-f0-9]{32}$')


class FreezeRun(WorkspaceCommand):
    expected_revision: int = Field(ge=0)


class WorkspaceDetail(BaseModel):
    api_version: Literal['2'] = '2'
    id: str
    name: str
    hypothesis: str | None = None
    description: str | None = None
    created_at: str
    draft: RunDraft
    run_ids: list[str] = Field(default_factory=list)
    metadata_available: bool = True


class WorkspaceHistory(BaseModel):
    api_version: Literal['2'] = '2'
    items: list[WorkspaceDetail]
