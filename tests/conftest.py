"""Synthetic authentication configuration for deterministic tests only."""
import os

os.environ.update({
    "PCG_GOOGLE_CLIENT_ID": "test-client.apps.googleusercontent.com",
    "PCG_GOOGLE_CLIENT_SECRET": "test-google-secret",
    "PCG_SESSION_SECRET": "test-session-secret-with-at-least-32-characters",
    "PCG_TRUSTED_ORIGIN": "https://testserver",
    "PCG_GOOGLE_SUB_ALLOWLIST": "test-subject",
    "PCG_SESSION_SECONDS": "900",
})

import pytest
from fastapi.testclient import TestClient
from google_boundary import GoogleBoundary, sign_in


@pytest.fixture
def authenticated_client():
    def make(app):
        GoogleBoundary().install(app)
        client = TestClient(app, base_url="https://testserver")
        assert sign_in(client).status_code == 303
        return client
    return make
