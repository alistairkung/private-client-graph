import pytest
from fastapi.testclient import TestClient

from private_client_graph.api.app import create_app
from private_client_graph.application.proposal_config import ProposalAnalysisConfig


@pytest.mark.parametrize('name,value', [
    ('PCG_PROPOSAL_ANALYSIS_LIMIT', None),
    ('PCG_PROPOSAL_ANALYSIS_LIMIT', '0'),
    ('PCG_PROPOSAL_ANALYSIS_LIMIT', '2147483648'),
    ('PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS', None),
    ('PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS', '-1'),
    ('PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS', 'nan'),
    ('DEEPSEEK_API_KEY', ''),
    ('DEEPSEEK_MODEL', ''),
])
def test_invalid_intake_configuration_fails_readiness(monkeypatch, name, value):
    monkeypatch.setenv('PCG_PROPOSAL_ANALYSIS_LIMIT', '10')
    monkeypatch.setenv('PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS', '3600')
    monkeypatch.setenv('DEEPSEEK_API_KEY', 'test-only')
    monkeypatch.setenv('DATABASE_URL', 'postgresql://localhost/test')
    if value is None:
        monkeypatch.delenv(name, raising=False)
    else:
        monkeypatch.setenv(name, value)
    application = create_app()
    with pytest.raises(ValueError):
        ProposalAnalysisConfig.from_environment()
    assert TestClient(application).get('/health').status_code == 503


def test_proposal_settings_are_independent_of_database_readiness(monkeypatch):
    monkeypatch.setenv("PCG_PROPOSAL_ANALYSIS_LIMIT", "10")
    monkeypatch.setenv("PCG_PROPOSAL_ANALYSIS_WINDOW_SECONDS", "3600")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-only")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-flash")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    config = ProposalAnalysisConfig.from_environment()

    assert config.limit == 10
    assert config.window_seconds == 3600
    assert config.model == "deepseek-flash"
    assert config.api_key.get_secret_value() == "test-only"
    # Parsing provider settings alone must not make the combined service ready.
    assert TestClient(create_app()).get("/health").status_code == 503
