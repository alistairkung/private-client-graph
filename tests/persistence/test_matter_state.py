from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from private_client_graph.canonical_state import reconstruct_graph, single_source_state
from private_client_graph.evaluation import evaluate_graph
from private_client_graph.graph import build_graph
from private_client_graph.models import ExtractionResult, GroundTruth
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.source import Source
from private_client_graph.persistence.matter_state import insert_matter, load_matter_state


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def state():
    return CanonicalState.model_validate_json(
        (ROOT / "tests/fixtures/canonical-state.json").read_text()
    )


def test_source_aware_matter_round_trip(database, state):
    engine = create_engine(database)
    matter_id = uuid4()
    with engine.begin() as connection:
        assert insert_matter(connection, matter_id=matter_id, external_reference="M-1", title="Synthetic", state=state)
    with engine.connect() as connection:
        restored = load_matter_state(connection, matter_id)
    assert restored == state
    assert reconstruct_graph(restored) == reconstruct_graph(state)
    engine.dispose()


def test_case_01_graph_and_evaluation_round_trip(database):
    case = ROOT / "cases/case_01"
    source = Source(id="source_001", title="Attendance note", text=(case / "source.txt").read_text())
    extraction = ExtractionResult.model_validate_json((case / "expected_extraction.json").read_text())
    truth = GroundTruth.model_validate_json((case / "ground_truth.json").read_text())
    graph = build_graph(extraction.relationships, document="source.txt", source_text=source.text)
    engine = create_engine(database)
    matter_id = uuid4()
    with engine.begin() as connection:
        insert_matter(connection, matter_id=matter_id, external_reference="M-1", title="Synthetic", state=single_source_state(source, graph))
    with engine.connect() as connection:
        actual = reconstruct_graph(load_matter_state(connection, matter_id))
    assert actual.model_dump() == graph.model_dump()
    assert evaluate_graph(actual, truth) == evaluate_graph(graph, truth)
    engine.dispose()


@pytest.fixture
def stored(database, state):
    engine = create_engine(database)
    owner = uuid4()
    other = uuid4()
    with engine.begin() as connection:
        insert_matter(connection, matter_id=owner, external_reference="A", title="A", state=state)
        foreign = CanonicalState.model_validate({
            "sources": [{"id": "foreign_source", "title": "Other", "text": "Other quote"}],
            "entities": [{"id": "foreign_entity", "name": "Other", "type": "person"}],
            "evidence": [{"id": "foreign_quote", "source_id": "foreign_source", "document": "Other", "supporting_text": "Other quote"}],
            "relationships": [],
        })
        insert_matter(connection, matter_id=other, external_reference="B", title="B", state=foreign)
    yield engine, {"owner": owner, "other": other}
    engine.dispose()


