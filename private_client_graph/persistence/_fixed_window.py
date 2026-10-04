"""Shared PostgreSQL fixed-window mechanics for the two deployment allowances.

The database clock keeps replicas on the same UTC bucket. ``at`` is an explicit
clock input for deterministic integration tests; HTTP callers never supply it.
"""

from datetime import datetime
from typing import Literal

from sqlalchemy import text

from .database import database_engine

_QuotaKind = Literal["showcase", "proposal"]
_TABLES = {
    "showcase": "showcase_live_quota",
    "proposal": "proposal_analysis_allowance",
}

_BUCKET = """
WITH bucket AS (
    SELECT to_timestamp(
        floor(extract(epoch FROM COALESCE(CAST(:at AS timestamptz), statement_timestamp()))
              / :window_seconds) * :window_seconds
    ) AS start
)
"""


def _quota_reset(
    quota: _QuotaKind, *, limit: int, window_seconds: int, at: datetime | None = None,
) -> datetime | None:
    # SQL identifiers come only from this fixed mapping, never from request data.
    table = _TABLES[quota]
    with database_engine().connect() as connection:
        return connection.execute(text(_BUCKET + f"""
            SELECT bucket.start + :window_seconds * interval '1 second'
            FROM bucket JOIN {table} q
              ON q.bucket_start = bucket.start AND q.window_seconds = :window_seconds
            WHERE q.attempts >= :limit
        """), {"limit": limit, "window_seconds": window_seconds, "at": at}).scalar_one_or_none()


def _claim_slot(
    quota: _QuotaKind, *, limit: int, window_seconds: int, at: datetime | None = None,
) -> datetime | None:
    """Commit one attempt, or return reset time if the conditional upsert lost.

    PostgreSQL locks the conflicting row and evaluates the WHERE guard against
    its latest value, including other claimants' commits. The transaction ends
    before any provider work, so downstream errors cannot undo consumption.
    """
    table = _TABLES[quota]
    with database_engine().begin() as connection:
        return connection.execute(text(_BUCKET + f"""
            , claimed AS (
                INSERT INTO {table} (window_seconds, bucket_start, attempts)
                SELECT :window_seconds, bucket.start, 1 FROM bucket
                ON CONFLICT (window_seconds, bucket_start) DO UPDATE
                SET attempts = {table}.attempts + 1
                WHERE {table}.attempts < :limit
                RETURNING 1
            )
            SELECT bucket.start + :window_seconds * interval '1 second'
            FROM bucket WHERE NOT EXISTS (SELECT 1 FROM claimed)
        """), {"limit": limit, "window_seconds": window_seconds, "at": at}).scalar_one_or_none()
