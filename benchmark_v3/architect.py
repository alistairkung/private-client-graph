"""Read completed Research Architect packets and render the coverage register."""

import argparse
import json
import stat
from pathlib import Path
from typing import Any

from benchmark_v3 import commissioning
from benchmark_v3.coverage import render_coverage
from benchmark_v3.portfolio import Portfolio, PortfolioProposal
from benchmark_v3.research_contracts import (
    PlanningRecord,
    PlanningResult,
    ReconciliationContext,
    ReconciliationRecord,
    SessionProvenance,
)


def read_architect_packet(directory: Path, profile: str) -> PlanningRecord | ReconciliationRecord | Portfolio:
    """Read a completed packet without writing decisions or admitting a family."""
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("Use the original architect packet directory.")
    handoff_bytes = _packet_bytes(directory / "handoff.json")
    handoff = json.loads(handoff_bytes)
    receipt = json.loads(_packet_bytes(directory / "receipt.json"))
    output = _packet_bytes(directory / "output.txt")
    provenance = _verify_receipt(handoff, receipt, output)
    metadata = handoff["research"]
    if metadata["profile"] != profile:
        raise ValueError(f"Expected an architect {profile} packet.")
    if profile in {"portfolio", "reconciliation"} and receipt.get("handoff_sha256") != commissioning.digest(
        handoff_bytes,
    ):
        raise ValueError(f"The {profile} handoff digest does not match its receipt.")
    result = commissioning.validate_architect_result(output.decode("utf-8"), metadata)
    if isinstance(result, PortfolioProposal):
        return Portfolio(**result.model_dump(), architect_session=provenance.session)
    if isinstance(result, PlanningResult):
        return PlanningRecord(schema_version=1, provenance=provenance, result=result)
    return ReconciliationRecord(
        schema_version=1,
        provenance=provenance,
        context=ReconciliationContext.model_validate(metadata["admission"]),
        result=result,
    )


def _packet_bytes(path: Path) -> bytes:
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("The packet handoff, output and receipt must be regular files.")
    return path.read_bytes()


def _verify_receipt(
    handoff: dict[str, Any], receipt: dict[str, Any], output: bytes,
) -> SessionProvenance:
    output_sha256 = commissioning.digest(output)
    if (
        handoff["role"] != "research_architect" or receipt["status"] != "completed"
        or receipt["session"] != handoff["session"]
        or receipt["packet_sha256"] != handoff["packet_sha256"]
        or receipt["output"] != {"bytes": len(output), "sha256": output_sha256}
        or receipt["observed_tool_actions"] != []
    ):
        raise ValueError("The Research Architect packet requires a matching completed receipt.")
    isolation = receipt["isolation"]
    if (
        isolation["model"] != handoff["model_requested"]
        or isolation["effort"] != handoff["effort_requested"]
        or isolation["permission_profile"] != {"id": "benchmark_packet", "extends": None}
        or isolation["approval_policy"] != "never"
        or isolation["ephemeral"] is not True
        or isolation["empty_workspace"] is not True
        or isolation["sandbox"] != {"type": "readOnly", "networkAccess": False}
        or isolation["instruction_sources"] != []
        or isolation["thread_environments"] != []
        or isolation["runtime_workspace_roots"] != []
    ):
        raise ValueError("The Research Architect receipt lacks the expected isolation evidence.")
    return SessionProvenance(
        session=handoff["session"],
        packet_sha256=handoff["packet_sha256"],
        prompt_sha256=handoff["prompt"]["sha256"],
        output_sha256=output_sha256,
        model=isolation["model"],
        effort=isolation["effort"],
        completed_at=receipt["completed_at"],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("coverage", help="Render the canonical qualitative register as Markdown.")
    for name in ("proposals", "portfolio", "reconcile"):
        commands.add_parser(name, help="Verify and print a completed architect packet.").add_argument(
            "packet_dir", type=Path,
        )
    args = parser.parse_args()
    try:
        if args.command == "coverage":
            print(render_coverage(), end="")
            return
        profile = {"proposals": "planning", "portfolio": "portfolio", "reconcile": "reconciliation"}[args.command]
        record = read_architect_packet(args.packet_dir, profile)
        print(record.model_dump_json(indent=2))
    except (ValueError, KeyError, TypeError, OSError) as error:
        parser.exit(1, f"Architect record rejected: {error}\n")


if __name__ == "__main__":
    main()
