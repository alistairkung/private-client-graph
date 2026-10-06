"""Concrete SQL projections of Matter Proposal facts; Alembic owns their constraints."""

from sqlalchemy import Column, Integer, MetaData, Table, Text, Uuid

metadata = MetaData()
proposals = Table(
    "matter_proposals", metadata,
    Column("id", Uuid, primary_key=True),
    Column("external_reference", Text, nullable=False),
    Column("matter_title", Text, nullable=False),
)

sources = Table(
    "proposal_sources", metadata,
    Column("proposal_id", Uuid, primary_key=True), Column("id", Text, primary_key=True),
    Column("position", Integer, nullable=False),
    Column("title", Text, nullable=False), Column("text", Text, nullable=False),
)
entities = Table(
    "proposal_entities", metadata,
    Column("proposal_id", Uuid, primary_key=True), Column("id", Text, primary_key=True),
    Column("position", Integer, nullable=False),
    Column("type", Text, nullable=False), Column("name", Text, nullable=False),
)
evidence = Table(
    "proposal_evidence", metadata,
    Column("proposal_id", Uuid, primary_key=True), Column("id", Text, primary_key=True),
    Column("position", Integer, nullable=False), Column("source_id", Text, nullable=False),
    Column("document", Text, nullable=False), Column("supporting_text", Text, nullable=False),
)
relationships = Table(
    "proposal_relationships", metadata,
    Column("proposal_id", Uuid, primary_key=True), Column("id", Integer, primary_key=True),
    Column("source_id", Text, nullable=False), Column("source_type", Text, nullable=False),
    Column("target_id", Text, nullable=False), Column("target_type", Text, nullable=False),
    Column("type", Text, nullable=False), Column("support_id", Text, nullable=False),
)
support = Table(
    "proposal_relationship_evidence", metadata,
    Column("proposal_id", Uuid, primary_key=True),
    Column("relationship_id", Integer, primary_key=True),
    Column("evidence_id", Text, primary_key=True), Column("position", Integer, nullable=False),
)
