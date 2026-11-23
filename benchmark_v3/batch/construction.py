"""Read a design and lineage bound by the owner's construction manifest."""

from pathlib import Path

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts
from benchmark_v3.batch.contracts import BatchManifest, FamilyAllocation
from benchmark_v3.design_candidate import CandidateDesign, verify_candidate
from benchmark_v3.portfolio import Portfolio


def load_design(root: Path, batch_id: str, allocation: FamilyAllocation) -> CandidateDesign:
    approved = allocation.approved_design
    if approved is None:
        raise ValueError("The family has no approved construction design.")
    directory = root / "approved-designs" / batch_id / allocation.family_id
    design = artifacts.read_bytes(directory / "design.json")
    lineage = artifacts.read_bytes(directory / "revision.json")
    if (commissioning.digest(design) != approved.design_sha256
            or commissioning.digest(lineage) != approved.lineage_sha256):
        raise ValueError("Construction design and lineage must match their approved digests.")
    candidate = CandidateDesign.model_validate(commissioning._read_json(design))
    if commissioning.json_text(candidate.model_dump(mode="json")).encode() != design:
        raise ValueError("Construction design must use canonical bytes.")
    record = commissioning._read_json(lineage)
    if (record["family"] != allocation.family_id
            or record["hypothesis"] != allocation.hypothesis.model_dump(mode="json")
            or record["child_design_sha256"] != approved.design_sha256):
        raise ValueError("Construction lineage does not bind this family, design and hypothesis.")
    return candidate


def verify_designs(root: Path, manifest: BatchManifest, portfolio: Portfolio) -> None:
    if manifest.phase != "construction":
        return
    slots = {slot.family_id: slot for slot in portfolio.slots}
    for allocation in manifest.families:
        design = load_design(root, manifest.batch_id, allocation)
        verify_candidate(slots[allocation.family_id], design)
        minimum = len(design.inventory) + (4 + 2 * len(design.sections)) * len(design.required) + 1
        assert allocation.approved_design is not None
        if allocation.sessions < minimum + allocation.approved_design.planned_masks:
            raise ValueError("Construction allowance cannot cover planned independent reviews and masks.")
