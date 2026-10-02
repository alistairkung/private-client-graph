"""Deterministic semantic-edge and approved-provenance scoring for Case 01."""

from private_client_graph.models import CanonicalGraph, EvaluationResult, GroundTruth
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.types import RelationshipType


def _edge(source: str, kind: RelationshipType, target: str) -> SemanticEdge:
    if kind in {"spouse_of", "sibling_of"}:
        source, target = sorted((source, target))
    return source, kind, target


def evaluate_graph(prediction: CanonicalGraph, ground_truth: GroundTruth) -> EvaluationResult:
    """Compare exact names and approved quotes, independent of model or ID values.

    All reference integrity is checked before scoring. Repeated semantic edges
    count once and pool their evidence. Every zero denominator yields 0.0,
    including provenance accuracy when there are no true-positive edges.
    """
    predicted_names, truth_names, evidence = _validated_lookups(prediction, ground_truth)
    predicted = _resolve_prediction(prediction, predicted_names, evidence)
    approved = _resolve_ground_truth(ground_truth, truth_names)

    predicted_edges, truth_edges = set(predicted), set(approved)
    true_positives = predicted_edges & truth_edges
    false_positives = predicted_edges - truth_edges
    false_negatives = truth_edges - predicted_edges
    passes = _score_provenance(true_positives, predicted, approved)

    return _build_evaluation_result(true_positives, false_positives, false_negatives, passes)


def _validated_lookups(
    prediction: CanonicalGraph, ground_truth: GroundTruth
) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    # Check all duplicate IDs before resolving either graph's relationships.
    predicted_names = {entity.id: entity.name for entity in prediction.entities}
    truth_names = {entity.id: entity.name for entity in ground_truth.entities}
    evidence = {item.id: item.supporting_text for item in prediction.evidence}
    for label, lookup, items in (
        ("predicted entity", predicted_names, prediction.entities),
        ("ground-truth entity", truth_names, ground_truth.entities),
        ("predicted evidence", evidence, prediction.evidence),
    ):
        if len(lookup) != len(items):
            raise ValueError(f"Duplicate {label} ID")

    return predicted_names, truth_names, evidence


def _resolve_prediction(
    prediction: CanonicalGraph, predicted_names: dict[str, str], evidence: dict[str, str]
) -> dict[SemanticEdge, set[str]]:
    predicted: dict[SemanticEdge, set[str]] = {}
    for relationship in prediction.relationships:
        try:
            source = predicted_names[relationship.source]
            target = predicted_names[relationship.target]
        except KeyError as error:
            raise ValueError(f"Unresolved predicted entity reference: {error.args[0]!r}") from error
        try:
            quotes = {evidence[evidence_id] for evidence_id in relationship.evidence_ids}
        except KeyError as error:
            raise ValueError(f"Unresolved predicted evidence reference: {error.args[0]!r}") from error
        predicted.setdefault(_edge(source, relationship.type, target), set()).update(quotes)

    return predicted


def _resolve_ground_truth(
    ground_truth: GroundTruth, truth_names: dict[str, str]
) -> dict[SemanticEdge, set[str]]:
    approved: dict[SemanticEdge, set[str]] = {}
    for relationship in ground_truth.relationships:
        try:
            source = truth_names[relationship.source]
            target = truth_names[relationship.target]
        except KeyError as error:
            raise ValueError(f"Unresolved ground-truth entity reference: {error.args[0]!r}") from error
        approved.setdefault(_edge(source, relationship.type, target), set()).update(
            relationship.approved_evidence
        )

    return approved


def _score_provenance(
    true_positives: set[SemanticEdge],
    predicted: dict[SemanticEdge, set[str]],
    approved: dict[SemanticEdge, set[str]],
) -> set[SemanticEdge]:
    return {edge for edge in true_positives if predicted[edge] & approved[edge]}


def _build_evaluation_result(
    true_positives: set[SemanticEdge],
    false_positives: set[SemanticEdge],
    false_negatives: set[SemanticEdge],
    passes: set[SemanticEdge],
) -> EvaluationResult:
    failures = true_positives - passes
    tp, fp, fn = len(true_positives), len(false_positives), len(false_negatives)
    return EvaluationResult(
        tp=tp, fp=fp, fn=fn,
        precision=tp / (tp + fp) if tp + fp else 0.0,
        recall=tp / (tp + fn) if tp + fn else 0.0,
        f1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
        true_positive_edges=sorted(true_positives),
        false_positive_edges=sorted(false_positives),
        false_negative_edges=sorted(false_negatives),
        provenance_passed=len(passes), provenance_failed=len(failures),
        provenance_accuracy=len(passes) / tp if tp else 0.0,
        provenance_passes=sorted(passes), provenance_failures=sorted(failures),
    )
