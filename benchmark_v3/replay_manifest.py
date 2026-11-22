"""Verify frozen inputs and matched controls for the Benchmark v3 pilot."""

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


FamilyId = Literal['A', 'B', 'C']
CONDITIONS: dict[FamilyId, tuple[str, ...]] = {
    'A': ('A0', 'A1', 'A2'), 'B': ('B0', 'B1'), 'C': ('C0', 'C1', 'C2'),
}
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
    conditions: dict[str, Sha256]
    contrast: TrusteeSwitch


class MatchedFamilyManifest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[2]
    family: Literal['B', 'C']
    freeze_sha256: Sha256
    conditions: dict[str, Sha256]


class SourceCommitments(BaseModel):
    # The custodian's freeze also records provenance outside the replay contract.
    order: dict[str, list[str]]
    sources_sha256: dict[str, Sha256]
    source_commitments: dict[str, dict[str, dict[str, Sha256]]]


class SourceFreeze(SourceCommitments):
    intervention: LiteralEdit
    declared_removed: list[SemanticEdge]
    declared_added: list[SemanticEdge]


class MatchedSourceFreeze(SourceCommitments):
    interventions: dict[str, LiteralEdit]
    candidates: list[SemanticEdge] = Field(min_length=2, max_length=2)
    required: dict[str, list[SemanticEdge]]


class SufficientEvidence(BaseModel):
    model_config = ConfigDict(extra='forbid')
    edge: SemanticEdge
    joint_only: bool = False
    alternatives: list[list[ApprovedSourceEvidence]] = Field(min_length=1)


class SavedIdeal(BaseModel):
    model_config = ConfigDict(extra='forbid')
    condition: str
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
    family: FamilyId
    manifest_sha256: str
    freeze_sha256: str
    conditions: dict[str, VerifiedCondition]
    edits: dict[str, LiteralEdit]
    required: dict[str, list[SemanticEdge]]
    candidates: set[SemanticEdge]
    unaffected: set[SemanticEdge]


def load_family(manifest_path: Path) -> VerifiedFamily:
    """Bind the saved ideals and ordered Sources before verifying the contrasts."""
    manifest_bytes = manifest_path.read_bytes()
    raw = _read_json(manifest_bytes)
    if isinstance(raw, dict) and raw.get('schema_version') == 2:
        manifest = MatchedFamilyManifest.model_validate(raw)
        return _load_matched_family(manifest_path.parent, manifest, checksum(manifest_bytes))
    family_a = FamilyManifest.model_validate(raw)
    return _load_family_a(manifest_path.parent, family_a, checksum(manifest_bytes))


def _load_family_a(root: Path, manifest: FamilyManifest, digest: str) -> VerifiedFamily:
    freeze = SourceFreeze.model_validate(_read_json(_verified_bytes(root / 'freeze.json', manifest.freeze_sha256)))
    conditions = _load_conditions(root, manifest, freeze)
    if freeze.intervention.model_dump() != manifest.contrast.model_dump(include={'source_id', 'before', 'after'}):
        raise ValueError('A2 literal edit differs from the preblind Source freeze')
    if (freeze.declared_removed, freeze.declared_added) != (manifest.contrast.removed, manifest.contrast.added):
        raise ValueError('Trustee switch differs from the preblind declaration')

    natural, permuted, held = (conditions[identity].sources for identity in CONDITIONS['A'])
    if permuted == natural or {source.id: source for source in permuted} != {source.id: source for source in natural}:
        raise ValueError('A1 must change only the order of the serialized A0 Sources')
    _verify_edit('A0', 'A2', natural, held, manifest.contrast)
    unaffected = _verify_annotations(conditions, manifest.contrast)
    required = {'A0': manifest.contrast.removed, 'A1': manifest.contrast.removed, 'A2': manifest.contrast.added}
    candidates = set(manifest.contrast.removed + manifest.contrast.added)
    return VerifiedFamily('A', digest, manifest.freeze_sha256, conditions, {'A2': freeze.intervention},
                          required, candidates, unaffected)


