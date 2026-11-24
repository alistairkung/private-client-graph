"""Commission, resume and review a local Benchmark v3 development batch."""

import argparse
import json
from pathlib import Path

from benchmark_v3.batch import admission, artifacts, authorisation, coordinator, freeze
from benchmark_v3.batch.contracts import (
    AdjudicationQuoteRecovery, AdmissionDecisions, AnnotationRecovery, AuditRecovery, BatchDecision, BatchManifest, BudgetAmendment, DeferredExceptionReview,
    DesignReview, FamilyContinuation, MilestoneEvidenceRepair, MilestoneRealismRepair,
    PilotDecision, SourceCutoffRecovery,
)
from benchmark_v3.portfolio import Portfolio
from benchmark_v3.research_contracts import Contract


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("schema").add_argument(
        "contract", choices=(
            "portfolio", "manifest", "approval", "design-review", "source-cutoff-recovery",
            "annotation-recovery", "adjudication-quote-recovery", "audit-recovery", "deferred-exception-review", "budget-amendment", "family-continuation", "milestone-realism-repair", "milestone-evidence-repair", "pilot", "admissions", "freeze",
        ),
    )
    commands.add_parser("coverage")
    digest = commands.add_parser("digest")
    digest.add_argument("contract", choices=("portfolio", "manifest"))
    digest.add_argument("file", type=Path)
    commission = commands.add_parser("commission")
    commission.add_argument("custody", type=Path)
    for name in ("portfolio", "manifest", "approval", "boundary"):
        commission.add_argument(name, type=Path)
    for name in ("run", "designs", "package", "reconcile", "quarantine", "freeze-preview"):
        command = commands.add_parser(name)
        command.add_argument("custody", type=Path)
        command.add_argument("batch")
        if name == "run":
            command.add_argument("--family")
            command.add_argument("--realism-amendment-reference")
            command.add_argument("--stop-after", choices=("audit", "masks"))
        if name in {"reconcile", "quarantine"}:
            command.add_argument("family")
            command.add_argument("reference")
    for name in ("recover-source-cutoffs", "recover-annotation", "recover-adjudication-quote", "release-audit", "record-deferred-review",
                 "release-milestone-realism-repair", "release-milestone-evidence-repair", "review-designs", "amend-budget", "continue-family",
                 "pilot-review", "admit", "freeze"):
        command = commands.add_parser(name)
        command.add_argument("custody", type=Path)
        command.add_argument("decisions", type=Path)
    args = parser.parse_args()
    try:
        _execute(args)
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f"Batch command rejected: {error}\n")


def _execute(args: argparse.Namespace) -> None:
    contracts: dict[str, type[Contract]] = {
        "portfolio": Portfolio, "manifest": BatchManifest, "approval": BatchDecision,
        "design-review": DesignReview, "source-cutoff-recovery": SourceCutoffRecovery,
        "adjudication-quote-recovery": AdjudicationQuoteRecovery,
        "audit-recovery": AuditRecovery,
        "annotation-recovery": AnnotationRecovery, "deferred-exception-review": DeferredExceptionReview,
        "budget-amendment": BudgetAmendment, "family-continuation": FamilyContinuation,
        "milestone-realism-repair": MilestoneRealismRepair,
        "milestone-evidence-repair": MilestoneEvidenceRepair,
        "pilot": PilotDecision, "admissions": AdmissionDecisions, "freeze": freeze.FreezeDecision,
    }
    if args.command == "schema":
        print(json.dumps(contracts[args.contract].model_json_schema(), indent=2))
        return
    if args.command == "coverage":
        digest, coverage = authorisation.admitted_coverage()
        print(json.dumps({"coverage_sha256": digest, "existing": [row.model_dump() for row in coverage]}, indent=2))
        return
    if args.command == "digest":
        print(authorisation.commitment(artifacts.read_contract(args.file.absolute(), contracts[args.contract])))
        return
    ledger = coordinator.open_ledger(args.custody)
    match args.command:
        case "commission":
            commission = coordinator.Commission(
                artifacts.read_contract(args.portfolio.absolute(), Portfolio),
                artifacts.read_contract(args.manifest.absolute(), BatchManifest),
                artifacts.read_contract(args.approval.absolute(), BatchDecision),
            )
            coordinator.commission_batch(ledger, commission, artifacts.read_bytes(args.boundary.absolute()))
        case "run":
            coordinator.run_batch(
                ledger, args.batch, family_id=args.family, stop_after=args.stop_after,
                realism_amendment_reference=args.realism_amendment_reference,
            )
        case "designs":
            print(json.dumps(coordinator.preview_design_review(ledger, args.batch), indent=2))
        case "recover-source-cutoffs":
            recovery = artifacts.read_contract(args.decisions.absolute(), SourceCutoffRecovery)
            coordinator.recover_source_cutoffs(ledger, recovery)
        case "recover-annotation":
            annotation = artifacts.read_contract(args.decisions.absolute(), AnnotationRecovery)
            print(coordinator.recover_annotation(ledger, annotation))
        case "recover-adjudication-quote":
            quote = artifacts.read_contract(args.decisions.absolute(), AdjudicationQuoteRecovery)
            print(coordinator.recover_adjudication_quote(ledger, quote))
        case "release-audit":
            audit = artifacts.read_contract(args.decisions.absolute(), AuditRecovery)
            print(coordinator.release_audit(ledger, audit))
        case "record-deferred-review":
            deferred = artifacts.read_contract(args.decisions.absolute(), DeferredExceptionReview)
            coordinator.record_deferred_review(ledger, deferred)
        case "amend-budget":
            amendment = artifacts.read_contract(args.decisions.absolute(), BudgetAmendment)
            print(coordinator.apply_budget_amendment(ledger, amendment))
        case "continue-family":
            release = artifacts.read_contract(args.decisions.absolute(), FamilyContinuation)
            coordinator.continue_family(ledger, release)
        case "review-designs":
            review = artifacts.read_contract(args.decisions.absolute(), DesignReview)
            coordinator.record_design_review(ledger, review)
        case "package":
            path, digest = admission.package_batch(ledger, args.batch)
            print(f"{path}\n{digest}")
        case "reconcile":
            coordinator.reconcile_dispatch(ledger, args.batch, args.family, args.reference)
        case "quarantine":
            coordinator.quarantine(ledger, args.batch, args.family, args.reference)
        case "release-milestone-realism-repair":
            plan = artifacts.read_contract(args.decisions.absolute(), MilestoneRealismRepair)
            print(coordinator.release_milestone_realism_repair(ledger, plan))
        case "release-milestone-evidence-repair":
            evidence_plan = artifacts.read_contract(args.decisions.absolute(), MilestoneEvidenceRepair)
            print(coordinator.release_milestone_evidence_repair(ledger, evidence_plan))
        case "pilot-review":
            decision = artifacts.read_contract(args.decisions.absolute(), PilotDecision)
            admission.record_pilot_review(ledger, decision)
        case "freeze-preview":
            path, digest = freeze.preview(ledger, args.batch)
            print(f"{path}\n{digest}")
        case "freeze":
            final_decision = artifacts.read_contract(args.decisions.absolute(), freeze.FreezeDecision)
            print(freeze.record(ledger, final_decision))
        case "admit":
            decisions = artifacts.read_contract(args.decisions.absolute(), AdmissionDecisions)
            for path in admission.record_admissions(ledger, decisions):
                print(path)


if __name__ == "__main__":
    main()
