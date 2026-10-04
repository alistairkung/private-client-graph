"""Real practitioner application with only Google HTTP calls substituted."""
from browser_auth import configure_browser_auth, serve

configure_browser_auth(4173)

from private_client_graph.api.app import create_app

if __name__ == "__main__":
    serve(create_app(), 4173)