def _load_matched_family(root: Path, manifest: MatchedFamilyManifest, digest: str) -> VerifiedFamily:
    freeze = MatchedSourceFreeze.model_validate(
        _read_json(_verified_bytes(root / 'freeze.json', manifest.freeze_sha256)))
    conditions = _load_conditions(root, manifest, freeze)
    base, *variants = conditions
    _verify_targets(manifest.family, freeze, set(conditions), set(variants))
    natural = conditions[base]
    base_edges = truth_edges(natural.saved.truth)
    candidates = set(freeze.candidates)
    unaffected = base_edges.keys() - candidates
    if not unaffected:
        raise ValueError(f'Family {manifest.family} requires at least one unaffected edge')

    for identity, condition in conditions.items():
        required = set(freeze.required[identity])
        edges = truth_edges(condition.saved.truth)
        if set(edges) != unaffected | required:
            raise ValueError(f'{identity} truth differs from the predeclared targets and unaffected edges')
        joint = {_edge(*item.edge) for item in condition.saved.sufficient_evidence if item.joint_only}
        if not required <= joint:
            raise ValueError(f'{identity} lacks a critical joint-only proof annotation')
        if identity == base:
            continue
        _verify_edit(base, identity, natural.sources, condition.sources, freeze.interventions[identity])
        _verify_shared_annotations(natural.saved, condition.saved, unaffected,
                                   base_edges.keys() - edges.keys(), edges.keys() - base_edges.keys())

    return VerifiedFamily(manifest.family, digest, manifest.freeze_sha256, conditions,
                          freeze.interventions, freeze.required, candidates, unaffected)


def _verify_targets(family: Literal['B', 'C'], freeze: MatchedSourceFreeze,
                    conditions: set[str], variants: set[str]) -> None:
    if set(freeze.interventions) != variants or set(freeze.required) != conditions:
        raise ValueError('Every matched condition requires a preblind target declaration and literal variant edit')
    first, second = freeze.candidates
    if (first[0] != second[0] or first[2] == second[2]
            or any(edge[1] != ('parent_of' if family == 'B' else 'beneficiary_of') for edge in freeze.candidates)):
        raise ValueError(f'Family {family} must declare two candidate endpoints for its critical edge')
    expected = {'B0': [], 'B1': [first]} if family == 'B' else {'C0': [first], 'C1': [second], 'C2': []}
    if freeze.required != expected:
        raise ValueError(f'Family {family} critical decisions differ from the protocol')
    if len({(edit.source_id, edit.before) for edit in freeze.interventions.values()}) != 1:
        raise ValueError('Variants must edit the same predeclared field')
    if len({edit.after for edit in freeze.interventions.values()}) != len(variants):
        raise ValueError('Variants must have distinct field values')


def _load_conditions(root: Path, manifest: FamilyManifest | MatchedFamilyManifest,
                     freeze: SourceCommitments) -> dict[str, VerifiedCondition]:
    identities = CONDITIONS[manifest.family]
    entries = (manifest.conditions, freeze.order, freeze.sources_sha256, freeze.source_commitments)
    if any(entry.keys() != set(identities) for entry in entries):
        expected = f"{', '.join(identities[:-1])} and {identities[-1]}"
        raise ValueError(f'The manifest and Source freeze must cover exactly {expected}')
    return {identity: _load_condition(root, identity, manifest.conditions[identity], freeze)
            for identity in identities}


def truth_edges(truth: GroundTruth) -> dict[SemanticEdge, GroundTruthRelationship]:
    """Index the complete truth with the protected semantic-edge normalization."""
    entities = {entity.id: entity for entity in truth.entities}
    if (len(entities) != len(truth.entities)
            or len({entity.name for entity in truth.entities}) != len(truth.entities)
            or any(not entity.id.strip() or not entity.name.strip() for entity in truth.entities)):
        raise ValueError('Benchmark truth requires nonempty, unique entity IDs and names')
    edges = {}
    for relationship in truth.relationships:
        source, target = entities.get(relationship.source), entities.get(relationship.target)
        if source is None or target is None:
            raise ValueError('Benchmark truth references an unknown entity ID')
        if source.id == target.id or (source.type, target.type) != ENDPOINT_TYPES[relationship.type]:
            raise ValueError('Benchmark truth has invalid relationship endpoints')
        edge = _edge(source.name, relationship.type, target.name)
        if edge in edges:
            raise ValueError('Duplicate semantic edge in benchmark truth')
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


