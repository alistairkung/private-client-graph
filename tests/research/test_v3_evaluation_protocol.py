import hashlib
import json
import os
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import TypeAdapter

from benchmark_v3 import commissioning
from benchmark_v3.evaluation_protocol import (
    GraphCounts, PlannedCondition, ProtocolResult, UnavailablePrediction, evaluate_protocol, require_compatible_scope,
)
from benchmark_v3.replay_manifest import SavedIdeal, VerifiedCondition
from benchmark_v3.retained_evaluation import BASELINE_INVENTORY_SHA256, evaluate_first_live_baseline
from private_client_graph.extraction.semantic import SOURCED_EXTRACTION_PROMPT
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.research.provider import ModelSettings
from private_client_graph.research.retained_inputs import value_digest


DIGEST = 'a' * 64
PREDICATE = 'trustee_of'
FIRST = {'source_id': 'terms', 'supporting_text': 'The office is defined here.'}
SECOND = {'source_id': 'register', 'supporting_text': 'The holder is Gray.'}
ALTERNATE = {'source_id': 'audit', 'supporting_text': 'The checked holder is Gray.'}


def planned(family: str, condition: str, *, empty: bool = False) -> PlannedCondition:
    sources = [Source(id=part['source_id'], title=part['source_id'], text=part['supporting_text'])
               for part in (FIRST, SECOND, ALTERNATE)]
    entities = [{'id': 'person', 'name': 'Gray', 'type': 'person'},
                {'id': 'trust', 'name': 'North trust', 'type': 'trust'}]
    relationship = {'source': 'person', 'target': 'trust', 'type': PREDICATE, 'approved_evidence': []}
    proof = {'edge': ['Gray', PREDICATE, 'North trust'], 'joint_only': True,
             'alternatives': [[FIRST, SECOND], [FIRST, ALTERNATE]]}
    key = SavedIdeal.model_validate({
        'condition': condition, 'truth': {'entities': entities, 'relationships': [] if empty else [relationship]},
        'source_approval': {'relationships': []},
        'ideal': {'relationships': []},
        'sufficient_evidence': [] if empty else [proof],
    })
    return PlannedCondition(family, VerifiedCondition(key, sources, 'b' * 64, 'c' * 64, {}))


def prediction(*fragments: dict[str, str]) -> SourcedExtractionResult:
    return SourcedExtractionResult.model_validate({
        'relationships': [dict(source_name='Gray', target_name='North trust', relationship_type=PREDICATE, **part)
                          for part in fragments],
    })


def evaluate(roster, predictions, *, digest=DIGEST, origin='offline_fixture'):
    return evaluate_protocol(roster, predictions, benchmark_sha256=digest, observation_origin=origin)


def test_failure_denominators_and_unweighted_family_macro():
    roster = [planned('A', 'A0'), planned('A', 'A1'), planned('B', 'B0'), planned('C', 'C0'),
              planned('D', 'D0'), planned('E', 'E0')]
    report = evaluate(roster, {
        'A0': prediction(FIRST, ALTERNATE),
        'A1': prediction(FIRST | {'supporting_text': 'Unquoted text.'}),
        'B0': UnavailablePrediction('provider_failure'),
        'C0': UnavailablePrediction('parse_failure'),
        'D0': UnavailablePrediction('uncertain'),
    })
    assert report.cohort.all_conditions == GraphCounts(1, 0, 5)
    assert report.cohort.valid_graph_only == GraphCounts(1, 0, 0)
    assert report.cohort.valid_graph_only_micro_f1 == 1
    assert report.cohort.all_condition_micro_f1 == 2 / 7
    assert report.cohort.construction_success_rate == report.cohort.exact_graph_accuracy == 1 / 6
    assert report.cohort.proof_completion_rate == report.cohort.joint_proof_completion_rate == 1 / 6
    assert report.cohort.proofs_without_graph == 5
    assert report.family_macro_f1 == pytest.approx((2 / 3) / 5)
    assert report.valid_graph_only_family_macro_f1 == 1
    assert report.valid_graph_only_macro_family_count == 1
    assert report.cohort.outcomes == {
        'scored': 1, 'validation_failure': 1, 'provider_failure': 1, 'parse_failure': 1,
        'uncertain': 1, 'not_attempted': 1,
    }
    assert report.conditions['A1'].graph is None
    assert 'does not occur verbatim' in report.conditions['A1'].failure_detail


