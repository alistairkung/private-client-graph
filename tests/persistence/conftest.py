"""Each persistence test owns a fresh disposable PostgreSQL database."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool


@pytest.fixture
def database(monkeypatch, request):
    admin_url = os.getenv("TEST_DATABASE_URL")
    if not admin_url:
        pytest.skip("Set TEST_DATABASE_URL to a disposable PostgreSQL server with CREATEDB")
    url = make_url(admin_url).set(drivername="postgresql+psycopg")
    name = f"pcg_test_{uuid4().hex}"
    admin = create_engine(url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    with admin.connect() as connection:
        connection.execute(text(f"CREATE DATABASE \"{name}\" TEMPLATE template0 ENCODING 'UTF8'"))
    database_url = url.set(database=name).render_as_string(hide_password=False)
    monkeypatch.setenv("DATABASE_URL", database_url)
    try:
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", getattr(request, "param", "head")], check=True)
        yield database_url
    finally:
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()
