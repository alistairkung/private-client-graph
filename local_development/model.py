"""Deterministic model substitute for synthetic protected local development."""

from private_client_graph.models import ExtractionResult, RelationshipCandidate, SourcedExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.models.sourced_extraction import source_extraction_from_legacy
from private_client_graph.models.types import RelationshipType


def extract_fixture(source: str, *, llm: object) -> ExtractionResult:
    del llm
    if source.startswith("Morgan Example is settlor"):
        roles: tuple[tuple[RelationshipType, str], ...] = (
            ("settlor_of", "settlor"),
            ("beneficiary_of", "beneficiary"),
            ("trustee_of", "trustee"),
        )
        relationships = [
            RelationshipCandidate(
                source_name="Morgan Example",
                relationship_type=relationship_type,
                target_name="Fictional Trust",
                supporting_text=f"Morgan Example is {role} of the Fictional Trust.",
            )
            for relationship_type, role in roles
        ]
    else:
        relationships = [
            RelationshipCandidate(
                source_name="Alice Example",
                relationship_type="parent_of",
                target_name="Ben Example",
                supporting_text="Alice Example is the parent of Ben Example.",
            )
        ]
    return ExtractionResult(relationships=relationships)


def extract_source_fixtures(sources: list[Source]) -> SourcedExtractionResult:
    """Apply the known local fixtures independently, retaining explicit Source identity."""
    relationships = []
    for source in sources:
        fixture = extract_fixture(source.text, llm=None)
        relationships.extend(source_extraction_from_legacy(fixture, source_id=source.id).relationships)
    return SourcedExtractionResult(relationships=relationships)
