"""Produce batch review packages and record exact independent human decisions."""

from pathlib import Path
from typing import Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation
from benchmark_v3.batch.contracts import AdmissionDecisions, PilotDecision
from benchmark_v3.batch.coordinator import family_status, load_commission
from benchmark_v3.batch.ledger import Ledger, timestamp
from benchmark_v3.batch.workflow import offline_report, review_commitments
from benchmark_v3.replay_manifest import BatchFamilyManifest, load_family


def package_batch(ledger: Ledger, batch_id: str) -> tuple[Path, str]:
    with ledger.coordinator_lock():
        manifest = load_commission(ledger, batch_id).manifest
        families = [_family_summary(ledger, batch_id, row.family_id) for row in manifest.families]
        snapshot = {
            "schema_version": 1, "batch_id": batch_id, "phase": manifest.phase,
            "portfolio_sha256": manifest.portfolio_sha256,
            "state": _batch_state(families),
            "task_session_ceiling": manifest.task_session_ceiling,
            "families": families,
        }
        if repair := ledger.construction_repair():
            snapshot["task_session_ceiling"] = repair.task_ceiling
            snapshot["construction_repair_sha256"] = authorisation.commitment(repair)
        content = (commissioning.json_text(snapshot) + "\n").encode()
        digest = commissioning.digest(content)
        path = ledger.root / "batches" / batch_id / "summaries" / digest
        artifacts.write_bytes(path / "summary.json", content)
        artifacts.write_bytes(path / "SUMMARY.md", _markdown(snapshot, digest).encode())
        return path / "SUMMARY.md", digest


def _batch_state(families: list[dict[str, Any]]) -> str:
    states = {row["state"] for row in families}
    if states <= {"admitted", "returned", "quarantined"}:
        return "closed"
    if any(row["exception"] for row in families if row["state"] not in {"returned", "quarantined"}):
        return "blocked"
    if states <= {"admission_ready", "admitted", "returned", "quarantined"}:
        return "awaiting_admission"
    return "running"


def _family_summary(ledger: Ledger, batch: str, family: str) -> dict[str, Any]:
    revision, state, blocking = family_status(ledger, batch, family)
    events = ledger.events(batch, family)
    ready = next((row["details"] for row in events
                  if row["revision"] == revision and row["kind"] == "transition" and row["name"] == "dossier"), None)
    dossier = None
    if ready:
        dossier = _verify_dossier(ledger, batch, family, revision, ready["family_sha256"])
    elif state == "admission_ready":
        state = "technical"
    sessions = [row["details"] for row in events if row["kind"] == "session"]
    attempts = ledger.attempts(family)
    return {
        "family_id": family, "revision": revision, "state": state, "exception": blocking,
        "family_sha256": ready["family_sha256"] if ready else None,
        "recommendation": dossier["recommendation"] if dossier else state,
        "dossier": f"../../{family}/{revision}/family/DOSSIER.md" if dossier else None,
        "charged_attempts": len(attempts),
        "completed_sessions": sum(row["status"] == "completed" for row in sessions),
        "unpriced_attempts": len(attempts) - sum(row["pricing"] == "priced" for row in sessions),
        "known_cost_usd": sum(row["cost_usd"] for row in sessions if row["pricing"] == "priced"),
    }


