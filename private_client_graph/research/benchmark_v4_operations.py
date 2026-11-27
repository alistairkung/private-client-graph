"""Account for this Run's attempts and the extraction work it inherits."""
from collections.abc import Sequence

from pydantic import BaseModel

from .benchmark_v4_run import VerifiedV4Run
from .metrics import estimate_cost
from .plan import Pricing
from .provider import TokenUsage


class BenchmarkStageUsage(BaseModel):
    attempts: int
    estimated_cost: float | None
    currency: str | None
    unpriced_attempts: int
    tokens: TokenUsage
    provider_seconds: float | None


class BenchmarkV4Operations(BaseModel):
    origin_run_id: str | None
    incremental: BenchmarkStageUsage
    inherited_extraction: BenchmarkStageUsage | None
    full_pipeline: BenchmarkStageUsage
    full_pipeline_seconds: float | None


def benchmark_v4_operations(retained: VerifiedV4Run, attempts: list[dict], pricing: Pricing | None,
                            *, live: bool) -> BenchmarkV4Operations:
    origin = retained.origin
    inherited = [(row, origin.pricing) for row in origin.attempts] if origin else []
    own = [(row, pricing) for row in attempts]
    full = _usage([*inherited, *own], live=live)
    # The composed pipeline constructs one final graph, using the current Run's local timings.
    local_seconds = sum((row.edit_seconds or 0) + (row.graph_seconds or 0)
                        for row in retained.results.values())
    return BenchmarkV4Operations(origin_run_id=origin.lineage.run_id if origin else None,
        incremental=_usage(own, live=live),
        inherited_extraction=_usage(inherited, live=live) if origin else None,
        full_pipeline=full,
        full_pipeline_seconds=(full.provider_seconds + local_seconds if full.provider_seconds is not None else None))


def _usage(rows: Sequence[tuple[dict, Pricing | None]], *, live: bool) -> BenchmarkStageUsage:
    usages = [TokenUsage.model_validate(row.get('response', {}).get('usage', {})) for row, _ in rows]
    prices = [estimate_cost(tokens, price) if live else None
              for tokens, (_, price) in zip(usages, rows, strict=True)]
    currencies = {price.currency for _, price in rows if price is not None}
    unpriced = prices.count(None)
    return BenchmarkStageUsage(
        attempts=len(rows), estimated_cost=(_total(prices) if len(currencies) == 1 else None),
        currency=next(iter(currencies)) if len(currencies) == 1 else None, unpriced_attempts=unpriced,
        tokens=TokenUsage(input_tokens=_token_total([row.input_tokens for row in usages]),
            output_tokens=_token_total([row.output_tokens for row in usages]),
            cached_tokens=_token_total([row.cached_tokens for row in usages])),
        provider_seconds=_total([row.get('provider_seconds') for row, _ in rows]))


def _total(values: Sequence[float | None]) -> float | None:
    known = [value for value in values if value is not None]
    return sum(known) if len(known) == len(values) and values else None


def _token_total(values: list[int | None]) -> int | None:
    known = [value for value in values if value is not None]
    return sum(known) if len(known) == len(values) and values else None
