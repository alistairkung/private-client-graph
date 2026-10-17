"""Exercise the protected local application with synthetic Google and fixture extraction."""
from browser_auth import configure_browser_auth, serve
from local_development.server import create_local_app

configure_browser_auth(4173)

if __name__ == "__main__":
    serve(create_local_app(origin="https://127.0.0.1:4173"), 4173)
