"""Server-side operational configuration for public showcase provider use."""

import os
from dataclasses import dataclass

from sqlalchemy.exc import SQLAlchemyError

from private_client_graph.persistence.database import database_engine
from private_client_graph.persistence.showcase_quota import claim_slot, quota_reset

from .contracts import AnalysisError, LiveAvailability
from .errors import AnalysisFailure


@dataclass(frozen=True)
class LiveConfig:
    enabled: bool = False
    limit: int = 0
    window_seconds: int = 0

    @classmethod
    def from_environment(cls) -> "LiveConfig":
        enabled = os.getenv("PCG_SHOWCASE_LIVE_ENABLED", "false").lower()
        if enabled not in ("true", "false"):
            raise ValueError("PCG_SHOWCASE_LIVE_ENABLED must be true or false")
        if enabled == "false":
            return cls()
        values = []
        for name in ("PCG_SHOWCASE_LIVE_LIMIT", "PCG_SHOWCASE_LIVE_WINDOW_SECONDS"):
            try:
                value = int(os.environ[name])
                if not 0 < value <= 2_147_483_647:
                    raise ValueError
            except (KeyError, ValueError) as exc:
                raise ValueError(f"{name} must be a positive 32-bit integer when live is enabled") from exc
            values.append(value)
        if not os.getenv("DEEPSEEK_API_KEY", "").strip():
            raise ValueError("DEEPSEEK_API_KEY is required when showcase live analysis is enabled")
        database_engine()  # Validate PostgreSQL configuration without connecting at startup.
        return cls(enabled=True, limit=values[0], window_seconds=values[1])


def live_availability(config: LiveConfig) -> LiveAvailability:
    if not config.enabled:
        return LiveAvailability(state="disabled")
    try:
        reset = quota_reset(limit=config.limit, window_seconds=config.window_seconds)
    except (SQLAlchemyError, ValueError):
        return LiveAvailability(state="unavailable")
    return LiveAvailability(state="exhausted" if reset else "available", resets_at=reset)


def require_live(config: LiveConfig) -> None:
    if not config.enabled:
        raise AnalysisFailure(AnalysisError(
            stage="availability", message="Live analysis is currently disabled.",
            live_analysis=LiveAvailability(state="disabled"),
        ), 503)


def consume_live_slot(config: LiveConfig) -> None:
    require_live(config)
    try:
        reset = claim_slot(limit=config.limit, window_seconds=config.window_seconds)
    except (SQLAlchemyError, ValueError) as exc:
        raise AnalysisFailure(AnalysisError(
            stage="availability", message="Live analysis is temporarily unavailable. Sample analysis remains available.",
            live_analysis=LiveAvailability(state="unavailable"),
        ), 503) from exc
    if reset is not None:
        raise AnalysisFailure(AnalysisError(
            stage="availability", message="Live analysis is unavailable until the next window.",
            live_analysis=LiveAvailability(state="exhausted", resets_at=reset),
        ), 429)
