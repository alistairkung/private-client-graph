"""Deterministic demonstration responses, explicitly not model performance."""
import json
from typing import Any

from .artifacts import checksum
from .fixtures import ROOT
from .provider import ModelRequest, ModelResponse


def recorded_response(request: ModelRequest, *, records: dict[str, Any] | None = None) -> ModelResponse:
    if records is None:
        records = json.loads((ROOT / 'research/fixtures/demonstration_responses.json').read_text())
    key = recording_key(request)
    response = records.get(request.stage, {}).get(key)
    if response is None:
        raise ValueError('No deterministic response recorded for this exact input')
    return ModelResponse(payload=response, returned_model='deterministic-substitute',
                         raw_response={'demonstration': True, 'payload': response})


def recording_key(request: ModelRequest) -> str:
    """Keep attributed recordings distinct from legacy source-string snapshots."""
    if request.sources is not None:
        raw = json.dumps([source.model_dump() for source in request.sources], sort_keys=True)
        return 'sourced:' + checksum(raw.encode())
    extraction = json.dumps(request.extraction.model_dump() if request.extraction else None, sort_keys=True)
    return checksum(request.source.encode()) + ':' + checksum(extraction.encode())
