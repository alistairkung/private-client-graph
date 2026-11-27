"""Versioned quality reporting over verified benchmark references and Run results."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Literal

from pydantic import BaseModel

from benchmark_v3.evaluation_protocol import Outcome, PlannedCondition, ProtocolResult
from benchmark_v3.replay_evidence import EvidencePair, _attached_evidence
from benchmark_v3.replay_manifest import SavedIdeal
from private_client_graph.evaluation import _edge
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.evaluation_result import SemanticEdge
from .benchmark_v4_scoring import BenchmarkV4Summary, DeliveredGraphMetrics, ObservationOrigin, _delivered
from .results import ResearchResult


@dataclass(frozen=True)
class ProofRouteMatch:
    required: tuple[EvidencePair, ...]
    matched: frozenset[EvidencePair]

    @property
    def coverage(self) -> Fraction:
        return Fraction(len(self.matched), len(self.required))


@dataclass(frozen=True)
class ProofMatch:
    edge: SemanticEdge
    joint_only: bool
    recovered: bool
    routes: tuple[ProofRouteMatch, ...]

    @property
    def coverage(self) -> Fraction:
        return max(route.coverage for route in self.routes)


def match_proof_routes(saved: SavedIdeal, state: CanonicalState | None) -> list[ProofMatch]:
    """Match distinct exact pairs on the same canonical edge, separately per route."""
    attachments = _attached_evidence(state) if state is not None else {}
    matches = []
    for proof in sorted(saved.sufficient_evidence, key=lambda proof: _edge(*proof.edge)):
        edge = _edge(*proof.edge)
        attached = attachments.get(edge, set())
        routes = []
        for alternative in proof.alternatives:
            required = {(item.source_id, item.supporting_text) for item in alternative}
            routes.append(ProofRouteMatch(tuple(sorted(required)), frozenset(required & attached)))
        matches.append(ProofMatch(edge, proof.joint_only, edge in attachments, tuple(routes)))
    return matches


class ProofRate(BaseModel):
    complete: int
    targets: int
    rate: float | None


class JointCoverage(BaseModel):
    targets: int
    mean: float | None


class EvidenceQuality(BaseModel):
    version: Literal['deterministic_evidence_quality_v1'] = 'deterministic_evidence_quality_v1'
    state: Literal['unmeasured', 'provisional', 'complete']
    scope_sha256: str
    scoring_sha256: str | None
    qualified_reference_sha256: str
    observation_origin: ObservationOrigin
    planned_inputs: int
    observed_inputs: int
    qualified_inputs: int
    observed_qualified_inputs: int
    expected_relationships: int
    observed_proof_targets: int
    observed_joint_targets: int
    combined_graph: DeliveredGraphMetrics | None
    qualified_graph: DeliveredGraphMetrics | None
    complete_proof: ProofRate
    joint_only_complete_proof: ProofRate
    joint_only_coverage: JointCoverage


@dataclass(frozen=True)
class JointTarget:
    condition: str
    outcome: Outcome
    proof: ProofMatch

    def status(self) -> Literal['complete', 'incomplete', 'missed', 'without_graph', 'not_attempted']:
        if self.outcome != 'scored':
            return 'not_attempted' if self.outcome == 'not_attempted' else 'without_graph'
        if not self.proof.recovered:
            return 'missed'
        return 'complete' if self.proof.coverage == 1 else 'incomplete'

    def report(self) -> dict:
        return {
            'condition': self.condition, 'outcome': self.outcome, 'edge': self.proof.edge, 'status': self.status(),
            'coverage': None if self.outcome == 'not_attempted' else float(self.proof.coverage),
            'alternatives': [
                {'matched': len(route.matched), 'required': len(route.required),
                 'members': [{'source_id': pair[0], 'quotation': pair[1], 'matched': pair in route.matched}
                             for pair in route.required]}
                for route in self.proof.routes
            ],
        }


@dataclass(frozen=True)
class EvidenceQualityReport:
    quality: EvidenceQuality
    joint_targets: tuple[JointTarget, ...]


def report_evidence_quality(
    protocol: ProtocolResult,
    planned: Sequence[PlannedCondition],
    results: Mapping[str, ResearchResult],
    *,
    mixed: BenchmarkV4Summary | None = None,
) -> EvidenceQualityReport:
    """Project scores without changing any frozen policy or stored result."""
    cohort = protocol.cohort
    observed = [row for row in protocol.conditions.values() if row.outcome != 'not_attempted']
    observed_proofs = sum(row.planned_proofs for row in observed)
    joint = _joint_targets(protocol, planned, results)
    observed_joint = sum(target.outcome != 'not_attempted' for target in joint)
    if len(joint) != cohort.planned_joint_proofs:
        raise ValueError('Joint-only reference count differs from the verified protocol')
    coverage_sum = sum((target.proof.coverage for target in joint), Fraction(0))
    combined = mixed.combined if mixed else None
    qualified = None
    if observed:
        qualified = mixed.qualified if mixed else _delivered(list(protocol.conditions.values()))
    quality = EvidenceQuality(
        state=mixed.state if mixed else _qualified_state(len(observed), cohort.planned_conditions),
        scope_sha256=mixed.scope_sha256 if mixed else protocol.scope.benchmark_sha256,
        scoring_sha256=mixed.scoring_sha256 if mixed else None,
        qualified_reference_sha256=protocol.scope.benchmark_sha256,
        observation_origin=protocol.scope.observation_origin,
        planned_inputs=cohort.planned_conditions + (1 if mixed else 0),
        observed_inputs=combined.inputs - combined.outcomes.get('not_attempted', 0) if combined else len(observed),
        qualified_inputs=cohort.planned_conditions, observed_qualified_inputs=len(observed),
        expected_relationships=cohort.all_conditions.tp + cohort.all_conditions.fn,
        observed_proof_targets=observed_proofs, observed_joint_targets=observed_joint,
        combined_graph=combined, qualified_graph=qualified,
        complete_proof=ProofRate(complete=cohort.complete_proofs, targets=cohort.planned_proofs,
            rate=cohort.proof_completion_rate if observed_proofs else None),
        joint_only_complete_proof=ProofRate(complete=cohort.complete_joint_proofs, targets=cohort.planned_joint_proofs,
            rate=cohort.joint_proof_completion_rate if observed_joint else None),
        joint_only_coverage=JointCoverage(targets=len(joint), mean=float(coverage_sum / len(joint)) if observed_joint else None),
    )
    return EvidenceQualityReport(quality, joint)


def _joint_targets(protocol: ProtocolResult, planned: Sequence[PlannedCondition],
                   results: Mapping[str, ResearchResult]) -> tuple[JointTarget, ...]:
    targets: list[JointTarget] = []
    for item in planned:
        saved = item.frozen.saved
        row = protocol.conditions[saved.condition]
        retained = results.get(saved.condition)
        state = retained.state if retained is not None else None
        if (state is not None) != (row.outcome == 'scored'):
            raise ValueError('Retained graph availability differs from the verified protocol')
        matches = [match for match in match_proof_routes(saved, state) if match.joint_only]
        if sum(match.coverage == 1 for match in matches) != row.complete_joint_proofs:
            raise ValueError('Exact evidence coverage differs from verified joint proof completion')
        targets.extend(JointTarget(saved.condition, row.outcome, match) for match in matches)
    return tuple(targets)


def _qualified_state(observed: int, planned: int) -> Literal['unmeasured', 'provisional', 'complete']:
    if not observed:
        return 'unmeasured'
    return 'complete' if observed == planned else 'provisional'
