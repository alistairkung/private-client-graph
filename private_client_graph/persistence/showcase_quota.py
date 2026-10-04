"""Concrete PostgreSQL quota for the single public live showcase.

The database clock keeps replicas on the same UTC bucket. ``at`` is an explicit
clock input for deterministic integration tests; HTTP callers never supply it.
Each claim commits before returning and is never refunded.
"""

from datetime import datetime

from sqlalchemy import text

from .database import database_engine

_BUCKET = """
WITH bucket AS (
    SELECT to_timestamp(
        floor(extract(epoch FROM COALESCE(CAST(:at AS timestamptz), statement_timestamp()))
              / :window_seconds) * :window_seconds
    ) AS start
)
"""


def quota_reset(*, limit: int, window_seconds: int, at: datetime | None = None) -> datetime | None:
    """Return the exhausted bucket's reset time, or None when a slot is available."""
    with database_engine().connect() as connection:
        return connection.execute(text(_BUCKET + """
            SELECT bucket.start + :window_seconds * interval '1 second'
            FROM bucket JOIN showcase_live_quota q
              ON q.bucket_start = bucket.start AND q.window_seconds = :window_seconds
            WHERE q.attempts >= :limit
        """), {"limit": limit, "window_seconds": window_seconds, "at": at}).scalar_one_or_none()


def claim_slot(*, limit: int, window_seconds: int, at: datetime | None = None) -> datetime | None:
    """Commit one attempt, or return reset time if the conditional upsert lost.

PostgreSQL locks the conflicting row and evaluates the WHERE guard against its
latest value, including other claimants' commits. The transaction ends before
any provider work, so errors downstream cannot roll back consumption.
"""
    with database_engine().begin() as connection:
        return connection.execute(text(_BUCKET + """
            , claimed AS (
                INSERT INTO showcase_live_quota (window_seconds, bucket_start, attempts)
                SELECT :window_seconds, bucket.start, 1 FROM bucket
                ON CONFLICT (window_seconds, bucket_start) DO UPDATE
                SET attempts = showcase_live_quota.attempts + 1
                WHERE showcase_live_quota.attempts < :limit
                RETURNING 1
            )
            SELECT bucket.start + :window_seconds * interval '1 second'
            FROM bucket WHERE NOT EXISTS (SELECT 1 FROM claimed)
        """), {"limit": limit, "window_seconds": window_seconds, "at": at}).scalar_one_or_none()
