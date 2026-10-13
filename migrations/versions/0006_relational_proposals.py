"""Proposal facts and the final coordinated canonical persistence cutover.

Frozen SQL mirrors the accepted-Matter guarantees, with separate ownership.
"""

from alembic import op
import sqlalchemy as sa
import os

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    connection = op.get_bind()
    connection.execute(sa.text("SET LOCAL lock_timeout = '5s'"))
    connection.execute(sa.text("SET LOCAL statement_timeout = '0'"))
    connection.execute(sa.text("LOCK TABLE matter_proposals IN ACCESS EXCLUSIVE MODE"))
    rows = connection.execute(sa.text("SELECT * FROM matter_proposals ORDER BY id")).mappings().all()
    if rows and os.getenv("PCG_MATTER_MIGRATION_QUIESCED") != "true":
        raise RuntimeError("Stop old application access and set PCG_MATTER_MIGRATION_QUIESCED=true before cutover")
    op.execute(SCHEMA)
    op.execute(PROVENANCE)
    for row in rows:
        _copy_legacy_proposal(connection, row)
    constraints = (
        "proposal_relationship_has_support, "
        "proposal_relationship_source_fk, proposal_relationship_target_fk, "
        "proposal_support_relationship_fk, proposal_support_evidence_fk"
    )
    connection.execute(sa.text(f"SET CONSTRAINTS {constraints} IMMEDIATE"))
    connection.execute(sa.text(f"SET CONSTRAINTS {constraints} DEFERRED"))
    op.drop_column("matter_proposals", "proposed_graph")
    op.drop_column("matter_proposals", "source_text")
    op.drop_column("matter_proposals", "source_title")


def downgrade() -> None:
    raise RuntimeError("Restore the pre-cutover backup with its matching application; do not discard canonical facts")


def _copy_legacy_proposal(connection, row) -> None:
    """Frozen conversion, deliberately independent of changing application code.

    The destination constraints validate references, types and provenance;
    exact reconstruction catches missing/extra fields or coerced values. Any
    failure rolls back this entire transactional migration, including the DDL.
    """
    graph = row["proposed_graph"]
    owner = row["id"]
    connection.execute(sa.text("""
        INSERT INTO proposal_sources (proposal_id,id,position,title,text)
        VALUES (:owner,'source_001',0,:title,:text)
    """), {"owner": owner, "title": row["source_title"], "text": row["source_text"]})
    for position, entity in enumerate(graph["entities"]):
        connection.execute(sa.text("""
            INSERT INTO proposal_entities (proposal_id,id,position,type,name)
            VALUES (:owner,:id,:position,:type,:name)
        """), {**entity, "owner": owner, "position": position})
    for position, item in enumerate(graph["evidence"]):
        connection.execute(sa.text("""
            INSERT INTO proposal_evidence (proposal_id,id,position,source_id,document,supporting_text)
            VALUES (:owner,:id,:position,'source_001',:document,:supporting_text)
        """), {**item, "owner": owner, "position": position})
    types = {entity["id"]: entity["type"] for entity in graph["entities"]}
    for position, edge in enumerate(graph["relationships"]):
        connection.execute(sa.text("""
            INSERT INTO proposal_relationships (proposal_id,id,source_id,target_id,source_type,target_type,type,support_id)
            VALUES (:owner,:position,:source,:target,:source_type,:target_type,:type,:support)
        """), {**edge, "owner": owner, "position": position,
               "source_type": types[edge["source"]], "target_type": types[edge["target"]],
               "support": edge["evidence_ids"][0]})
        for index, evidence_id in enumerate(edge["evidence_ids"]):
            connection.execute(sa.text("""
                INSERT INTO proposal_relationship_evidence VALUES (:owner,:edge,:evidence,:position)
            """), {"owner": owner, "edge": position, "evidence": evidence_id, "position": index})
    if _reconstructed_graph(connection, owner) != graph:
        raise ValueError(f"Matter Proposal {owner} cannot be reconstructed exactly; no state was converted")


