"""Benchmark v2 eligibility for ordinary quotation and Source attribution reporting."""
import hashlib
import json
from pathlib import Path
from typing import Any

from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.evaluation import _edge, _resolve_ground_truth, evaluate_graph
from private_client_graph.models import GroundTruth
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.research.benchmark_decisions import DecisionTargets
from private_client_graph.research.source_attribution import SourceEvidenceApproval, diagnose_source_attribution

VERSION = 'benchmark_v2_evidence_v1'


def verify_evidence_policy() -> None:
    """Reject scorer or protocol drift before producing a v2 report for either arm."""
    study = Path(__file__).resolve().parent
    lock = json.loads((study / 'development.lock.json').read_bytes())
    paths = {study / name: lock['documents'][name] for name in ('evidence-policy-v1.md', 'evidence_policy.py')}
    scorer = 'private_client_graph/research/benchmark_decisions.py'
    paths[study.parent / scorer] = lock['scorers'][scorer]
    for path, digest in paths.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f'Evidence policy differs from the frozen {path.name}')


def _eligible_truth(truth: GroundTruth, exempt: set[SemanticEdge]) -> GroundTruth:
    names = {entity.id: entity.name for entity in truth.entities}
    approvals = _resolve_ground_truth(truth, names)
    unapproved_edges = {edge for edge, quotations in approvals.items() if not quotations}
    if unapproved_edges != exempt:
        raise ValueError('Only explicitly joint-only targets may lack ordinary approved quotations')
    eligible = [rel for rel in truth.relationships if _edge(names[rel.source], rel.type, names[rel.target]) not in exempt]
    return GroundTruth(entities=truth.entities, relationships=eligible)


def ordinary_evidence(state: CanonicalState, truth: GroundTruth, labels: DecisionTargets,
                      approval: SourceEvidenceApproval | None) -> dict[str, Any]:
    """Apply the historical scorers to eligible edges on the actual retained graph."""
    exempt = {_edge(*item.edge) for item in labels.sufficiency if item.joint_only}
    if exempt:
        if approval is not None or labels.ordinary_source_approval is None:
            raise ValueError('Joint-only annotations require one frozen eligible-edge Source approval')
        approval = labels.ordinary_source_approval
    elif labels.ordinary_source_approval is not None:
        raise ValueError('Eligible-edge approval overrides require a joint-only target')

    eligible = _eligible_truth(truth, exempt)
    score = evaluate_graph(reconstruct_graph(state), eligible)
    attribution = diagnose_source_attribution(state, eligible, approval) if approval is not None else None
    return dict(version=VERSION, not_applicable=sorted(exempt), quotation=dict(
        assessed=score.tp, passed=score.provenance_passed, failed=score.provenance_failed,
        accuracy=None if exempt and not eligible.relationships else score.provenance_accuracy,
        passes=score.provenance_passes, failures=score.provenance_failures),
        source_attribution=attribution.model_dump(mode='json') if attribution is not None else None)
