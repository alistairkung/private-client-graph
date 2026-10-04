"""One complete Matter per row; graph contents remain domain-owned JSONB."""

from sqlalchemy import Column, MetaData, Table, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()
matters = Table(
    "matters",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("external_reference", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("source_title", Text, nullable=False),
    Column("source_text", Text, nullable=False),
    Column("current_graph", JSONB, nullable=False),
)
