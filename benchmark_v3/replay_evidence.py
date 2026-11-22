"""Apply the frozen v2 evidence policy to a retained Benchmark v3 result."""

from typing import Any

from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.evaluation import _edge, evaluate_graph
from private_client_graph.models import GroundTruth
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.research.source_attribution import diagnose_source_attribution

from .replay_manifest import SavedIdeal, SufficientEvidence, truth_edges


EVIDENCE_POLICY_VERSION = 'benchmark_v2_evidence_v1'
SUFFICIENCY_VERSION = 'attached_sufficient_set_v1'
EvidencePair = tuple[str, str]


def assess_evidence(state: CanonicalState, saved: SavedIdeal) -> dict[str, Any]:
    """Score ordinary provenance and critical proof on the actual retained graph."""
    expected = truth_edges(saved.truth)
    annotations = {_edge(*item.edge): item for item in saved.sufficient_evidence}
    if len(annotations) != len(saved.sufficient_evidence) or annotations.keys() - expected.keys():
        raise ValueError('Sufficient sets must annotate distinct ground-truth edges')
    exempt = {edge for edge, item in annotations.items() if item.joint_only}
    if exempt != {edge for edge, relationship in expected.items() if not relationship.approved_evidence}:
        raise ValueError('Only joint-only edges may lack ordinary approved quotations')

    eligible = GroundTruth(entities=saved.truth.entities,
        relationships=[relationship for edge, relationship in expected.items() if edge not in exempt])
    quote_score = evaluate_graph(reconstruct_graph(state), eligible)
    attribution = diagnose_source_attribution(state, eligible, saved.source_approval)
    proof = _assess_sufficient_sets(state, annotations)
    return dict(version=EVIDENCE_POLICY_VERSION, not_applicable=sorted(exempt),
        quotation=dict(assessed=quote_score.tp, passed=quote_score.provenance_passed,
            failed=quote_score.provenance_failed,
            accuracy=None if exempt and not eligible.relationships else quote_score.provenance_accuracy,
            passes=quote_score.provenance_passes, failures=quote_score.provenance_failures),
        source_attribution=attribution.model_dump(mode='json'), sufficiency=proof)


def _assess_sufficient_sets(state: CanonicalState,
                            annotations: dict[SemanticEdge, SufficientEvidence]) -> dict[str, Any]:
    source_text = {source.id: source.text for source in state.sources}
    attachments = _attached_evidence(state)
    decisions = []
    for edge, item in sorted(annotations.items()):
        alternatives = _verified_alternatives(item, source_text)
        attached = attachments.get(edge)
        if attached is None:
            decisions.append(dict(edge=edge, status='missed', missing_by_alternative=[sorted(parts) for parts in alternatives]))
            continue
        # Each alternative must fit on one relationship. Candidates contributing
        # separate quotes already pool on that relationship during construction.
        missing = [parts - attached for parts in alternatives]
        incomplete = all(missing)
        decisions.append(dict(edge=edge, status='incomplete' if incomplete else 'complete',
            missing_by_alternative=[sorted(parts) for parts in missing] if incomplete else []))

    complete = sum(row['status'] == 'complete' for row in decisions)
    assessed = sum(row['status'] != 'missed' for row in decisions)
    planned = len(decisions)
    return dict(version=SUFFICIENCY_VERSION, planned=planned, assessed=assessed,
        complete=complete, incomplete=assessed - complete, missed=planned - assessed,
        complete_over_correct=complete / assessed if assessed else None,
        complete_over_planned=complete / planned if planned else None, targets=decisions)


def _attached_evidence(state: CanonicalState) -> dict[SemanticEdge, set[EvidencePair]]:
    names = {entity.id: entity.name for entity in state.entities}
    evidence = {item.id: (item.source_id, item.supporting_text) for item in state.evidence}
    attachments = {}
    for relationship in state.relationships:
        edge = _edge(names[relationship.source], relationship.type, names[relationship.target])
        attachments[edge] = {evidence[identity] for identity in relationship.evidence_ids}
    return attachments


def _verified_alternatives(item: SufficientEvidence, source_text: dict[str, str]) -> list[set[EvidencePair]]:
    alternatives = []
    for group in item.alternatives:
        parts = {(quote.source_id, quote.supporting_text) for quote in group}
        if not parts or len(parts) != len(group):
            raise ValueError('Sufficient sets require nonempty, distinct Source/quote pairs')
        if item.joint_only and len({source_id for source_id, _ in parts}) < 2:
            raise ValueError('Every joint-only alternative must use multiple Sources')
        if any(source_id not in source_text or not text.strip() or text not in source_text[source_id]
               for source_id, text in parts):
            raise ValueError('Sufficient evidence must occur verbatim in its specified Source')
        alternatives.append(parts)
    if any(left <= right for i, left in enumerate(alternatives) for j, right in enumerate(alternatives) if i != j):
        raise ValueError('Sufficient alternatives must be distinct and inclusion-minimal')
    return alternatives