def _markdown(snapshot: dict[str, Any], digest: str) -> str:
    lines = [
        f"# Benchmark v3 batch {snapshot['batch_id']}", "",
        f"State **{snapshot['state']}**. Review commitment `{digest}`.", "",
        "| Family | State | Recommendation | Sessions charged | Unpriced | Known USD |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for row in snapshot["families"]:
        family = row["family_id"]
        label = f"[{family}]({row['dossier']})" if row["dossier"] else family
        lines.append(
            f"| {label} | {row['state']} | {row['recommendation']} | {row['charged_attempts']} | "
            f"{row['unpriced_attempts']} | {row['known_cost_usd']:.2f} |"
        )
    for row in snapshot["families"]:
        if row["family_sha256"]:
            lines.extend(["", f"Family {row['family_id']} commitment `{row['family_sha256']}`."])
        if exception := row["exception"]:
            lines.extend(["", f"Family {row['family_id']} · {exception['stage']} · {exception['code']}. "
                          f"{exception['human_action'] or 'Documentary repair is permitted.'} "
                          "[Retained exception evidence](summary.json)."])
    return "\n".join(lines) + "\n"


def record_pilot_review(ledger: Ledger, decision: PilotDecision) -> None:
    with ledger.coordinator_lock():
        commission = load_commission(ledger, decision.pilot_batch_id)
        ledger.require_running()
        if commission.manifest.phase != "pilot" or decision.owner != commission.decision.owner:
            raise ValueError("Pilot continuation requires the commissioning owner's decision.")
        path = (ledger.root / "batches" / decision.pilot_batch_id / "summaries"
                / decision.summary_sha256 / "summary.json")
        content = artifacts.read_bytes(path)
        snapshot = commissioning._read_json(content)
        if commissioning.digest(content) != decision.summary_sha256 or snapshot["batch_id"] != decision.pilot_batch_id:
            raise ValueError("Pilot review must match the exact batch summary.")
        if decision.status == "continue":
            for row in snapshot["families"]:
                current = _family_summary(ledger, decision.pilot_batch_id, row["family_id"])
                if (row["state"] not in {"admission_ready", "admitted", "returned", "quarantined"}
                        or any(row[key] != current[key] for key in (
                            "revision", "family_sha256", "charged_attempts",
                        ))
                        or current["state"] not in {"admission_ready", "admitted", "returned", "quarantined"}):
                    raise ValueError("Continuation requires determinate current outcomes for all pilot families.")
        ledger.event(decision.pilot_batch_id, None, 0, "pilot_decision", "owner", None, decision.status,
                     decision.model_dump(mode="json"))


def record_admissions(ledger: Ledger, decisions: AdmissionDecisions) -> list[Path]:
    with ledger.coordinator_lock():
        commission = load_commission(ledger, decisions.batch_id)
        ledger.require_running()
        if decisions.owner != commission.decision.owner:
            raise ValueError("Admission requires the commissioning owner's explicit decisions.")
        rows = _validate_decisions(ledger, decisions)
        with ledger.transaction() as connection:
            for family, revision, _, record in rows:
                ledger._append(connection, decisions.batch_id, family, revision, "human_decision", "owner",
                               "admission_ready", record["status"], record)
        for _, _, path, record in rows:
            artifacts.write_json(path, record)
        return [path for _, _, path, _ in rows]


def _validate_decisions(
    ledger: Ledger, decisions: AdmissionDecisions,
) -> list[tuple[str, int, Path, dict[str, Any]]]:
    rows = []
    for decision in decisions.decisions:
        family = decision.family_id
        revision, state, blocking = family_status(ledger, decisions.batch_id, family)
        events = ledger.events(decisions.batch_id, family)
        ready = next((event["details"] for event in events if event["kind"] == "transition"
                      and event["name"] == "dossier" and event["revision"] == revision), None)
        if (
            blocking or state not in {"admission_ready", "admitted", "returned"} or not ready
            or ready["family_sha256"] != decision.family_sha256
        ):
            raise ValueError(f"Family {family} requires the exact technically reviewed dossier.")
        dossier = _verify_dossier(ledger, decisions.batch_id, family, revision, decision.family_sha256)
        previous = next((event for event in events if event["kind"] == "human_decision"), None)
        record = {
            "schema_version": 1, "family": family, "split": "development",
            "status": "admitted" if decision.disposition == "accept" else "returned",
            "owner_decision": decision.disposition,
            "signature": {
                "reviewer": decisions.owner, "source": decisions.source, "reviewed_commit": decisions.reviewed_commit,
                "decision_date": decisions.decided_on.isoformat(),
                "recorded_at": previous["details"]["signature"]["recorded_at"] if previous else timestamp(),
                "reviewed_family_sha256": decision.family_sha256,
            },
            "reason": decision.reason, "portfolio_sha256": dossier["portfolio_sha256"],
            "hypothesis": dossier["hypothesis"], "manifest_sha256": dossier["review_files"]["manifest.json"],
            "freeze_sha256": dossier["review_files"]["freeze.json"],
            "review_files": dossier["review_files"] | {"dossier.json": decision.family_sha256},
            "approved_conditions": sorted(dossier["manifest"]["conditions"]) if decision.disposition == "accept" else [],
        }
        directory = ledger.root / "batches" / decisions.batch_id / family / str(revision) / "family"
        rows.append((family, revision, directory / "admission.json", record))
    return rows


def _verify_dossier(ledger: Ledger, batch: str, family: str, revision: int, expected: str) -> dict[str, Any]:
    root = ledger.root / "batches" / batch / family / str(revision) / "family"
    content = artifacts.read_bytes(root / "dossier.json")
    if commissioning.digest(content) != expected:
        raise ValueError(f"Family {family} dossier digest changed after technical recommendation.")
    dossier = commissioning._read_json(content)
    manifest = BatchFamilyManifest.model_validate(dossier["manifest"])
    if review_commitments(root, manifest) != dossier["review_files"]:
        raise ValueError(f"Family {family} reviewed artifact bytes changed.")
    verified = load_family(root / "manifest.json")
    if verified.family != family or verified.manifest_sha256 != dossier["review_files"]["manifest.json"]:
        raise ValueError(f"Family {family} manifest commitment does not match the dossier.")
    if offline_report(root) != dossier["replay"]:
        raise ValueError(f"Family {family} retained replay differs from its reviewed report.")
    return dossier
