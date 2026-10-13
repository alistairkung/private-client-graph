from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine, text

from private_client_graph.models.canonical_state import CanonicalState


def test_source_aware_proposal_round_trip_and_confirmation(database):
    from private_client_graph.persistence.proposal_state import insert_proposal, load_proposal_state
    from private_client_graph.persistence.matter_proposals import promote_proposal, reference_claims
    from private_client_graph.persistence.matter_state import load_matter_state

    state = CanonicalState.model_validate_json(
        (Path(__file__).resolve().parents[2] / 'tests/fixtures/canonical-state.json').read_text()
    )
    engine = create_engine(database)
    proposal_id = uuid4()
    with engine.begin() as connection:
        insert_proposal(connection, proposal_id=proposal_id, external_reference='R-85', title='Synthetic', state=state)
        connection.execute(reference_claims.insert().values(canonical_reference='r-85', resource_kind='matter_proposal', resource_id=proposal_id))
    with engine.begin() as connection:
        assert load_proposal_state(connection, proposal_id) == state
        matter_id = promote_proposal(connection, proposal_id)
    assert matter_id is not None and matter_id != proposal_id
    with engine.connect() as connection:
        assert load_matter_state(connection, matter_id) == state
        for table in ['matter_proposals', 'proposal_sources', 'proposal_entities', 'proposal_evidence', 'proposal_relationships', 'proposal_relationship_evidence']:
            assert connection.scalar(text(f'SELECT count(*) FROM {table}')) == 0
        assert connection.scalar(text('SELECT resource_id FROM external_matter_reference_claims')) == matter_id
    engine.dispose()


def test_whole_discard_removes_all_source_aware_facts(database):
    from private_client_graph.persistence.proposal_state import insert_proposal
    from private_client_graph.persistence.matter_proposals import discard_proposal, find_reference, reference_claims

    state = CanonicalState.model_validate_json(
        (Path(__file__).resolve().parents[2] / 'tests/fixtures/canonical-state.json').read_text()
    )
    engine = create_engine(database)
    proposal_id = uuid4()
    with engine.begin() as connection:
        insert_proposal(connection, proposal_id=proposal_id, external_reference='R-85', title='Synthetic', state=state)
        connection.execute(reference_claims.insert().values(canonical_reference='r-85', resource_kind='matter_proposal', resource_id=proposal_id))
    assert discard_proposal(proposal_id)
    assert find_reference('R-85') is None
    with engine.connect() as connection:
        for table in ['matter_proposals', 'proposal_sources', 'proposal_entities', 'proposal_evidence', 'proposal_relationships', 'proposal_relationship_evidence', 'matters']:
            assert connection.scalar(text(f'SELECT count(*) FROM {table}')) == 0
    engine.dispose()


def test_failed_fact_copy_retains_the_complete_source_aware_proposal(database):
    import pytest
    from sqlalchemy.exc import IntegrityError
    from private_client_graph.persistence.proposal_state import insert_proposal, load_proposal_state
    from private_client_graph.persistence.matter_proposals import promote_proposal, reference_claims

    state = CanonicalState.model_validate_json(
        (Path(__file__).resolve().parents[2] / 'tests/fixtures/canonical-state.json').read_text()
    )
    engine = create_engine(database)
    proposal_id = uuid4()
    with engine.begin() as connection:
        insert_proposal(connection, proposal_id=proposal_id, external_reference='R-85', title='Synthetic', state=state)
        connection.execute(reference_claims.insert().values(canonical_reference='r-85', resource_kind='matter_proposal', resource_id=proposal_id))
        connection.execute(text("ALTER TABLE matter_evidence ADD CHECK (id <> 'quote_a')"))
    with pytest.raises(IntegrityError):
        with engine.begin() as connection:
            promote_proposal(connection, proposal_id)
    with engine.connect() as connection:
        assert load_proposal_state(connection, proposal_id) == state
        assert connection.scalar(text('SELECT resource_id FROM external_matter_reference_claims')) == proposal_id
        for table in ['matters', 'matter_sources', 'matter_entities', 'matter_evidence', 'matter_relationships', 'matter_relationship_evidence']:
            assert connection.scalar(text(f'SELECT count(*) FROM {table}')) == 0
    engine.dispose()


def test_single_source_api_does_not_consume_a_multisource_proposal(database):
    import pytest
    from private_client_graph.persistence.proposal_state import insert_proposal, load_proposal_state
    from private_client_graph.persistence.matter_proposals import confirm_proposal, get_proposal

    state = CanonicalState.model_validate_json(
        (Path(__file__).resolve().parents[2] / 'tests/fixtures/canonical-state.json').read_text()
    )
    engine = create_engine(database)
    proposal_id = uuid4()
    with engine.begin() as connection:
        insert_proposal(connection, proposal_id=proposal_id, external_reference='R-85', title='Synthetic', state=state)
    for operation in [get_proposal, confirm_proposal]:
        with pytest.raises(ValueError, match='exactly one Source'):
            operation(proposal_id)
    with engine.connect() as connection:
        assert load_proposal_state(connection, proposal_id) == state
        assert connection.scalar(text('SELECT count(*) FROM matters')) == 0
    engine.dispose()
