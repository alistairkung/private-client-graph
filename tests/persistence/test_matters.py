import subprocess
import sys

import pytest

from fastapi.testclient import TestClient

from private_client_graph.api.app import create_app


def test_migration_seed_and_collection(database, authenticated_client):
    client = authenticated_client(create_app())
    assert client.get("/api/matters").json() == []
    subprocess.run([sys.executable, "-m", "private_client_graph.seed_evergreen"], check=True)
    response = client.get("/api/matters")
    assert response.status_code == 200
    assert response.json() == [{
        "id": "ff985caf-60c5-4e65-a238-f3c26381c369",
        "external_reference": "PC/2026/0142",
        "title": "Evergreen Family Trust",
    }]


def test_repeat_seed_preserves_complete_existing_snapshot(database, monkeypatch, tmp_path, authenticated_client):
    from sqlalchemy import create_engine, text
    from private_client_graph.seed_evergreen import seed_evergreen
    from private_client_graph import seed_evergreen as seed_module

    assert seed_evergreen() is True
    engine = create_engine(database)
    with engine.begin() as connection:
        before = dict(connection.execute(text("SELECT * FROM matters")).mappings().one())
    assert seed_evergreen() is False
    with engine.begin() as connection:
        assert dict(connection.execute(text("SELECT * FROM matters")).mappings().one()) == before
        # Simulate valid state already held by the datastore, independent of fixtures.
        connection.execute(text("""
            UPDATE matters SET title = 'Evergreen succession advice',
                external_reference = 'PC/2026/0999', source_title = 'Revised synthetic note',
                source_text = 'Fictional replacement source',
                current_graph = '{"entities": [], "relationships": [], "evidence": []}'::jsonb
        """))
        existing = dict(connection.execute(text("SELECT * FROM matters")).mappings().one())
    (tmp_path / "source.txt").write_text("Changed fictional seed input")
    (tmp_path / "expected_extraction.json").write_text('{"relationships": []}')
    monkeypatch.setattr(seed_module, "CASE", tmp_path)
    assert seed_evergreen() is False
    (tmp_path / "source.txt").unlink()
    assert seed_evergreen() is False
    with engine.connect() as connection:
        assert dict(connection.execute(text("SELECT * FROM matters")).mappings().one()) == existing
    engine.dispose()
    response = authenticated_client(create_app()).get("/api/matters")
    assert response.json()[0]["title"] == "Evergreen succession advice"
    assert response.json()[0]["external_reference"] == "PC/2026/0999"


def test_reads_do_not_consult_fixtures_or_extract(database, monkeypatch, authenticated_client):
    from pathlib import Path
    from private_client_graph.seed_evergreen import seed_evergreen

    seed_evergreen()

    def unavailable(*args, **kwargs):
        raise AssertionError("Matter listing must not read benchmark fixtures")

    monkeypatch.setattr(Path, "read_text", unavailable)
    client = authenticated_client(create_app())
    assert client.get("/api/matters").json()[0]["title"] == "Evergreen Family Trust"


