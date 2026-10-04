"""Synchronous PostgreSQL connections shared by commands and application reads."""

import os
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url


def database_engine() -> Engine:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL must configure PostgreSQL")
    return _engine(url)


@lru_cache(maxsize=1)
def _engine(database_url: str) -> Engine:
    url = make_url(database_url)
    if url.get_backend_name() not in ("postgresql", "postgres"):
        raise ValueError("DATABASE_URL must configure PostgreSQL")
    return create_engine(
        url.set(drivername="postgresql+psycopg"),
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3, "options": "-c statement_timeout=5000"},
    )
