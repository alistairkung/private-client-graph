import subprocess
import sys

from fastapi.testclient import TestClient

from private_client_graph.api.app import create_app


def test_migration_seed_and_collection(database):
    client = TestClient(create_app())
    assert client.get("/api/matters").json() == []
    subprocess.run([sys.executable, "-m", "private_client_graph.seed_evergreen"], check=True)
    response = client.get("/api/matters")
    assert response.status_code == 200
    assert response.json() == [{
        "id": "ff985caf-60c5-4e65-a238-f3c26381c369",
        "external_reference": "PC/2026/0142",
        "title": "Evergreen Family Trust",
    }]


def test_repeat_seed_preserves_complete_existing_snapshot(database, monkeypatch, tmp_path):
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
    response = TestClient(create_app()).get("/api/matters")
    assert response.json()[0]["title"] == "Evergreen succession advice"
    assert response.json()[0]["external_reference"] == "PC/2026/0999"


def test_reads_do_not_consult_fixtures_or_extract(database, monkeypatch):
    from pathlib import Path
    from private_client_graph.seed_evergreen import seed_evergreen

    seed_evergreen()

    def unavailable(*args, **kwargs):
        raise AssertionError("Matter listing must not read benchmark fixtures")

    monkeypatch.setattr(Path, "read_text", unavailable)
    client = TestClient(create_app())
    assert client.get("/api/matters").json()[0]["title"] == "Evergreen Family Trust"


def test_readiness_without_seed_and_unavailable_database(database, monkeypatch):
    client = TestClient(create_app())
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


def test_invalid_seed_input_does_not_insert_partial_matter(database, monkeypatch, tmp_path):
    import pytest
    from private_client_graph import seed_evergreen as seed_module

    (tmp_path / "source.txt").write_text("This note contains no fixture evidence.")
    (tmp_path / "expected_extraction.json").write_text(
        (seed_module.CASE / "expected_extraction.json").read_text()
    )
    monkeypatch.setattr(seed_module, "CASE", tmp_path)
    with pytest.raises(ValueError):
        seed_module.seed_evergreen()
    assert TestClient(create_app()).get("/api/matters").json() == []


def test_concurrent_seed_commands_insert_only_one_matter(database):
    commands = [subprocess.Popen(
        [sys.executable, "-m", "private_client_graph.seed_evergreen"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    ) for _ in range(2)]
    outputs = [command.communicate(timeout=20) for command in commands]
    assert all(command.returncode == 0 for command in commands), outputs
    assert sorted(output[0].strip() for output in outputs) == [
        "Evergreen already exists; unchanged.", "Evergreen inserted.",
    ]
    assert len(TestClient(create_app()).get("/api/matters").json()) == 1