def _reconstructed_graph(connection, owner):
    entities = connection.execute(sa.text("""
        SELECT id,type,name FROM proposal_entities WHERE proposal_id=:owner ORDER BY position
    """), {"owner": owner}).mappings()
    evidence = connection.execute(sa.text("""
        SELECT id,document,supporting_text FROM proposal_evidence WHERE proposal_id=:owner ORDER BY position
    """), {"owner": owner}).mappings()
    edges = connection.execute(sa.text("""
        SELECT id,source_id AS source,type,target_id AS target FROM proposal_relationships
        WHERE proposal_id=:owner ORDER BY id
    """), {"owner": owner}).mappings()
    relationships = []
    for edge in edges:
        quotes = connection.scalars(sa.text("""
            SELECT evidence_id FROM proposal_relationship_evidence
            WHERE proposal_id=:owner AND relationship_id=:edge ORDER BY position
        """), {"owner": owner, "edge": edge["id"]}).all()
        relationships.append({"source": edge["source"], "type": edge["type"],
                              "target": edge["target"], "evidence_ids": list(quotes)})
    return {"entities": [dict(item) for item in entities],
            "evidence": [dict(item) for item in evidence], "relationships": relationships}


SCHEMA = """
CREATE TABLE proposal_sources (
    proposal_id uuid NOT NULL REFERENCES matter_proposals(id) ON DELETE CASCADE,
    id text COLLATE "C" NOT NULL CHECK (pcg_matter_nonblank(id)),
    position integer NOT NULL CHECK (position >= 0),
    title text NOT NULL, text text COLLATE "C" NOT NULL,
    evidence_lock boolean NOT NULL DEFAULT false,
    PRIMARY KEY (proposal_id, id), UNIQUE (proposal_id, position)
);
CREATE TABLE proposal_entities (
    proposal_id uuid NOT NULL REFERENCES matter_proposals(id) ON DELETE CASCADE,
    id text COLLATE "C" NOT NULL CHECK (pcg_matter_nonblank(id)),
    position integer NOT NULL CHECK (position >= 0),
    type text NOT NULL CHECK (type IN ('person','trust')),
    name text NOT NULL CHECK (pcg_matter_nonblank(name)),
    PRIMARY KEY (proposal_id, id), UNIQUE (proposal_id, position),
    UNIQUE (proposal_id, id, type)
);
CREATE TABLE proposal_evidence (
    proposal_id uuid NOT NULL REFERENCES matter_proposals(id) ON DELETE CASCADE,
    id text COLLATE "C" NOT NULL CHECK (pcg_matter_nonblank(id)),
    position integer NOT NULL CHECK (position >= 0),
    source_id text COLLATE "C" NOT NULL,
    document text NOT NULL, supporting_text text COLLATE "C" NOT NULL CHECK (pcg_matter_nonblank(supporting_text)),
    PRIMARY KEY (proposal_id, id), UNIQUE (proposal_id, position),
    CONSTRAINT proposal_evidence_source_fk FOREIGN KEY (proposal_id, source_id)
        REFERENCES proposal_sources(proposal_id, id) ON DELETE RESTRICT NOT DEFERRABLE
);
CREATE INDEX proposal_evidence_source ON proposal_evidence (proposal_id, source_id);
CREATE TABLE proposal_relationships (
    proposal_id uuid NOT NULL REFERENCES matter_proposals(id) ON DELETE CASCADE,
    id integer NOT NULL CHECK (id >= 0),
    source_id text COLLATE "C" NOT NULL, target_id text COLLATE "C" NOT NULL,
    source_type text NOT NULL, target_type text NOT NULL,
    type text NOT NULL, support_id text COLLATE "C" NOT NULL,
    PRIMARY KEY (proposal_id, id),
    CONSTRAINT proposal_relationship_source_fk FOREIGN KEY (proposal_id, source_id, source_type)
        REFERENCES proposal_entities(proposal_id, id, type) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT proposal_relationship_target_fk FOREIGN KEY (proposal_id, target_id, target_type)
        REFERENCES proposal_entities(proposal_id, id, type) DEFERRABLE INITIALLY DEFERRED,
    CHECK (source_id <> target_id),
    CHECK ((type IN ('parent_of','sibling_of','spouse_of') AND source_type = 'person' AND target_type = 'person')
        OR (type IN ('settlor_of','trustee_of','beneficiary_of') AND source_type = 'person' AND target_type = 'trust'))
);
CREATE UNIQUE INDEX proposal_canonical_edge ON proposal_relationships (
    proposal_id, type,
    (CASE WHEN type IN ('spouse_of','sibling_of') THEN LEAST(source_id,target_id) ELSE source_id END),
    (CASE WHEN type IN ('spouse_of','sibling_of') THEN GREATEST(source_id,target_id) ELSE target_id END)
);
CREATE TABLE proposal_relationship_evidence (
    proposal_id uuid NOT NULL, relationship_id integer NOT NULL,
    evidence_id text COLLATE "C" NOT NULL,
    position integer NOT NULL CHECK (position >= 0),
    PRIMARY KEY (proposal_id, relationship_id, evidence_id),
    UNIQUE (proposal_id, relationship_id, position),
    CONSTRAINT proposal_support_relationship_fk FOREIGN KEY (proposal_id, relationship_id)
        REFERENCES proposal_relationships(proposal_id, id) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT proposal_support_evidence_fk FOREIGN KEY (proposal_id, evidence_id)
        REFERENCES proposal_evidence(proposal_id, id) DEFERRABLE INITIALLY DEFERRED
);
ALTER TABLE proposal_relationships ADD CONSTRAINT proposal_relationship_has_support
    FOREIGN KEY (proposal_id, id, support_id)
    REFERENCES proposal_relationship_evidence(proposal_id, relationship_id, evidence_id)
    DEFERRABLE INITIALLY DEFERRED;
"""


