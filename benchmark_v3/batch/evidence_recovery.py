"""Reconcile independently approved quotations on one invariant edge after a paired audit return."""

from dataclasses import dataclass
from typing import Any

from pydantic import TypeAdapter

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, authorisation, science
from benchmark_v3.batch.contracts import (
    Adjudication, AuditReview, DesignOutput, MaskAssignment, MilestoneEvidenceRepair, RealismReview, Reading,
)
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.replay_manifest import BatchSourceFreeze, SavedIdeal, truth_edges
from private_client_graph.evaluation import _edge
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.source import Source

RELEASE = "milestone_invariant_evidence"
MASK_EQUIVALENCE_INSTRUCTIONS = (
    " Use only the condition keys enumerated in the schema; place cross-condition findings in the summary, "
    "objections, or limitations. Keep all masked questions neutral and omit condition identifiers and expected "
    "answers. Use canonical order for symmetric edge endpoints. Explain whether one independent observation "
    "can satisfy assignments with identical rendered Sources, reviewer question, risk, and expectations. "
    "Set equivalent_views_reusable to false if separate observations are scientifically required."
)
AUDIT_INSTRUCTIONS = (
    " This is a fresh audit after reconciliation of one invariant ordinary evidence route. The prior objections "
    "are challenges to resolve independently. Determine whether both exact quotations remain independently "
    "sufficient on the invariant edge, and whether the matched condition retains its documented scope. "
    "Include every proposed Source view with your own independently derived expectations. Return if the "
    "evidence, contrast, or controls are inadequate."
)


@dataclass(frozen=True)
class RecoveredEvidence:
    plan_sha256: str
    design: DesignOutput
    freeze: BatchSourceFreeze
    bundles: dict[str, list[Source]]
    realism: dict[str, RealismReview]
    agreements: dict[str, dict[str, Any]]
    adjudications: dict[str, Adjudication]
    prior_audit: AuditReview
    exact_route_checks: dict[str, list[str]]


def derive(runner: SessionRunner, slot: FamilySlot, plan: MilestoneEvidenceRepair) -> RecoveredEvidence:
    _verify_scope(runner, plan)
    family = runner.directory / "family"
    freeze = artifacts.read_contract(family / "freeze.json", BatchSourceFreeze)
    if not freeze.variants:
        raise ValueError("Invariant evidence reconciliation requires a locked matched comparison.")
    design = artifacts.read_contract(runner.directory / "design.json", DesignOutput)
    natural = TypeAdapter(list[Source]).validate_json(artifacts.read_bytes(family / "sources" / f"{freeze.natural}.json"))
    bundles, reconstructed = science.freeze_bundles(slot, design, natural)
    if reconstructed != freeze or any(
        _json([source.model_dump(mode="json") for source in sources]).encode() + b"\n"
        != artifacts.read_bytes(family / "sources" / f"{condition}.json")
        for condition, sources in bundles.items()
    ):
        raise ValueError("The original Source views differ from their frozen exact commitments.")
    original = _original_reviews(runner, bundles)
    harmonized = _harmonize_ordinary_edge(plan.invariant_edge, bundles, original[2])
    exact_route_checks = {
        condition: _replay_routes(plan.invariant_edge, condition, review, bundles[condition], original[1][condition])
        for condition, review in harmonized.items()
    }

    output, receipt, _ = runner.committed_packet("audit", "audit", "audit")
    if (receipt["output_sha256"], receipt["receipt_sha256"]) != (plan.audit_output_sha256, plan.audit_receipt_sha256):
        raise ValueError("Reconciliation requires the exact retained audit receipt and output.")
    audit = AuditReview.model_validate(commissioning._read_json(output))
    if audit.verdict != "repair" or not audit.objections or not audit.masks:
        raise ValueError("An independent auditor must request this bounded evidence repair and specify controls.")
    # Preserve the returned plan's semantic expectations when its symmetric endpoints are in display order.
    prior_masks = [mask.model_copy(update={
        "present": [_edge(*edge) for edge in mask.present],
        "absent": [_edge(*edge) for edge in mask.absent],
    }) for mask in audit.masks]
    for mask in prior_masks:
        science.mask_sources(mask, bundles[mask.condition])
    audit = audit.model_copy(update={"masks": prior_masks})
    return RecoveredEvidence(
        authorisation.commitment(plan), design, freeze, bundles, original[0], original[1], harmonized, audit,
        exact_route_checks,
    )


