"""Alembic owns schema changes; initialization is a separate explicit command."""

from alembic import context

from private_client_graph.persistence.database import database_engine
from private_client_graph.persistence.matters import metadata

if context.is_offline_mode():
    context.configure(
        url=database_engine().url,
        target_metadata=metadata,
        literal_binds=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    with database_engine().connect() as connection:
        context.configure(connection=connection, target_metadata=metadata)
        with context.begin_transaction():
            context.run_migrations()