@pytest.mark.parametrize("sql", [
    "UPDATE matter_evidence SET source_id='missing' WHERE matter_id=:owner AND id='quote_a'",
    "UPDATE matter_relationships SET source_id='missing' WHERE matter_id=:owner AND id=0",
    "UPDATE matter_relationship_evidence SET evidence_id='missing' WHERE matter_id=:owner AND relationship_id=0",
    "UPDATE matter_relationship_evidence SET relationship_id=99 WHERE matter_id=:owner AND relationship_id=0",
    "INSERT INTO matter_relationship_evidence VALUES (:owner,0,'quote_a',99)",
    "UPDATE matter_relationships SET source_id='foreign_entity' WHERE matter_id=:owner AND id=0",
    "UPDATE matter_relationship_evidence SET evidence_id='foreign_quote' WHERE matter_id=:owner AND relationship_id=0",
    "UPDATE matter_evidence SET source_id='foreign_source' WHERE matter_id=:owner AND id='quote_a'",
    "UPDATE matter_entities SET matter_id=:other WHERE matter_id=:owner AND id='shared_alex'",
    "UPDATE matter_sources SET matter_id=:other WHERE matter_id=:owner AND id='note_a'",
    "UPDATE matter_relationships SET matter_id=:other WHERE matter_id=:owner AND id=0",
    "UPDATE matter_relationship_evidence SET matter_id=:other WHERE matter_id=:owner AND relationship_id=0",
    "UPDATE matter_relationships SET type='unknown' WHERE matter_id=:owner AND id=0",
    "UPDATE matter_relationships SET target_id='shared_alex',target_type='person' WHERE matter_id=:owner AND id=0",
    "UPDATE matter_relationships SET source_type='trust' WHERE matter_id=:owner AND id=0",
    "INSERT INTO matter_relationships SELECT matter_id,99,target_id,source_id,target_type,source_type,type,support_id FROM matter_relationships WHERE matter_id=:owner AND id=2",
    "INSERT INTO matter_relationships SELECT matter_id,99,source_id,target_id,source_type,target_type,type,support_id FROM matter_relationships WHERE matter_id=:owner AND id=0",
    "INSERT INTO matter_relationships VALUES (:owner,99,'morgan','trust','person','trust','trustee_of','quote_a')",
    "DELETE FROM matter_relationship_evidence WHERE matter_id=:owner AND relationship_id=1",
    "UPDATE matter_evidence SET supporting_text='Invented' WHERE matter_id=:owner AND id='quote_b'",
    "UPDATE matter_evidence SET supporting_text='Alex Lee' WHERE matter_id=:owner AND id='quote_b'",
    "UPDATE matter_evidence SET source_id='note_a' WHERE matter_id=:owner AND id='quote_b'",
    "UPDATE matter_sources SET text='Changed text' WHERE matter_id=:owner AND id='note_b'",
    "UPDATE matter_sources SET text=text || ' Extra text.' WHERE matter_id=:owner AND id='note_b'",
    "INSERT INTO matter_evidence VALUES (:owner,'invented',99,'note_b','Label','Invented')",
    "INSERT INTO matter_evidence VALUES (:owner,'duplicate',99,'note_b','Different label','Alex Lee is a beneficiary of Cedar Trust.')",
])
def test_database_rejects_invalid_canonical_writes(stored, sql):
    engine, params = stored
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text(sql), params)


def test_long_exact_quotes_are_distinct_without_hash_identity(stored):
    engine, params = stored
    # Deterministic, poorly compressible text exceeding a B-tree index entry.
    import hashlib
    quote = "".join(hashlib.sha256(str(i).encode()).hexdigest() for i in range(500))
    second = quote + "!"
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO matter_sources (matter_id,id,position,title,text) VALUES (:owner,'long',99,'Long',:text)"), {**params, "text": second})
        for position, value in enumerate([quote, second], 10):
            connection.execute(text("INSERT INTO matter_evidence VALUES (:owner,:id,:position,'long','Long',:quote)"), {**params, "id": str(position), "position": position, "quote": value})
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO matter_evidence VALUES (:owner,'again',100,'long','Long',:quote)"), {**params, "quote": quote})


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"])
def test_concurrent_equal_quote_inserts_cannot_bypass_uniqueness(stored, isolation):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.exc import DBAPIError

    engine, params = stored
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO matter_sources (matter_id,id,position,title,text) VALUES (:owner,'concurrent',90,'Note','New quote.')"), params)
    ready = Barrier(2, timeout=5)

    def insert_quote(index):
        try:
            with engine.connect().execution_options(isolation_level=isolation) as connection:
                with connection.begin():
                    connection.execute(text("SELECT count(*) FROM matter_evidence"))
                    ready.wait()
                    connection.execute(text("INSERT INTO matter_evidence VALUES (:owner,:id,:position,'concurrent','Note','New quote.')"), {**params, "id": f"new-{index}", "position": 90 + index})
            return "committed"
        except DBAPIError as error:
            return error.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(insert_quote, [0, 1]))
    assert results.count("committed") == 1, results
    assert set(results) <= {"committed", "23505", "40001"}, results


