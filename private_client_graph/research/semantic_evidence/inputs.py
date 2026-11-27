"""Build the fixed formal-proof roster from verified Benchmark v4 attachments."""
import json
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import Field

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

from .judging import Contract, JudgePacket, Quotation, make_packet

EXTRACTOR_RUN: Literal['ee1defcdc6f85a3ba12efcfc78b70da2'] = 'ee1defcdc6f85a3ba12efcfc78b70da2'
EXTRACTOR_MANIFEST_SHA256 = 'bedcfd11c136a1070a79eb38a465a45f4af8554e21a6162b8ad1b124ea44273b'
VERSION: Literal['pcg-semantic-evidence-v1'] = 'pcg-semantic-evidence-v1'
EXPECTED_TARGETS = 71
EXPECTED_RECOVERED = 67
CONTROL_COUNT = 2
ExactOutcome = Literal['complete', 'incomplete', 'missing_relationship', 'unavailable_graph']


class Baseline(Contract):
    exact_outcome: ExactOutcome
    best_exact_pair_coverage: float
    joint_only: bool
    matches_any_approved_pair: tuple[str, ...] = ()
    approved_route_source_set_present: bool | None = None


class Item(Contract):
    id: str = Field(pattern=r'^[a-f0-9]{64}$')
    edge: SemanticEdge
    packet: JudgePacket | None = None
    source_ids: dict[str, str] = Field(default_factory=dict)
    family: str | None = None
    condition: str | None = None
    baseline: Baseline | None = None
    control: str | None = None


class AssessmentInputs(Contract):
    extractor_run: str = Field(default=EXTRACTOR_RUN, pattern=r'^[a-f0-9]{32}$')
    extractor_manifest_sha256: str
    evidence_quality: EvidenceQuality
    targets: tuple[Item, ...]
    controls: tuple[Item, ...]

    @property
    def dispatchable(self) -> tuple[Item, ...]:
        return tuple(sorted((item for item in (*self.targets, *self.controls) if item.packet is not None),
                            key=lambda item: item.id))


def extract_inputs(run_directory: Path, workload: BenchmarkWorkload) -> AssessmentInputs:
    """Verify the committed Run before freezing its qualified formal targets."""
    manifest_sha256 = checksum((run_directory / 'manifest.json').read_bytes())
    bundle = Bundle.open(run_directory)
    if getattr(bundle.plan, 'run_id', None) != run_directory.name:
        raise ValueError('Expected the original identified Benchmark v4 Run directory')
    attempts, authority_reasons = retained_run_attempts(bundle)
    if authority_reasons:
        raise ValueError('Retained Extractor v1 attempt authority could not be verified')
    retained = evaluate_retained_run(bundle, workload, attempts=attempts)
    if retained.evaluation.summary.state != 'complete':
        raise ValueError('Semantic Evidence requires a complete Benchmark v4 Run')
    protocol = retained.evaluation.qualified
    return AssessmentInputs(
        extractor_run=run_directory.name, extractor_manifest_sha256=manifest_sha256,
        evidence_quality=report_evidence_quality(protocol, workload.qualified, retained.results,
            mixed=retained.evaluation.summary).quality,
        targets=tuple(_retained_targets(workload, retained)),
        controls=_controls(),
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
            targets.append(_retained_item(condition.family, saved.condition,
                attached.get(proof.edge), condition.frozen.sources, proof, has_graph=state is not None))
    return targets


def _retained_item(family: str, condition: str, pairs: set[EvidencePair] | None,
                   sources: Sequence[Source], proof: ProofMatch, *, has_graph: bool) -> Item:
    identity = _item_id(condition, proof.edge)
    if pairs is None:
        outcome: ExactOutcome = 'missing_relationship' if has_graph else 'unavailable_graph'
        return Item(id=identity, edge=proof.edge, family=family, condition=condition,
            baseline=Baseline(exact_outcome=outcome, best_exact_pair_coverage=0, joint_only=proof.joint_only))
    quotes, source_ids, quote_ids = _verified_quotes(pairs, sources)
    return Item(id=identity, edge=proof.edge, packet=make_packet(proof.edge, quotes), source_ids=source_ids,
                family=family, condition=condition, baseline=_baseline(proof, pairs, quote_ids))


def _baseline(proof: ProofMatch, pairs: set[EvidencePair], quote_ids: dict[EvidencePair, str]) -> Baseline:
    matched_ids = {quote_ids[pair] for route in proof.routes for pair in route.matched}
    attached_sources = {source for source, _ in pairs}
    routes_covered = any({source for source, _ in route.required} <= attached_sources for route in proof.routes)
    return Baseline(exact_outcome='complete' if proof.coverage == 1 else 'incomplete',
        best_exact_pair_coverage=float(proof.coverage), joint_only=proof.joint_only,
        matches_any_approved_pair=tuple(sorted(matched_ids)), approved_route_source_set_present=routes_covered)


def _verified_quotes(pairs: set[EvidencePair], sources: Sequence[Source],
                     ) -> tuple[tuple[Quotation, ...], dict[str, str], dict[EvidencePair, str]]:
    sources_by_id = {source.id: source.text for source in sources}
    if not pairs or any(not text.strip() or text not in sources_by_id.get(source, '') for source, text in pairs):
        raise ValueError('An attached quotation is missing or does not occur verbatim in its attributed Source')
    labels = {source: f'S{index}' for index, source in enumerate(sorted({source for source, _ in pairs}), 1)}
    quote_ids = {pair: f'Q{index}' for index, pair in enumerate(sorted(pairs), 1)}
    quotes = tuple(Quotation(id=identity, source=labels[source], text=text)
                   for (source, text), identity in quote_ids.items())
    return quotes, {label: source for source, label in labels.items()}, quote_ids


def _item_id(*parts: object) -> str:
    return checksum(json.dumps((VERSION, *parts), ensure_ascii=False, separators=(',', ':')).encode())


def _controls() -> tuple[Item, ...]:
    trustee: SemanticEdge = ('Nora Vale', 'trustee_of', 'Hearth Trust')
    return (
        _control('post_cutoff', trustee, (
            'This deed appoints Nora Vale as trustee of the Hearth Trust with effect from 1 July 2040.',),
            cutoff=date(2040, 6, 30)),
        _control('conflicting_authority', trustee, (
            'A board summary says Nora Vale is the trustee of the Hearth Trust.',
            'The signed operative deed names only Cora Rill as trustee of the Hearth Trust and expressly '
            'supersedes this board summary. Nora Vale has no trustee appointment under the deed.')),
    )


def _control(label: str, edge: SemanticEdge, texts: tuple[str, ...], *, cutoff: date | None = None) -> Item:
    sources = [Source(id=f'control-{i}', text=text, title='Synthetic control') for i, text in enumerate(texts, 1)]
    quotes, source_ids, _ = _verified_quotes({(source.id, source.text) for source in sources}, sources)
    return Item(id=_item_id('control', label), edge=edge, packet=make_packet(edge, quotes, cutoff=cutoff),
                source_ids=source_ids, control=label)