def test_approved_exact_alternative_joint_proof_and_exact_empty_graph():
    roster = [planned('A', 'A0'), planned('A', 'A1'), planned('A', 'A2'),
              planned('B', 'B0', empty=True), planned('C', 'C0', empty=True)]
    report = evaluate(roster, {
        'A0': prediction(FIRST, ALTERNATE),
        'A1': prediction(SECOND, ALTERNATE),  # Quotes from incompatible alternatives alone are insufficient.
        'A2': prediction(),
        'B0': prediction(),
    })
    assert report.cohort.valid_graphs == 4
    assert report.cohort.exact_graphs == 3  # Includes the delivered empty graph in B0.
    assert report.conditions['C0'].graph is None  # A missing empty graph is unavailable.
    assert report.cohort.complete_joint_proofs == 1
    assert report.cohort.incomplete_proofs == report.cohort.missed_proofs == 1
    assert report.cohort.attribution_assessed == report.cohort.quote_assessed == 0
    assert report.families['B'].all_condition_micro_f1 == 0  # Frozen zero-denominator convention.


def test_scope_guards_protocol_commitment_roster_order_and_observation_origin():
    roster = [planned('A', 'A0'), planned('A', 'A1')]
    baseline = evaluate(roster, {})
    serialization = TypeAdapter(ProtocolResult)
    assert serialization.validate_json(serialization.dump_json(baseline)) == baseline
    require_compatible_scope(baseline, evaluate(roster, {'A0': prediction(FIRST)}))
    for other in (
        evaluate(roster, {}, digest='e' * 64), evaluate(roster[::-1], {}, origin='live'),
        evaluate(roster[::-1], {}), evaluate(roster, {}, origin='live'),
        replace(baseline, scope=replace(baseline.scope, protocol_version='unknown')),
        replace(baseline, scope=replace(baseline.scope, sufficiency_policy='unknown')),
    ):
        with pytest.raises(ValueError, match='scope|protocol'):
            require_compatible_scope(baseline, other)
    with pytest.raises(ValueError, match='distinct'):
        evaluate([roster[0], roster[0]], {})
    with pytest.raises(ValueError, match='outside'):
        evaluate(roster, {'V0': prediction(FIRST)})


