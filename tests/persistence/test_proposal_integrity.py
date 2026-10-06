from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.persistence.proposal_state import insert_proposal, load_proposal_state


@pytest.fixture
def state():
    return CanonicalState.model_validate_json(
        (Path(__file__).resolve().parents[2] / "tests/fixtures/canonical-state.json").read_text()
    )


@pytest.fixture
def stored(database, state):
    engine = create_engine(database)
    owner = uuid4()
    other = uuid4()
    with engine.begin() as connection:
        insert_proposal(connection, proposal_id=owner, external_reference="A", title="A", state=state)
        foreign = CanonicalState.model_validate({
            "sources": [{"id": "foreign_source", "title": "Other", "text": "Other quote"}],
            "entities": [{"id": "foreign_entity", "name": "Other", "type": "person"}],
            "evidence": [{"id": "foreign_quote", "source_id": "foreign_source", "document": "Other", "supporting_text": "Other quote"}],
            "relationships": [],
        })
        insert_proposal(connection, proposal_id=other, external_reference="B", title="B", state=foreign)
    yield engine, {"owner": owner, "other": other}
    engine.dispose()


@pytest.mark.parametrize("sql", [
    "UPDATE proposal_evidence SET source_id='missing' WHERE proposal_id=:owner AND id='quote_a'",
    "UPDATE proposal_relationships SET source_id='missing' WHERE proposal_id=:owner AND id=0",
    "UPDATE proposal_relationship_evidence SET evidence_id='missing' WHERE proposal_id=:owner AND relationship_id=0",
    "UPDATE proposal_relationship_evidence SET relationship_id=99 WHERE proposal_id=:owner AND relationship_id=0",
    "INSERT INTO proposal_relationship_evidence VALUES (:owner,0,'quote_a',99)",
    "UPDATE proposal_relationships SET source_id='foreign_entity' WHERE proposal_id=:owner AND id=0",
    "UPDATE proposal_relationship_evidence SET evidence_id='foreign_quote' WHERE proposal_id=:owner AND relationship_id=0",
    "UPDATE proposal_evidence SET source_id='foreign_source' WHERE proposal_id=:owner AND id='quote_a'",
    "UPDATE proposal_entities SET proposal_id=:other WHERE proposal_id=:owner AND id='shared_alex'",
    "UPDATE proposal_sources SET proposal_id=:other WHERE proposal_id=:owner AND id='note_a'",
    "UPDATE proposal_relationships SET proposal_id=:other WHERE proposal_id=:owner AND id=0",
    "UPDATE proposal_relationship_evidence SET proposal_id=:other WHERE proposal_id=:owner AND relationship_id=0",
    "UPDATE proposal_relationships SET type='unknown' WHERE proposal_id=:owner AND id=0",
    "UPDATE proposal_relationships SET target_id='shared_alex',target_type='person' WHERE proposal_id=:owner AND id=0",
    "UPDATE proposal_relationships SET source_type='trust' WHERE proposal_id=:owner AND id=0",
    "INSERT INTO proposal_relationships SELECT proposal_id,99,target_id,source_id,target_type,source_type,type,support_id FROM proposal_relationships WHERE proposal_id=:owner AND id=2",
    "INSERT INTO proposal_relationships SELECT proposal_id,99,source_id,target_id,source_type,target_type,type,support_id FROM proposal_relationships WHERE proposal_id=:owner AND id=0",
    "INSERT INTO proposal_relationships VALUES (:owner,99,'morgan','trust','person','trust','trustee_of','quote_a')",
    "DELETE FROM proposal_relationship_evidence WHERE proposal_id=:owner AND relationship_id=1",
    "UPDATE proposal_evidence SET supporting_text='Invented' WHERE proposal_id=:owner AND id='quote_b'",
    "UPDATE proposal_evidence SET supporting_text='Alex Lee' WHERE proposal_id=:owner AND id='quote_b'",
    "UPDATE proposal_evidence SET source_id='note_a' WHERE proposal_id=:owner AND id='quote_b'",
    "UPDATE proposal_sources SET text='Changed text' WHERE proposal_id=:owner AND id='note_b'",
    "UPDATE proposal_sources SET text=text || ' Extra text.' WHERE proposal_id=:owner AND id='note_b'",
    "INSERT INTO proposal_evidence VALUES (:owner,'invented',99,'note_b','Label','Invented')",
    "INSERT INTO proposal_evidence VALUES (:owner,'duplicate',99,'note_b','Different label','Alex Lee is a beneficiary of Cedar Trust.')",
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
        connection.execute(text("INSERT INTO proposal_sources (proposal_id,id,position,title,text) VALUES (:owner,'long',99,'Long',:text)"), {**params, "text": second})
        for position, value in enumerate([quote, second], 10):
            connection.execute(text("INSERT INTO proposal_evidence VALUES (:owner,:id,:position,'long','Long',:quote)"), {**params, "id": str(position), "position": position, "quote": value})
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO proposal_evidence VALUES (:owner,'again',100,'long','Long',:quote)"), {**params, "quote": quote})


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"])
def test_concurrent_equal_quote_inserts_cannot_bypass_uniqueness(stored, isolation):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from sqlalchemy.exc import DBAPIError

    engine, params = stored
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO proposal_sources (proposal_id,id,position,title,text) VALUES (:owner,'concurrent',90,'Note','New quote.')"), params)
    ready = Barrier(2, timeout=5)

    def insert_quote(index):
        try:
            with engine.connect().execution_options(isolation_level=isolation) as connection:
                with connection.begin():
                    connection.execute(text("SELECT count(*) FROM proposal_evidence"))
                    ready.wait()
                    connection.execute(text("INSERT INTO proposal_evidence VALUES (:owner,:id,:position,'concurrent','Note','New quote.')"), {**params, "id": f"new-{index}", "position": 90 + index})
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
                connection.execute(text("UPDATE proposal_relationships SET support_id=:retained WHERE proposal_id=:owner AND id=0"), {**params, "retained": retained})
                connection.execute(text("DELETE FROM proposal_relationship_evidence WHERE proposal_id=:owner AND relationship_id=0 AND evidence_id=:removed"), {**params, "removed": removed})
            return "committed"
        except DBAPIError as error:
            return error.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(remove_support, ["quote_a", "quote_b"]))
    assert results.count("committed") == 1, results
    assert set(results) == {"committed", "23503"}, results
    with engine.connect() as connection:
        assert len(load_proposal_state(connection, params["owner"]).relationships[0].evidence_ids) == 1


def test_duplicate_quotes_in_one_statement_are_rejected(stored):
    engine, params = stored
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text("""
                INSERT INTO proposal_evidence VALUES
                (:owner,'new-a',90,'note_b','A','Alex Lee'),
                (:owner,'new-b',91,'note_b','B','Alex Lee')
            """), params)



