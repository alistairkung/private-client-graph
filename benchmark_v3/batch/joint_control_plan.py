"""Build exact missing joint-control proposals for independent scientific confirmation."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal

from benchmark_v3 import commissioning
from benchmark_v3.batch import artifacts, audit_boundary, authorisation, read_format_recovery, science
from benchmark_v3.batch.contracts import Adjudication, MaskAssignment, MilestoneAudit, Risk
from benchmark_v3.replay_manifest import BatchSourceFreeze, SufficientEvidence
from benchmark_v3.research_contracts import Contract, Digest, Text
from private_client_graph.evaluation import _edge
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.source import Source
from private_client_graph.research.source_attribution import ApprovedSourceEvidence

if TYPE_CHECKING:
    from benchmark_v3.batch.sessions import SessionRunner

RELEASE = "joint-control-plan-confirmation"
JOB = "joint-plan-confirmation"
QUESTION = "Which relationships are supported at the requested snapshot by these supplied records? Cite exact evidence."


class Confirmation(Contract):
    verdict: Literal["accept", "return"]
    confirmed_views: list[Digest]
    findings: Text
    objections: list[Text]
    limitations: list[Text]


@dataclass(frozen=True)
class Plan:
    audit: audit_boundary.RecheckedAudit
    proposed: list[MaskAssignment]
    excerpt_derivatives: list[dict[str, Any]]

    @property
    def commitments(self) -> dict[str, dict[str, Any]]:
        return {authorisation.commitment(view): view.model_dump(mode="json") for view in self.proposed}


def released(runner: "SessionRunner") -> dict[str, Any] | None:
    return next((row["details"] for row in runner.ledger.events(runner.manifest.batch_id, runner.family)
                 if (row["revision"], row["kind"], row["name"]) == (runner.revision, "reconcile", RELEASE)), None)


def retained_audit(runner: "SessionRunner", record: dict[str, Any]) -> audit_boundary.RecheckedAudit:
    job = record["job"]
    if job.removesuffix("-format-retry") not in {"audit", audit_boundary.RECHECK} or not runner.ledger.requires_delivery_attestation:
        raise ValueError("Joint-plan confirmation requires the exact independently failed audit attempt.")
    raw, receipt, _ = runner.committed_packet("audit", job, "audit")
    original = commissioning._read_json(raw)
    review = audit_boundary.RecheckedAudit.model_validate({"excerpt_controls": [], **original})
    if (review.verdict != "accept" or review.objections or receipt["receipt_sha256"] != record["receipt_sha256"]
            or commissioning.digest(artifacts.read_bytes(runner.directory / "family" / "freeze.json")) != record["freeze_sha256"]):
        raise ValueError("The retained accepted audit and exact frozen Sources must match the release.")
    return review


def build_plan(
    accepted: audit_boundary.RecheckedAudit, earlier: list[MilestoneAudit], bundles: dict[str, list[Source]],
    freeze: BatchSourceFreeze, risks: set[Risk], reviews: dict[str, Adjudication],
) -> Plan:
    accepted, derivatives = _recover_exact_excerpt_format(accepted, bundles)
    valid, whole = audit_boundary.original_views(accepted, bundles)
    carried = {authorisation.commitment(view): view for view in valid.masks}
    excerpts = {authorisation.commitment(view): view for view in accepted.excerpt_controls}
    previous_views = []
    for audit in earlier:
        previous, pending = audit_boundary.original_views(audit, bundles)
        previous_views.append((previous, pending))
        carried.update({authorisation.commitment(view): view for view in previous.masks})
        for excerpt in getattr(audit, "excerpt_controls", ()):
            excerpts[authorisation.commitment(excerpt)] = excerpt

    proposed = []
    for condition, review in reviews.items():
        sources = bundles[condition]
        assigned = [view for view in carried.values() if view.condition == condition and view.risk == "joint_proof"]
        for proof in review.key.sufficient_evidence:
            proposed.extend(_missing_views(condition, proof, sources, assigned))

    if not proposed:
        raise ValueError("A fresh joint-plan review needs independently reviewable missing assignments.")
    plan = accepted.model_copy(update={"masks": [*carried.values(), *proposed],
                                       "excerpt_controls": list(excerpts.values())})
    science.verify_audit(audit_boundary.targeted_audit(plan, bundles), bundles, freeze, risks, reviews)
    audit_boundary.verify_recheck(plan, valid, whole, accepted.excerpt_controls, bundles)
    for previous, pending in previous_views:
        audit_boundary.verify_recheck(plan, previous, pending, [], bundles)
    return Plan(plan, proposed, derivatives)


def _recover_exact_excerpt_format(
    audit: audit_boundary.RecheckedAudit, bundles: dict[str, list[Source]],
) -> tuple[audit_boundary.RecheckedAudit, list[dict[str, Any]]]:
    reviewed = []
    derivatives = []
    for view in audit.excerpt_controls:
        by_id = {source.id: source.text for source in bundles[view.condition]}
        quotes = dict(view.retained_quotes)
        for identity, quote in view.retained_quotes.items():
            if identity not in by_id:
                raise ValueError("A recovered excerpt must preserve its exact Source attribution.")
            if quote not in by_id[identity]:
                quotes[identity] = read_format_recovery.exact_whitespace_span(quote, by_id[identity])
        corrected = view.model_copy(update={"retained_quotes": quotes})
        audit_boundary.render_excerpt(corrected, bundles[view.condition])
        reviewed.append(corrected)
        if corrected != view:
            derivatives.append({"prior_sha256": authorisation.commitment(view),
                                "exact_whitespace_derivative_sha256": authorisation.commitment(corrected)})
    return audit.model_copy(update={"excerpt_controls": reviewed}), derivatives


def _missing_views(
    condition: str, proof: SufficientEvidence, sources: list[Source], assigned: list[MaskAssignment],
) -> list[MaskAssignment]:
    edge = _edge(*proof.edge)
    pairs = [(view, {source.id: source.text for source in science.mask_sources(view, sources)}) for view in assigned]
    proposed = []
    for alternative in proof.alternatives:
        included = {quote.source_id for quote in alternative}
        if len(included) < 2:
            continue
        if not any(edge in view.present and set(text) == included
                   and all(quote.supporting_text in text[quote.source_id] for quote in alternative)
                   for view, text in pairs):
            positive = _view(condition, sources, included, edge, positive=True)
            pairs.append((positive, {source.id: source.text for source in sources if source.id in included}))
            proposed.append(positive)
        for missing in sorted(included):
            if any(edge in view.absent and {
                quote.source_id for quote in alternative if quote.supporting_text not in text.get(quote.source_id, "")
            } == {missing} for view, text in pairs):
                continue
            remaining = included - {missing}
            negative = _view(condition, sources, remaining, edge, positive=False)
            surviving = [route for route in proof.alternatives if {quote.source_id for quote in route} <= remaining]
            if surviving:
                negative = _isolate_single_standalone_route(negative, missing, alternative, surviving, sources)
            pairs.append((negative, {source.id: source.text for source in science.mask_sources(negative, sources)}))
            proposed.append(negative)
    return proposed


def _view(condition: str, sources: list[Source], included: set[str], edge: SemanticEdge,
          *, positive: bool) -> MaskAssignment:
    return MaskAssignment(
        condition=condition, risk="joint_proof",
        reason="Proposed isolated sufficient subset." if positive else "Proposed proper subset after one Source removal.",
        question=QUESTION, included=[source.id for source in sources if source.id in included],
        present=[edge] if positive else [], absent=[] if positive else [edge],
    )


def _isolate_single_standalone_route(
    negative: MaskAssignment, missing: str, alternative: list[ApprovedSourceEvidence],
    surviving: list[list[ApprovedSourceEvidence]], sources: list[Source],
) -> MaskAssignment:
    if len(surviving) == 1 and len(surviving[0]) == 1:
        competing = surviving[0][0]
        candidate = negative.model_copy(update={
            "reason": "Isolate the selected joint proof after suppressing the independently approved standalone route.",
            "remove_quotes": {competing.source_id: competing.supporting_text},
        })
        rendered = {source.id: source.text for source in science.mask_sources(candidate, sources)}
        if all(quote.supporting_text in rendered[quote.source_id] for quote in alternative if quote.source_id != missing):
            return candidate
    raise ValueError("A proposed proper subset contains an independently approved alternative route.")