def test_exact_private_first_live_baseline(monkeypatch, capsys):
    # Private data are opt-in and remain outside the source tree and CI.
    custody = os.environ.get('PCG_V3_PRIVATE_BASELINE_CUSTODY')
    if not custody:
        pytest.skip('Set PCG_V3_PRIVATE_BASELINE_CUSTODY to run the exact private regression')
    monkeypatch.setenv('DEEPSEEK_API_KEY', '')  # A valid credential is never necessary here.
    root = Path(custody)
    result = evaluate_first_live_baseline(
        root / 'live-baseline-2026-11-24', root / 'admissions-2026-11-24/ADMISSIONS.json',
    )
    metrics = result.cohort
    assert result.scope.protocol_version == 'benchmark_v3_evaluation_v1'
    assert result.scope.benchmark_sha256 == 'c864f58786d21fd3f5b9735023c93df62256e537133f15fa602d3cf3d8d13b70'
    assert result.scope.observation_origin == 'live'
    assert result.run_artifact_sha256 == BASELINE_INVENTORY_SHA256
    from private_client_graph.research.cli import main as research_cli
    research_cli(['inspect-v3-baseline', str(root / 'live-baseline-2026-11-24'),
                  str(root / 'admissions-2026-11-24/ADMISSIONS.json')])
    replay = json.loads(capsys.readouterr().out)
    quality = replay['quality']
    assert replay['archive_inventory_sha256'] == BASELINE_INVENTORY_SHA256
    assert replay['qualified_protocol']['cohort']['all_condition_micro_f1'] == 182 / 214
    assert quality['combined_graph'] is None and quality['qualified_graph']['f1'] == 182 / 214
    assert quality['complete_proof'] == {'complete': 18, 'targets': 71, 'rate': 18 / 71}
    assert quality['joint_only_complete_proof'] == {'complete': 0, 'targets': 30, 'rate': 0.0}
    assert quality['joint_only_coverage'] == {'targets': 30, 'mean': 13 / 300}

    assert (len(result.families), metrics.planned_conditions, metrics.valid_graphs, metrics.exact_graphs) == (19, 34, 30, 20)
    assert metrics.all_conditions == GraphCounts(91, 10, 22)
    assert metrics.valid_graph_only == GraphCounts(91, 10, 5)
    assert metrics.expected_edges_without_graph == 17
    assert metrics.all_condition_micro_f1 == 182 / 214
    assert metrics.valid_graph_only_micro_f1 == 182 / 197
    assert result.family_macro_f1 == 0.8307504873294347
    assert result.valid_graph_only_family_macro_f1 == 0.9044634377967712
    assert result.valid_graph_only_macro_family_count == 18
    assert metrics.exact_graph_accuracy == 20 / 34
    assert metrics.valid_graph_only_exact_accuracy == 20 / 30
    assert metrics.construction_success_rate == 30 / 34
    assert (metrics.complete_proofs, metrics.planned_proofs) == (18, 71)
    assert (metrics.complete_joint_proofs, metrics.planned_joint_proofs) == (0, 30)
    assert (metrics.incomplete_proofs, metrics.missed_proofs, metrics.proofs_without_graph) == (44, 5, 4)
    assert (metrics.quote_passed, metrics.quote_assessed, metrics.attribution_passed, metrics.attribution_assessed) == (23, 66, 23, 74)
    assert metrics.outcomes == {'scored': 30, 'validation_failure': 4}
    config = json.loads((root / 'live-baseline-2026-11-24/CONFIGURATION.json').read_text())
    plan = json.loads(commissioning.trusted_bytes('planning/experiments/PROOF-COMPLETENESS-v1.json'))
    assert plan['wire_parameters_without_messages_sha256'] == value_digest(config['exact_wire_parameters_and_schema'])
    failed = {name: row.failure_detail for name, row in result.conditions.items() if row.graph is None}
    assert set(failed) == {'A0', 'B1', 'C2', 'AZ000'}
    assert failed['C2'] == 'Candidate 0: supporting_text does not occur verbatim in source'
    assert all(failed[cid].startswith('Conflicting entity types for ') for cid in ('A0', 'B1', 'AZ000'))

    archived = json.loads((root / 'live-baseline-2026-11-24/RESULTS.json').read_text())
    for family, computed in result.families.items():
        previous = archived['families'][family]
        assert computed.valid_graph_only == GraphCounts(previous['tp'], previous['fp'], previous['fn'])
        assert computed.all_conditions.fn == previous['fn'] + previous['expected_edges_unscored']
        assert computed.valid_graphs == previous['scored']
        assert computed.exact_graphs == previous['exact']
        assert computed.complete_proofs == previous['set_complete']
        assert computed.planned_proofs == previous['evidence_all_planned']


def test_preregistered_matrix_and_prompt_commitments():
    admission = json.loads(commissioning.trusted_bytes('admissions/2026-11-24.json'))
    plan = json.loads(commissioning.trusted_bytes('planning/experiments/PROOF-COMPLETENESS-v1.json'))
    roster = [condition for family in admission['families'] for condition in family['conditions']]
    schedule = plan['pair_schedule']
    assert plan['benchmark_sha256'] == admission['private_register_sha256']
    assert plan['protocol_version'] == 'benchmark_v3_evaluation_v1' and plan['split'] == 'development'
    assert not plan['execution_authorised'] and plan['status'] == 'preregistered_unexecuted'
    assert plan['retries'] == 0 and plan['settings'] == ModelSettings().model_dump(mode='json')
    assert plan['planned_paid_attempts'] == sum(len(pair['arms']) for pair in schedule) == 68
    assert plan['planned_families'] == len(admission['families']) == 19

    def digest(text):
        return hashlib.sha256(text.encode()).hexdigest()

    seed = plan['schedule_seed']
    assert [pair['condition'] for pair in schedule] == sorted(roster, key=lambda cid: digest(f'{seed}:{cid}'))
    assert len(schedule) == plan['planned_conditions'] == 34
    for i, pair in enumerate(schedule):
        assert pair['arms'] == (['control', 'treatment'] if i % 2 == 0 else ['treatment', 'control'])
    operation = plan['treatment_text_operation']
    prompt = SOURCED_EXTRACTION_PROMPT
    assert digest(prompt) == plan['control_prompt_sha256']
    assert prompt.count(operation['insert_before']) == 1
    assert digest(prompt.replace(operation['insert_before'], operation['insert'] + operation['insert_before'], 1)) == plan['treatment_prompt_sha256']
