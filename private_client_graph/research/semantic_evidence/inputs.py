"""Freeze approved routes and verified attachments from a completed Benchmark v4 Run."""
import json
from collections.abc import Sequence
from fractions import Fraction
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from benchmark_v3.replay_evidence import EvidencePair, _attached_evidence
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.source import Source
from private_client_graph.research.artifacts import Bundle, checksum
from private_client_graph.research.benchmark_v4 import BenchmarkWorkload
from private_client_graph.research.benchmark_v4_run import VerifiedV4Run, evaluate_retained_run
from private_client_graph.research.evidence_quality import (
    EvidenceQuality, ProofMatch, match_proof_routes, report_evidence_quality,
)
from private_client_graph.research.live_accounting import retained_run_attempts

from .judging import Contract, JudgePacket, Quotation, exact_matches, make_packet

VERSION: Literal['pcg-semantic-evidence-equivalence'] = 'pcg-semantic-evidence-equivalence'
EXPECTED_TARGETS = 71
EXPECTED_MULTI_SOURCE = 30
ExactOutcome = Literal['complete', 'incomplete', 'missing_relationship', 'unavailable_graph']


class Baseline(Contract):
    exact_outcome: ExactOutcome
    best_exact_pair_coverage: float
    joint_only: bool


class Item(Contract):
    id: str = Field(pattern=r'^[a-f0-9]{64}$')
    edge: SemanticEdge
    family: str
    condition: str
    baseline: Baseline
    source_ids: dict[str, str]
    members: tuple[Quotation, ...]
    quotations: tuple[Quotation, ...]
    alternatives: tuple[tuple[str, ...], ...]

    @property
    def packet(self) -> JudgePacket | None:
        return make_packet(self.edge, self.members, self.quotations)

    @property
    def exact(self) -> dict[str, str]:
        return exact_matches(self.members, self.quotations)

    @model_validator(mode='after')
    def validate_evidence(self) -> Self:
        members = {member.id: member for member in self.members}
        if (not self.alternatives or any(not route or len(set(route)) != len(route) for route in self.alternatives)
                or {identity for route in self.alternatives for identity in route} != members.keys()):
            raise ValueError('Approved alternatives must cover the frozen required evidence members')
        for quotes in (self.members, self.quotations):
            if (len({quote.id for quote in quotes}) != len(quotes)
                    or len({(quote.source, quote.text) for quote in quotes}) != len(quotes)
                    or any(not quote.text.strip() for quote in quotes)):
                raise ValueError('Evidence IDs and Source–quotation pairs must be distinct and nonblank')
        if ({quote.source for quote in (*self.members, *self.quotations)} != self.source_ids.keys()
                or len(set(self.source_ids.values())) != len(self.source_ids)):
            raise ValueError('Quotation Source mapping must be complete and one-to-one')
        exact = set(self.exact)
        coverage = max(Fraction(len(exact.intersection(route)), len(route)) for route in self.alternatives)
        multi_source = all(len({members[identity].source for identity in route}) > 1 for route in self.alternatives)
        outcome = self.baseline.exact_outcome
        if (float(coverage) != self.baseline.best_exact_pair_coverage or self.baseline.joint_only != multi_source
                or (outcome == 'complete') != (coverage == 1)
                or bool(self.quotations) != (outcome in ('complete', 'incomplete'))):
            raise ValueError('Frozen exact matches differ from the deterministic baseline')
        return self


class AssessmentInputs(Contract):
    extractor_run: str = Field(pattern=r'^[a-f0-9]{32}$')
    extractor_manifest_sha256: str
    evidence_quality: EvidenceQuality
    targets: tuple[Item, ...]

    @property
    def dispatchable(self) -> tuple[Item, ...]:
        return tuple(sorted((item for item in self.targets if item.packet is not None), key=lambda item: item.id))


def extract_inputs(run_directory: Path, workload: BenchmarkWorkload) -> AssessmentInputs:
    """Verify the committed Run before freezing its qualified formal targets."""
    manifest_sha256 = checksum((run_directory / 'manifest.json').read_bytes())
    bundle = Bundle.open(run_directory)
    if getattr(bundle.plan, 'run_id', None) != run_directory.name:
        raise ValueError('Expected the original identified Benchmark v4 Run directory')
    attempts, authority_reasons = retained_run_attempts(bundle)
    if authority_reasons:
        raise ValueError('Retained Run attempt authority could not be verified')
    retained = evaluate_retained_run(bundle, workload, attempts=attempts)
    if retained.evaluation.summary.state != 'complete':
        raise ValueError('Semantic Evidence requires a complete Benchmark v4 Run')
    return AssessmentInputs(
        extractor_run=run_directory.name, extractor_manifest_sha256=manifest_sha256,
        evidence_quality=report_evidence_quality(retained.evaluation.qualified, workload.qualified, retained.results,
            mixed=retained.evaluation.summary).quality,
        targets=tuple(_retained_targets(workload, retained)),
    )


def _retained_targets(workload: BenchmarkWorkload, retained: VerifiedV4Run) -> list[Item]:
    targets = []
    for condition in workload.qualified:
        saved = condition.frozen.saved
        row = retained.evaluation.qualified.conditions[saved.condition]
        result = retained.results.get(saved.condition)
        state = result.state if result is not None else None
        if (state is not None) != (row.graph is not None):
            raise ValueError('Retained graph availability differs from the verified proof result')
        attached = _attached_evidence(state) if state is not None else {}
        for proof in match_proof_routes(saved, state):
            targets.append(_retained_item(condition.family, saved.condition, attached.get(proof.edge),
                           condition.frozen.sources, proof, has_graph=state is not None))
    return targets


def _retained_item(family: str, condition: str, pairs: set[EvidencePair] | None,
                   sources: Sequence[Source], proof: ProofMatch, *, has_graph: bool) -> Item:
    required = {pair for route in proof.routes for pair in route.required}
    actual = pairs if pairs is not None else set()
    _verify_quotations(required | actual, sources)
    labels = {source: f'S{index}' for index, source in enumerate(sorted({source for source, _ in required | actual}), 1)}
    members = _quotations(required, labels, 'M')
    member_ids = {pair: member.id for pair, member in zip(sorted(required), members, strict=True)}
    outcome: ExactOutcome
    if pairs is None:
        outcome = 'missing_relationship' if has_graph else 'unavailable_graph'
    else:
        outcome = 'complete' if proof.coverage == 1 else 'incomplete'
    return Item(
        id=checksum(json.dumps((condition, proof.edge), ensure_ascii=False, separators=(',', ':')).encode()),
        edge=proof.edge, family=family, condition=condition,
        baseline=Baseline(exact_outcome=outcome, best_exact_pair_coverage=float(proof.coverage),
                          joint_only=proof.joint_only),
        source_ids={label: source for source, label in labels.items()},
        members=members, quotations=_quotations(actual, labels, 'Q'),
        alternatives=tuple(tuple(member_ids[pair] for pair in route.required) for route in proof.routes),
    )


def _verify_quotations(pairs: set[EvidencePair], sources: Sequence[Source]) -> None:
    sources_by_id = {source.id: source.text for source in sources}
    if any(not text.strip() or text not in sources_by_id.get(source, '') for source, text in pairs):
        raise ValueError('An evidence quotation does not occur verbatim in its attributed Source')


def _quotations(pairs: set[EvidencePair], labels: dict[str, str], prefix: str) -> tuple[Quotation, ...]:
    return tuple(Quotation(id=f'{prefix}{index}', source=labels[source], text=text)
                 for index, (source, text) in enumerate(sorted(pairs), 1))
