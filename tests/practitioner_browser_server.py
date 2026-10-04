"""Real practitioner application with only Google and model calls substituted."""
from browser_auth import configure_browser_auth, serve

configure_browser_auth(4173)

from private_client_graph.api.app import create_app
from private_client_graph.application import matter_proposals
from private_client_graph.models import ExtractionResult, RelationshipCandidate


def extract_fixture(source, *, llm):
    if source.startswith("Morgan Example is settlor"):
        return ExtractionResult(relationships=[RelationshipCandidate(
            source_name="Morgan Example",
            relationship_type=f"{role}_of",
            target_name="Fictional Trust",
            supporting_text=f"Morgan Example is {role} of the Fictional Trust.",
        ) for role in ("settlor", "beneficiary", "trustee")])
    return ExtractionResult(relationships=[RelationshipCandidate(
        source_name="Alice Example",
        relationship_type="parent_of",
        target_name="Ben Example",
        supporting_text="Alice Example is the parent of Ben Example.",
    )])


matter_proposals.extract_relationships_from_text = extract_fixture

if __name__ == "__main__":
    serve(create_app(), 4173)