PROVENANCE = """
CREATE FUNCTION pcg_proposal_source_immutable() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF (NEW.proposal_id, NEW.id, NEW.text) IS DISTINCT FROM (OLD.proposal_id, OLD.id, OLD.text) THEN
        RAISE EXCEPTION 'Finalized Source identity and text are immutable' USING ERRCODE = '23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER proposal_source_immutable BEFORE UPDATE ON proposal_sources
FOR EACH ROW EXECUTE FUNCTION pcg_proposal_source_immutable();

CREATE FUNCTION pcg_proposal_evidence_valid() RETURNS trigger
LANGUAGE plpgsql VOLATILE AS $$
DECLARE source_text text;
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF (NEW.proposal_id, NEW.source_id, NEW.supporting_text)
            IS DISTINCT FROM (OLD.proposal_id, OLD.source_id, OLD.supporting_text) THEN
            RAISE EXCEPTION 'Evidence attribution and quote are immutable' USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    END IF;
    -- A real row write serializes all inserts for this Source, including under
    -- Repeatable Read (where a stale snapshot must fail with serialization error).
    -- A lock alone would not refresh such a snapshot. This flag is not domain state.
    UPDATE proposal_sources SET evidence_lock = NOT evidence_lock
        WHERE proposal_id = NEW.proposal_id AND id = NEW.source_id
        RETURNING text INTO source_text;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Unresolved Evidence Source' USING ERRCODE = '23503';
    END IF;
    IF strpos(source_text, NEW.supporting_text) = 0 THEN
        RAISE EXCEPTION 'Evidence must occur verbatim in Source' USING ERRCODE = '23514';
    END IF;
    -- This subsequent query obtains a fresh Read Committed snapshot after a
    -- competing Source writer finishes. Compare full text, never digest identity.
    IF EXISTS (SELECT 1 FROM proposal_evidence
        WHERE proposal_id = NEW.proposal_id AND source_id = NEW.source_id
            AND supporting_text = NEW.supporting_text COLLATE "C") THEN
        RAISE EXCEPTION 'Duplicate Source and exact quote' USING ERRCODE = '23505';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER proposal_evidence_valid BEFORE INSERT OR UPDATE ON proposal_evidence
FOR EACH ROW EXECUTE FUNCTION pcg_proposal_evidence_valid();
"""