@pytest.mark.parametrize("statements", [
    ["WITH removed AS (DELETE FROM proposal_sources WHERE proposal_id=:owner AND id='note_a' RETURNING proposal_id,id,position,title) INSERT INTO proposal_sources (proposal_id,id,position,title,text) SELECT proposal_id,id,position,title,'Unrelated text' FROM removed"],
    ["DELETE FROM proposal_sources WHERE proposal_id=:owner AND id='note_a'",
     "INSERT INTO proposal_sources (proposal_id,id,position,title,text) VALUES (:owner,'note_a',1,'Replacement','Unrelated text')"],
    ["UPDATE proposal_sources SET id='temporary' WHERE proposal_id=:owner AND id='note_a'",
     "UPDATE proposal_sources SET id='note_a' WHERE proposal_id=:owner AND id='note_b'",
     "UPDATE proposal_sources SET id='note_b' WHERE proposal_id=:owner AND id='temporary'"],
    ["UPDATE proposal_sources SET proposal_id=:other, position=99 WHERE proposal_id=:owner AND id='note_a'",
     "INSERT INTO proposal_sources (proposal_id,id,position,title,text) VALUES (:owner,'note_a',1,'Replacement','Unrelated text')"],
])
def test_source_replacement_cannot_rebind_retained_evidence(stored, statements):
    engine, params = stored
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            for statement in statements:
                connection.execute(text(statement), params)


@pytest.mark.parametrize('sql', [
    "UPDATE proposal_relationships SET source_id='matter_person' WHERE proposal_id=:owner AND id=0",
    "UPDATE proposal_relationship_evidence SET evidence_id='matter_quote' WHERE proposal_id=:owner AND relationship_id=0",
    "INSERT INTO proposal_evidence VALUES (:owner,'mixed',99,'matter_source','Label','Other quote')",
    "INSERT INTO proposal_sources (proposal_id,id,position,title,text) VALUES (:matter_only,'s',0,'Note','Text')",
])
def test_proposal_references_cannot_resolve_through_matter_tables(stored, sql):
    from private_client_graph.persistence.matter_state import insert_matter

    engine, params = stored
    matter_only = uuid4()
    state = CanonicalState.model_validate({
        'sources': [{'id': 'matter_source', 'title': 'Other', 'text': 'Other quote'}],
        'entities': [{'id': 'matter_person', 'name': 'Other', 'type': 'person'}],
        'evidence': [{'id': 'matter_quote', 'source_id': 'matter_source', 'document': 'Other', 'supporting_text': 'Other quote'}],
        'relationships': [],
    })
    with engine.begin() as connection:
        for owner in [params['owner'], matter_only]:
            insert_matter(connection, matter_id=owner, external_reference=str(owner), title='Other', state=state)
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            connection.execute(text(sql), {**params, 'matter_only': matter_only})