def _load_condition(root: Path, identity: str, digest: str,
                    freeze: SourceCommitments) -> VerifiedCondition:
    saved_path = root / f'{identity}.json'
    saved_bytes = _verified_bytes(saved_path, digest)
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
    return VerifiedCondition(saved, sources, digest, freeze.sources_sha256[identity], annotations)


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


def _verify_edit(base: str, variant: str, natural: list[Source], edited_sources: list[Source],
                 edit: LiteralEdit) -> None:
    original = next((source for source in natural if source.id == edit.source_id), None)
    if original is None:
        raise ValueError(f'The precommitted {variant} edit references an unknown Source')
    position = original.text.find(edit.before)
    if position < 0 or original.text.find(edit.before, position + 1) >= 0:
        raise ValueError(f'The precommitted {variant} field must occur exactly once in its {base} Source body')
    if edit.before == edit.after:
        raise ValueError(f'{variant} must change the precommitted literal field')
    replacement = original.model_copy(update={'text': original.text.replace(edit.before, edit.after, 1)})
    expected = [replacement if source.id == original.id else source for source in natural]
    if edited_sources != expected:
        raise ValueError(f'{variant} must differ from {base} only by the precommitted literal Source body edit')


def _verify_annotations(conditions: dict[str, VerifiedCondition],
                        contrast: TrusteeSwitch) -> set[SemanticEdge]:
    natural, permuted, held = [conditions[identity].saved for identity in CONDITIONS['A']]
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
    _verify_shared_annotations(natural, held, unaffected, removed, added)
    for saved, critical in ((natural, removed), (permuted, removed), (held, added)):
        if not critical <= {_edge(*item.edge) for item in saved.sufficient_evidence}:
            raise ValueError(f'{saved.condition} lacks the critical trustee proof annotation')
    return unaffected


def _verify_shared_annotations(natural: SavedIdeal, variant: SavedIdeal, unaffected: set[SemanticEdge],
                               removed: set[SemanticEdge], added: set[SemanticEdge]) -> None:
    base_edges, variant_edges = truth_edges(natural.truth), truth_edges(variant.truth)
    if any(base_edges[edge] != variant_edges[edge] for edge in unaffected):
        raise ValueError(f'{variant.condition} changed unaffected ground-truth approvals')
    _verify_entities(natural.truth, variant.truth, removed, added, variant.condition)
    _verify_unaffected_evidence(natural, variant, unaffected)


def _verify_entities(natural: GroundTruth, held: GroundTruth,
                     removed: set[SemanticEdge], added: set[SemanticEdge], variant: str) -> None:
    base_entities = {entity.name: entity for entity in natural.entities}
    held_entities = {entity.name: entity for entity in held.entities}
    allowed_removed = _changed_endpoint_names(removed, variant)
    allowed_added = _changed_endpoint_names(added, variant)
    if (any(base_entities[name] != held_entities[name] for name in base_entities.keys() & held_entities.keys())
            or base_entities.keys() - held_entities.keys() - allowed_removed
            or held_entities.keys() - base_entities.keys() - allowed_added):
        raise ValueError(f'{variant} changed an entity outside the predeclared edge change')


def _changed_endpoint_names(edges: set[SemanticEdge], variant: str) -> set[str]:
    if variant == 'A2':
        return {source for source, _, _ in edges}
    return {name for source, _, target in edges for name in (source, target)}


def _verify_unaffected_evidence(natural: SavedIdeal, variant: SavedIdeal,
                                unaffected: set[SemanticEdge]) -> None:
    def approvals(saved: SavedIdeal) -> list[SourceEvidenceRelationship]:
        names = {entity.id: entity.name for entity in saved.truth.entities}
        return [rel for rel in saved.source_approval.relationships
                if _edge(names.get(rel.source, ''), rel.type, names.get(rel.target, '')) in unaffected]

    if approvals(natural) != approvals(variant):
        raise ValueError(f'{variant.condition} changed unaffected Source approvals')
    base_sets = [item for item in natural.sufficient_evidence if _edge(*item.edge) in unaffected]
    variant_sets = [item for item in variant.sufficient_evidence if _edge(*item.edge) in unaffected]
    if base_sets != variant_sets:
        raise ValueError(f'{variant.condition} changed unaffected sufficient evidence sets')
