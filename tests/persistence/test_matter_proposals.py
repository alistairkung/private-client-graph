import pytest
from pydantic import ValidationError
from uuid import uuid4

from private_client_graph.application.proposal_contracts import ProposalMetadata


def test_metadata_preserves_opaque_display_values_and_trims_only_edges():
    metadata = ProposalMetadata(
        external_reference="  PC / Straße-0042  ",
        matter_title="  Fictional  Chen / Trust 👩‍💻  ",
        source_title="  Synthetic note — first meeting  ",
    )
    assert metadata.model_dump() == {
        "external_reference": "PC / Straße-0042",
        "matter_title": "Fictional  Chen / Trust 👩‍💻",
        "source_title": "Synthetic note — first meeting",
    }


@pytest.mark.parametrize("field,value", [
    ("external_reference", " \t "),
    ("external_reference", "x" * 101),
    ("matter_title", "x" * 201),
    ("source_title", "x" * 201),
    ("external_reference", "Ref\n01"),
    ("matter_title", "Title\x00suffix"),
    ("source_title", "Title\u2028suffix"),
])
def test_metadata_rejects_empty_overlong_control_or_multiline_values(field, value):
    values = {"external_reference": "R-1", "matter_title": "Fictional Matter", "source_title": "Note"}
    values[field] = value
    with pytest.raises(ValidationError):
        ProposalMetadata.model_validate(values)


def test_proposal_detail_requires_evidence_to_occur_in_its_source():
    from private_client_graph.application.proposal_contracts import MatterProposalDetail

    values = {
        "id": uuid4(), "external_reference": "R-1", "matter_title": "Synthetic Matter",
        "authoritative_source": {"title": "Note", "text": "Fictional Alice is trustee."},
        "proposed_graph": {"entities": [], "relationships": [], "evidence": [
            {"id": "ev-1", "document": "Note", "supporting_text": "Alice is trustee"},
        ]},
    }
    detail = MatterProposalDetail.model_validate(values)
    assert detail.authoritative_source.text == "Fictional Alice is trustee."
    values["authoritative_source"]["text"] = "Unrelated fictional source"
    with pytest.raises(ValidationError, match="Evidence"):
        MatterProposalDetail.model_validate(values)


def test_saved_proposal_is_durable_and_claims_its_canonical_reference(database):
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.matter_proposals import find_reference, get_proposal, list_proposals, save_proposal

    assert list_proposals() == []
    assert get_proposal(uuid4()) is None
    proposal = save_proposal(
        ProposalMetadata(external_reference=" PC/Straße-01 ", matter_title="Synthetic Trust", source_title="Note"),
        "Fictional source without relationships.",
        CanonicalGraph(entities=[], relationships=[], evidence=[]),
    )
    assert get_proposal(proposal.id) == proposal
    assert list_proposals()[0].model_dump(mode="json") == {
        "id": str(proposal.id), "external_reference": "PC/Straße-01", "matter_title": "Synthetic Trust",
    }
    assert set(proposal.model_dump()) == {
        "id", "external_reference", "matter_title", "authoritative_source", "proposed_graph",
    }
    owner = find_reference(" pc/STRASSE-01 ")
    assert owner.model_dump(mode="json") == {
        "resource_kind": "matter_proposal", "resource_id": str(proposal.id),
        "location": f"/api/matter-proposals/{proposal.id}",
    }
    assert f"/api/matter-proposals/{proposal.id}" in owner.model_dump_json()
    assert find_reference("PC/Straße-02") is None


def test_competing_creations_reserve_one_reference_and_identify_the_winner(database):
    from concurrent.futures import ThreadPoolExecutor
    from private_client_graph.persistence.proposal_errors import DuplicateReference
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.matter_proposals import list_proposals, save_proposal

    def create(reference):
        try:
            return save_proposal(
                ProposalMetadata(external_reference=reference, matter_title="Synthetic Trust", source_title="Note"),
                "Fictional source.", CanonicalGraph(entities=[], relationships=[], evidence=[]),
            )
        except DuplicateReference as error:
            return error.owner

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(create, [" PC/Straße ", "pc/STRASSE"] * 4))
    assert len(list_proposals()) == 1
    winner = list_proposals()[0]
    assert sum(hasattr(result, "proposed_graph") for result in results) == 1
    for owner in [result for result in results if not hasattr(result, "proposed_graph")]:
        assert owner.resource_id == winner.id
        assert owner.resource_kind == "matter_proposal"
        assert owner.location == f"/api/matter-proposals/{winner.id}"


