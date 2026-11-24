"""Verified lock for the traced baseline. The original extraction pin remains in baseline.json."""

import hashlib
import json

from private_client_graph.extraction import sourced_extraction_messages
from private_client_graph.research.artifacts import dependency_versions
from private_client_graph.research.fixtures import ROOT
from private_client_graph.research.provider import ModelSettings
from private_client_graph.research.retained_inputs import value_digest

TRACED_LOCK_SHA256 = 'b7f9674ec4252bb23651f56515b0e1f082083e6193df55a41b30c8543aee9795'


def baseline_configuration() -> dict:
    pin = json.loads((ROOT / 'benchmark_v2/baseline.json').read_bytes())
    files = {**pin['files'], 'uv.lock': TRACED_LOCK_SHA256}
    for path, expected in files.items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError(f'Baseline implementation drift in {path}')
    if dependency_versions() != pin['dependencies']:
        raise ValueError('Installed baseline dependencies differ from the original Run')
    settings = ModelSettings(timeout_seconds=90.0)
    prompt = sourced_extraction_messages([])[0][1]
    if hashlib.sha256(prompt.encode()).hexdigest() != pin['prompt'] or value_digest(settings.model_dump()) != pin['settings']:
        raise ValueError('Baseline prompt or settings drift')
    return pin
