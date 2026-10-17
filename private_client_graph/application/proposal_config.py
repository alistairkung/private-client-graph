"""Required deployment settings for authenticated synthetic proposal analysis."""

import os
from dataclasses import dataclass
from pathlib import Path

from pydantic import SecretStr


@dataclass(frozen=True)
class ProposalAnalysisConfig:
    limit: int
    window_seconds: int
    api_key: SecretStr
    model: str
    task_root: Path | None = None
    authorization: str | None = None

    @classmethod
    def from_environment(cls) -> "ProposalAnalysisConfig":
        limit = _positive_integer_setting("PCG_PROPOSAL_ANALYSIS_LIMIT")
        window_seconds = _positive_integer_setting("PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS")
        api_key = os.getenv("DEEPSEEK_API_KEY", "").strip()
        model = os.getenv("DEEPSEEK_MODEL", "deepseek-flash").strip()
        if not api_key or not model:
            raise ValueError("DEEPSEEK_API_KEY and a non-empty DEEPSEEK_MODEL are required")
        return cls(
            limit=limit,
            window_seconds=window_seconds,
            api_key=SecretStr(api_key),
            model=model,
            task_root=Path(root).expanduser().resolve() if (root := os.getenv("PCG_PROVIDER_TASK_ROOT", "").strip()) else None,
            authorization=os.getenv("PCG_PROVIDER_AUTHORIZATION", "").strip() or None,
        )


def _positive_integer_setting(name: str) -> int:
    try:
        value = int(os.environ[name])
        if not 0 < value <= 2_147_483_647:
            raise ValueError
    except (KeyError, ValueError) as exc:
        raise ValueError(f"{name} must be a positive 32-bit integer") from exc
    return value
