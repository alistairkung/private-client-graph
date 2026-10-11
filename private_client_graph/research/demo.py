"""Deterministic demonstration responses, explicitly not model performance."""
import json
from typing import Any

from .artifacts import checksum
from .fixtures import ROOT
from .provider import ModelRequest, ModelResponse


def recorded_response(request: ModelRequest, *, records: dict[str, Any] | None = None) -> ModelResponse:
    if records is None:
        records = json.loads((ROOT / 'research/fixtures/demonstration_responses.json').read_text())
    extraction = json.dumps(request.extraction.model_dump() if request.extraction else None, sort_keys=True)
    key = checksum(request.source.encode()) + ':' + checksum(extraction.encode())
    response = records.get(request.stage, {}).get(key)
    if response is None:
        raise ValueError('No deterministic response recorded for this exact input')
    return ModelResponse(payload=response, returned_model='deterministic-substitute',
                         raw_response={'demonstration': True, 'payload': response})
