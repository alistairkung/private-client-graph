"""Concrete SQL projections of Matter facts; Alembic owns their constraints."""

from sqlalchemy import Column, Integer, Table, Text, Uuid

from .matters import metadata

sources = Table(
    "matter_sources", metadata,
    Column("matter_id", Uuid, primary_key=True), Column("id", Text, primary_key=True),
    Column("position", Integer, nullable=False),
    Column("title", Text, nullable=False), Column("text", Text, nullable=False),
)
entities = Table(
    "matter_entities", metadata,
    Column("matter_id", Uuid, primary_key=True), Column("id", Text, primary_key=True),
    Column("position", Integer, nullable=False),
    Column("type", Text, nullable=False), Column("name", Text, nullable=False),
)
evidence = Table(
    "matter_evidence", metadata,
    Column("matter_id", Uuid, primary_key=True), Column("id", Text, primary_key=True),
    Column("position", Integer, nullable=False), Column("source_id", Text, nullable=False),
    Column("document", Text, nullable=False), Column("supporting_text", Text, nullable=False),
)
relationships = Table(
    "matter_relationships", metadata,
    Column("matter_id", Uuid, primary_key=True), Column("id", Integer, primary_key=True),
    Column("source_id", Text, nullable=False), Column("source_type", Text, nullable=False),
    Column("target_id", Text, nullable=False), Column("target_type", Text, nullable=False),
    Column("type", Text, nullable=False), Column("support_id", Text, nullable=False),
)
support = Table(
    "matter_relationship_evidence", metadata,
    Column("matter_id", Uuid, primary_key=True),
    Column("relationship_id", Integer, primary_key=True),
    Column("evidence_id", Text, primary_key=True), Column("position", Integer, nullable=False),
)
