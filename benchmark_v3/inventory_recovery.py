"""Preview an inventory-only correction to a pinned design candidate offline."""

import json
import re
from dataclasses import dataclass
from itertools import groupby
from pathlib import Path

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts
from benchmark_v3.batch.contracts import AuthorBrief
from benchmark_v3.design_candidate import CandidateDesign, verify_candidate
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.research_contracts import Contract, Digest, FamilyId, HypothesisRef

_INVENTORY_FAILURE = "Source provenance must form a unique chronological inventory."
_WHITESPACE = re.compile(r"[ \t\r\n]*")


class InventoryRecoveryScope(Contract):
    family_id: FamilyId
    hypothesis: HypothesisRef
    output_sha256: Digest
    receipt_sha256: Digest


@dataclass(frozen=True)
class InventoryPreview:
    before: tuple[str, ...]
    after: tuple[str, ...]
    permutation: tuple[int, ...]
    entry_sha256: dict[str, str]
    reordered_output: bytes
    validation_error: str | None


def preview_inventory_recovery(directory: Path, scope: InventoryRecoveryScope) -> InventoryPreview:
    """Verify the allowlisted parent and dry-run a unique permutation for human review."""
    packet_dir = directory / "packet"
    request = commissioning._read_json(artifacts.read_bytes(packet_dir / "request.json"))
    if request.get("role") != "designer" or request.get("prompt") != "candidate-designer-v1":
        raise ValueError("Inventory recovery requires the design-candidate packet profile.")
    slot = FamilySlot.model_validate_json(request["inputs"]["portfolio_slot"])
    if slot.family_id != scope.family_id or slot.hypothesis != scope.hypothesis:
        raise ValueError("The candidate is outside the pinned recovery scope.")

    output, receipt = artifacts.completed_packet(packet_dir, request)
    if (receipt["output_sha256"] != scope.output_sha256
            or receipt["receipt_sha256"] != scope.receipt_sha256
            or output != artifacts.read_bytes(directory / "original-response.txt")):
        raise ValueError("The original response and receipt must match the recovery scope.")

    failure = commissioning._read_json(artifacts.read_bytes(directory / "validation.json"))
    if failure.get("status") != "design rejected" or failure.get("reason") != _INVENTORY_FAILURE:
        raise ValueError("Recovery requires an original inventory validation failure.")
    design = CandidateDesign.model_validate(commissioning._read_json(output))
    if _validation_error(slot, design) != _INVENTORY_FAILURE:
        raise ValueError("The unchanged validator must reproduce the original failure.")
    if design.sections or design.scaling_snapshots or any(item.order is not None for item in design.matched):
        raise ValueError("Review section, prefix and order controls separately from inventory recovery.")

    before = tuple(item.source_id for item in design.inventory)
    after = _unique_order(design.inventory)
    if before == after:
        raise ValueError("The inventory failure cannot be repaired by reordering.")
    permutation = tuple(before.index(source_id) for source_id in after)
    reordered, entries = _permute_inventory(output, permutation)
    candidate = CandidateDesign.model_validate(commissioning._read_json(reordered))
    expected = design.model_copy(update={"inventory": [design.inventory[i] for i in permutation]})
    if candidate != expected:
        raise ValueError("An inventory permutation must preserve every other design field.")
    return InventoryPreview(
        before=before, after=after, permutation=permutation,
        entry_sha256=dict(zip(before, map(commissioning.digest, entries), strict=True)),
        reordered_output=reordered, validation_error=_validation_error(slot, candidate),
    )


def _validation_error(slot: FamilySlot, design: CandidateDesign) -> str | None:
    try:
        verify_candidate(slot, design)
    except ValueError as error:
        return str(error)
    return None


def _unique_order(inventory: list[AuthorBrief]) -> tuple[str, ...]:
    ids = {item.source_id for item in inventory}
    if len(ids) != len(inventory) or any(len(set(item.received)) != len(item.received) for item in inventory):
        raise ValueError("Source IDs and received dependencies must be unique.")
    ordered = sorted(inventory, key=lambda item: item.created_on)
    seen: set[str] = set()
    result: list[str] = []
    for _, group in groupby(ordered, key=lambda item: item.created_on):
        remaining = list(group)
        while remaining:
            ready = [item for item in remaining if set(item.received) <= seen]
            if not ready:
                raise ValueError("A dependency is missing, cyclic or dated after its recipient.")
            if len(ready) != 1:
                raise ValueError("More than one chronological, dependency-consistent order is possible.")
            item = ready[0]
            result.append(item.source_id)
            seen.add(item.source_id)
            remaining.remove(item)
    return tuple(result)


def _permute_inventory(output: bytes, permutation: tuple[int, ...]) -> tuple[bytes, list[bytes]]:
    # Keep each original JSON entry and all separators verbatim, including
    # whitespace and escapes. Only move the top-level inventory values.
    text = output.decode("utf-8")
    spans = _inventory_spans(text, len(permutation))
    entries = [text[start:end] for start, end in spans]
    parts: list[str] = []
    previous = 0
    for (start, end), index in zip(spans, permutation, strict=True):
        parts.extend((text[previous:start], entries[index]))
        previous = end
    parts.append(text[previous:])
    return "".join(parts).encode(), [entry.encode() for entry in entries]


def _inventory_spans(text: str, count: int) -> list[tuple[int, int]]:
    decoder = json.JSONDecoder()
    position = _space(text, 0) + 1
    while True:
        key, end = decoder.raw_decode(text, _space(text, position))
        value = _space(text, _space(text, end) + 1)
        if key == "inventory":
            break
        _, end = decoder.raw_decode(text, value)
        position = _space(text, end) + 1

    spans = []
    position = value + 1
    for _ in range(count):
        start = _space(text, position)
        _, end = decoder.raw_decode(text, start)
        spans.append((start, end))
        position = _space(text, end) + 1
    return spans


def _space(text: str, position: int) -> int:
    match = _WHITESPACE.match(text, position)
    assert match is not None
    return match.end()
