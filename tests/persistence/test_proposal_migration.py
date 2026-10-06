import json
import subprocess
import sys
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text

from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.persistence.matter_state import load_matter_state
from private_client_graph.persistence.proposal_state import load_proposal_state


GRAPH = {
    'entities': [{'id': 'z', 'name': 'Alice', 'type': 'person'}, {'id': 'a', 'name': 'Trust', 'type': 'trust'}],
    'evidence': [{'id': 'q', 'document': 'Legacy label', 'supporting_text': 'Alice is a beneficiary.'}],
    'relationships': [{'source': 'z', 'target': 'a', 'type': 'beneficiary_of', 'evidence_ids': ['q']}],
}
SOURCE = 'Alice is a beneficiary.'


def legacy_state(engine, proposal_graph=GRAPH):
    matter_id, proposal_id = uuid4(), uuid4()
    with engine.begin() as connection:
        connection.execute(text("""
            INSERT INTO matters VALUES (:id,'M-1','Accepted','Matter source',:source,CAST(:graph AS jsonb))
        """), {'id': matter_id, 'source': SOURCE, 'graph': json.dumps(GRAPH)})
        connection.execute(text("""
            INSERT INTO matter_proposals VALUES (:id,'P-1','Pending','Proposal source',:source,CAST(:graph AS jsonb))
        """), {'id': proposal_id, 'source': SOURCE, 'graph': json.dumps(proposal_graph)})
        for kind, owner, ref in [('matter', matter_id, 'm-1'), ('matter_proposal', proposal_id, 'p-1')]:
            connection.execute(text('INSERT INTO external_matter_reference_claims VALUES (:ref,:kind,:id)'), {'ref': ref, 'kind': kind, 'id': owner})
    return matter_id, proposal_id


def upgrade():
    return subprocess.run([sys.executable, '-m', 'alembic', 'upgrade', 'head'], capture_output=True, text=True)


@pytest.mark.parametrize('database', ['0004'], indirect=True)
def test_combined_cutover_preserves_matters_pending_proposals_and_claims(database, monkeypatch):
    engine = create_engine(database)
    matter_id, proposal_id = legacy_state(engine)
    monkeypatch.setenv('PCG_MATTER_MIGRATION_QUIESCED', 'true')
    result = upgrade()
    assert result.returncode == 0, result.stderr
    with engine.connect() as connection:
        for load, owner, title in [(load_matter_state, matter_id, 'Matter source'), (load_proposal_state, proposal_id, 'Proposal source')]:
            state = load(connection, owner)
            assert reconstruct_graph(state).model_dump() == GRAPH
            assert state.sources[0].title == title
            assert state.sources[0].text == SOURCE
            assert state.evidence[0].document == 'Legacy label'
        assert set(connection.scalars(text('SELECT resource_id FROM external_matter_reference_claims'))) == {matter_id, proposal_id}
        assert set(connection.scalars(text("SELECT column_name FROM information_schema.columns WHERE table_name='matter_proposals'"))) == {'id', 'external_reference', 'matter_title'}
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '0006'
    engine.dispose()


@pytest.mark.parametrize('database', ['0004'], indirect=True)
@pytest.mark.parametrize('graph', [
    {**GRAPH, 'entities': []},
    {**GRAPH, 'evidence': [{**GRAPH['evidence'][0], 'supporting_text': 'Invented'}]},
    {**GRAPH, 'relationships': [{**GRAPH['relationships'][0], 'evidence_ids': []}]},
    {**GRAPH, 'unrecognised_authority': 'Do not discard'},
    {**GRAPH, 'relationships': GRAPH['relationships'] * 2},
    {**GRAPH, 'evidence': GRAPH['evidence'] + [{**GRAPH['evidence'][0], 'id': 'another'}]},
])
def test_invalid_pending_state_rolls_back_both_conversions(database, monkeypatch, graph):
    engine = create_engine(database)
    matter_id, proposal_id = legacy_state(engine, graph)
    monkeypatch.setenv('PCG_MATTER_MIGRATION_QUIESCED', 'true')
    result = upgrade()
    assert result.returncode != 0
    with engine.connect() as connection:
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '0004'
        assert connection.scalar(text('SELECT current_graph FROM matters WHERE id=:id'), {'id': matter_id}) == GRAPH
        assert connection.scalar(text('SELECT proposed_graph FROM matter_proposals WHERE id=:id'), {'id': proposal_id}) == graph
        assert connection.scalar(text("SELECT to_regclass('matter_sources')")) is None
        assert connection.scalar(text("SELECT to_regclass('proposal_sources')")) is None
        assert connection.scalar(text('SELECT count(*) FROM external_matter_reference_claims')) == 2
    engine.dispose()


