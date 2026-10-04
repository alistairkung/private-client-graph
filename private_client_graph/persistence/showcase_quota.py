"""Concrete PostgreSQL quota for the single public live showcase.

The database clock keeps replicas on the same UTC bucket. ``at`` is an explicit
clock input for deterministic integration tests; HTTP callers never supply it.
Each claim commits before returning and is never refunded.
"""

from datetime import datetime

from ._fixed_window import _claim_slot, _quota_reset


def quota_reset(*, limit: int, window_seconds: int, at: datetime | None = None) -> datetime | None:
    """Return the exhausted bucket's reset time, or None when a slot is available."""
    return _quota_reset("showcase", limit=limit, window_seconds=window_seconds, at=at)


def claim_slot(*, limit: int, window_seconds: int, at: datetime | None = None) -> datetime | None:
    """Commit one attempt, or return the exhausted bucket's reset time."""
    return _claim_slot("showcase", limit=limit, window_seconds=window_seconds, at=at)
