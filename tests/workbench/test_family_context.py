"""Deterministic family-context contract checks using a synthetic admission and dossier."""
import json
from pathlib import Path
from typing import NamedTuple

import pytest

from benchmark_v3.commissioning import coverage_register
from benchmark_v3.evaluation_protocol import ConditionCommitment, EvaluationScope
from benchmark_v3.research_contracts import CoverageRegister
from private_client_graph.research.artifacts import checksum
from private_client_graph.workbench.family_context import project_family_context, read_family_context


class SyntheticAdmission(NamedTuple):
    scope: EvaluationScope
    roster: list[dict]
    records: dict
    wording: dict
    coverage: CoverageRegister


@pytest.fixture
def synthetic_admission(tmp_path: Path):
    ref = {'hypothesis_id': 'synthetic-office', 'revision': 1, 'hypothesis_sha256': '1' * 64}
    dossier = tmp_path / 'dossier.json'
    dossier.write_text(json.dumps({'family_id': 'Q', 'revision': 2, 'hypothesis': ref,
                                  'raw_review': 'private review content'}))
    digest = checksum(dossier.read_bytes())
    entry = {'family': 'Q', 'revision': 2, 'conditions': ['Q0'], 'primary_axis': 'entity-identity',
             'secondary_axes': [], 'technical_dossier_sha256': digest}
    record = {
        'family_id': 'Q', 'technical_revision': 2, 'technical_dossier_sha256': digest,
        'custody_locator': str(dossier), 'hypothesis': ref, 'hypothesis_text': 'Frozen hypothesis.',
        'shortcuts': 'Using the wrong register.', 'admission_scope': 'One synthetic record.',
        'condition_details': {'Q0': {'ordered_sources_sha256': '2' * 64, 'key_file_sha256': '3' * 64}},
    }
    scope = EvaluationScope(benchmark_sha256='4' * 64, observation_origin='live',
                            conditions=(ConditionCommitment('Q', 'Q0', '2' * 64, '3' * 64),))
    wording = {'Q': {'description': 'Identify the officeholder.', 'condition_intents': {'Q0': 'Check the register.'}}}
    return SyntheticAdmission(scope, [entry], {'Q': record}, wording, coverage_register())


def test_versioned_family_context_exposes_only_inspection_fields(synthetic_admission):
    context = project_family_context(*synthetic_admission)
    family = context.families['Q']
    assert family.hypothesis_basis == 'versioned_hypothesis'
    assert family.hypothesis_text == 'Frozen hypothesis.'
    assert family.condition_intents == {'Q0': 'Check the register.'}
    assert family.secondary_axes == []
    assert family.verified_findings == []
    assert 'custody_locator' not in context.model_dump_json()
    assert 'private review content' not in context.model_dump_json()


def test_missing_optional_hypothesis_leaves_the_family_unenriched(synthetic_admission):
    synthetic_admission.records['Q'].pop('hypothesis')
    assert project_family_context(*synthetic_admission).families == {}


def test_absent_secondary_axes_are_distinct_from_an_empty_list(synthetic_admission):
    synthetic_admission.roster[0].pop('secondary_axes')
    assert project_family_context(*synthetic_admission).families['Q'].secondary_axes is None


def test_changed_condition_key_cannot_receive_admitted_context(synthetic_admission):
    synthetic_admission.records['Q']['condition_details']['Q0']['key_file_sha256'] = '0' * 64
    with pytest.raises(ValueError, match='roster'):
        project_family_context(*synthetic_admission)


def test_unbound_hypothesis_rejected_even_when_family_id_matches(synthetic_admission):
    synthetic_admission.records['Q']['hypothesis']['revision'] = 2
    with pytest.raises(ValueError, match='hypothesis'):
        project_family_context(*synthetic_admission)


def test_unknown_benchmark_has_no_family_context(synthetic_admission):
    scope = synthetic_admission.scope
    assert read_family_context(scope, b'{}') is None


def test_missing_historical_coverage_does_not_use_an_unrelated_dossier(synthetic_admission):
    synthetic_admission.roster[0]['preserved_admission_sha256'] = 'a' * 64
    assert project_family_context(*synthetic_admission).families == {}


def test_dossier_commitment_is_checked_before_projecting_context(synthetic_admission):
    Path(synthetic_admission.records['Q']['custody_locator']).write_text('{}')
    with pytest.raises(ValueError, match='dossier commitment'):
        project_family_context(*synthetic_admission)
