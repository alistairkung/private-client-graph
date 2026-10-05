from pathlib import Path

from private_client_graph.api.auth import CSRF_COOKIE

PDF = Path(__file__).parents[1] / "fixtures" / "synthetic-proposal.pdf"


def test_local_model_substitution_creates_proposal_through_public_api(
    database, monkeypatch, authenticated_client
):
    from local_development.server import create_local_app
    from private_client_graph.application import matter_proposals

    original_constructor = matter_proposals._construct_model
    original_extractor = matter_proposals.extract_relationships_from_text
    try:
        app = create_local_app(origin="https://testserver")
        client = authenticated_client(app)
        response = client.post(
            "/api/matter-proposals",
            data={
                "external_reference": "LOCAL/001",
                "matter_title": "Local synthetic Matter",
                "source_title": "Synthetic attendance note",
                "synthetic_confirmation": "true",
            },
            files={"pdf": ("synthetic.pdf", PDF.read_bytes(), "application/pdf")},
            headers={
                "origin": "https://testserver",
                "x-csrftoken": client.cookies[CSRF_COOKIE],
            },
        )
    finally:
        matter_proposals._construct_model = original_constructor
        matter_proposals.extract_relationships_from_text = original_extractor

    assert response.status_code == 201, response.text
    assert response.json()["proposed_graph"]["evidence"][0]["supporting_text"] == (
        "Alice Example is the parent of Ben Example."
    )
