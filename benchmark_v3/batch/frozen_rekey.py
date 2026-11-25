"""Independently relock documentary evidence against the same scientific freeze."""

from dataclasses import dataclass, replace
from typing import Any

from pydantic import Field, TypeAdapter

from benchmark_v3 import commissioning
from benchmark_v3.batch import annotation_recovery, artifacts, audit_boundary, authorisation, read_format_recovery, science
from benchmark_v3.batch.contracts import Adjudication, DesignOutput, MaskAssignment, MilestoneAudit, Reading, RealismReview
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.replay_manifest import BatchSourceFreeze, SavedIdeal, truth_edges
from benchmark_v3.research_contracts import Contract, Digest, Text
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.source import Source

POLICY = (
    " Apply the same documentary rules to every edge in this file. Prefer one record per semantic edge. "
    "Distinguish historical appointment or assertion from evidence of status at the requested cutoff. "
    "Identify exactly which span is independently sufficient and which spans require nearby naming or scope "
    "context. Store genuinely different supporting routes as separate approved alternatives. Reconstruct the "
    "complete file and report any unresolved objections independently."
)


class ReturnedRekeyRetry(Contract):
    boundary_sha256: Digest
    previous_release_sha256: Digest
    returned_adjudication_sha256: Digest


class FrozenEvidenceReview(Contract):
    parent_revision: int
    manifest_sha256: Digest
    audit_receipt_sha256: Digest
    freeze_sha256: Digest
    rationale: Text
    mask_corrections: dict[Digest, list[SemanticEdge]] = Field(default_factory=dict, exclude_if=lambda value: not value)
    retry: ReturnedRekeyRetry | None = Field(default=None, exclude_if=lambda value: value is None)


@dataclass(frozen=True)
class ReopenedCase:
    design: DesignOutput
    freeze: BatchSourceFreeze
    bundles: dict[str, list[Source]]
    realism: dict[str, RealismReview]
    readings: dict[str, tuple[Reading, Reading]]
    agreements: dict[str, dict[str, Any]]
    locked: dict[str, Adjudication]
    audit: MilestoneAudit
    stages: dict[str, dict[str, Any]]


def recorded(runner: SessionRunner) -> FrozenEvidenceReview | None:
    batch, family = runner.manifest.batch_id, runner.family
    event = next((row for row in runner.ledger.events(batch, family)
                  if row["kind"] == "reconcile" and row["revision"] == runner.revision
                  and row["name"].startswith("pooled-release") and "frozen_evidence_review" in row["details"]), None)
    if event is None:
        return None
    record = FrozenEvidenceReview.model_validate(event["details"]["frozen_evidence_review"])
    if (not runner.ledger.requires_delivery_attestation or not runner.ledger.pooled_revision(batch, family, runner.revision)
            or record.parent_revision != runner.revision - (3 if record.retry else 1) or record.parent_revision < 1
            or record.manifest_sha256 != authorisation.commitment(runner.manifest)
            or event["details"]["parent_sha256"] != authorisation.commitment(record)):
        raise ValueError("Evidence review requires its exact immutable pooled lineage.")
    if record.retry is not None and _retry_record(runner, record.retry.boundary_sha256) != record:
        raise ValueError("Independent evidence retry differs from its exact retained release and return.")
    return record


def _retry_record(runner: SessionRunner, boundary_sha256: str) -> FrozenEvidenceReview:
    from benchmark_v3.batch import autonomous_realism

    held_revision = runner.revision - 1
    events = runner.ledger.events(runner.manifest.batch_id, runner.family)
    restored = [row for row in events if row["revision"] == held_revision and row["kind"] == "reconcile"
                and row["name"] == "verified_documentary_lineage"]
    previous = replace(runner, revision=held_revision - 1, directory=runner.directory.with_name(str(held_revision - 1)))
    record = recorded(previous)
    if (record is None or record.retry is not None or len(restored) != 1
            or restored[0]["details"]["boundary_sha256"] != boundary_sha256
            or restored[0]["details"]["parent_freeze_sha256"] != record.freeze_sha256
            or any(row["revision"] == held_revision for row in runner.ledger.attempts(runner.family))):
        raise ValueError("The exact restored evidence lineage is required for one independent retry.")
    returned = autonomous_realism.document_adjudication_return(previous)
    return record.model_copy(update={"retry": ReturnedRekeyRetry(
        boundary_sha256=boundary_sha256, previous_release_sha256=authorisation.commitment(record),
        returned_adjudication_sha256=returned["receipt_sha256"],
    )})