def test_readiness_without_seed_and_unavailable_database(database, monkeypatch, authenticated_client):
    client = authenticated_client(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert client.get("/api/matters").json() == []
    # A nonexistent database on the real PostgreSQL server cannot be used.
    monkeypatch.setenv("DATABASE_URL", database + "_unavailable")
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    response = client.get("/api/matters")
    assert response.status_code == 503
    assert response.json() == {"error": {"message": "Matters could not be loaded."}}
    assert client.get("/api/showcase/case-01").status_code == 200
    assert client.post("/api/showcase/case-01/analysis", json={"mode": "sample"}).status_code == 200


def test_seed_contains_domain_valid_graph_and_verbatim_source_evidence(database):
    from sqlalchemy import create_engine, text
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.seed_evergreen import seed_evergreen

    seed_evergreen()
    engine = create_engine(database)
    with engine.connect() as connection:
        snapshot = connection.execute(text("SELECT source_title, source_text, current_graph FROM matters")).mappings().one()
    engine.dispose()
    graph = CanonicalGraph.model_validate(snapshot["current_graph"])
    assert snapshot["source_title"] == "Attendance Note – Meeting with Alice Chen"
    assert len(graph.relationships) == 6
    assert len(graph.entities) == 5
    assert all(item.supporting_text in snapshot["source_text"] for item in graph.evidence)


def test_invalid_seed_input_does_not_insert_partial_matter(database, monkeypatch, tmp_path, authenticated_client):
    import pytest
    from private_client_graph import seed_evergreen as seed_module

    (tmp_path / "source.txt").write_text("This note contains no fixture evidence.")
    (tmp_path / "expected_extraction.json").write_text(
        (seed_module.CASE / "expected_extraction.json").read_text()
    )
    monkeypatch.setattr(seed_module, "CASE", tmp_path)
    with pytest.raises(ValueError):
        seed_module.seed_evergreen()
    assert authenticated_client(create_app()).get("/api/matters").json() == []


def test_concurrent_seed_commands_insert_only_one_matter(database, authenticated_client):
    commands = [subprocess.Popen(
        [sys.executable, "-m", "private_client_graph.seed_evergreen"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ) for _ in range(2)]
    outputs = [command.communicate(timeout=20) for command in commands]
    assert all(command.returncode == 0 for command in commands), outputs
    assert sorted(output[0].strip() for output in outputs) == [
        "Evergreen already exists; unchanged.", "Evergreen inserted.",
    ]
    assert len(authenticated_client(create_app()).get("/api/matters").json()) == 1


def test_matter_detail_returns_complete_persisted_state(database, authenticated_client):
    from private_client_graph.seed_evergreen import seed_evergreen

    seed_evergreen()
    response = authenticated_client(create_app()).get("/api/matters/ff985caf-60c5-4e65-a238-f3c26381c369")
    assert response.status_code == 200
    detail = response.json()
    assert set(detail) == {"id", "external_reference", "title", "authoritative_source", "current_graph"}
    assert detail["external_reference"] == "PC/2026/0142"
    assert detail["title"] == "Evergreen Family Trust"
    assert set(detail["authoritative_source"]) == {"title", "text"}
    assert detail["authoritative_source"]["title"] == "Attendance Note – Meeting with Alice Chen"
    assert len(detail["current_graph"]["relationships"]) == 6
    assert all(item["supporting_text"] in detail["authoritative_source"]["text"]
               for item in detail["current_graph"]["evidence"])


def test_missing_and_invalid_matter_uuid(database, authenticated_client):
    client = authenticated_client(create_app())
    assert client.get("/api/matters/00000000-0000-0000-0000-000000000000").status_code == 404
    response = client.get("/api/matters/not-a-uuid")
    assert response.status_code == 422
    assert response.json() == {"error": {"message": "Invalid Matter UUID."}}


@pytest.mark.parametrize("values", [
    {"source_text": "Inconsistent synthetic source"},
    {"current_graph": {"entities": "invalid"}},
])
def test_invalid_persisted_state_never_reaches_browser(database, values, authenticated_client):
    from sqlalchemy import create_engine, update
    from private_client_graph.persistence.matters import matters
    from private_client_graph.seed_evergreen import seed_evergreen

    seed_evergreen()
    engine = create_engine(database)
    client = authenticated_client(create_app())
    with engine.begin() as connection:
        connection.execute(update(matters).values(**values))
    response = client.get("/api/matters/ff985caf-60c5-4e65-a238-f3c26381c369")
    assert response.status_code == 503
    assert response.json() == {"error": {"message": "Matter could not be loaded."}}
    engine.dispose()


def test_detail_reads_only_persisted_state(database, monkeypatch, authenticated_client):
    from pathlib import Path
    from sqlalchemy import create_engine, update
    from private_client_graph.persistence.matters import matters
    from private_client_graph.seed_evergreen import seed_evergreen
    from langchain_deepseek import ChatDeepSeek

    seed_evergreen()
    engine = create_engine(database)
    with engine.begin() as connection:
        connection.execute(update(matters).values(source_title="Persisted note", source_text="Persisted text",
            current_graph={"entities": [], "relationships": [], "evidence": []}))
    engine.dispose()

    def forbidden(*args, **kwargs):
        raise AssertionError("Matter reads must not load fixtures or invoke a provider")

    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(ChatDeepSeek, "invoke", forbidden)
    response = authenticated_client(create_app()).get("/api/matters/ff985caf-60c5-4e65-a238-f3c26381c369")
    assert response.status_code == 200
    assert response.json()["authoritative_source"] == {"title": "Persisted note", "text": "Persisted text"}
    assert response.json()["current_graph"] == {"entities": [], "relationships": [], "evidence": []}
