import pytest
from pydantic import ValidationError

from private_client_graph.models import ExtractionResult, RelationshipCandidate


def test_relationship_candidate_accepts_case_01_relationship():
    candidate = RelationshipCandidate(
        source_name="Alice Chen",
        relationship_type="parent_of",
        target_name="Bob Chen",
        supporting_text=(
            "Alice Chen confirmed that Alice Chen and David Chen "
            "are the parents of Bob Chen."
        ),
    )

    assert candidate.source_name == "Alice Chen"
    assert candidate.relationship_type == "parent_of"
    assert candidate.target_name == "Bob Chen"


def test_relationship_candidate_rejects_unknown_relationship_type():
    with pytest.raises(ValidationError):
        RelationshipCandidate(
            source_name="Alice Chen",
            relationship_type="cousin_of",
            target_name="Carol Wong",
            supporting_text="Carol Wong is Alice Chen's cousin.",
        )


def test_extraction_result_holds_relationship_candidates():
    result = ExtractionResult(
        relationships=[
            RelationshipCandidate(
                source_name="Bob Chen",
                relationship_type="beneficiary_of",
                target_name="Evergreen Family Trust",
                supporting_text=(
                    "Alice Chen confirmed that Bob Chen is a beneficiary "
                    "of the Evergreen Family Trust."
                ),
            )
        ]
    )

    assert len(result.relationships) == 1
