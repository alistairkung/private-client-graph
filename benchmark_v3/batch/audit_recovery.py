"""Bind a single fresh audit to the retained exception and a bounded mask plan."""

from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import adjudication_recovery, artifacts, authorisation, continuation
from benchmark_v3.batch.contracts import AuditMaskView, AuditRecovery, RecoveredAuditReview
from benchmark_v3.replay_manifest import BatchSourceFreeze

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner

JOB = "audit-recovery"
FAILURE = "Audit must review sufficiency for each critical edge."
INSTRUCTIONS = (
    " The audit rules include the proposed exact Source views. Independently determine whether they suffice "
    "and derive their expected observations. Keep each cited removal and Source selection exact if you accept. "
    "Assess the proposed combined cut-off view against the appointment and designation evidence separately. "
    "Explain the missing fact and remaining alternative evidence for each dependency and whether the other "
    "views distinguish those explanations. If distinct deletion views or additional investigations are needed, "
    "return with objections rather than consolidating them to fit a limit."
)
MASK_INSTRUCTIONS = (
    " For apparent but unresolved legal relationships, record which facts or authority the supplied evidence "
    "does not establish, explaining which surviving passages make the issue relevant. Do not infer the "
    "contents of any unavailable material."
)


def recorded(runner: "SessionRunner") -> AuditRecovery | None:
    return next((AuditRecovery.model_validate(row["details"])
                 for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if row["revision"] == runner.revision and row["kind"] == "reconcile" and row["name"] == JOB), None)


def verify_authority(runner: "SessionRunner", decision: AuditRecovery) -> None:
    budget = continuation.recorded_budget(runner.ledger.events(runner.manifest.batch_id),
                                          expected_sha256=decision.budget_amendment_sha256)
    if (decision.owner != runner.owner or decision.family_id != runner.family
            or decision.batch_id != runner.manifest.batch_id or budget is None
            or decision.manifest_sha256 != authorisation.commitment(runner.manifest)):
        raise ValueError("Fresh audit requires the exact owner, family, manifest and budget amendment.")
    _, receipt, _ = runner.committed_packet("audit", "audit", "audit")
    if (receipt["output_sha256"], receipt["receipt_sha256"]) != (decision.output_sha256, decision.receipt_sha256):
        raise ValueError("Fresh audit must bind the retained audit output and receipt.")
    recovery = adjudication_recovery.recorded(runner)
    if recovery is None or recovery["derivative_sha256"] != decision.adjudication_derivative_sha256:
        raise ValueError("Fresh audit requires the exact validated adjudication derivative.")
    freeze = artifacts.read_bytes(runner.directory / "family" / "freeze.json")
    if commissioning.digest(freeze) != decision.freeze_sha256:
        raise ValueError("Fresh audit requires the exact Source freeze.")
    recorded_freeze = BatchSourceFreeze.model_validate_json(freeze)
    views = {_view_key(view) for view in decision.views}
    combined = decision.combined_cutoff_view
    if (len(views) != len(decision.views) or _view_key(combined) not in views
            or combined.risk != "joint_proof" or not combined.remove_quotes
            or {view.condition for view in decision.views} != {recorded_freeze.natural}
            or recorded_freeze.variants):
        raise ValueError("Fresh audit requires distinct natural-condition views and a combined joint-proof deletion.")


def rules(decision: AuditRecovery) -> dict[str, Any]:
    return {
        "proposed_exact_views": [_projection(view) for view in decision.views],
        "combined_cutoff_view": decision.combined_cutoff_view.model_dump(mode="json"),
    }


def verify_plan(review: RecoveredAuditReview, decision: AuditRecovery) -> None:
    if review.cutoff_assessment.decision != "justified":
        raise ValueError("Independent audit requires separate cut-off checks. Mask dispatch is held.")
    actual = {_view_key(AuditMaskView.model_validate(mask.model_dump(include=set(AuditMaskView.model_fields)))): mask
              for mask in review.masks}
    if len(review.masks) != len(decision.views) or actual.keys() != {_view_key(view) for view in decision.views}:
        raise ValueError("Independent audit requires a different mask plan. Mask dispatch is held.")
    for view in decision.views:
        mask = actual[_view_key(view)]
        if not set(view.present) <= set(mask.present) or not set(view.absent) <= set(mask.absent):
            raise ValueError("Independent audit did not retain a mandatory mask observation. Mask dispatch is held.")


def _projection(view: AuditMaskView) -> dict[str, Any]:
    return view.model_dump(mode="json", include=set(AuditMaskView.model_fields))


def _view_key(view: AuditMaskView) -> str:
    return commissioning.json_text(_projection(view) | {"included": sorted(view.included)})
