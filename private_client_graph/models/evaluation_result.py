from pydantic import BaseModel

from .types import RelationshipType


SemanticEdge = tuple[str, RelationshipType, str]


class EvaluationResult(BaseModel):
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    true_positive_edges: list[SemanticEdge]
    false_positive_edges: list[SemanticEdge]
    false_negative_edges: list[SemanticEdge]
    provenance_passed: int
    provenance_failed: int
    provenance_accuracy: float
    provenance_passes: list[SemanticEdge]
    provenance_failures: list[SemanticEdge]
