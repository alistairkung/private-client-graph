"""Synthetic authentication configuration for deterministic tests only."""
import os

os.environ.update({
    "PCG_GOOGLE_CLIENT_ID": "test-client.apps.googleusercontent.com",
    "PCG_GOOGLE_CLIENT_SECRET": "test-google-secret",
    "PCG_SESSION_SECRET": "test-session-secret-with-at-least-32-characters",
    "PCG_TRUSTED_ORIGIN": "https://testserver",
    "PCG_GOOGLE_SUB_ALLOWLIST": "test-subject",
    "PCG_SESSION_SECONDS": "900",
    "PCG_PROPOSAL_ANALYSIS_LIMIT": "100",
    "PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS": "86400",
    "DEEPSEEK_API_KEY": "test-only",
})

import pytest
from fastapi.testclient import TestClient
from google_boundary import make_google_boundary, sign_in


@pytest.fixture
def authenticated_client():
    def make(app):
        make_google_boundary().install(app)
        client = TestClient(app, base_url="https://testserver")
        assert sign_in(client).status_code == 303
        return client
    return make


from tempfile import SpooledTemporaryFile
from starlette import formparsers


@pytest.fixture
def tracked_upload_files(monkeypatch):
    files = []

    def temporary_file(*args, **kwargs):
        file = SpooledTemporaryFile(*args, **kwargs)
        files.append(file)
        return file

    # Observe real filesystem resources, leaving multipart and PDF parsing real.
    monkeypatch.setattr(formparsers, "SpooledTemporaryFile", temporary_file)
    yield files
    for file in files:
        file.close()