def test_seed_reserves_accepted_matter_reference_and_blocks_proposals(database):
    from private_client_graph.persistence.proposal_errors import DuplicateReference
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.matter_proposals import find_reference, list_proposals, save_proposal
    from private_client_graph.persistence.seeds.evergreen import EVERGREEN_ID, seed_evergreen

    assert seed_evergreen() is True
    assert seed_evergreen() is False
    owner = find_reference(" pc/2026/0142 ")
    assert owner.resource_kind == "matter"
    assert owner.resource_id == EVERGREEN_ID
    assert owner.location == f"/api/matters/{EVERGREEN_ID}"
    with pytest.raises(DuplicateReference) as caught:
        save_proposal(
            ProposalMetadata(external_reference="pc/2026/0142", matter_title="Another synthetic Matter", source_title="Note"),
            "Fictional source.", CanonicalGraph(entities=[], relationships=[], evidence=[]),
        )
    assert caught.value.owner == owner
    assert list_proposals() == []


def test_discard_removes_whole_proposal_releases_reference_and_creates_no_matter(database):
    from private_client_graph.application.matters import list_matters
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.matter_proposals import discard_proposal, find_reference, get_proposal, save_proposal

    metadata = ProposalMetadata(external_reference="Synthetic-1", matter_title="Synthetic Trust", source_title="Note")
    proposal = save_proposal(metadata, "Fictional source.", CanonicalGraph(entities=[], relationships=[], evidence=[]))
    assert discard_proposal(proposal.id) is True
    assert get_proposal(proposal.id) is None
    assert find_reference("synthetic-1") is None
    assert list_matters() == []
    assert discard_proposal(proposal.id) is False
    replacement = save_proposal(metadata, "Fictional replacement.", CanonicalGraph(entities=[], relationships=[], evidence=[]))
    assert replacement.id != proposal.id


def test_rejected_insert_rolls_back_proposal_and_reference_claim(database):
    from sqlalchemy import text
    from private_client_graph.persistence.proposal_errors import ProposalPersistenceFailure
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.database import database_engine
    from private_client_graph.persistence.matter_proposals import find_reference, list_proposals, save_proposal

    with database_engine().begin() as connection:
        connection.execute(text("ALTER TABLE matter_proposals ADD CHECK (source_text <> 'Rejected synthetic source')"))
    with pytest.raises(ProposalPersistenceFailure) as caught:
        save_proposal(
            ProposalMetadata(external_reference="Synthetic-1", matter_title="Synthetic Trust", source_title="Note"),
            "Rejected synthetic source", CanonicalGraph(entities=[], relationships=[], evidence=[]),
        )
    assert caught.value.ambiguous is False
    assert list_proposals() == []
    assert find_reference("Synthetic-1") is None


@pytest.mark.parametrize("completion_unknown", [False, True])
def test_lost_commit_acknowledgement_is_ambiguous_and_reference_recovers_saved_proposal(database, monkeypatch, completion_unknown):
    import psycopg
    from private_client_graph.persistence.proposal_errors import ProposalPersistenceFailure
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.database import database_engine
    from private_client_graph.persistence.matter_proposals import find_reference, get_proposal, save_proposal

    dialect = database_engine().dialect
    original_commit = dialect.do_commit

    def lose_acknowledgement(connection):
        original_commit(connection)
        error = psycopg.errors.StatementCompletionUnknown if completion_unknown else psycopg.OperationalError
        raise error("Synthetic lost commit acknowledgement")

    with monkeypatch.context() as fault:
        fault.setattr(dialect, "do_commit", lose_acknowledgement)
        with pytest.raises(ProposalPersistenceFailure) as caught:
            save_proposal(
                ProposalMetadata(external_reference="Synthetic-1", matter_title="Synthetic Trust", source_title="Note"),
                "Fictional source.", CanonicalGraph(entities=[], relationships=[], evidence=[]),
            )
    assert caught.value.ambiguous is True
    owner = find_reference("Synthetic-1")
    assert owner.resource_kind == "matter_proposal"
    assert get_proposal(owner.resource_id).authoritative_source.text == "Fictional source."


def test_failed_discard_preserves_proposal_and_reference_together(database):
    from sqlalchemy import text
    from private_client_graph.persistence.proposal_errors import ProposalPersistenceFailure
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.database import database_engine
    from private_client_graph.persistence.matter_proposals import discard_proposal, find_reference, get_proposal, save_proposal

    proposal = save_proposal(
        ProposalMetadata(external_reference="Synthetic-1", matter_title="Synthetic Trust", source_title="Note"),
        "Fictional source.", CanonicalGraph(entities=[], relationships=[], evidence=[]),
    )
    with database_engine().begin() as connection:
        connection.execute(text("""
            CREATE FUNCTION reject_discard() RETURNS trigger AS $$
            BEGIN RAISE EXCEPTION 'Synthetic rejection'; END;
            $$ LANGUAGE plpgsql
        """))
        connection.execute(text("""
            CREATE TRIGGER reject_discard BEFORE DELETE ON matter_proposals
            FOR EACH ROW EXECUTE FUNCTION reject_discard()
        """))
    with pytest.raises(ProposalPersistenceFailure) as caught:
        discard_proposal(proposal.id)
    assert caught.value.ambiguous is False
    assert get_proposal(proposal.id) == proposal
    assert find_reference("Synthetic-1").resource_id == proposal.id