def _verify_scope(runner: SessionRunner, plan: MilestoneEvidenceRepair) -> None:
    manifest = runner.manifest
    freeze_path = runner.directory / "family" / "freeze.json"
    if (
        manifest.phase != "milestone" or manifest.repair_cycles != 1 or runner.revision != 1
        or plan.batch_id != manifest.batch_id or plan.family_id != runner.family
        or plan.manifest_sha256 != authorisation.commitment(manifest)
        or plan.freeze_sha256 != commissioning.digest(artifacts.read_bytes(freeze_path))
    ):
        raise ValueError("Evidence repair requires the exact original milestone, family revision and Source freeze.")


def _original_reviews(
    runner: SessionRunner, bundles: dict[str, list[Source]],
) -> tuple[dict[str, RealismReview], dict[str, dict[str, Any]], dict[str, Adjudication]]:
    realism, agreements, adjudications = {}, {}, {}
    for index, (condition, sources) in enumerate(bundles.items()):
        tag = f"{index:03}"
        raw, _, _ = runner.committed_packet("realism", f"realism-{tag}", "realism")
        realism[condition] = RealismReview.model_validate(commissioning._read_json(raw))
        if realism[condition].verdict != "pass" or realism[condition].objections:
            raise ValueError("The original documentary realism reviews must have passed first.")
        annotations = []
        for reader in ("a", "b"):
            raw, _, _ = runner.committed_packet("blind", f"reading-{tag}-{reader}-full", "annotation")
            annotations.append(Reading.model_validate(commissioning._read_json(raw)))
        agreement = science.compare_readings(annotations[0], annotations[1], sources)
        agreements[condition] = agreement
        raw, _, _ = runner.committed_packet("adjudicate", f"adjudicate-{tag}", "adjudication")
        adjudication = Adjudication.model_validate(commissioning._read_json(raw))
        if adjudication.key.condition != "local":
            raise ValueError("The original adjudication must have been condition-local.")
        key = adjudication.key.model_copy(update={"condition": condition})
        locked = artifacts.read_contract(runner.directory / "family" / f"{condition}.json", SavedIdeal)
        if key != locked:
            raise ValueError("The original independently reviewed key differs from the locked key.")
        review = adjudication.model_copy(update={"key": key})
        science.verify_adjudication(condition, review, sources, agreement)
        adjudications[condition] = review
    return realism, agreements, adjudications


def _harmonize_ordinary_edge(
    edge: SemanticEdge, bundles: dict[str, list[Source]], reviews: dict[str, Adjudication],
) -> dict[str, Adjudication]:
    proofs = [next((item for item in review.key.sufficient_evidence if item.edge == edge), None)
              for review in reviews.values()]
    if edge != _edge(*edge) or any(proof is None or proof.joint_only for proof in proofs):
        raise ValueError("Every original key must independently support the same ordinary invariant edge.")
    alternatives = [proof.alternatives for proof in proofs if proof is not None]
    if any(len(route) != 1 for routes in alternatives for route in routes):
        raise ValueError("Invariant reconciliation is confined to interchangeable singleton quotations.")
    source_ids = {route[0].source_id for routes in alternatives for route in routes}
    if len(source_ids) != 1:
        raise ValueError("Every proof must use the same immutable Source.")
    source_id = next(iter(source_ids))
    sources = [next(source for source in bundle if source.id == source_id) for bundle in bundles.values()]
    if any(source != sources[0] for source in sources[1:]):
        raise ValueError("The evidence Source must be exactly identical in every condition.")

    existing = [{route[0].supporting_text for route in routes} for routes in alternatives]
    all_quotes = sorted(set.union(*existing), key=lambda quote: (len(quote), quote))
    if (len(all_quotes) < 2 or any(quote not in sources[0].text for quote in all_quotes)
            or any(short not in long for short, long in zip(all_quotes, all_quotes[1:]))
            or all_quotes[0] not in set.intersection(*existing)):
        raise ValueError("Repair requires nested, exact alternatives with a shared independently approved span.")
    return {condition: _project_approvals(review, edge, source_id, all_quotes)
            for condition, review in reviews.items()}