def make_format_retry(runner: SessionRunner, slot: FamilySlot, boundary_sha256: str) -> FrozenEvidenceReview:
    record = _retry_record(runner, boundary_sha256)
    reopen(runner, slot, record)
    return record


def verify_returned_inputs(runner: SessionRunner, slot: FamilySlot, record: FrozenEvidenceReview) -> None:
    case = reopen(runner, slot, record)
    condition = science.condition_ids(slot)[0]
    _, _, request = runner.committed_result("adjudicate", "adjudicate-000", "adjudication", Adjudication)
    inputs = request["inputs"]
    if (TypeAdapter(list[Source]).validate_json(inputs["sources"]) != case.bundles[condition]
            or tuple(Reading.model_validate_json(inputs[f"annotation_{name}"]) for name in ("a", "b"))
            != case.readings[condition]):
        raise ValueError("The adjudication return must bind the exact frozen documentary file and independent readings.")


def make_release(
    runner: SessionRunner, slot: FamilySlot, rationale: str, *, mask_corrections: dict[str, list[SemanticEdge]] | None = None,
) -> FrozenEvidenceReview:
    _, receipt, _ = _read_audit(runner)
    freeze_path = runner.directory / "family" / "freeze.json"
    record = FrozenEvidenceReview(
        parent_revision=runner.revision, manifest_sha256=authorisation.commitment(runner.manifest),
        audit_receipt_sha256=receipt["receipt_sha256"], freeze_sha256=commissioning.digest(artifacts.read_bytes(freeze_path)),
        rationale=rationale, mask_corrections=mask_corrections or {},
    )
    case = _reopen(runner, slot, record)
    candidate_control_corrections(case.audit, record.mask_corrections)
    return record


def reopen(runner: SessionRunner, slot: FamilySlot, record: FrozenEvidenceReview) -> ReopenedCase:
    prior = replace(runner, revision=record.parent_revision, directory=runner.directory.with_name(str(record.parent_revision)))
    return _reopen(prior, slot, record)