def test_competing_support_removal_cannot_leave_an_unsupported_relationship(stored):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.exc import DBAPIError

    engine, params = stored
    ready = Barrier(2, timeout=5)

    def remove_support(removed):
        retained = "quote_b" if removed == "quote_a" else "quote_a"
        try:
            with engine.begin() as connection:
                ready.wait()
                connection.execute(text("UPDATE matter_relationships SET support_id=:retained WHERE matter_id=:owner AND id=0"), {**params, "retained": retained})
                connection.execute(text("DELETE FROM matter_relationship_evidence WHERE matter_id=:owner AND relationship_id=0 AND evidence_id=:removed"), {**params, "removed": removed})
            return "committed"
        except DBAPIError as error:
            return error.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(remove_support, ["quote_a", "quote_b"]))
    assert results.count("committed") == 1, results
    assert set(results) == {"committed", "23503"}, results
    with engine.connect() as connection:
        assert len(load_matter_state(connection, params["owner"]).relationships[0].evidence_ids) == 1


def test_duplicate_quotes_in_one_statement_are_rejected(stored):
    engine, params = stored
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO matter_evidence VALUES
                (:owner,'new-a',90,'note_b','A','Alex Lee'),
                (:owner,'new-b',91,'note_b','B','Alex Lee')
            """), params)


def test_insert_rollback_leaves_no_partial_matter(database, state):
    engine = create_engine(database)
    matter_id = uuid4()
    with pytest.raises(RuntimeError):
        with engine.begin() as connection:
            insert_matter(connection, matter_id=matter_id, external_reference="A", title="A", state=state)
            raise RuntimeError("abort before commit")
    with engine.connect() as connection:
        for table in ["matters", "matter_sources", "matter_entities", "matter_evidence", "matter_relationships", "matter_relationship_evidence"]:
            assert connection.scalar(text(f"SELECT count(*) FROM {table}")) == 0
    engine.dispose()


def test_relational_state_cannot_be_presented_against_an_arbitrary_single_source(database, state, authenticated_client):
    from private_client_graph.api.app import create_app

    engine = create_engine(database)
    matter_id = uuid4()
    with engine.begin() as connection:
        insert_matter(connection, matter_id=matter_id, external_reference="A", title="A", state=state)
    response = authenticated_client(create_app()).get(f"/api/matters/{matter_id}")
    assert response.status_code == 503
    assert response.json() == {"error": {"message": "Matter could not be loaded."}}
    engine.dispose()


def test_atomic_aggregate_removal_leaves_no_dangling_support(stored):
    engine, params = stored
    with engine.begin() as connection:
        connection.execute(text("DELETE FROM matters WHERE id=:owner"), params)
    with engine.connect() as connection:
        for table in ["matter_sources", "matter_entities", "matter_evidence", "matter_relationships", "matter_relationship_evidence"]:
            assert connection.scalar(text(f"SELECT count(*) FROM {table} WHERE matter_id=:owner"), params) == 0


@pytest.mark.parametrize("statements", [
    ["WITH removed AS (DELETE FROM matter_sources WHERE matter_id=:owner AND id='note_a' RETURNING matter_id,id,position,title) INSERT INTO matter_sources (matter_id,id,position,title,text) SELECT matter_id,id,position,title,'Unrelated text' FROM removed"],
    ["DELETE FROM matter_sources WHERE matter_id=:owner AND id='note_a'",
     "INSERT INTO matter_sources (matter_id,id,position,title,text) VALUES (:owner,'note_a',1,'Replacement','Unrelated text')"],
    ["UPDATE matter_sources SET id='temporary' WHERE matter_id=:owner AND id='note_a'",
     "UPDATE matter_sources SET id='note_a' WHERE matter_id=:owner AND id='note_b'",
     "UPDATE matter_sources SET id='note_b' WHERE matter_id=:owner AND id='temporary'"],
    ["UPDATE matter_sources SET matter_id=:other, position=99 WHERE matter_id=:owner AND id='note_a'",
     "INSERT INTO matter_sources (matter_id,id,position,title,text) VALUES (:owner,'note_a',1,'Replacement','Unrelated text')"],
])
def test_source_replacement_cannot_rebind_retained_evidence(stored, statements):
    engine, params = stored
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement), params)
