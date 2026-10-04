"""Required deployment settings for authenticated synthetic proposal analysis."""

import os
from dataclasses import dataclass

from pydantic import SecretStr

from private_client_graph.persistence.database import database_engine


@dataclass(frozen=True)
class ProposalAnalysisConfig:
    limit: int
    window_seconds: int
    api_key: SecretStr
    model: str

    @classmethod
    def from_environment(cls) -> "ProposalAnalysisConfig":
        values = []
        for name in ("PCG_PROPOSAL_ANALYSIS_LIMIT", "PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS"):
            try:
                value = int(os.environ[name])
                if not 0 < value <= 2_147_483_647:
                    raise ValueError
            except (KeyError, ValueError) as exc:
                raise ValueError(f"{name} must be a positive 32-bit integer") from exc
            values.append(value)
        key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-flash").strip()
        if not key or not model:
            raise ValueError("DEEPSEEK_API_KEY and a non-empty DEEPSEEK_MODEL are required")
        database_engine()
        return cls(values[0], values[1], SecretStr(key), model)
