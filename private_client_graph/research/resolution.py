"""Constrained semantic edits, applied without changing relationship semantics."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from private_client_graph.models import ExtractionResult


class EndpointEdit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    candidate_index: int = Field(ge=0)
    endpoint: Literal["source_name", "target_name"]
    name: str = Field(min_length=1)


class EndpointEdits(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    edits: list[EndpointEdit]


def no_resolution(extraction: ExtractionResult) -> ExtractionResult:
    return extraction.model_copy(deep=True)


def apply_edits(
    extraction: ExtractionResult, source: str, response: object
) -> ExtractionResult:
    edits = EndpointEdits.model_validate(response)
    names = {name for candidate in extraction.relationships
             for name in (candidate.source_name, candidate.target_name)}
    result = no_resolution(extraction)
    targets: set[tuple[int, str]] = set()
    for edit in edits.edits:
        target = (edit.candidate_index, edit.endpoint)
        if target in targets or edit.candidate_index >= len(result.relationships):
            raise ValueError("Duplicate or unknown edit target")
        if not edit.name.strip() or (edit.name not in source and edit.name not in names):
            raise ValueError("Replacement must be an existing name or exact Source text")
        targets.add(target)
        setattr(result.relationships[edit.candidate_index], edit.endpoint, edit.name)
    return result
