"""Frozen provenance for actual fresh outputs reused as saved research inputs."""
import hashlib
import json
from typing import Literal

from pydantic import BaseModel, ConfigDict

from .inputs import ResearchInput


def value_digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':')).encode()).hexdigest()


def input_digests(sample: ResearchInput) -> dict[str, str]:
    return {
        'source_digest': value_digest({'source': sample.source,
            'sources': [source.model_dump(mode='json') for source in sample.sources] if sample.sources is not None else None}),
        'truth_digest': value_digest({'truth': sample.truth.model_dump(mode='json'),
            'source_evidence': sample.source_evidence.model_dump(mode='json') if sample.source_evidence else None}),
        'extraction_digest': value_digest({'extraction': sample.extraction.model_dump(mode='json') if sample.extraction else None,
            'sourced_extraction': sample.sourced_extraction.model_dump(mode='json') if sample.sourced_extraction else None}),
    }


class RetainedSampleLineage(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    original_sample_id: str
    original_cohort: Literal['fresh'] = 'fresh'
    extraction_attempt_id: str
    snapshot_digest: str
    source_digest: str
    truth_digest: str
    extraction_digest: str


class RetainedInputLineage(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)
    experiment_id: str
    run_id: str
    plan_digest: str
    artifact_digest: str
    samples: dict[str, RetainedSampleLineage]
