"""Frozen display metadata shared by repository catalogs and Run provenance."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class CaseMetadata(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    id: str
    case_id: str
    name: str
    description: str | None
    fixture_name: str
    fixture_description: str | None
    kind: Literal['benchmark', 'diagnostic', 'historical']
    metadata_available: bool

    @field_validator('name', 'fixture_name', 'description', 'fixture_description')
    @classmethod
    def nonblank_labels(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError('Case labels and descriptions must not be blank')
        return value


