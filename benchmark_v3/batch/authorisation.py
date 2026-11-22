"""Verify live commissioning inputs against custodian and owner commitments."""

from pathlib import Path
from typing import Any

from benchmark_v3 import commissioning, packet
from benchmark_v3.batch.contracts import BatchDecision, BatchManifest
from benchmark_v3.portfolio import ExistingFamily, Portfolio, PortfolioProposal
from benchmark_v3.replay_manifest import load_family
from benchmark_v3.research_contracts import Contract, HypothesisRef


def commitment(value: Contract) -> str:
    return commissioning.digest(commissioning.json_text(value.model_dump(mode="json")).encode())


def admitted_coverage() -> tuple[str, list[ExistingFamily]]:
    register = commissioning.coverage_register()
    existing = []
    for row in register.families:
        commissioning.verify_coverage_family(row)
        manifest_name = f"family_{row.family_id.lower()}/manifest.json"
        manifest = load_family(commissioning.development_artifact_path(manifest_name))
        existing.append(ExistingFamily(
            family_id=row.family_id, admission_sha256=row.admission_sha256,
            primary_axis=row.primary_axis, secondary_axes=row.secondary_axes,
            conditions=list(manifest.conditions),
        ))
    admissions = commissioning.admitted_family_ids()
    if admissions != {row.family_id for row in existing}:
        raise ValueError("Owner admissions and the coverage register disagree.")
    return commitment(register), existing


def verify_portfolio(portfolio: PortfolioProposal, *, require_current_coverage: bool = True) -> None:
    if require_current_coverage:
        coverage, existing = admitted_coverage()
        if portfolio.coverage_sha256 != coverage or portfolio.existing != existing:
            raise ValueError("The portfolio must bind the current admitted development coverage.")
    history = commissioning.proposal_history()
    taxonomy = {axis.id for axis in commissioning.coverage_register().taxonomy}
    if {axis for gap in portfolio.gaps for axis in gap.axes} - taxonomy:
        raise ValueError("Portfolio gaps must use the registered taxonomy.")
    for slot in portfolio.slots:
        key = f"{slot.hypothesis.hypothesis_id}@{slot.hypothesis.revision}"
        proposal = history.get(key)
        if proposal is None or proposal[1] != slot.hypothesis:
            raise ValueError(f"Family {slot.family_id} has an invalid hypothesis digest.")
        hypothesis = proposal[0]
        if (
            {slot.primary_axis, *slot.secondary_axes} - taxonomy
            or hypothesis.family_id != slot.family_id
            or hypothesis.objective.primary_axis != slot.primary_axis
            or hypothesis.objective.secondary_axes != slot.secondary_axes
            or hypothesis.grounding.retainer != slot.retainer
            or hypothesis.grounding.legal_workflow != slot.workflow
            or hypothesis.feasibility.conditions != 1 + len(slot.matched_conditions)
        ):
            raise ValueError(f"Family {slot.family_id} differs from its hypothesis scope.")


def verify_commission(
    portfolio: Portfolio, manifest: BatchManifest, decision: BatchDecision,
    boundary_evidence: bytes, *, resuming: bool = False,
) -> None:
    plan_digest = commitment(portfolio)
    if (
        manifest.portfolio_sha256 != plan_digest or decision.portfolio.portfolio_sha256 != plan_digest
        or decision.portfolio.status != "approved"
        or decision.manifest_sha256 != commitment(manifest)
        or decision.owner != decision.portfolio.owner
        or decision.owner == portfolio.architect_session
    ):
        raise ValueError("Commissioning requires explicit owner approval of the exact portfolio and budget.")
    previous = manifest.previous_portfolio
    if portfolio.revision == 1 and previous is not None:
        raise ValueError("An initial portfolio has no predecessor.")
    if portfolio.revision > 1 and (
        previous is None or commitment(previous) != portfolio.previous_revision_sha256
        or previous.portfolio_id != portfolio.portfolio_id or previous.revision != portfolio.revision - 1
    ):
        raise ValueError("The portfolio revision does not match its immediate predecessor.")
    verify_portfolio(portfolio, require_current_coverage=not resuming)
    verify_boundary(manifest, boundary_evidence)
    slots = {slot.family_id: slot for slot in portfolio.slots}
    for family in manifest.families:
        slot = slots.get(family.family_id)
        if slot is None or slot.hypothesis != family.hypothesis:
            raise ValueError("The batch must commission exact portfolio hypothesis revisions.")
        minimum = slot.expected_sources + 4 * (1 + len(slot.matched_conditions)) + 2
        if family.sessions < max(slot.estimated_sessions, minimum):
            raise ValueError("The family allocation must cover the planned estimate and mandatory base sessions.")
        verify_hypothesis(family.family_id, family.hypothesis, decision.owner)


def verify_hypothesis(family_id: str, ref: HypothesisRef, owner: str) -> None:
    key = f"{ref.hypothesis_id}@{ref.revision}"
    proposal = commissioning.proposal_history().get(key)
    if (proposal is None or proposal[1] != ref or proposal[0].family_id != family_id
            or proposal[2] is None or proposal[2].status != "approved" or proposal[2].owner != owner):
        raise ValueError(f"Family {family_id} requires the owner's exact hypothesis approval.")


def verify_boundary(manifest: BatchManifest, evidence: bytes) -> None:
    scope = manifest.scope
    if scope.packet_implementation_sha256 != commissioning.digest(Path(packet.__file__).read_bytes()):
        raise ValueError("The approved packet isolation implementation has changed.")
    if scope.os_boundary_evidence_sha256 != commissioning.digest(evidence):
        raise ValueError("The approved isolation evidence digest does not match.")
    probe = commissioning._read_json(evidence)
    checks: dict[str, dict[str, Any]] = {
        "inside": {"returncode": 0, "denied": False, "matched_inside_count": True},
        "outside": {"denied": True, "matched_inside_count": False},
        "repository": {"denied": True, "matched_inside_count": False},
    }
    if not isinstance(probe, dict) or any(
        not isinstance(probe.get(name), dict) or any(probe[name].get(key) != value for key, value in expected.items())
        for name, expected in checks.items()
    ):
        raise ValueError("The scope requires successful inside, outside and repository boundary checks.")
