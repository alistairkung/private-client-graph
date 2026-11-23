"""Deterministic checks around independently produced scientific judgements."""

from typing import Any

from benchmark_v3.batch.contracts import Adjudication, AuditReview, DesignOutput, MaskAssignment, Reading, Risk
from benchmark_v3.commissioning import json_text
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.replay_evidence import assess_evidence
from benchmark_v3.replay_manifest import BatchSourceFreeze, SufficientEvidence, source_commitments, truth_edges
from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.evaluation import _edge, evaluate_graph
from private_client_graph.graph import build_canonical_state
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.source import Source
from private_client_graph.research.retained_inputs import value_digest


def condition_ids(slot: FamilySlot) -> list[str]:
    return [f"{slot.family_id}{index:03}" for index in range(1 + len(slot.matched_conditions))]


def verify_design(slot: FamilySlot, design: DesignOutput) -> None:
    if len(design.inventory) != slot.expected_sources or len(design.matched) != len(slot.matched_conditions):
        raise ValueError("Design inventory or condition count differs from the approved portfolio.")
    seen: set[str] = set()
    previous = None
    for item in design.inventory:
        if (
            item.source_id in seen or not set(item.received) <= seen
            or len(item.received) != len(set(item.received)) or item.created_on > design.cutoff
            or (previous is not None and previous > item.created_on)
        ):
            raise ValueError("Source provenance must form a unique chronological inventory.")
        previous = item.created_on
        seen.add(item.source_id)
    sections = [source_id for section in design.sections.values() for source_id in section]
    if any(not section for section in design.sections.values()) or (
        sections and (set(sections) != seen or len(sections) != len(seen))
    ):
        raise ValueError("Sections must partition the complete Source inventory once each.")
    if slot.tier == "giant" and not sections:
        raise ValueError("The giant Matter requires section assignments and whole-file reconciliation.")
    if design.scaling_snapshots != sorted(set(design.scaling_snapshots)) or any(
        count >= len(seen) for count in design.scaling_snapshots
    ):
        raise ValueError("Scaling snapshots must be increasing proper prefixes of the inventory.")
    candidates = set(design.candidates)
    if not candidates or len(candidates) != len(design.candidates) or any(
        edge != _edge(*edge) for edge in candidates
    ):
        raise ValueError("Commit distinct canonical critical candidates before authoring.")
    if design.required.keys() != set(condition_ids(slot)) or any(
        not set(requirements) <= candidates or len(requirements) != len(set(requirements))
        for requirements in design.required.values()
    ):
        raise ValueError("Every planned condition needs an exact critical target declaration.")


def freeze_bundles(
    slot: FamilySlot, design: DesignOutput, natural: list[Source],
) -> tuple[dict[str, list[Source]], BatchSourceFreeze]:
    base, *siblings = condition_ids(slot)
    variants = dict(zip(siblings, design.matched, strict=True))
    by_id = {source.id: source for source in natural}
    if list(by_id) != [entry.source_id for entry in design.inventory] or len(by_id) != len(natural):
        raise ValueError("Authored Sources must match the complete dated inventory.")
    bundles = {base: natural}
    for condition, control in variants.items():
        if control.order is not None:
            if set(control.order) != by_id.keys() or len(control.order) != len(natural):
                raise ValueError("An order-only control must retain all Source bytes.")
            ordered = [by_id[identity] for identity in control.order]
            if ordered == natural or design.required[base] != design.required[condition]:
                raise ValueError("An order-only control changes order and preserves its target declaration.")
            bundles[condition] = ordered
        elif control.edit is not None:
            edit = control.edit
            original = by_id.get(edit.source_id)
            if (original is None or original.text.count(edit.before) != 1
                    or original.text.find(edit.before, original.text.index(edit.before) + 1) != -1
                    or edit.before == edit.after):
                raise ValueError("The predeclared edit must replace exactly one occurrence in one Source.")
            replacement = original.model_copy(update={"text": original.text.replace(edit.before, edit.after, 1)})
            bundles[condition] = [replacement if source.id == edit.source_id else source for source in natural]
    freeze = BatchSourceFreeze(
        natural=base, variants={name: control.edit for name, control in variants.items()},
        candidates=design.candidates, required=design.required,
        order={name: [source.id for source in sources] for name, sources in bundles.items()},
        sources_sha256={name: value_digest([source.model_dump(mode="json") for source in sources])
                        for name, sources in bundles.items()},
        source_commitments={name: source_commitments(sources) for name, sources in bundles.items()},
    )
    return bundles, freeze


def check_reading(
    reading: Reading, sources: list[Source],
) -> dict[SemanticEdge, set[tuple[str, str]]]:
    inventory = {source.id for source in sources}
    if set(reading.reviewed_sources) != inventory or len(reading.reviewed_sources) != len(inventory):
        raise ValueError("Reading does not account for every Source exactly once.")
    state = build_canonical_state(reading.candidates.relationships, sources=sources)
    names = {entity.id: entity.name for entity in state.entities}
    evidence = {item.id: (item.source_id, item.supporting_text) for item in state.evidence}
    return {_edge(names[edge.source], edge.type, names[edge.target]): {evidence[i] for i in edge.evidence_ids}
            for edge in state.relationships}


def compare_readings(first: Reading, second: Reading, sources: list[Source]) -> dict[str, Any]:
    left, right = check_reading(first, sources), check_reading(second, sources)
    common = left.keys() & right.keys()
    disagreements = sorted(edge for edge in left.keys() | right.keys() if left.get(edge) != right.get(edge))
    return {
        "common_edges": sorted(common), "reader_a_only": sorted(left.keys() - right.keys()),
        "reader_b_only": sorted(right.keys() - left.keys()), "disagreements": disagreements,
    }


