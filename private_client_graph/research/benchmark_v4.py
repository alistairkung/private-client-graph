"""Verified Benchmark v4 workload and private reference loading."""
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from benchmark_v3.commissioning import trusted_bytes
from benchmark_v3.evaluation_protocol import GRAPH_SCORER, PROTOCOL_VERSION, PlannedCondition
from benchmark_v3.replay_manifest import VerifiedFamily
from benchmark_v3.retained_evaluation import BASELINE_INVENTORY_SHA256, load_admitted_families
from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.graph import build_canonical_state
from private_client_graph.models import ExtractionResult, GroundTruth, SourcedExtractionResult
from private_client_graph.models.canonical_state import CanonicalState
from private_client_graph.models.ground_truth_relationship import GroundTruthRelationship
from private_client_graph.models.sourced_extraction import SourcedRelationshipCandidate
from private_client_graph.models.source import Source
from .artifacts import checksum
from .exploratory_reference import ConsensusReference, read_reference
from .exploratory_release import Digest, ExploratoryRelease
from .inputs import ResearchInput

Methodology = Literal['original_qualification', 'consensus_adjudication']


class QualifiedCohort(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    methodology: Literal['original_qualification']
    evidence_protocol: Literal['benchmark_v3_evaluation_v1']
    matter_count: Literal[19]
    input_count: Literal[34]
    public_register: Literal['admissions/2026-11-24.json']
    public_register_sha256: Digest
    private_register_sha256: Digest
    historical_archive_inventory_sha256: Digest


class ConsensusInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    methodology: Literal['consensus_adjudication']
    evidence_protocol: Literal['adjudicated_citation_overlap_v1']
    matter: Literal['U']
    input: Literal['u8']
    source_count: Literal[65]
    release_id: str
    release_manifest_sha256: Digest
    source_file_sha256: Digest
    source_array_sha256: Digest
    reference_sha256: Digest
    reference_freeze_sha256: Digest
    reviewer_count: Literal[10]
    support_threshold: Literal[6]
    unanimous_relationships: Literal[6]
    adjudicated_relationships: Literal[6]
    zero_support_propositions: Literal[4]
    limitation: str


class BenchmarkDefinition(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    version: Literal['pcg-benchmark-v4']
    matter_count: Literal[20]
    input_count: Literal[35]
    graph_scorer: Literal['semantic_edges_v1']
    qualified: QualifiedCohort
    consensus: ConsensusInput


class EvaluationInput(BaseModel):
    id: str
    sample_id: str
    matter: str
    reference_methodology: Methodology
    source_count: int


class BenchmarkRoster(BaseModel):
    definition: BenchmarkDefinition
    sha256: Digest
    inputs: list[EvaluationInput]


@dataclass(frozen=True)
class BenchmarkWorkload:
    roster: BenchmarkRoster
    family_details: dict[str, VerifiedFamily]
    qualified: tuple[PlannedCondition, ...]
    consensus: ConsensusReference
    consensus_state: CanonicalState
    inputs: tuple[ResearchInput, ...]

    def require_plan_inputs(self, identity: str, inputs: list[ResearchInput]) -> None:
        if identity != self.roster.sha256 or tuple(inputs) != self.inputs:
            raise ValueError('Run inputs differ from the frozen Benchmark v4 workload')


def load_roster() -> BenchmarkRoster:
    raw = Path(__file__).with_name('benchmark-v4.json').read_bytes()
    definition = BenchmarkDefinition.model_validate_json(raw)
    cohort = definition.qualified
    register = trusted_bytes(cohort.public_register)
    if (checksum(register) != cohort.public_register_sha256
            or cohort.historical_archive_inventory_sha256 != BASELINE_INVENTORY_SHA256
            or definition.graph_scorer != GRAPH_SCORER or cohort.evidence_protocol != PROTOCOL_VERSION):
        raise ValueError('Benchmark v4 qualified cohort commitments differ')
    public = json.loads(register)
    if public['private_register_sha256'] != cohort.private_register_sha256:
        raise ValueError('Benchmark v4 private admission register commitment differs')
    inputs = [
        EvaluationInput(id=condition, sample_id=f'v4_{condition.lower()}', matter=family['family'],
                        reference_methodology=cohort.methodology,
                        source_count=source_count)
        for family in public['families']
        for condition, source_count in zip(family['conditions'], family['source_counts'], strict=True)
    ]
    if len(inputs) != cohort.input_count or len({item.matter for item in inputs}) != cohort.matter_count:
        raise ValueError('Benchmark v4 qualified roster size differs')
    u8 = definition.consensus
    inputs.append(EvaluationInput(id=u8.input, sample_id='v4_u8', matter=u8.matter,
                                  reference_methodology=u8.methodology, source_count=u8.source_count))
    if (len({item.sample_id for item in inputs}) != definition.input_count
            or len({item.matter for item in inputs}) != definition.matter_count):
        raise ValueError('Benchmark v4 roster identities differ')
    return BenchmarkRoster(definition=definition, sha256=checksum(raw), inputs=inputs)


def configured_custody() -> Path | None:
    directory = os.getenv('PCG_BENCHMARK_V4_CUSTODY')
    return Path(directory) if directory else None


def load_workload(custody: Path) -> BenchmarkWorkload:
    """Read the exact frozen Sources and references via their separate custody paths."""
    roster = load_roster()
    u8 = roster.definition.consensus
    if not custody.is_absolute() or custody.resolve() != custody or custody.stat().st_mode & 0o077:
        raise ValueError('Benchmark v4 requires a private absolute custody directory')
    admissions = custody / 'admissions-2026-11-24' / 'ADMISSIONS.json'
    families = load_admitted_families(admissions)
    qualified = tuple(PlannedCondition(item.matter, families[item.matter].conditions[item.id])
                      for item in roster.inputs[:-1])
    release = ExploratoryRelease(custody / u8.release_id, u8.release_manifest_sha256).read()
    if (release.manifest.workload_id != u8.release_id
            or release.manifest.source_file_sha256 != u8.source_file_sha256
            or release.manifest.source_array_sha256 != u8.source_array_sha256):
        raise ValueError('Benchmark v4 U8 Source commitments differ')
    sources = [Source.model_validate(source.model_dump()) for source in release.sources]
    reference = _load_consensus_reference(custody / '2026-11-27-u8-consensus', u8, sources)
    state = _consensus_state(reference, sources)
    graph = reconstruct_graph(state)
    truth = GroundTruth(entities=graph.entities, relationships=[
        GroundTruthRelationship(source=row.source, type=row.type, target=row.target, approved_evidence=[])
        for row in graph.relationships
    ])
    inputs = [_research_input(item, planned.frozen.sources, planned.frozen.saved.truth,
            planned.frozen.sources_sha256, planned.frozen.case_sha256)
        for item, planned in zip(roster.inputs[:-1], qualified, strict=True)]
    inputs.append(_research_input(roster.inputs[-1], sources, truth,
                                 u8.source_file_sha256, u8.reference_sha256))
    return BenchmarkWorkload(roster, families, qualified, reference, state, tuple(inputs))


def _load_consensus_reference(directory: Path, u8: ConsensusInput, sources: list[Source]) -> ConsensusReference:
    path = directory / 'REFERENCE-FREEZE.json'
    if (directory.resolve() != directory or directory.stat().st_mode & 0o077
            or path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o077):
        raise ValueError('Benchmark v4 U8 requires private reference custody')
    raw = path.read_bytes()
    if checksum(raw) != u8.reference_freeze_sha256:
        raise ValueError('Benchmark v4 U8 reference freeze commitment differs')
    freeze = json.loads(raw)
    if (freeze['reference_sha256'], freeze['source_file_sha256'], freeze['reader_count']) != (
            u8.reference_sha256, u8.source_file_sha256, u8.reviewer_count):
        raise ValueError('Benchmark v4 U8 reference freeze and manifest differ')
    reference = read_reference(directory / 'WORKBENCH-REFERENCE.json', u8.reference_sha256,
        workload_id=u8.release_id, source_file_sha256=u8.source_file_sha256, sources=list(sources))
    if (reference.majority != u8.support_threshold
            or sum(row.counts.support == u8.reviewer_count for row in reference.relationships)
                != u8.unanimous_relationships
            or sum(row.counts.support >= u8.support_threshold for row in reference.relationships)
                != u8.adjudicated_relationships
            or sum(row.evidence_decision == 'supported' for row in reference.relationships)
                != u8.adjudicated_relationships
            or sum(row.counts.support == 0 for row in reference.relationships)
                != u8.zero_support_propositions
            or len(reference.relationships) != u8.adjudicated_relationships + u8.zero_support_propositions):
        raise ValueError('Benchmark v4 U8 reference dispositions differ')
    return reference


def _consensus_state(reference: ConsensusReference, sources: list[Source]) -> CanonicalState:
    return build_canonical_state([
        SourcedRelationshipCandidate(source_name=row.source, relationship_type=row.predicate,
            target_name=row.target, source_id=member.source_id, supporting_text=member.quote)
        for row in reference.relationships if row.evidence_decision == 'supported'
        for route in row.routes if route.approved for member in route.members
    ], sources=sources)


def _research_input(item: EvaluationInput, sources: list[Source], truth: GroundTruth,
                    source_digest: str, reference_digest: str) -> ResearchInput:
    if len(sources) != item.source_count:
        raise ValueError('Benchmark v4 frozen Source count differs from its roster')
    # The existing fresh extraction runner expects a template. Its empty saved
    # extraction is never executed. Truth and commitments are scorer-side fields.
    return ResearchInput(sample_id=item.sample_id, case_id=item.matter, cohort='authored',
        source=sources[0].text, sources=sources, truth=truth,
        extraction=ExtractionResult(relationships=[]),
        sourced_extraction=SourcedExtractionResult(relationships=[]),
        origin_hashes={'sources': source_digest, 'reference': reference_digest})
