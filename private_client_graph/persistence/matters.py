"""Matter identity; canonical facts live in owner-scoped child records."""

from sqlalchemy import Column, MetaData, Table, Text, Uuid

metadata = MetaData()
matters = Table(
    "matters",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("external_reference", Text, nullable=False),
    Column("title", Text, nullable=False),
)
