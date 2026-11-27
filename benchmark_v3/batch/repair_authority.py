"""Read the immutable milestone repair mandate without changing its spending limits."""

from typing import TYPE_CHECKING, Any

from benchmark_v3.batch.authorisation import commitment
from benchmark_v3.batch.contracts import BatchManifest

if TYPE_CHECKING:
    from benchmark_v3.batch.ledger import Ledger
    from benchmark_v3.batch.sessions import SessionRunner

AMENDMENT = "autonomous_realism_amendment"
REVISION = "autonomous_realism_repair"
STOP = "autonomous_realism_stop"
PLAN_JOB = "repair-plan"
EXACT_PLAN_JOB = "repair-plan-exact-classification"
LOCAL_PLAN_JOB = "repair-plan-local-records"
BUDGET_PLAN_JOB = "repair-budget-plan"
PLAN_RECOVERY = "realism_plan_reference_recovery"
LOCAL_PLAN_RECOVERY = "realism_local_plan_recovery"
RETAINED_DESIGN_NOTE = "realism-retained-design-review-note"
LEGACY_REVISED_ATTACHMENTS = "Rewrite this record using the revised received correspondence."
LEGACY_REVISED_INSTRUCTIONS = "Write this record using its revised instructions."
LEGACY_REVISED_CONTEXT = "Write this record using its revised instructions and received correspondence."
CAPACITY_SUCCESSOR = "realism_capacity_successor"
VERIFY_JOB = "repair-verification"
SCOPE_REVIEW_RETRY = "scope-review-representation"
VERIFY_RETRY_INSTRUCTIONS = (
    " Independently classify every remaining objection to preserving the scope, provenance or contrast. "
    "Use changed when there is a material objection. With preserved, put nonblocking documentary observations "
    "in scope, provenance or contrast, and return an empty objections array."
)
FORMAT_RETRY = "-format-retry"


def enabled(ledger: "Ledger", manifest: BatchManifest) -> bool:
    if manifest.phase != "milestone" or not manifest.repair_cycles:
        return False
    rows = [row for row in ledger.events(manifest.batch_id) if row["kind"] == AMENDMENT]
    if any(row["details"]["manifest_sha256"] != commitment(manifest) for row in rows):
        raise ValueError("The realism amendment differs from the commissioned manifest.")
    return bool(manifest.autonomous_realism or rows)


def recorded_classification_retry(runner: "SessionRunner") -> dict[str, Any] | None:
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    return next((row["details"]["exact_classification"] for row in events
                 if (row["revision"], row["kind"], row["name"]) == (runner.revision, "reconcile", PLAN_RECOVERY)
                 and "exact_classification" in row["details"]), None)


def recorded_local_retry(runner: "SessionRunner") -> dict[str, Any] | None:
    return next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if (row["revision"], row["kind"], row["name"]) == (runner.revision, "reconcile", LOCAL_PLAN_RECOVERY)), None)
