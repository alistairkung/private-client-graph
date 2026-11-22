"""Verify the frozen inputs and matched controls for Benchmark v3 Family A."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, model_validator

from private_client_graph.evaluation import _edge
from private_client_graph.graph import ENDPOINT_TYPES
from private_client_graph.models import GroundTruth, SourcedExtractionResult
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.models.ground_truth_relationship import GroundTruthRelationship
from private_client_graph.models.source import Source
from private_client_graph.research.artifacts import checksum
from private_client_graph.research.retained_inputs import value_digest
from private_client_graph.research.source_attribution import (
    ApprovedSourceEvidence, SourceEvidenceApproval, SourceEvidenceRelationship,
)


ConditionId = Literal['A0', 'A1', 'A2']
CONDITIONS: tuple[ConditionId, ...] = ('A0', 'A1', 'A2')
Sha256 = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
_SOURCES = TypeAdapter(list[Source])


class LiteralEdit(BaseModel):
    model_config = ConfigDict(extra='forbid')
    source_id: str = Field(min_length=1)
    before: str = Field(min_length=1)
    after: str = Field(min_length=1)


class TrusteeSwitch(LiteralEdit):
    removed: list[SemanticEdge] = Field(min_length=1, max_length=1)
    added: list[SemanticEdge] = Field(min_length=1, max_length=1)

    @model_validator(mode='after')
    def verify_switch(self) -> 'TrusteeSwitch':
        ((successor, old_role, trust),) = self.removed
        ((incumbent, new_role, new_trust),) = self.added
        if old_role != 'trustee_of' or new_role != old_role or new_trust != trust or successor == incumbent:
            raise ValueError('A2 must switch the trustee on the same trust')
        if self.before == self.after:
            raise ValueError('A2 must change the precommitted literal field')
        return self


class FamilyManifest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[1]
    family: Literal['A']
    freeze_sha256: Sha256
    conditions: dict[ConditionId, Sha256]
    contrast: TrusteeSwitch


class SourceFreeze(BaseModel):
    # The custodian's freeze also records provenance outside the replay contract.
    order: dict[ConditionId, list[str]]
    sources_sha256: dict[ConditionId, Sha256]
    intervention: LiteralEdit
    source_commitments: dict[ConditionId, dict[str, dict[str, Sha256]]]
    declared_removed: list[SemanticEdge]
    declared_added: list[SemanticEdge]


class SufficientEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    edge: SemanticEdge
    joint_only: bool = False
    alternatives: list[list[ApprovedSourceEvidence]] = Field(min_length=1)


class SavedIdeal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    condition: ConditionId
    truth: GroundTruth
    source_approval: SourceEvidenceApproval
    ideal: SourcedExtractionResult
    sufficient_evidence: list[SufficientEvidence]


@dataclass(frozen=True)
class VerifiedCondition:
    saved: SavedIdeal
    sources: list[Source]
    case_sha256: str
    sources_sha256: str
    annotation_sha256: dict[str, str]

    @property
    def sample_id(self) -> str:
        return f'benchmark_v3_{self.saved.condition.lower()}'


@dataclass(frozen=True)
class VerifiedFamily:
    manifest_sha256: str
    freeze_sha256: str
    conditions: dict[ConditionId, VerifiedCondition]
    contrast: TrusteeSwitch
    unaffected: set[SemanticEdge]


def load_family(manifest_path: Path) -> VerifiedFamily:
    """Bind the saved ideals and ordered Sources before verifying either contrast."""
    manifest_bytes = manifest_path.read_bytes()
    manifest = FamilyManifest.model_validate(_read_json(manifest_bytes))
    root = manifest_path.parent
    freeze = SourceFreeze.model_validate(_read_json(_verified_bytes(root / 'freeze.json', manifest.freeze_sha256)))
    if any(set(entries) != set(CONDITIONS) for entries in (manifest.conditions, freeze.order, freeze.sources_sha256, freeze.source_commitments)):
        raise ValueError('The manifest and Source freeze must cover exactly A0, A1 and A2')
    if freeze.intervention.model_dump() != manifest.contrast.model_dump(include={'source_id', 'before', 'after'}):
        raise ValueError('A2 literal edit differs from the preblind Source freeze')

    if (freeze.declared_removed, freeze.declared_added) != (manifest.contrast.removed, manifest.contrast.added):
        raise ValueError('Trustee switch differs from the preblind declaration')

    conditions = {identity: _load_condition(root, identity, manifest, freeze) for identity in CONDITIONS}
    _verify_sources(conditions, manifest.contrast)
    unaffected = _verify_annotations(conditions, manifest.contrast)
    return VerifiedFamily(checksum(manifest_bytes), manifest.freeze_sha256, conditions, manifest.contrast, unaffected)


def truth_edges(truth: GroundTruth) -> dict[SemanticEdge, GroundTruthRelationship]:
    """Index the complete truth with the protected semantic-edge normalization."""
    entities = {entity.id: entity for entity in truth.entities}
    if (len(entities) != len(truth.entities)
            or len({entity.name for entity in truth.entities}) != len(truth.entities)
            or any(not entity.id.strip() or not entity.name.strip() for entity in truth.entities)):
        raise ValueError('Family A truth requires nonempty, unique entity IDs and names')
    edges = {}
    for relationship in truth.relationships:
        source, target = entities.get(relationship.source), entities.get(relationship.target)
        if source is None or target is None:
            raise ValueError('Family A truth references an unknown entity ID')
        if source.id == target.id or (source.type, target.type) != ENDPOINT_TYPES[relationship.type]:
            raise ValueError('Family A truth has invalid relationship endpoints')
        edge = _edge(source.name, relationship.type, target.name)
        if edge in edges:
            raise ValueError('Duplicate semantic edge in Family A truth')
        edges[edge] = relationship
    return edges


def _read_json(data: bytes) -> object:
    def unique_fields(pairs: list[tuple[str, object]]) -> dict[str, object]:
        values = dict(pairs)
        if len(values) != len(pairs):
            raise ValueError('Duplicate field in benchmark JSON')
        return values

    return json.loads(data.decode('utf-8'), object_pairs_hook=unique_fields)


def _verified_bytes(path: Path, expected: str) -> bytes:
    data = path.read_bytes()
    if checksum(data) != expected:
        raise ValueError(f'Digest mismatch for {path}')
    return data


def _load_condition(root: Path, identity: ConditionId, manifest: FamilyManifest,
                    freeze: SourceFreeze) -> VerifiedCondition:
    saved_path = root / f'{identity}.json'
    saved_bytes = _verified_bytes(saved_path, manifest.conditions[identity])
    raw_saved = _read_json(saved_bytes)
    saved = SavedIdeal.model_validate(raw_saved)
    if saved.condition != identity:
        raise ValueError(f'Saved condition identity mismatch for {identity}')
    # The shared truth models allow extra fields. Reject any that would be discarded
    # before comparisons so a matched control never hides an unexamined field.
    assert isinstance(raw_saved, dict)
    if saved.truth.model_dump(mode='json') != raw_saved['truth']:
        raise ValueError(f'Unexpected field in ground truth for {identity}')
    source_path = root / 'sources' / f'{identity}.json'
    raw_sources = _read_json(source_path.read_bytes())
    if value_digest(raw_sources) != freeze.sources_sha256[identity]:
        raise ValueError(f'Digest mismatch for {source_path}')
    sources = _SOURCES.validate_python(raw_sources)
    if [source.model_dump(mode='json') for source in sources] != raw_sources:
        raise ValueError(f'Source array contains fields outside the extraction contract for {identity}')
    order = [source.id for source in sources]
    if not order or len(set(order)) != len(order) or any(not identity.strip() for identity in order):
        raise ValueError(f'Source IDs must be nonempty and unique for {identity}')
    if order != freeze.order[identity]:
        raise ValueError(f'Source order differs from the preblind freeze for {identity}')
    if source_commitments(sources) != freeze.source_commitments[identity]:
        raise ValueError(f'Individual Source commitment mismatch for {identity}')
    annotations = {key: value_digest(raw_saved[key]) for key in ('truth', 'source_approval', 'sufficient_evidence')}
    return VerifiedCondition(saved, sources, manifest.conditions[identity], freeze.sources_sha256[identity], annotations)


def source_commitments(sources: list[Source]) -> dict[str, dict[str, str]]:
    """Commit the exact UTF-8 fields as well as each serialized Source object."""
    return {
        source.id: {
            'id_sha256': checksum(source.id.encode()),
            'title_sha256': checksum(source.title.encode()),
            'body_sha256': checksum(source.text.encode()),
            'serialized_source_sha256': value_digest(source.model_dump(mode='json')),
        }
        for source in sources
    }


def _verify_sources(conditions: dict[ConditionId, VerifiedCondition], contrast: TrusteeSwitch) -> None:
    natural, permuted, held = [conditions[identity].sources for identity in CONDITIONS]
    by_id = {source.id: source for source in natural}
    if permuted == natural or {source.id: source for source in permuted} != by_id:
        raise ValueError('A1 must change only the order of the serialized A0 Sources')
    edited = by_id.get(contrast.source_id)
    if edited is None:
        raise ValueError('The precommitted A2 edit references an unknown Source')
    position = edited.text.find(contrast.before)
    if position < 0 or edited.text.find(contrast.before, position + 1) >= 0:
        raise ValueError('The precommitted A2 field must occur exactly once in its A0 Source body')
    replacement = edited.model_copy(update={'text': edited.text.replace(contrast.before, contrast.after, 1)})
    expected = [replacement if source.id == edited.id else source for source in natural]
    if held != expected:
        raise ValueError('A2 must differ from A0 only by the precommitted literal Source body edit')


def _verify_annotations(conditions: dict[ConditionId, VerifiedCondition],
                        contrast: TrusteeSwitch) -> set[SemanticEdge]:
    natural, permuted, held = [conditions[identity].saved for identity in CONDITIONS]
    for field, digest in conditions['A0'].annotation_sha256.items():
        if digest != conditions['A1'].annotation_sha256[field]:
            raise ValueError(f'A1 changed frozen A0 {field}')
    base_edges = truth_edges(natural.truth)
    held_edges = truth_edges(held.truth)
    removed, added = set(contrast.removed), set(contrast.added)
    if set(base_edges) - set(held_edges) != removed or set(held_edges) - set(base_edges) != added:
        raise ValueError('A2 truth differs by more than the predeclared trustee switch')
    unaffected = base_edges.keys() & held_edges.keys()
    if not unaffected:
        raise ValueError('Family A requires at least one unaffected edge')
    if any(base_edges[edge] != held_edges[edge] for edge in unaffected):
        raise ValueError('A2 changed unaffected ground-truth approvals')
    _verify_entities(natural.truth, held.truth, removed, added)
    _verify_unaffected_evidence(natural, held, unaffected)
    for saved, critical in ((natural, removed), (permuted, removed), (held, added)):
        if not critical <= {_edge(*item.edge) for item in saved.sufficient_evidence}:
            raise ValueError(f'{saved.condition} lacks the critical trustee proof annotation')
    return unaffected


def _verify_entities(natural: GroundTruth, held: GroundTruth,
                     removed: set[SemanticEdge], added: set[SemanticEdge]) -> None:
    base_entities = {entity.name: entity for entity in natural.entities}
    held_entities = {entity.name: entity for entity in held.entities}
    if (any(base_entities[name] != held_entities[name] for name in base_entities.keys() & held_entities.keys())
            or base_entities.keys() - held_entities.keys() - {edge[0] for edge in removed}
            or held_entities.keys() - base_entities.keys() - {edge[0] for edge in added}):
        raise ValueError('A2 changed an entity outside the predeclared trustee switch')


def _verify_unaffected_evidence(natural: SavedIdeal, held: SavedIdeal,
                                unaffected: set[SemanticEdge]) -> None:
    def approvals(saved: SavedIdeal) -> list[SourceEvidenceRelationship]:
        names = {entity.id: entity.name for entity in saved.truth.entities}
        return [rel for rel in saved.source_approval.relationships
                if _edge(names.get(rel.source, ''), rel.type, names.get(rel.target, '')) in unaffected]

    if approvals(natural) != approvals(held):
        raise ValueError('A2 changed unaffected Source approvals')
    base_sets = [item for item in natural.sufficient_evidence if _edge(*item.edge) in unaffected]
    held_sets = [item for item in held.sufficient_evidence if _edge(*item.edge) in unaffected]
    if base_sets != held_sets:
        raise ValueError('A2 changed unaffected sufficient evidence sets')