def _reopen(prior: SessionRunner, slot: FamilySlot, record: FrozenEvidenceReview) -> ReopenedCase:
    root = prior.directory / "family"
    freeze_bytes = artifacts.read_bytes(root / "freeze.json")
    if commissioning.digest(freeze_bytes) != record.freeze_sha256:
        raise ValueError("The reviewed Source freeze changed.")
    freeze = BatchSourceFreeze.model_validate_json(freeze_bytes)
    design = artifacts.read_contract(prior.directory / "design.json", DesignOutput)
    natural = TypeAdapter(list[Source]).validate_json(artifacts.read_bytes(root / "sources" / f"{freeze.natural}.json"))
    bundles, expected = science.freeze_bundles(slot, design, natural)
    if (freeze != expected or any(artifacts.read_bytes(root / "sources" / f"{condition}.json")
                                  != (_source_text(sources) + "\n").encode()
                                  for condition, sources in bundles.items())):
        raise ValueError("Evidence review requires every exact locked condition.")
    audit, receipt, request = _read_audit(prior)
    if (audit.verdict not in {"repair", "return"} or not audit.objections
            or receipt["receipt_sha256"] != record.audit_receipt_sha256
            or commissioning._read_json(request["inputs"]["paired_bundles"]) != {
                condition: commissioning._read_json(_source_text(sources)) for condition, sources in bundles.items()
            }):
        raise ValueError("Evidence review requires an authenticated independent return on the same frozen Sources.")
    _verify_reviewed_scope(audit, bundles, freeze)
    audit_boundary.original_views(audit, bundles)
    locked = TypeAdapter(dict[str, Adjudication]).validate_json(request["inputs"]["provisional_keys"])
    if locked.keys() != bundles.keys():
        raise ValueError("The retained audit and freeze differ in their exact conditions.")
    inherited = recorded(prior)
    original = reopen(prior, slot, inherited) if inherited is not None else None
    if original is not None and (original.freeze != freeze or original.design != design):
        raise ValueError("A follow-up evidence review requires the identical retained Sources and design.")
    realism, readings, agreements = {}, {}, {}
    stages = _stages(prior)
    for index, (condition, sources) in enumerate(bundles.items()):
        if original is None:
            realism[condition] = _realism(prior, design, sources, index)
            first, second = (_reading(prior, design, index, name, sources) for name in ("a", "b"))
        else:
            realism[condition] = original.realism[condition]
            first, second = original.readings[condition]
            verify_same_semantics(locked[condition], original.locked[condition])
        readings[condition] = first, second
        agreements[condition] = science.compare_readings(first, second, sources)
        if locked[condition].key != artifacts.read_contract(root / f"{condition}.json", SavedIdeal):
            raise ValueError("A previous adjudicated key differs from the audited bytes.")
        science.verify_adjudication(condition, locked[condition], sources, agreements[condition])
    recorded_blind = stages["blind"]["outputs"]
    outputs = {
        "readings": {name: [reply.model_dump(mode="json") for reply in pair] for name, pair in readings.items()},
        "agreements": agreements,
    }
    if recorded_blind != {name: commissioning.digest(commissioning.json_text(value).encode())
                          for name, value in outputs.items()}:
        raise ValueError("The reopened independent readings differ from the frozen agreement commitment.")
    if original is not None:
        if all(locked[condition].key == previous.key for condition, previous in original.locked.items()):
            raise ValueError("A second evidence review requires an intervening independently changed key.")
        if audit.objections == original.audit.objections:
            raise ValueError("A second evidence review requires changed independent scientific objections.")
        masks = {authorisation.commitment(mask): mask for mask in [*original.audit.masks, *audit.masks]}
        audit = audit.model_copy(update={"masks": list(masks.values()),
                                         "objections": list(dict.fromkeys([*original.audit.objections, *audit.objections]))})
    return ReopenedCase(design, freeze, bundles, realism, readings, agreements, locked, audit, stages)


def _read_audit(runner: SessionRunner) -> tuple[MilestoneAudit, dict[str, Any], dict[str, Any]]:
    result_type = MilestoneAudit if recorded(runner) is None else audit_boundary.RecheckedAudit
    return runner.committed_result("audit", "audit", "audit", result_type)


def _verify_reviewed_scope(
    audit: MilestoneAudit, bundles: dict[str, list[Source]], freeze: BatchSourceFreeze,
) -> None:
    if ({name: set(findings) for name, findings in audit.completeness.items()}
            != {name: {source.id for source in sources} for name, sources in bundles.items()}
            or {name: set(findings) for name, findings in audit.sufficiency.items()}
            != {name: {commissioning.json_text(edge) for edge in edges} for name, edges in freeze.required.items()}):
        raise ValueError("Evidence review requires a retained return examining every Source and critical edge.")


def _stages(runner: SessionRunner) -> dict[str, dict[str, Any]]:
    stages = {row["name"]: row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
              if row["revision"] == runner.revision and row["kind"] == "transition"
              and row["name"] in {"design", "author", "realism", "freeze", "blind", "adjudicate"}}
    if len(stages) != 6:
        raise ValueError("The earlier gate chain must be complete before independent evidence review.")
    return stages


