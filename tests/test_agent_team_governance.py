"""Exercise governance failures through the offline validator's public CLI."""

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools/validate_agent_teams.py"


@pytest.fixture
def governance_repo(tmp_path):
    for directory in (".codex", ".agents", ".github", "docs"):
        shutil.copytree(ROOT / directory, tmp_path / directory)
    shutil.copy(ROOT / "AGENTS.md", tmp_path / "AGENTS.md")
    return tmp_path


def validate(root, catalogue=None):
    command = [sys.executable, str(VALIDATOR), "--root", str(root)]
    if catalogue is not None:
        command.extend(["--catalogue", str(catalogue)])
    return subprocess.run(command, capture_output=True, text=True, check=False)


def test_repository_team_conventions_are_valid_offline():
    result = validate(ROOT)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize("field", ["model", "model_reasoning_effort", "sandbox_mode"])
def test_role_configuration_cannot_pin_capability_or_add_unsupported_controls(governance_repo, field):
    role = governance_repo / ".codex/agents/conventions_auditor.toml"
    role.write_text(role.read_text() + f'\n{field} = "high"\n')
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "model/effort belong to the orchestrator" in result.stdout


@pytest.mark.parametrize("limit", ["3", "0", "true"])
def test_concurrency_rejects_values_outside_the_team_limit(governance_repo, limit):
    config = governance_repo / ".codex/config.toml"
    config.write_text(config.read_text().replace("= 2", f"= {limit}"))
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "concurrency must be an integer from 1 to 2" in result.stdout


def test_fallback_does_not_silently_escalate_reasoning(governance_repo):
    config = governance_repo / ".codex/config.toml"
    config.write_text(config.read_text().replace('"low"', '"high"'))
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "economical fallback effort must be low" in result.stdout


def test_unknown_project_agent_key_is_rejected(governance_repo):
    config = governance_repo / ".codex/config.toml"
    config.write_text(config.read_text() + "recursive_delegation = false\n")
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "expected repository keys" in result.stdout


def test_role_must_be_discoverable_through_a_team(governance_repo):
    role = governance_repo / ".codex/agents/conventions_auditor.toml"
    extra = role.with_name("orphan.toml")
    extra.write_text(
        role.read_text()
        .replace("conventions_auditor", "orphan")
        .replace("Read AGENTS", "First read AGENTS")
    )
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "role not registered in any team" in result.stdout


def test_duplicate_role_identity_is_rejected(governance_repo):
    role = governance_repo / ".codex/agents/conventions_auditor.toml"
    role.with_name("duplicate.toml").write_text(role.read_text())
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "duplicate role ID" in result.stdout
    assert "duplicate instructions" in result.stdout


@pytest.mark.parametrize("replacement", ["", "## Scope and non-goals\n\n"])
def test_contract_requires_nonempty_scope(governance_repo, replacement):
    contract = governance_repo / "docs/agents/teams/code-standards.md"
    text = contract.read_text()
    start = text.index("## Scope and non-goals")
    end = text.index("## Roles")
    contract.write_text(text[:start] + replacement + text[end:])
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "missing or empty section Scope and non-goals" in result.stdout


def test_broken_skill_reference_is_reported(governance_repo):
    skill = governance_repo / ".agents/skills/code-review/SKILL.md"
    skill.unlink()
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "broken or external local reference" in result.stdout


def test_role_instruction_reference_is_checked(governance_repo):
    role = governance_repo / ".codex/agents/conventions_auditor.toml"
    role.write_text(role.read_text().replace("docs/CODE_STYLE.md", "docs/missing.md"))
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "missing instruction reference docs/missing.md" in result.stdout


def test_team_must_be_listed_in_discovery_index(governance_repo):
    index = governance_repo / "docs/agents/teams.md"
    index.write_text(
        index.read_text().replace(
            "[code-standards](teams/code-standards.md)", "code-standards"
        )
    )
    result = validate(governance_repo)
    assert result.returncode == 1
    assert "team missing from index" in result.stdout


@pytest.mark.parametrize("levels, expected_code", [(["low", "medium"], 0), (["high"], 1)])
def test_optional_catalogue_validates_model_effort_pair(governance_repo, levels, expected_code):
    catalogue = governance_repo / "catalogue.json"
    catalogue.write_text(json.dumps({
        "models": [{
            "slug": "gpt-6-luna",
            "supported_reasoning_levels": [{"effort": effort} for effort in levels],
        }],
    }))
    result = validate(governance_repo, catalogue)
    assert result.returncode == expected_code, result.stdout + result.stderr
    if expected_code:
        assert "unsupported by gpt-6-luna" in result.stdout


def test_catalogue_does_not_assume_a_permanent_model_list(governance_repo):
    config = governance_repo / ".codex/config.toml"
    config.write_text(config.read_text().replace("gpt-6-luna", "future-economical-model"))
    catalogue = governance_repo / "catalogue.json"
    catalogue.write_text(json.dumps({
        "models": [{
            "slug": "future-economical-model",
            "supported_reasoning_levels": [{"effort": "low"}],
        }],
    }))
    result = validate(governance_repo, catalogue)
    assert result.returncode == 0, result.stdout + result.stderr


def test_malformed_input_reports_an_actionable_error(governance_repo):
    catalogue = governance_repo / "catalogue.json"
    catalogue.write_text('{"models": [{}]}')
    result = validate(governance_repo, catalogue)
    assert result.returncode == 1
    assert "Invalid governance input" in result.stderr


def test_shared_governance_preserves_unrelated_runtime_integrations(governance_repo):
    config = governance_repo / ".codex/config.toml"
    config.write_text(
        config.read_text() + '\n[mcp_servers.motion]\nurl = "https://mcp.motion.dev"\n'
    )
    result = validate(governance_repo)
    assert result.returncode == 0, result.stdout + result.stderr
