"""Freeze an explicitly reviewed, reconciled development corpus."""

from datetime import date
from pathlib import Path
from typing import Any, Literal

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation
from benchmark_v3.batch.coordinator import family_status, load_commission
from benchmark_v3.batch.ledger import Ledger
from benchmark_v3.research_contracts import Contract, Digest, Slug, Text


class FreezeDecision(Contract):
    schema_version: Literal[1]
    batch_id: Slug
    snapshot_sha256: Digest
    disposition: Literal["freeze"]
    owner: Text
    decided_on: date
    decision_reference: Text
    stopping_rationale: Text


def _candidate(ledger: Ledger, batch_id: str) -> dict[str, Any]:
    commission = load_commission(ledger, batch_id)
    coverage_sha256, families = authorisation.admitted_coverage()
    if len(families) > 20:
        raise ValueError("The development freeze exceeds the approved twenty-family target.")
    register = commissioning.coverage_register()
    reconciliations = {}
    for family in register.families:
        if family.hypothesis is None:
            continue
        reconciliation = commissioning.saved_reconciliation(family)
        if reconciliation is None:
            raise ValueError(f"Family {family.family_id} requires Architect coverage reconciliation before freeze.")
        reconciliations[family.family_id] = authorisation.commitment(reconciliation)

    registered = {row.family_id: row for row in families}
    closed = {"admitted", "returned", "quarantined"}
    for batch in ledger.batch_ids():
        for item in load_commission(ledger, batch).manifest.families:
            revision, state, blocking = family_status(ledger, batch, item.family_id)
            if state not in closed or (state == "returned" and blocking and blocking["repair_permitted"]):
                raise ValueError(f"Resolve Family {item.family_id} before final freeze.")
            if state == "admitted":
                directory = ledger.root / "batches" / batch / item.family_id / str(revision) / "family"
                digest = commissioning.digest(artifacts.read_bytes(directory / "admission.json"))
                if item.family_id not in registered or registered[item.family_id].admission_sha256 != digest:
                    raise ValueError(f"Publish Family {item.family_id}'s exact admission to the development register.")
    return {
        "schema_version": 1, "namespace": "development", "task_id": commission.manifest.task_id,
        "batch_id": batch_id, "target_families": 20, "admitted_families": len(families),
        "condition_count": sum(len(row.conditions) for row in families),
        "coverage_sha256": coverage_sha256, "portfolio_sha256": commission.manifest.portfolio_sha256,
        "families": [family.model_dump(mode="json") for family in families],
        "reconciliations": reconciliations,
    }


def _preview(ledger: Ledger, batch_id: str) -> tuple[Path, str]:
    content = (commissioning.json_text(_candidate(ledger, batch_id)) + "\n").encode()
    digest = commissioning.digest(content)
    path = ledger.root / "freezes" / digest / "candidate.json"
    artifacts.write_bytes(path, content)
    return path, digest


def preview(ledger: Ledger, batch_id: str) -> tuple[Path, str]:
    with ledger.coordinator_lock():
        return _preview(ledger, batch_id)


def record(ledger: Ledger, decision: FreezeDecision) -> Path:
    with ledger.coordinator_lock():
        commission = load_commission(ledger, decision.batch_id)
        if decision.owner != commission.decision.owner:
            raise ValueError("Final freeze requires the commissioning owner's explicit instruction.")
        previous = [
            event for batch in ledger.batch_ids() for event in ledger.events(batch)
            if event["kind"] == "task_freeze"
        ]
        encoded = decision.model_dump(mode="json")
        if previous:
            if previous[0]["details"] != encoded:
                raise ValueError("The task already has an immutable benchmark freeze.")
            path = ledger.root / "freezes" / decision.snapshot_sha256 / "candidate.json"
            if commissioning.digest(artifacts.read_bytes(path)) != decision.snapshot_sha256:
                raise ValueError("The retained frozen snapshot changed.")
        else:
            ledger.require_running()
            path, digest = _preview(ledger, decision.batch_id)
            if digest != decision.snapshot_sha256:
                raise ValueError("The owner decision must identify the exact current freeze snapshot.")
            ledger.event(decision.batch_id, None, 0, "task_freeze", "owner", None, "frozen", encoded)
        target = path.with_name("freeze.json")
        artifacts.write_json(target, encoded)
        return target