def verify_adjudication(
    condition: str, review: Adjudication, sources: list[Source], agreement: dict[str, Any],
) -> None:
    if review.key.condition != condition or set(review.source_audit) != {source.id for source in sources}:
        raise ValueError("Adjudication must identify its condition and account for every Source.")
    if set(review.disagreement_resolutions) != {json_text(edge) for edge in agreement["disagreements"]}:
        raise ValueError("Adjudication must resolve every graph or attached-evidence disagreement.")
    if review.unresolved:
        raise ValueError("Adjudication has unresolved scientific objections.")
    saved = review.key
    truth_edges(saved.truth)
    state = build_canonical_state(saved.ideal.relationships, sources=sources)
    score = evaluate_graph(reconstruct_graph(state), saved.truth)
    evidence = assess_evidence(state, saved)
    if (score.fp or score.fn or evidence["quotation"]["failed"] or evidence["source_attribution"]["failed"]
            or evidence["sufficiency"]["incomplete"] or evidence["sufficiency"]["missed"]):
        raise ValueError("Provisional key fails canonical replay or the existing evidence policies.")


def audit_risks(
    slot: FamilySlot, adjudications: dict[str, Adjudication], agreements: dict[str, dict[str, Any]],
) -> set[Risk]:
    risks: set[Risk] = set()
    if slot.tier in {"complex", "giant"} or (slot.tier == "administrative" and slot.expected_sources >= 51):
        risks.add("large_or_complex")
    if any(row["disagreements"] for row in agreements.values()):
        risks.add("reader_disagreement")
    if any(
        len({pair.source_id for pair in alternative}) > 1
        for review in adjudications.values()
        for proof in review.key.sufficient_evidence
        for alternative in proof.alternatives
    ):
        risks.add("joint_proof")
    return risks


def verify_audit(
    review: AuditReview, bundles: dict[str, list[Source]], freeze: BatchSourceFreeze,
    required_risks: set[Risk], adjudications: dict[str, Adjudication],
) -> None:
    conditions = bundles.keys()
    if any(index.keys() != conditions for index in (
        review.completeness, review.sufficiency, review.negative_controls, review.shortcuts, review.matched_controls,
    )):
        raise ValueError("Audit must cover all conditions and all standard checks.")
    for condition, sources in bundles.items():
        if review.completeness[condition].keys() != {source.id for source in sources}:
            raise ValueError("Audit must account for every Source independently of the adjudication.")
        if review.sufficiency[condition].keys() != {json_text(edge) for edge in freeze.required[condition]}:
            raise ValueError("Audit must review sufficiency for each critical edge.")
    if review.verdict != "accept":
        return
    expected = required_risks | set(review.risks)
    if review.objections or {mask.risk for mask in review.masks} != expected:
        raise ValueError("Acceptance requires resolved objections and targeted independent masks for every risk.")
    masks = []
    for mask in review.masks:
        if mask.condition not in bundles:
            raise ValueError("A targeted mask must reference a frozen condition.")
        masks.append((mask, mask_sources(mask, bundles[mask.condition])))
    for condition, adjudication in adjudications.items():
        for proof in adjudication.key.sufficient_evidence:
            _verify_joint_mask_plan(condition, proof, masks)


def _verify_joint_mask_plan(
    condition: str, proof: SufficientEvidence, masks: list[tuple[MaskAssignment, list[Source]]],
) -> None:
    related = [(mask, {source.id: source.text for source in sources})
               for mask, sources in masks if mask.condition == condition and mask.risk == "joint_proof"]
    edge = _edge(*proof.edge)
    for alternative in proof.alternatives:
        source_ids = {quote.source_id for quote in alternative}
        if len(source_ids) < 2:
            continue
        positive = any(
            edge in mask.present and set(text) == source_ids
            and all(quote.supporting_text in text[quote.source_id] for quote in alternative)
            for mask, text in related
        )
        deletions = set()
        for mask, text in related:
            absent_sources = {
                quote.source_id for quote in alternative
                if quote.supporting_text not in text.get(quote.source_id, "")
            }
            if edge in mask.absent and len(absent_sources) == 1:
                deletions.update(absent_sources)
        if not positive or deletions != source_ids:
            raise ValueError("Each joint alternative needs an independent sufficient subset and one deletion per Source.")


def mask_sources(mask: MaskAssignment, sources: list[Source]) -> list[Source]:
    selected = set(mask.included)
    if (
        len(selected) != len(mask.included) or not selected <= {source.id for source in sources}
        or not mask.remove_quotes.keys() <= selected
        or (len(selected) == len(sources) and not mask.remove_quotes
            and not (mask.risk == "joint_proof" and mask.present and not mask.absent))
        or not (mask.present or mask.absent) or set(mask.present) & set(mask.absent)
        or any(edge != _edge(*edge) for edge in [*mask.present, *mask.absent])
    ):
        raise ValueError("A targeted mask must remove evidence and precommit distinct edge expectations.")
    result = []
    for source in sources:
        if source.id not in selected:
            continue
        quote = mask.remove_quotes.get(source.id)
        if quote is None:
            result.append(source)
        elif source.text.count(quote) == 1:
            result.append(source.model_copy(update={"text": source.text.replace(quote, "[redacted]", 1)}))
        else:
            raise ValueError("Masked text must occur exactly once in its assigned Source.")
    return result
