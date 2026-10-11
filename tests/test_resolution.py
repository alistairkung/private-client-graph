import pytest

from private_client_graph.models import ExtractionResult
from private_client_graph.resolution import resolve_generative, no_resolution


SOURCE = "Elizabeth Tan is the settlor of Harbour Trust. Beth is Elizabeth Tan's nickname. Beth is a beneficiary of Harbour Trust."


def candidates():
    return ExtractionResult(relationships=[
        dict(source_name="Elizabeth Tan", relationship_type="settlor_of", target_name="Harbour Trust", supporting_text="Elizabeth Tan is the settlor of Harbour Trust."),
        dict(source_name="Beth", relationship_type="beneficiary_of", target_name="Harbour Trust", supporting_text="Beth is a beneficiary of Harbour Trust."),
    ])


def test_resolution_changes_only_requested_endpoint_without_mutating_input():
    original = candidates()
    result = resolve_generative(original, SOURCE, lambda request: {"edits": [
        {"candidate_index": 1, "endpoint": "source_name", "name": "Elizabeth Tan"}
    ]})
    assert result.relationships[1].source_name == "Elizabeth Tan"
    assert result.relationships[1].supporting_text == "Beth is a beneficiary of Harbour Trust."
    assert result.relationships[1].relationship_type == "beneficiary_of"
    assert result.relationships[1].target_name == "Harbour Trust"
    assert result.relationships[0] == original.relationships[0]
    assert len(result.relationships) == 2
    assert original.relationships[1].source_name == "Beth"
    assert no_resolution(original) == original
    assert no_resolution(original) is not original


@pytest.mark.parametrize("response", [
    {"edits": [{"candidate_index": 2, "endpoint": "source_name", "name": "Beth"}]},
    {"edits": [{"candidate_index": -1, "endpoint": "source_name", "name": "Beth"}]},
    {"edits": [{"candidate_index": True, "endpoint": "source_name", "name": "Beth"}]},
    {"edits": [{"candidate_index": 1, "endpoint": "supporting_text", "name": "Beth"}]},
    {"edits": [{"candidate_index": 1, "endpoint": "source_name", "name": "Invented Person"}]},
    {"edits": [{"candidate_index": 1, "endpoint": "source_name", "name": " "}]},
    {"edits": [{"candidate_index": 1, "endpoint": "source_name", "name": "Beth", "relationship_type": "trustee_of"}]},
    {"edits": [], "relationships": []},
    {"edits": [{"candidate_index": 1, "endpoint": "source_name", "name": "Beth"}] * 2},
])
def test_invalid_edits_reject_whole_result(response):
    original = candidates()
    before = original.model_dump()
    with pytest.raises(ValueError):
        resolve_generative(original, SOURCE, lambda request: response)
    assert original.model_dump() == before


def test_uncertain_identity_keeps_everything_and_existing_graph_rules_still_apply():
    from private_client_graph.graph import build_graph

    original = candidates()
    assert resolve_generative(original, SOURCE, lambda request: {"edits": []}) == original
    invalid = resolve_generative(original, SOURCE, lambda request: {"edits": [
        {"candidate_index": 1, "endpoint": "source_name", "name": "Harbour Trust"}
    ]})
    with pytest.raises(ValueError, match="self-relationship"):
        build_graph(invalid.relationships, document="source.txt", source_text=SOURCE)
