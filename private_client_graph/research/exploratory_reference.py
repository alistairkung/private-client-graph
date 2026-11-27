"""Private inspection of an exploratory consensus reference, outside scored runs."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from benchmark_v3.exploratory_consensus import Citation
from private_client_graph.evaluation import _edge
from private_client_graph.models.source import Source
from private_client_graph.models.types import RelationshipType
from private_client_graph.research.artifacts import checksum


class ReferenceContract(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)


class VoteCounts(ReferenceContract):
    support: int = Field(ge=0, le=10)
    reject: int = Field(ge=0, le=10)
    uncertain: int = Field(ge=0, le=10)
    omitted: int = Field(ge=0, le=10)


class InspectedRoute(ReferenceContract):
    approved: bool
    members: list[Citation] = Field(min_length=1)


class InspectedRelationship(ReferenceContract):
    source: str
    predicate: RelationshipType
    target: str
    counts: VoteCounts
    evidence_decision: Literal['supported', 'unresolved', 'below_majority']
    evidence_reason: str | None
    routes: list[InspectedRoute]

    @model_validator(mode='after')
    def verify_dispositions(self) -> 'InspectedRelationship':
        counts = self.counts
        if counts.support + counts.reject + counts.uncertain + counts.omitted != 10:
            raise ValueError('An exploratory proposition must account for ten votes.')
        if ((counts.support >= 6) != (self.evidence_decision != 'below_majority')
                or (self.evidence_decision == 'supported') != any(route.approved for route in self.routes)):
            raise ValueError('An exploratory proposition has an incompatible evidence disposition.')
        return self


class ConsensusReference(ReferenceContract):
    schema_version: Literal[1]
    kind: Literal['exploratory_ai_consensus']
    workload_id: str
    source_file_sha256: str
    cutoff: str
    reviewer_count: Literal[10]
    majority: Literal[6]
    official_benchmark_eligible: Literal[False]
    relationships: list[InspectedRelationship]
    limitations: list[str]
    reviewer_open_questions: list[str]


def read_reference(
    path: Path, digest: str, *, workload_id: str, source_file_sha256: str, sources: list[Source],
) -> ConsensusReference:
    if (not path.is_absolute() or path.resolve() != path or not path.is_file()
            or path.stat().st_mode & 0o077 or path.parent.stat().st_mode & 0o077):
        raise ValueError('The exploratory reference must be a private regular file.')
    raw = path.read_bytes()
    if checksum(raw) != digest:
        raise ValueError('The exploratory reference differs from its frozen commitment.')
    reference = ConsensusReference.model_validate_json(raw)
    if (reference.workload_id, reference.source_file_sha256) != (workload_id, source_file_sha256):
        raise ValueError('The exploratory reference and Source release do not match.')
    edges = {_edge(row.source, row.predicate, row.target) for row in reference.relationships}
    if len(edges) != len(reference.relationships):
        raise ValueError('The exploratory reference repeats an ontology proposition.')
    text = {source.id: source.text for source in sources}
    if any(
        not member.quote.strip() or member.quote not in text.get(member.source_id, '')
        for row in reference.relationships for route in row.routes for member in route.members
    ):
        raise ValueError('The exploratory reference contains an invalid Source body quotation.')
    return reference
