"""Reopen a failed hypothesis using a fresh documentary lineage."""

from pathlib import Path

from pydantic import Field

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation
from benchmark_v3.batch.contracts import DesignOutput, MilestoneAudit
from benchmark_v3.batch.repair_authority import REVISION
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.research_contracts import Contract, Digest, Text


MERITS_JOB = "clean-design-merits"


class AuditedReplacement(Contract):
    audit_receipt_sha256: Digest
    independent_assessment_sha256: Digest


class CleanRedesign(Contract):
    parent_revision: int
    manifest_sha256: Digest
    parent_design_sha256: Digest | None
    reason: Text
    audited_replacement: AuditedReplacement | None = Field(default=None, exclude_if=lambda value: value is None)
    retained_design_revision: int | None = Field(default=None, exclude_if=lambda value: value is None)


def details(
    runner: SessionRunner, prior: int, reason: str, audit: AuditedReplacement | None = None,
    *, retained_design_revision: int | None = None,
) -> CleanRedesign:
    design = _prior_design(runner, prior, retained_design_revision)
    return CleanRedesign(
        parent_revision=prior, manifest_sha256=authorisation.commitment(runner.manifest),
        parent_design_sha256=_design_digest(design), reason=reason, audited_replacement=audit,
        retained_design_revision=retained_design_revision,
    )


def recorded(runner: SessionRunner) -> CleanRedesign | None:
    batch, family = runner.manifest.batch_id, runner.family
    event = next((row for row in runner.ledger.events(batch, family) if row["kind"] == "reconcile"
                  and row["revision"] == runner.revision and row["name"].startswith("pooled-release")
                  and "documentary_redesign" in row["details"]), None)
    if event is None:
        return None
    prior = runner.revision - 1
    record = CleanRedesign.model_validate(event["details"]["documentary_redesign"])
    if (not runner.ledger.requires_delivery_attestation or prior < 1
            or record != details(runner, prior, record.reason, record.audited_replacement,
                                 retained_design_revision=record.retained_design_revision)
            or event["details"]["parent_sha256"] != authorisation.commitment(record)
            or not runner.ledger.historical_pooled_revision(batch, family, runner.revision)):
        raise ValueError("Fresh documentary design requires the exact reviewed replacement lineage.")
    if record.audited_replacement is not None:
        if reviewed_audit_receipt(runner, prior) != record.audited_replacement.audit_receipt_sha256:
            raise ValueError("The frozen scientific return differs from the replacement commitment.")
    return record


def reviewed_audit_receipt(runner: SessionRunner, revision: int) -> str:
    prior = SessionRunner(runner.ledger, runner.manifest, runner.family, revision,
                          runner.directory.with_name(str(revision)), runner.owner)
    review, receipt, _ = prior.committed_result("audit", "audit", "audit", MilestoneAudit)
    if review.verdict != "return" or not review.objections or not (prior.directory / "family" / "freeze.json").is_file():
        raise ValueError("An audited replacement requires a frozen file and an independent scientific return.")
    return str(receipt["receipt_sha256"])


def require_merits(runner: SessionRunner) -> None:
    from benchmark_v3.batch.author_context import AuthorContextReview

    review, _, request = runner.committed_result("author", MERITS_JOB, "audit", AuthorContextReview)
    design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
    supplied = DesignOutput.model_validate_json(request["inputs"]["intended_intervention"])
    if (review.verdict != "accept" or review.objections or supplied != design
            or review.findings.keys() != {row.source_id for row in design.inventory}):
        raise ValueError("The large-file replacement requires independent merits approval of this exact design.")


def fresh_slot(slot: FamilySlot, record: CleanRedesign) -> FamilySlot:
    return slot.model_copy(update={"independent_authoring": [
        *slot.independent_authoring,
        "Design a genuinely fresh fictional file with distinct named participants and a new chronology. "
        "Address the prior documentary or evidence topology failure while preserving the exact commissioned "
        "hypothesis, workload, matched contrast and scientific intent. All authors and dependent reviews are fresh.",
        f"Scope of the retained failure for this new design: {record.reason}",
    ]})


def verify_distinct(runner: SessionRunner, design: DesignOutput, record: CleanRedesign) -> None:
    if record.parent_design_sha256 is None:
        return
    path = _prior_design(runner, record.parent_revision, record.retained_design_revision)
    if _design_digest(path) != record.parent_design_sha256:
        raise ValueError("The replacement's distinctness reference differs from its commitment.")
    parent = artifacts.read_contract(path, DesignOutput)
    current_names = {name.casefold() for left, _, right in design.candidates for name in (left, right)}
    previous_names = {name.casefold() for left, _, right in parent.candidates for name in (left, right)}
    if current_names & previous_names or design.neutral_brief == parent.neutral_brief or design.cutoff == parent.cutoff:
        raise ValueError("A replacement requires a distinct documentary history and scored endpoint names.")
    if record.audited_replacement is not None or runner.ledger.requires_workload_merits:
        prior_ids = {row.source_id for row in parent.inventory}
        if prior_ids.intersection(row.source_id for row in design.inventory):
            raise ValueError("An independent replacement at this scale requires fresh Source identities.")


def _design_digest(path: Path) -> str | None:
    return commissioning.digest(artifacts.read_bytes(path)) if path.exists() else None


def _prior_design(runner: SessionRunner, prior: int, retained: int | None) -> Path:
    path = runner.directory.parent / str(prior) / "design.json"
    if retained is None:
        return path
    batch, family = runner.manifest.batch_id, runner.family
    release = next((row["details"] for row in runner.ledger.events(batch, family)
                    if (row["revision"], row["kind"], row["name"]) == (prior, "transition", REVISION)), None)
    anchor = runner.directory.parent / str(retained) / "design.json"
    if (not runner.ledger.requires_workload_merits or not 0 < retained < prior or path.exists()
            or release is None or release.get("parent_revision") != retained or not anchor.is_file()
            or any(row["revision"] == prior for row in runner.ledger.attempts(family))):
        raise ValueError("A skipped unstarted repair must retain its exact reviewed predecessor design.")
    return anchor
