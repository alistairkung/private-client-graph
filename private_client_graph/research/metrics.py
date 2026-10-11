"""Research diagnostics alongside, never inside, the existing graph evaluator."""
from dataclasses import dataclass
from itertools import combinations
from typing import Any, Iterator

from pydantic import BaseModel, Field

from private_client_graph.graph import ENDPOINT_TYPES
from private_client_graph.models import ExtractionResult
from private_client_graph.models.types import EntityType, RelationshipType
from .inputs import EndpointIdentity, ResearchInput
from .plan import Pricing
from .provider import TokenUsage


class IdentityError(BaseModel):
    kind: str
    left: EndpointIdentity
    right: EndpointIdentity


class IdentityDiagnostics(BaseModel):
    incorrect_merges: int = 0
    missed_merges: int = 0
    different_truth_pairs: int = 0
    same_truth_pairs: int = 0
    eligible_pairs: int = 0
    errors: list[IdentityError] = Field(default_factory=list)


@dataclass(frozen=True)
class _AnnotatedEndpoint:
    annotation: EndpointIdentity
    name: str
    entity_type: EntityType


def identity_diagnostics(sample: ResearchInput, output: ExtractionResult) -> dict[str, Any] | None:
    if sample.annotations is None:
        return None

    endpoints = _annotated_endpoints(sample, output)
    diagnostics = IdentityDiagnostics()
    for left, right in _comparable_pairs(endpoints):
        _record_identity_comparison(diagnostics, left, right)
    return diagnostics.model_dump()


def _annotated_endpoints(
    sample: ResearchInput,
    output: ExtractionResult,
) -> list[_AnnotatedEndpoint]:
    endpoints = []
    assert sample.annotations is not None
    for label in sample.annotations:
        candidate = output.relationships[label.candidate_index]
        endpoints.append(_AnnotatedEndpoint(
            annotation=label,
            name=getattr(candidate, label.endpoint),
            entity_type=_endpoint_type(candidate.relationship_type, label.endpoint),
        ))
    return endpoints


def _endpoint_type(relationship_type: RelationshipType, endpoint: str) -> EntityType:
    position = 0 if endpoint == 'source_name' else 1
    return ENDPOINT_TYPES[relationship_type][position]


def _comparable_pairs(
    endpoints: list[_AnnotatedEndpoint],
) -> Iterator[tuple[_AnnotatedEndpoint, _AnnotatedEndpoint]]:
    return (
        (left, right)
        for left, right in combinations(endpoints, 2)
        if left.entity_type == right.entity_type
    )


def _record_identity_comparison(
    diagnostics: IdentityDiagnostics,
    left: _AnnotatedEndpoint,
    right: _AnnotatedEndpoint,
) -> None:
    same_truth = left.annotation.participant == right.annotation.participant
    same_prediction = left.name == right.name
    diagnostics.eligible_pairs += 1
    if same_truth:
        diagnostics.same_truth_pairs += 1
    else:
        diagnostics.different_truth_pairs += 1
    if same_truth == same_prediction:
        return

    kind = 'missed_merges' if same_truth else 'incorrect_merges'
    setattr(diagnostics, kind, getattr(diagnostics, kind) + 1)
    diagnostics.errors.append(IdentityError(
        kind=kind,
        left=left.annotation,
        right=right.annotation,
    ))


def estimate_cost(usage: TokenUsage, pricing: Pricing | None) -> float | None:
    if pricing is None or usage.input_tokens is None or usage.output_tokens is None:
        return None
    if usage.cached_tokens is None:
        # No knowledge of the cache split: only a uniform price can be applied.
        if pricing.cached_input_per_million != pricing.input_per_million:
            return None
        cached = 0
    else:
        cached = usage.cached_tokens
    if cached and pricing.cached_input_per_million is None:
        return None
    return ((usage.input_tokens - cached) * pricing.input_per_million
            + cached * (pricing.cached_input_per_million or 0)
            + usage.output_tokens * pricing.output_per_million) / 1_000_000
