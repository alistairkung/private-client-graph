"""Deterministic model substitute for synthetic protected local development."""

from private_client_graph.models import ExtractionResult, RelationshipCandidate
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
