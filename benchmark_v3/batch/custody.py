"""Filesystem custody and the restricted future evaluation handoff."""

import os
import stat
from pathlib import Path
from typing import Literal

from benchmark_v3.batch import artifacts
from benchmark_v3.portfolio import Tier
from benchmark_v3.research_contracts import Contract, Digest, Slug, Text


class EvaluationBrief(Contract):
    schema_version: Literal[1]
    namespace: Literal["evaluation"]
    target_families: Literal[20]
    workloads: dict[Tier, int]
    difficulty_axes: list[Slug]
    distribution: Literal["independent_matter_families"]


class EvaluationLineage(Contract):
    schema_version: Literal[1]
    namespace: Literal["evaluation"]
    portfolio_id: Slug
    portfolio_sha256: Digest
    hypothesis_sha256: Digest
    commissioner: Text


def private_directory(path: Path) -> Path:
    path = path.absolute()
    if path.resolve() != path or any((parent / ".git").exists() for parent in (path, *path.parents)):
        raise ValueError("Use a canonical custody path outside Git checkouts.")
    path.mkdir(parents=True, mode=0o700, exist_ok=True)
    info = path.stat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("Custody requires a directory private to the current OS account.")
    return path


def namespace_directory(path: Path, namespace: Literal["development", "evaluation"]) -> Path:
    directory = private_directory(path)
    if (directory / "ledger-v1.sqlite").exists() and namespace != "development":
        raise ValueError("A development ledger cannot be used for evaluation custody.")
    artifacts.write_json(directory / "namespace.json", {"namespace": namespace, "schema_version": 1})
    return directory


def evaluation_ledger_path(directory: Path, *, development_uid: int, role: str) -> Path:
    """Validate the future ledger mount in the evaluation service account."""
    if role != "evaluation_custodian" or os.getuid() == development_uid:
        raise ValueError("Evaluation custody requires its own OS account and custodian role.")
    return namespace_directory(directory, "evaluation") / "evaluation-ledger-v1.sqlite"


def evaluation_handoff(
    brief: EvaluationBrief, *, development: Path, evaluation: Path, role: str,
) -> dict:
    """Project only the approved taxonomy. Evaluation execution is a future deployment."""
    if role != "evaluation_commissioner":
        raise ValueError("Only the evaluation commissioner may receive this brief.")
    development, evaluation = private_directory(development), private_directory(evaluation)
    if development.is_relative_to(evaluation) or evaluation.is_relative_to(development):
        raise ValueError("Development and evaluation must use disjoint custody directories.")
    # No free-form text fields cross this boundary. Axis IDs come from the public taxonomy.
    from benchmark_v3.commissioning import coverage_register

    if set(brief.difficulty_axes) - {axis.id for axis in coverage_register().taxonomy}:
        raise ValueError("Evaluation may receive only registered difficulty axes.")
    if (sum(brief.workloads.values()) != brief.target_families
            or any(count < 0 for count in brief.workloads.values())):
        raise ValueError("Evaluation workload counts must allocate twenty independent families.")
    return brief.model_dump(mode="json")
