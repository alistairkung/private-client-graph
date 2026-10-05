"""Real practitioner application with only Google and model calls substituted."""
from browser_auth import configure_browser_auth, serve
from local_development.model import extract_fixture

configure_browser_auth(4173)

from private_client_graph.api.app import create_app
from private_client_graph.application import matter_proposals


matter_proposals.extract_relationships_from_text = extract_fixture

if __name__ == "__main__":
    serve(create_app(), 4173)