@pytest.mark.parametrize('database', ['0005'], indirect=True)
def test_pending_proposals_require_quiescence_even_without_matters(database, monkeypatch):
    engine = create_engine(database)
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO matter_proposals VALUES (:id,'P-1','Pending','Source',:source,CAST(:graph AS jsonb))"), {'id': uuid4(), 'source': SOURCE, 'graph': json.dumps(GRAPH)})
    monkeypatch.delenv('PCG_MATTER_MIGRATION_QUIESCED', raising=False)
    result = upgrade()
    assert result.returncode != 0
    assert 'PCG_MATTER_MIGRATION_QUIESCED' in result.stderr
    with engine.connect() as connection:
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '0005'
        assert connection.scalar(text('SELECT proposed_graph FROM matter_proposals')) == GRAPH
    engine.dispose()


@pytest.mark.parametrize('database', ['0004'], indirect=True)
def test_case_01_pending_proposal_migrates_and_confirms_without_evaluation_change(database, monkeypatch):
    from private_client_graph.models import ExtractionResult, GroundTruth
    from private_client_graph.graph import build_graph
    from private_client_graph.evaluation import evaluate_graph
    from private_client_graph.persistence.matter_proposals import confirm_proposal

    case = Path(__file__).resolve().parents[2] / 'cases/case_01'
    source = (case / 'source.txt').read_text()
    extraction = ExtractionResult.model_validate_json((case / 'expected_extraction.json').read_text())
    truth = GroundTruth.model_validate_json((case / 'ground_truth.json').read_text())
    graph = build_graph(extraction.relationships, document='Legacy label', source_text=source)
    engine = create_engine(database)
    proposal_id = uuid4()
    with engine.begin() as connection:
        connection.execute(text("INSERT INTO matter_proposals VALUES (:id,'P-1','Pending','Source title',:source,CAST(:graph AS jsonb))"), {'id': proposal_id, 'source': source, 'graph': graph.model_dump_json()})
        connection.execute(text("INSERT INTO external_matter_reference_claims VALUES ('p-1','matter_proposal',:id)"), {'id': proposal_id})
    monkeypatch.setenv('PCG_MATTER_MIGRATION_QUIESCED', 'true')
    result = upgrade()
    assert result.returncode == 0, result.stderr
    matter = confirm_proposal(proposal_id)
    assert matter.current_graph == graph
    assert evaluate_graph(matter.current_graph, truth) == evaluate_graph(graph, truth)
    assert matter.authoritative_source.title == 'Source title'
    engine.dispose()


@pytest.mark.parametrize('database', ['0004'], indirect=True)
def test_pre_cutover_backup_restores_both_legacy_authorities(database, monkeypatch, tmp_path):
    import shutil
    from sqlalchemy.engine import make_url

    dump, restore = shutil.which('pg_dump'), shutil.which('pg_restore')
    if not dump or not restore:
        pytest.skip('PostgreSQL client tools required for backup recovery rehearsal')
    engine = create_engine(database)
    matter_id, proposal_id = legacy_state(engine)
    url = make_url(database).set(drivername='postgresql').render_as_string(hide_password=False)
    backup = tmp_path / 'before-cutover.dump'
    subprocess.run([dump, '--dbname', url, '--format=custom', '--file', str(backup)], check=True)
    monkeypatch.setenv('PCG_MATTER_MIGRATION_QUIESCED', 'true')
    result = upgrade()
    assert result.returncode == 0, result.stderr
    # Disposable test database only: rehearse restoring the complete pre-cutover
    # backup before reopening writes, never merging old/new canonical state.
    with engine.begin() as connection:
        connection.execute(text('DROP SCHEMA public CASCADE'))
        connection.execute(text('CREATE SCHEMA public'))
    subprocess.run([restore, '--dbname', url, '--exit-on-error', '--no-owner', str(backup)], check=True)
    with engine.connect() as connection:
        assert connection.scalar(text('SELECT version_num FROM alembic_version')) == '0004'
        assert connection.scalar(text('SELECT current_graph FROM matters WHERE id=:id'), {'id': matter_id}) == GRAPH
        assert connection.scalar(text('SELECT proposed_graph FROM matter_proposals WHERE id=:id'), {'id': proposal_id}) == GRAPH
        assert set(connection.scalars(text('SELECT resource_id FROM external_matter_reference_claims'))) == {matter_id, proposal_id}
        assert connection.scalar(text("SELECT to_regclass('proposal_sources')")) is None
    engine.dispose()
