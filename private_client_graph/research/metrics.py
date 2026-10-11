"""Research diagnostics alongside, never inside, the existing graph evaluator."""
from itertools import combinations
from typing import Any

from private_client_graph.graph import ENDPOINT_TYPES
from private_client_graph.models import ExtractionResult
from .inputs import ResearchInput
from .plan import Pricing
from .provider import TokenUsage


def identity_diagnostics(sample: ResearchInput, output: ExtractionResult) -> dict[str, Any] | None:
    if sample.annotations is None:
        return None
    endpoints = []
    for label in sample.annotations:
        candidate = output.relationships[label.candidate_index]
        side = 0 if label.endpoint == 'source_name' else 1
        endpoints.append((label, getattr(candidate, label.endpoint),
                          ENDPOINT_TYPES[candidate.relationship_type][side]))
    diagnostics: dict[str, Any] = {'incorrect_merges': 0, 'missed_merges': 0,
                                 'different_truth_pairs': 0, 'same_truth_pairs': 0,
                                 'eligible_pairs': 0, 'errors': []}
    for (left, left_name, left_type), (right, right_name, right_type) in combinations(endpoints, 2):
        if left_type != right_type:
            continue
        same_truth = left.participant == right.participant
        same_prediction = left_name == right_name
        diagnostics['eligible_pairs'] += 1
        diagnostics['same_truth_pairs' if same_truth else 'different_truth_pairs'] += 1
        if same_truth != same_prediction:
            kind = 'missed_merges' if same_truth else 'incorrect_merges'
            diagnostics[kind] += 1
            diagnostics['errors'].append({'kind': kind, 'left': left.model_dump(), 'right': right.model_dump()})
    return diagnostics


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
