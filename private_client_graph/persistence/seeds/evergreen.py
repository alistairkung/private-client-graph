"""Explicit insert-only initialization; never used by ordinary Matter reads."""

from pathlib import Path
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from private_client_graph.canonical_state import reconstruct_graph, single_source_state
from private_client_graph.graph import build_graph
from private_client_graph.models import ExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.persistence.database import database_engine
from private_client_graph.persistence.matters import matters
from private_client_graph.persistence.matter_proposals import reference_claims

EVERGREEN_ID = UUID("ff985caf-60c5-4e65-a238-f3c26381c369")
CASE = Path(__file__).resolve().parents[3] / "cases" / "case_01"


def seed_evergreen() -> bool:
    """Return whether Evergreen was inserted, preserving all existing state."""
    with database_engine().begin() as connection:
        if connection.scalar(select(matters.c.id).where(matters.c.id == EVERGREEN_ID)):
            return False
        source = (CASE / "source.txt").read_text(encoding="utf-8")
        extraction = ExtractionResult.model_validate_json(
            (CASE / "expected_extraction.json").read_text(encoding="utf-8")
        )
        graph = build_graph(extraction.relationships, document="source.txt", source_text=source)
        source_title = "Attendance Note – Meeting with Alice Chen"
        snapshot = reconstruct_graph(single_source_state(
            Source(id="source_001", title=source_title, text=source), graph,
        ))
        statement = insert(matters).values(
            id=EVERGREEN_ID,
            external_reference="PC/2026/0142",
            title="Evergreen Family Trust",
            source_title=source_title,
            source_text=source,
            current_graph=snapshot.model_dump(mode="json"),
        ).on_conflict_do_nothing(index_elements=[matters.c.id]).returning(matters.c.id)
        inserted = connection.scalar(statement) is not None
        if inserted:
            connection.execute(reference_claims.insert().values(
                canonical_reference="pc/2026/0142",
                resource_kind="matter",
                resource_id=EVERGREEN_ID,
            ))
        return inserted


if __name__ == "__main__":
    print("Evergreen inserted." if seed_evergreen() else "Evergreen already exists; unchanged.")