@pytest.mark.parametrize("values", [
    {"source_text": "Unrelated synthetic text"},
    {"proposed_graph": {"entities": "invalid"}},
])
def test_corrupt_proposal_never_leaves_read_boundary_but_can_be_discarded(database, values):
    from sqlalchemy import update
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.database import database_engine
    from private_client_graph.persistence.matter_proposals import discard_proposal, find_reference, get_proposal, proposals, save_proposal

    proposal = save_proposal(
        ProposalMetadata(external_reference="Synthetic-1", matter_title="Synthetic Trust", source_title="Note"),
        "Fictional Alice is trustee.", CanonicalGraph.model_validate({
            "entities": [], "relationships": [], "evidence": [
                {"id": "ev-1", "document": "Note", "supporting_text": "Alice is trustee"},
            ],
        }),
    )
    with database_engine().begin() as connection:
        connection.execute(update(proposals).where(proposals.c.id == proposal.id).values(**values))
    with pytest.raises(ValueError):
        get_proposal(proposal.id)
    assert discard_proposal(proposal.id) is True
    assert find_reference("Synthetic-1") is None


def test_migration_reserves_existing_matter_references_without_fixture_access(database):
    import subprocess
    import sys
    from sqlalchemy import insert
    from private_client_graph.persistence.database import database_engine
    from private_client_graph.persistence.matters import matters
    from private_client_graph.persistence.matter_proposals import find_reference

    subprocess.run([sys.executable, "-m", "alembic", "downgrade", "0002"], check=True)
    existing_id = uuid4()
    with database_engine().begin() as connection:
        connection.execute(insert(matters).values(
            id=existing_id, external_reference=" Legacy/Straße-42 ", title="Existing synthetic Matter",
            source_title="Legacy source", source_text="Fictional source.",
            current_graph={"entities": [], "relationships": [], "evidence": []},
        ))
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True)
    owner = find_reference("legacy/STRASSE-42")
    assert owner.resource_kind == "matter"
    assert owner.resource_id == existing_id


def test_concurrent_discard_consumes_only_one_proposal(database):
    from concurrent.futures import ThreadPoolExecutor
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.matter_proposals import discard_proposal, find_reference, get_proposal, save_proposal

    proposal = save_proposal(
        ProposalMetadata(external_reference="Synthetic-1", matter_title="Synthetic Trust", source_title="Note"),
        "Fictional source.", CanonicalGraph(entities=[], relationships=[], evidence=[]),
    )
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda _: discard_proposal(proposal.id), range(8)))
    assert results.count(True) == 1
    assert get_proposal(proposal.id) is None
    assert find_reference("Synthetic-1") is None


def test_server_rejection_at_commit_proves_rollback(database):
    from sqlalchemy import text
    from private_client_graph.persistence.proposal_errors import ProposalPersistenceFailure
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.database import database_engine
    from private_client_graph.persistence.matter_proposals import find_reference, list_proposals, save_proposal

    with database_engine().begin() as connection:
        connection.execute(text("""
            CREATE FUNCTION reject_proposal_commit() RETURNS trigger AS $$
            BEGIN RAISE check_violation USING MESSAGE = 'Synthetic deferred rejection'; END;
            $$ LANGUAGE plpgsql
        """))
        connection.execute(text("""
            CREATE CONSTRAINT TRIGGER reject_proposal_commit AFTER INSERT ON matter_proposals
            DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION reject_proposal_commit()
        """))
    with pytest.raises(ProposalPersistenceFailure) as caught:
        save_proposal(
            ProposalMetadata(external_reference="Synthetic-1", matter_title="Synthetic Trust", source_title="Note"),
            "Fictional source.", CanonicalGraph(entities=[], relationships=[], evidence=[]),
        )
    assert caught.value.ambiguous is False
    assert list_proposals() == []
    assert find_reference("Synthetic-1") is None


def test_invalid_source_evidence_cannot_persist_a_proposal_or_reservation(database):
    from private_client_graph.models import CanonicalGraph
    from private_client_graph.persistence.matter_proposals import find_reference, list_proposals, save_proposal

    with pytest.raises(ValidationError, match="Evidence"):
        save_proposal(
            ProposalMetadata(external_reference="Synthetic-1", matter_title="Synthetic Trust", source_title="Note"),
            "Fictional source.", CanonicalGraph.model_validate({
                "entities": [], "relationships": [], "evidence": [
                    {"id": "ev-1", "document": "Note", "supporting_text": "Absent quotation"},
                ],
            }),
        )
    assert list_proposals() == []
    assert find_reference("Synthetic-1") is None
