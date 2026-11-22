"""Commission, resume and review a local Benchmark v3 development batch."""

import argparse
import json
from pathlib import Path

from benchmark_v3.batch import admission, artifacts, authorisation, coordinator, freeze
from benchmark_v3.batch.contracts import (
    AdmissionDecisions, BatchDecision, BatchManifest, DesignReview, PilotDecision, SourceCutoffRecovery,
)
from benchmark_v3.portfolio import Portfolio
from benchmark_v3.research_contracts import Contract


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("schema").add_argument(
        "contract", choices=(
            "portfolio", "manifest", "approval", "design-review", "source-cutoff-recovery",
            "pilot", "admissions", "freeze",
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
        if name in {"reconcile", "quarantine"}:
            command.add_argument("family")
            command.add_argument("reference")
    for name in ("recover-source-cutoffs", "review-designs", "pilot-review", "admit", "freeze"):
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
            coordinator.run_batch(ledger, args.batch)
        case "designs":
            print(json.dumps(coordinator.preview_design_review(ledger, args.batch), indent=2))
        case "recover-source-cutoffs":
            recovery = artifacts.read_contract(args.decisions.absolute(), SourceCutoffRecovery)
            coordinator.recover_source_cutoffs(ledger, recovery)
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
