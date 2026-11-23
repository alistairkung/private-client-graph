"""Independently relock documentary evidence against the same scientific freeze."""

from dataclasses import dataclass, replace
from typing import Any

from pydantic import TypeAdapter

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, audit_boundary, authorisation, science
from benchmark_v3.batch.contracts import Adjudication, DesignOutput, MilestoneAudit, Reading, RealismReview
from benchmark_v3.batch.sessions import SessionRunner
from benchmark_v3.portfolio import FamilySlot
from benchmark_v3.replay_manifest import BatchSourceFreeze, SavedIdeal, truth_edges
from benchmark_v3.research_contracts import Contract, Digest, Text
from private_client_graph.models.source import Source

POLICY = (
    " Apply the same documentary rules to every edge in this file. Prefer one record per semantic edge. "
    "Distinguish historical appointment or assertion from evidence of status at the requested cutoff. "
    "Identify exactly which span is independently sufficient and which spans require nearby naming or scope "
    "context. Store genuinely different supporting routes as separate approved alternatives. Reconstruct the "
    "complete file and report any unresolved objections independently."
)


class FrozenEvidenceReview(Contract):
    parent_revision: int
    manifest_sha256: Digest
    audit_receipt_sha256: Digest
    freeze_sha256: Digest
    rationale: Text


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
            or record.parent_revision != runner.revision - 1 or record.parent_revision < 1
            or record.manifest_sha256 != authorisation.commitment(runner.manifest)
            or event["details"]["parent_sha256"] != authorisation.commitment(record)):
        raise ValueError("Evidence review requires its exact immutable pooled lineage.")
    return record


def make_release(runner: SessionRunner, slot: FamilySlot, rationale: str) -> FrozenEvidenceReview:
    _, receipt, _ = _read_audit(runner)
    freeze_path = runner.directory / "family" / "freeze.json"
    record = FrozenEvidenceReview(
        parent_revision=runner.revision, manifest_sha256=authorisation.commitment(runner.manifest),
        audit_receipt_sha256=receipt["receipt_sha256"],
        freeze_sha256=commissioning.digest(artifacts.read_bytes(freeze_path)), rationale=rationale,
    )
    _reopen(runner, slot, record)
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
    if (audit.verdict != "repair" or not audit.objections or receipt["receipt_sha256"] != record.audit_receipt_sha256
            or commissioning._read_json(request["inputs"]["paired_bundles"]) != {
                condition: commissioning._read_json(_source_text(sources)) for condition, sources in bundles.items()
            }):
        raise ValueError("Evidence review requires an authenticated independent return on the same frozen Sources.")
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
    report, _, request = prior.committed_result("blind", f"reading-{index:03}-{name}-full", "annotation", Reading)
    if request["inputs"]["sources"] != _source_text(sources) or request["inputs"]["neutral_brief"] != design.neutral_brief:
        raise ValueError("A full-file blind packet does not bind the same frozen condition.")
    return report


def _source_text(sources: list[Source]) -> str:
    return commissioning.json_text([source.model_dump(mode="json") for source in sources])


def verify_same_semantics(new: Adjudication, original: Adjudication) -> None:
    left, right = new.key.truth, original.key.truth
    current = {(item.name, item.type) for item in left.entities}
    prior = {(item.name, item.type) for item in right.entities}
    if truth_edges(left).keys() != truth_edges(right).keys() or current != prior:
        raise ValueError("Independent evidence review disagreed with the frozen graph or identified roster.")
