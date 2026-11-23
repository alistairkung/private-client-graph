"""Read the immutable milestone repair mandate without changing its spending limits."""

from typing import TYPE_CHECKING

from benchmark_v3.batch.authorisation import commitment
from benchmark_v3.batch.contracts import BatchManifest

if TYPE_CHECKING:
    from benchmark_v3.batch.ledger import Ledger

AMENDMENT = "autonomous_realism_amendment"
REVISION = "autonomous_realism_repair"
STOP = "autonomous_realism_stop"
PLAN_JOB = "repair-plan"
BUDGET_PLAN_JOB = "repair-budget-plan"
PLAN_RECOVERY = "realism_plan_reference_recovery"
CAPACITY_SUCCESSOR = "realism_capacity_successor"
VERIFY_JOB = "repair-verification"
FORMAT_RETRY = "-format-retry"


def enabled(ledger: "Ledger", manifest: BatchManifest) -> bool:
    if manifest.phase != "milestone" or not manifest.repair_cycles:
        return False
    rows = [row for row in ledger.events(manifest.batch_id) if row["kind"] == AMENDMENT]
    if any(row["details"]["manifest_sha256"] != commitment(manifest) for row in rows):
        raise ValueError("The realism amendment differs from the commissioned manifest.")
    return bool(manifest.autonomous_realism or rows)
