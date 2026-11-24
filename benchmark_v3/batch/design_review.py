"""Bind a batch-wide design review to the original committed designs."""

from typing import TYPE_CHECKING, Any

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation
from benchmark_v3.batch.contracts import (
    BatchManifest, DesignCommitment, DesignNameCorrection, DesignOutput, DesignReview,
)
from benchmark_v3.batch.ledger import Ledger

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner


def committed_designs(ledger: Ledger, manifest: BatchManifest) -> list[DesignCommitment]:
    if not manifest.requires_design_review:
        raise ValueError("This batch does not require a design review.")
    commitments = []
    for allocation in manifest.families:
        family = allocation.family_id
        records = ledger.events(manifest.batch_id, family)
        try:
            commitments.append(_committed_design(ledger, manifest.batch_id, family))
        except _DesignNotCommitted:
            if manifest.phase != "milestone" or not _design_halted(records):
                raise
    return commitments


class _DesignNotCommitted(ValueError):
    pass


def _design_halted(records: list[dict[str, Any]]) -> bool:
    latest = next((row for row in reversed(records)
                   if row["kind"] in {"exception", "task_halt", "reconcile"}), None)
    return latest is not None and (
        latest["kind"], latest["details"].get("stage"), latest["details"].get("remaining_work")
    ) == ("exception", "design", "family_halted")


def recorded_review(ledger: Ledger, manifest: BatchManifest, owner: str) -> DesignReview | None:
    if not manifest.requires_design_review:
        return None
    for event in ledger.events(manifest.batch_id):
        if event["kind"] == "design_review":
            review = DesignReview.model_validate(event["details"])
            verify_review(ledger, manifest, owner, review)
            return review
    return None


def verify_review(ledger: Ledger, manifest: BatchManifest, owner: str, review: DesignReview) -> None:
    if (
        review.batch_id != manifest.batch_id or review.owner != owner
        or review.manifest_sha256 != authorisation.commitment(manifest)
    ):
        raise ValueError("Design review requires the commissioning owner and exact manifest.")
    expected = {design.family_id: design.design_sha256 for design in committed_designs(ledger, manifest)}
    if {design.family_id: design.design_sha256 for design in review.designs} != expected:
        raise ValueError("Design review must cover every exact committed design.")
    for disposition in review.designs:
        if disposition.name_correction is None:
            continue
        if manifest.phase != "milestone":
            raise ValueError("Documentary name corrections require the milestone design checkpoint.")
        directory = ledger.root / "batches" / manifest.batch_id / disposition.family_id / "1"
        design = artifacts.read_contract(directory / "design.json", DesignOutput)
        apply_name_correction(design, disposition.name_correction)


def apply_name_correction(design: DesignOutput, correction: DesignNameCorrection) -> DesignOutput:
    previous, replacement = correction.before, correction.after
    matching = [brief for brief in design.inventory if brief.source_id == correction.source_id]
    if (len(matching) != 1 or matching[0].author.count(previous) != 1
            or design.private_history.count(previous) != 1 or replacement in design.model_dump_json()
            or design.model_dump_json().count(previous) != 2):
        raise ValueError("The correction must affect only one documentary author and their private history.")
    author = matching[0].model_copy(update={"author": matching[0].author.replace(previous, replacement)})
    derived = DesignOutput.model_validate(design.model_dump(mode="json") | {
        "inventory": [
            (author if brief.source_id == correction.source_id else brief).model_dump(mode="json")
            for brief in design.inventory
        ],
        "private_history": design.private_history.replace(previous, replacement),
    })
    if authorisation.commitment(derived) != correction.revised_design_sha256:
        raise ValueError("The name-corrected design differs from the approved derivative.")
    return derived


def verified_authoring_design(
    runner: "SessionRunner", design: DesignOutput, expected: str,
) -> DesignOutput:
    review = recorded_review(runner.ledger, runner.manifest, runner.owner)
    correction = next((row.name_correction for row in review.designs
                       if row.family_id == runner.family), None) if review else None
    if correction is None:
        raise ValueError("The parent authoring commitment lacks its approved documentary correction.")
    content = artifacts.read_bytes(runner.directory / "reviewed-design.json")
    revised = apply_name_correction(design, correction)
    if commissioning.digest(content) != expected or revised != DesignOutput.model_validate_json(content):
        raise ValueError("The prior documentary design derivative changed.")
    return revised


def _committed_design(ledger: Ledger, batch_id: str, family: str) -> DesignCommitment:
    commitment = next((
        row["details"]["outputs"]["design"]
        for row in ledger.events(batch_id, family)
        if row["revision"] == 1 and row["kind"] == "transition" and row["name"] == "design"
    ), None)
    if commitment is None:
        raise _DesignNotCommitted(f"Family {family} has no committed design for review.")
    content = artifacts.read_bytes(ledger.root / "batches" / batch_id / family / "1" / "design.json")
    if not content.endswith(b"\n") or commissioning.digest(content[:-1]) != commitment:
        raise ValueError(f"Family {family} committed design bytes changed.")
    return DesignCommitment(family_id=family, design_sha256=commitment)
