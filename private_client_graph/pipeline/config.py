"""Finite semantic capabilities; operational provider settings belong to consumers."""
from typing import Literal

from pydantic import BaseModel, ConfigDict


class PipelineConfig(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')

    resolver: Literal['none', 'generative'] = 'none'