def _realism(prior: SessionRunner, design: DesignOutput, sources: list[Source], index: int) -> RealismReview:
    report, _, request = prior.committed_result("realism", f"realism-{index:03}", "realism", RealismReview)
    if (report.verdict != "pass" or report.objections or report.source_findings.keys() != {source.id for source in sources}
            or request["inputs"]["sources"] != _source_text(sources)
            or request["inputs"]["neutral_brief"] != design.neutral_brief):
        raise ValueError("A prior documentary realism pass did not bind the exact condition.")
    return report


def _reading(prior: SessionRunner, design: DesignOutput, index: int, name: str, sources: list[Source]) -> Reading:
    job = f"reading-{index:03}-{name}-full"
    _, _, request = prior.committed_packet("blind", job, "annotation")
    inputs = request["inputs"]
    if inputs["sources"] != _source_text(sources) or inputs["neutral_brief"] != design.neutral_brief:
        raise ValueError("A full-file blind packet does not bind the same frozen condition.")
    recovery = annotation_recovery.recorded(prior)
    if recovery and recovery["decision"]["reader_job"] == job:
        return annotation_recovery.reopen(prior, recovery)[0]
    whitespace = read_format_recovery.reopen_whitespace(prior, job, inputs)
    if whitespace is not None:
        return whitespace[0]
    selected = read_format_recovery.selected_job(prior, job, inputs)
    report, _, committed_request = prior.committed_result("blind", selected, "annotation", Reading)
    if committed_request["inputs"] != inputs:
        raise ValueError("The retained independent reading does not bind the original packet inputs.")
    return report


def _source_text(sources: list[Source]) -> str:
    return commissioning.json_text([source.model_dump(mode="json") for source in sources])


def verify_same_semantics(new: Adjudication, original: Adjudication) -> None:
    left, right = new.key.truth, original.key.truth
    current = {(item.name, item.type) for item in left.entities}
    prior = {(item.name, item.type) for item in right.entities}
    if truth_edges(left).keys() != truth_edges(right).keys() or current != prior:
        raise ValueError("Independent evidence review disagreed with the frozen graph or identified roster.")


def candidate_control_corrections(
    review: MilestoneAudit, corrections: dict[str, list[SemanticEdge]],
) -> dict[str, MaskAssignment]:
    """Nominate only exact, still unexecuted positive precommitments for reassessment."""
    masks = {authorisation.commitment(mask): mask for mask in review.masks}
    if any(mask not in masks or not edges or len(edges) != len(set(edges)) or not set(edges) <= set(masks[mask].present)
           for mask, edges in corrections.items()):
        raise ValueError("A precommitment correction must bind its exact retained positive expectations.")
    return {digest: masks[digest] for digest in corrections}


def unsuperseded_controls(review: MilestoneAudit, nominated: dict[str, MaskAssignment]) -> MilestoneAudit:
    return review.model_copy(update={"masks": [mask for mask in review.masks if authorisation.commitment(mask) not in nominated]})


def verify_mask_corrections(
    review: MilestoneAudit, original: dict[str, MaskAssignment], corrections: dict[str, list[SemanticEdge]],
) -> None:
    """Keep each old view and require an independently checked negative for its unsupported edges."""
    for digest, previous in original.items():
        changed = set(corrections[digest])
        target = previous.model_dump(exclude={"reason", "present", "absent"})
        if not any(candidate.model_dump(exclude={"reason", "present", "absent"}) == target
                   and set(candidate.present) == set(previous.present) - changed
                   and set(candidate.absent) == set(previous.absent) | changed
                   for candidate in review.masks):
            raise ValueError("The independent audit must precommit the same view with the exact corrected expectations.")
        if any(candidate.model_dump(exclude={"reason", "present", "absent"}) == target and changed & set(candidate.present)
               for candidate in review.masks):
            raise ValueError("An independently superseded positive may not remain in the new control plan.")