def _project_approvals(
    review: Adjudication, edge: SemanticEdge, source_id: str, quotes: list[str],
) -> Adjudication:
    original = review.key
    key = original.model_dump(mode="json")
    names = {entity["id"]: entity["name"] for entity in key["truth"]["entities"]}
    relationships = key["truth"]["relationships"]
    truth = next(row for row in relationships if _edge(names[row["source"]], row["type"], names[row["target"]]) == edge)
    approval = next(row for row in key["source_approval"]["relationships"]
                    if (row["source"], row["type"], row["target"]) == (truth["source"], truth["type"], truth["target"]))
    prior_quotes = set(truth["approved_evidence"])
    if not prior_quotes or not prior_quotes <= set(quotes) or {
        (pair["source_id"], pair["supporting_text"]) for pair in approval["approved_evidence"]
    } != {(source_id, quote) for quote in prior_quotes}:
        raise ValueError("Repair must preserve every original ordinary approval on the shared Source.")
    evidence = [{"source_id": source_id, "supporting_text": quote} for quote in quotes]
    truth["approved_evidence"] = quotes
    approval["approved_evidence"] = evidence
    proof = next(row for row in key["sufficient_evidence"] if tuple(row["edge"]) == edge)
    proof["alternatives"] = [[pair] for pair in evidence]
    for candidate in key["ideal"]["relationships"]:
        if _edge(candidate["source_name"], candidate["relationship_type"], candidate["target_name"]) == edge:
            if candidate["source_id"] != source_id or candidate["supporting_text"] not in prior_quotes:
                raise ValueError("The original ideal must attribute the invariant edge to the shared Source.")
            candidate["supporting_text"] = quotes[0]
    corrected = SavedIdeal.model_validate(key)
    if truth_edges(original.truth).keys() != truth_edges(corrected.truth).keys():
        raise ValueError("Evidence repair must preserve the entire independently reconstructed graph.")
    return review.model_copy(update={"key": corrected})


def _replay_routes(
    edge: SemanticEdge, condition: str, review: Adjudication, sources: list[Source], agreement: dict[str, Any],
) -> list[str]:
    proof = next(item for item in review.key.sufficient_evidence if item.edge == edge)
    checks = []
    for route in proof.alternatives:
        pair = route[0]
        candidates = [
            candidate.model_copy(update={"supporting_text": pair.supporting_text})
            if _edge(candidate.source_name, candidate.relationship_type, candidate.target_name) == edge else candidate
            for candidate in review.key.ideal.relationships
        ]
        ideal = review.key.ideal.model_copy(update={"relationships": candidates})
        candidate_key = review.key.model_copy(update={"ideal": ideal})
        science.verify_adjudication(condition, review.model_copy(update={"key": candidate_key}), sources, agreement)
        checks.append(commissioning.digest(_json(pair.model_dump(mode="json")).encode()))
    return checks


def proposed_views(review: AuditReview) -> list[dict[str, Any]]:
    return [
        mask.model_dump(mode="json", include={"condition", "risk", "included", "remove_quotes", "question"})
        for mask in review.masks
    ]


def verify_controls(original: AuditReview, fresh: AuditReview) -> None:
    keyed = {_view_key(mask): mask for mask in fresh.masks}
    for mask in original.masks:
        item = keyed.get(_view_key(mask))
        if item is None or not set(mask.present) <= set(item.present) or not set(mask.absent) <= set(item.absent):
            raise ValueError("The fresh audit must retain every required original control and derive compatible expectations.")


def _view_key(mask: MaskAssignment) -> str:
    return _json(mask.model_dump(mode="json", include={
        "condition", "risk", "included", "remove_quotes", "question",
    }) | {"included": sorted(mask.included)})


def observation_key(mask: MaskAssignment, sources: list[Source]) -> str:
    return _json({
        "sources": [source.model_dump(mode="json") for source in sources],
        "question": mask.question, "risk": mask.risk,
        "present": sorted(mask.present), "absent": sorted(mask.absent),
    })


_json = commissioning.json_text
