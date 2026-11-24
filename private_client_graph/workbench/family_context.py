"""Versioned research context for the verified Run inspection response."""
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

from benchmark_v3 import commissioning
from benchmark_v3.batch.artifacts import read_bytes
from benchmark_v3.evaluation_protocol import ConditionCommitment, EvaluationScope
from benchmark_v3.research_contracts import AdmittedFamily, CoverageRegister, HypothesisRef, VerifiedFinding
from private_client_graph.research.artifacts import checksum


class FamilyResearchContext(BaseModel):
    revision: str | int
    dossier_sha256: str
    description: str
    shortcuts: str
    hypothesis_text: str
    hypothesis_basis: Literal['historical_admission', 'versioned_hypothesis']
    hypothesis: HypothesisRef | None
    primary_axis: str
    secondary_axes: list[str] | None
    condition_intents: dict[str, str]
    verified_findings: list[VerifiedFinding]
    incidental_challenges: list[str]
    scope_limits: str


class RunFamilyContext(BaseModel):
    schema_version: Literal[1] = 1
    benchmark_sha256: str
    axis_definitions: dict[str, str]
    families: dict[str, FamilyResearchContext]


def read_family_context(scope: EvaluationScope, admission_bytes: bytes) -> RunFamilyContext | None:
    """Project display metadata for an already custody-verified live Run."""
    if scope.observation_origin != 'live':
        return None
    copy = json.loads(Path(__file__).with_name('family_context_copy.json').read_bytes())
    if scope.benchmark_sha256 != copy['benchmark_sha256']:
        return None
    public = json.loads(commissioning.trusted_bytes('admissions/2026-11-24.json'))
    if checksum(admission_bytes) != scope.benchmark_sha256 or public['private_register_sha256'] != scope.benchmark_sha256:
        raise ValueError('Family research context admission commitment differs')
    admitted = json.loads(admission_bytes)['families']
    coverage = commissioning.coverage_register()
    return project_family_context(scope, public['families'], admitted, copy['families'], coverage)


def project_family_context(scope: EvaluationScope, roster: list[dict], admitted: dict,
                           copy: dict, coverage: CoverageRegister) -> RunFamilyContext:
    """Join the inspection roster to reviewed copy and edition-specific research records."""
    _verify_roster(scope, roster, admitted)
    families = {}
    coverage_by_id = {row.family_id: row for row in coverage.families}
    for entry in roster:
        family = entry['family']
        wording = copy.get(family)
        if not wording or set(wording['condition_intents']) != set(entry['conditions']):
            continue
        context = _family_context(entry, admitted[family], wording, coverage_by_id.get(family))
        if context is not None:
            families[family] = context
    return RunFamilyContext(benchmark_sha256=scope.benchmark_sha256, families=families,
                            axis_definitions={axis.id: axis.description for axis in coverage.taxonomy})


def _verify_roster(scope: EvaluationScope, roster: list[dict], admitted: dict) -> None:
    commitments = []
    for entry in roster:
        family = entry['family']
        record = admitted[family]
        if (record['family_id'] != family or record['technical_revision'] != entry['revision']
                or record['technical_dossier_sha256'] != entry['technical_dossier_sha256']):
            raise ValueError('Family research context revision differs from admission')
        for condition in entry['conditions']:
            key = record['condition_details'][condition]
            commitments.append(ConditionCommitment(
                family, condition, key['ordered_sources_sha256'], key['key_file_sha256'],
            ))
    if tuple(commitments) != scope.conditions:
        raise ValueError('Family research context differs from the verified Run roster')


def _family_context(entry: dict, record: dict, wording: dict,
                    coverage: AdmittedFamily | None) -> FamilyResearchContext | None:
    if not all(record.get(key) for key in ('hypothesis_text', 'shortcuts', 'admission_scope')):
        return None
    if entry.get('preserved_admission_sha256') and coverage is None:
        return None
    hypothesis = record.get('hypothesis')
    if hypothesis is None and (coverage is None or coverage.protocol != 'historical'):
        return None
    findings: list[VerifiedFinding] = []
    incidental: list[str] = []
    if coverage is not None:
        if (coverage.admission_sha256 != entry.get('preserved_admission_sha256')
                or coverage.hypothesis != (HypothesisRef.model_validate(hypothesis) if hypothesis else None)):
            raise ValueError('Family coverage does not match the admitted research record')
        reconciliation = commissioning.saved_reconciliation(coverage)
        findings = reconciliation.result.verified_findings if reconciliation else coverage.verified_findings
        incidental = coverage.incidental_challenges
    else:
        dossier_bytes = read_bytes(Path(record['custody_locator']))
        if checksum(dossier_bytes) != entry['technical_dossier_sha256']:
            raise ValueError('Family research dossier commitment differs')
        dossier = json.loads(dossier_bytes)
        if dossier.get('family_id') != entry['family'] or dossier.get('revision') != entry['revision']:
            raise ValueError('Family research dossier revision differs from admission')
        if dossier.get('hypothesis') != hypothesis:
            raise ValueError('Family hypothesis does not match the admitted dossier')
    return FamilyResearchContext(
        revision=entry['revision'], dossier_sha256=entry['technical_dossier_sha256'],
        description=wording['description'], shortcuts=record['shortcuts'],
        hypothesis_text=record['hypothesis_text'], hypothesis=hypothesis,
        hypothesis_basis='versioned_hypothesis' if hypothesis else 'historical_admission',
        primary_axis=entry['primary_axis'], secondary_axes=entry.get('secondary_axes'),
        condition_intents=wording['condition_intents'], verified_findings=findings,
        incidental_challenges=incidental, scope_limits=record['admission_scope'],
    )
