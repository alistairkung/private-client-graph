import json
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.persistence.matter_state import load_matter_state


def _legacy_matter(engine, graph, source="Alice is a beneficiary."):
    matter_id = uuid4()
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO matters VALUES (:id,:ref,'Stored title','Stored source',:source,CAST(:graph AS jsonb))
        """), {"id": matter_id, "ref": str(matter_id), "source": source, "graph": json.dumps(graph)})
        connection.execute(text("INSERT INTO external_matter_reference_claims VALUES (:ref,'matter',:id)"), {"id": matter_id, "ref": str(matter_id)})
    return matter_id


def _upgrade():
    return subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], capture_output=True, text=True)


@pytest.mark.parametrize("database", ["0004"], indirect=True)
def test_migration_preserves_reviewed_state_and_claim_without_fixtures(database, monkeypatch):
    engine = create_engine(database)
    graph = {
        "entities": [{"id": "z", "name": "Alice", "type": "person"}, {"id": "a", "name": "Trust", "type": "trust"}],
        "evidence": [{"id": "q", "document": "Legacy label", "supporting_text": "Alice is a beneficiary."}],
        "relationships": [{"source": "z", "target": "a", "type": "beneficiary_of", "evidence_ids": ["q"]}],
    }
    matter_id = _legacy_matter(engine, graph)
    monkeypatch.setenv("PCG_MATTER_MIGRATION_QUIESCED", "true")
    result = _upgrade()
    assert result.returncode == 0, result.stderr
    with engine.connect() as connection:
        state = load_matter_state(connection, matter_id)
        assert reconstruct_graph(state).model_dump() == graph
        assert state.sources[0].title == "Stored source"
        assert state.sources[0].text == "Alice is a beneficiary."
        assert connection.scalar(text("SELECT resource_id FROM external_matter_reference_claims")) == matter_id
        columns = connection.scalars(text("SELECT column_name FROM information_schema.columns WHERE table_name='matters'"))
        assert set(columns) == {"id", "title", "external_reference"}
    engine.dispose()


@pytest.mark.parametrize("database", ["0004"], indirect=True)
def test_migration_requires_quiescence_acknowledgement(database, monkeypatch):
    engine = create_engine(database)
    _legacy_matter(engine, {"entities": [], "relationships": [], "evidence": []})
    monkeypatch.delenv("PCG_MATTER_MIGRATION_QUIESCED", raising=False)
    result = _upgrade()
    assert result.returncode != 0
    assert "PCG_MATTER_MIGRATION_QUIESCED" in result.stderr
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0004"
    engine.dispose()


@pytest.mark.parametrize("database", ["0004"], indirect=True)
@pytest.mark.parametrize("graph", [
    {"entities": [], "relationships": [{"source": "missing", "target": "absent", "type": "parent_of", "evidence_ids": ["q"]}], "evidence": []},
    {"entities": [], "relationships": [], "evidence": [{"id": "q", "document": "x", "supporting_text": "Invented"}]},
    {"entities": [], "relationships": [], "evidence": [], "unrecognised_authority": "Must not silently discard"},
    {"entities": [{"id": "a", "type": "person", "name": "Alice"}, {"id": "b", "type": "person", "name": "Bob"}],
     "relationships": [{"source": "a", "target": "b", "type": "parent_of", "evidence_ids": []}], "evidence": []},
])
def test_invalid_legacy_graph_aborts_entire_conversion(database, monkeypatch, graph):
    engine = create_engine(database)
    _legacy_matter(engine, graph)
    monkeypatch.setenv("PCG_MATTER_MIGRATION_QUIESCED", "true")
    result = _upgrade()
    assert result.returncode != 0
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0004"
        assert connection.scalar(text("SELECT current_graph FROM matters")) == graph
        assert connection.scalar(text("SELECT to_regclass('matter_sources')")) is None
    engine.dispose()


@pytest.mark.parametrize("database", ["0004"], indirect=True)
def test_case_01_migration_preserves_graph_and_evaluation_with_pending_proposal(database, monkeypatch):
    from pathlib import Path
    from private_client_graph.models import ExtractionResult, GroundTruth
    from private_client_graph.graph import build_graph
    from private_client_graph.evaluation import evaluate_graph

    case = Path(__file__).resolve().parents[2] / "cases/case_01"
    source = (case / "source.txt").read_text()
    extraction = ExtractionResult.model_validate_json((case / "expected_extraction.json").read_text())
    truth = GroundTruth.model_validate_json((case / "ground_truth.json").read_text())
    graph = build_graph(extraction.relationships, document="source.txt", source_text=source)
    engine = create_engine(database)
    matter_id = _legacy_matter(engine, graph.model_dump(), source)
    proposal_id = uuid4()
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO matter_proposals VALUES (:id,'PENDING','Pending','Pending source',:source,CAST(:graph AS jsonb))
        """), {"id": proposal_id, "source": source, "graph": graph.model_dump_json()})
        connection.execute(text("INSERT INTO external_matter_reference_claims VALUES ('pending','matter_proposal',:id)"), {"id": proposal_id})
        pending = dict(connection.execute(text("SELECT * FROM matter_proposals")).mappings().one())
    monkeypatch.setenv("PCG_MATTER_MIGRATION_QUIESCED", "true")
    result = _upgrade()
    assert result.returncode == 0, result.stderr
    with engine.connect() as connection:
        actual = reconstruct_graph(load_matter_state(connection, matter_id))
        assert actual.model_dump() == graph.model_dump()
        assert evaluate_graph(actual, truth) == evaluate_graph(graph, truth)
        assert dict(connection.execute(text("SELECT * FROM matter_proposals")).mappings().one()) == pending
    engine.dispose()
