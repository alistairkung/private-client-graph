"""Validate PCG's small repository convention, not arbitrary Codex configurations."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import tomllib


REQUIRED_SECTIONS = (
    "Purpose and ownership",
    "Scope and non-goals",
    "Roles",
    "Model and reasoning policy",
    "Tools and skills",
    "Handoffs",
    "Repository boundaries",
    "Delegation limits",
    "Completion and validation",
    "Escalation",
)
ROLE_FIELDS = {"name", "description", "developer_instructions"}
DEFAULT_FIELDS = {
    "max_concurrent_threads_per_session",
    "default_subagent_model",
    "default_subagent_reasoning_effort",
}
LOCAL_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
ROLE_REFERENCE = re.compile(r"(?:AGENTS\.md|docs/[\w./-]+\.md)")


def validate_repository(root: Path, catalogue: dict | None = None) -> list[str]:
    """Return all governance errors; stay offline unless a catalogue is supplied."""
    root = root.resolve()
    errors: list[str] = []
    roles = _validate_roles(root, errors)
    _validate_contracts(root, roles, errors)
    _validate_defaults(root, catalogue, errors)
    return errors


def _read_toml(path: Path, errors: list[str]) -> dict:
    try:
        return tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        errors.append(f"{path.name}: cannot read TOML: {error}")
        return {}


def _validate_roles(root: Path, errors: list[str]) -> set[Path]:
    roles = set((root / ".codex/agents").glob("*.toml"))
    if not roles:
        errors.append("No native roles found in .codex/agents")
    names: set[str] = set()
    instructions: dict[str, str] = {}
    for path in sorted(roles):
        role = _read_toml(path, errors)
        if set(role) != ROLE_FIELDS:
            errors.append(
                f"{path.name}: use only {sorted(ROLE_FIELDS)}; "
                "model/effort belong to the orchestrator"
            )
        for field in ROLE_FIELDS:
            if not isinstance(role.get(field), str) or not role[field].strip():
                errors.append(f"{path.name}: {field} must be a non-empty string")
        name = role.get("name")
        if not isinstance(name, str):
            continue
        if name != path.stem or not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            errors.append(f"{path.name}: name must match filename and use snake_case")
        if name in names:
            errors.append(f"{path.name}: duplicate role ID {name}")
        names.add(name)
        text = role.get("developer_instructions")
        if not isinstance(text, str):
            continue
        normalized = " ".join(text.split())
        if normalized in instructions:
            errors.append(f"{path.name}: duplicate instructions from {instructions[normalized]}")
        instructions[normalized] = path.name
        for reference in ROLE_REFERENCE.findall(text):
            if not (root / reference).is_file():
                errors.append(f"{path.name}: missing instruction reference {reference}")
    return roles


def _local_targets(path: Path, root: Path, errors: list[str]) -> set[Path]:
    targets: set[Path] = set()
    for link in LOCAL_LINK.findall(path.read_text()):
        if re.match(r"[a-zA-Z][\w+.-]*:", link) or link.startswith("#"):
            continue
        target = (path.parent / link.split("#", 1)[0]).resolve()
        if not target.is_relative_to(root) or not target.exists():
            errors.append(f"{path.name}: broken or external local reference {link}")
        targets.add(target)
    return targets


def _validate_contracts(root: Path, roles: set[Path], errors: list[str]) -> None:
    directory = root / "docs/agents"
    index = directory / "teams.md"
    if not index.is_file():
        errors.append("Missing team index docs/agents/teams.md")
        return
    indexed = _local_targets(index, root, errors)
    contracts = sorted((directory / "teams").glob("*.md"))
    if not contracts:
        errors.append("No team contracts found")
    registered: set[Path] = set()
    for path in contracts:
        if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", path.stem):
            errors.append(f"{path.name}: team ID must use kebab-case")
        if path not in indexed:
            errors.append(f"{path.name}: team missing from index")
        text = path.read_text()
        if re.search(r"<[A-Za-z][^>]*>", text):
            errors.append(f"{path.name}: unresolved template placeholder")
        sections = re.split(r"^## (.+)\n", text, flags=re.MULTILINE)
        contents = dict(zip(sections[1::2], sections[2::2]))
        for heading in REQUIRED_SECTIONS:
            if not contents.get(heading, "").strip():
                errors.append(f"{path.name}: missing or empty section {heading}")
        targets = _local_targets(path, root, errors)
        linked_roles = targets & roles
        if not linked_roles:
            errors.append(f"{path.name}: no native roles registered")
        registered.update(linked_roles)
    for path in sorted(roles - registered):
        errors.append(f"{path.name}: role not registered in any team")
    for name in ("team-template.md", "ecosystem-audit.md", "runtime-verification.md"):
        path = directory / name
        if not path.is_file():
            errors.append(f"Missing governance document {path.name}")
        else:
            _local_targets(path, root, errors)


def _validate_defaults(root: Path, catalogue: dict | None, errors: list[str]) -> None:
    config = _read_toml(root / ".codex/config.toml", errors)
    if not isinstance(config.get("agents"), dict):
        errors.append("Project config must contain the shared agents table")
        return
    defaults = config["agents"]
    if set(defaults) != DEFAULT_FIELDS:
        errors.append(f"agents: expected repository keys {sorted(DEFAULT_FIELDS)}")
    limit = defaults.get("max_concurrent_threads_per_session")
    if type(limit) is not int or not 1 <= limit <= 2:
        errors.append("agents: concurrency must be an integer from 1 to 2")
    model = defaults.get("default_subagent_model")
    if not isinstance(model, str) or not model.strip():
        errors.append("agents: fallback model must be a non-empty identifier")
    effort = defaults.get("default_subagent_reasoning_effort")
    if effort != "low":
        errors.append(
            "agents: economical fallback effort must be low; select deeper reasoning per task"
        )
    if catalogue is not None:
        models = {entry["slug"]: entry for entry in catalogue["models"]}
        if model not in models:
            errors.append(f"agents: fallback model {model!r} absent from supplied catalogue")
        elif effort not in {
            level["effort"] for level in models[model]["supported_reasoning_levels"]
        }:
            errors.append(f"agents: fallback effort {effort!r} unsupported by {model}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--catalogue", type=Path, help="Optional JSON from codex debug models; no inference")
    args = parser.parse_args()
    try:
        catalogue = json.loads(args.catalogue.read_text()) if args.catalogue else None
        errors = validate_repository(args.root, catalogue)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Invalid governance input: {error}\n")
    for error in errors:
        print(error)
    if not errors:
        print("Agent team conventions validated (runtime behavior requires the separate smoke check).")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
