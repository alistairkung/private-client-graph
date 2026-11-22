"""Bind a batch-wide human design review to the original committed designs."""

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation
from benchmark_v3.batch.contracts import BatchManifest, DesignCommitment, DesignReview
from benchmark_v3.batch.ledger import Ledger


def committed_designs(ledger: Ledger, manifest: BatchManifest) -> list[DesignCommitment]:
    if not manifest.requires_design_review:
        raise ValueError("This batch does not require a design review.")
    return [
        _committed_design(ledger, manifest.batch_id, family.family_id)
        for family in manifest.families
    ]


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
        raise ValueError("Design review must accept every exact committed design.")


def _committed_design(ledger: Ledger, batch_id: str, family: str) -> DesignCommitment:
    commitment = next((
        row["details"]["outputs"]["design"]
        for row in ledger.events(batch_id, family)
        if row["revision"] == 1 and row["kind"] == "transition" and row["name"] == "design"
    ), None)
    if commitment is None:
        raise ValueError(f"Family {family} has no committed design for review.")
    content = artifacts.read_bytes(ledger.root / "batches" / batch_id / family / "1" / "design.json")
    if not content.endswith(b"\n") or commissioning.digest(content[:-1]) != commitment:
        raise ValueError(f"Family {family} committed design bytes changed.")
    return DesignCommitment(family_id=family, design_sha256=commitment)
