"""Provider-free checks of exact, route-specific partial evidence reporting."""

from dataclasses import replace

import pytest

from benchmark_v3.evaluation_protocol import PlannedCondition, UnavailablePrediction, evaluate_protocol
from benchmark_v3.replay_manifest import SavedIdeal, VerifiedCondition
from private_client_graph.graph import build_canonical_state
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.models.sourced_extraction import SourcedRelationshipCandidate
from private_client_graph.research.evidence_quality import report_evidence_quality
from private_client_graph.research.results import ResearchResult


def _pair(identity):
    return {'source_id': identity, 'supporting_text': f'Evidence {identity}.'}


def _planned(identity='K0', *, proof=True):
    relationship = {'source': 'person', 'target': 'trust', 'type': 'trustee_of', 'approved_evidence': []}
    key = SavedIdeal.model_validate({
        'condition': identity,
        'truth': {
            'entities': [{'id': 'person', 'name': 'Tess', 'type': 'person'},
                         {'id': 'trust', 'name': 'Trust', 'type': 'trust'}],
            'relationships': [relationship] if proof else [],
        },
        'source_approval': {'relationships': []},
        'ideal': {'relationships': []},
        'sufficient_evidence': [{
            'edge': ['Tess', 'trustee_of', 'Trust'], 'joint_only': True,
            'alternatives': [[_pair(item) for item in 'abc'], [_pair(item) for item in 'de']],
        }] if proof else [],
    })
    sources = [Source(id=item, title=item, text=f'Evidence {item}.') for item in 'abcde']
    sources.append(Source(id='copy', title='Copy', text='Evidence a.'))
    return PlannedCondition('K', VerifiedCondition(key, sources, 'a' * 64, 'b' * 64, {}))


def _prediction(*pairs):
    return SourcedExtractionResult(relationships=[
        SourcedRelationshipCandidate.model_validate({'source_name': 'Tess', 'target_name': 'Trust',
             'relationship_type': 'trustee_of', **pair})
        for pair in pairs
    ])


def _report(planned, predictions):
    protocol = evaluate_protocol(planned, predictions, benchmark_sha256='c' * 64, observation_origin='offline_fixture')
    results = {
        item.frozen.saved.condition: ResearchResult(
            sample_id=item.frozen.saved.condition, case_id=item.family, cohort='authored',
            state=build_canonical_state(predictions[item.frozen.saved.condition].relationships,
                                        sources=item.frozen.sources),
        )
        for item in planned if protocol.conditions[item.frozen.saved.condition].outcome == 'scored'
    }
    return report_evidence_quality(protocol, planned, results)


@pytest.mark.parametrize(('pairs', 'coverage', 'status', 'route_matches'), [
    ([_pair('a')], 1 / 3, 'incomplete', [1, 0]),
    ([_pair('a'), _pair('b'), _pair('b')], 2 / 3, 'incomplete', [2, 0]),
    ([_pair('a'), _pair('b'), _pair('c')], 1.0, 'complete', [3, 0]),
    ([_pair('a'), _pair('d')], 0.5, 'incomplete', [1, 1]),
    ([_pair('d'), _pair('e')], 1.0, 'complete', [0, 2]),
    ([_pair('a') | {'source_id': 'copy'}], 0.0, 'incomplete', [0, 0]),
    ([_pair('a') | {'supporting_text': 'Evidence a'}], 0.0, 'incomplete', [0, 0]),
    ([_pair('a') | {'source_name': 'Other'}], 0.0, 'missed', [0, 0]),
    ([_pair('a') | {'supporting_text': 'Invented quotation.'}], 0.0, 'without_graph', [0, 0]),
])
def test_exact_attached_pairs_are_scored_within_a_single_approved_route(pairs, coverage, status, route_matches):
    report = _report([_planned()], {'K0': _prediction(*pairs)})
    target = report.joint_targets[0].report()
    assert (target['coverage'], target['status']) == (coverage, status)
    assert [route['matched'] for route in target['alternatives']] == route_matches
    for route in target['alternatives']:
        assert sum(member['matched'] for member in route['members']) == route['matched']
    assert report.quality.joint_only_coverage.mean == coverage
    assert report.quality.joint_only_complete_proof.complete == int(status == 'complete')


def test_averages_over_planned_targets_and_distinguishes_missing_empty_and_unavailable_graphs():
    planned = [_planned(f'K{i}') for i in range(5)]
    predictions = {'K0': _prediction(_pair('a'), _pair('b')), 'K1': _prediction(),
                   'K2': UnavailablePrediction('provider_failure'), 'K3': _prediction(_pair('d'), _pair('e'))}
    report = _report(planned, predictions)
    quality = report.quality
    assert quality.state == 'provisional'
    assert quality.observed_inputs == quality.observed_proof_targets == quality.observed_joint_targets == 4
    assert quality.qualified_graph.valid_graphs == 3
    assert quality.joint_only_coverage.targets == quality.complete_proof.targets == 5
    assert quality.joint_only_coverage.mean == 1 / 3
    assert quality.complete_proof.rate == quality.joint_only_complete_proof.rate == 1 / 5
    assert [target.status() for target in report.joint_targets] == [
        'incomplete', 'missed', 'without_graph', 'complete', 'not_attempted',
    ]
    assert report.joint_targets[-1].report()['coverage'] is None


def test_zero_targets_and_unobserved_target_scope_are_unavailable():
    empty = _planned('K1', proof=False)
    no_targets = _report([empty], {'K1': _prediction()}).quality
    assert no_targets.state == 'complete'
    assert no_targets.qualified_graph.exact_graphs == 1
    assert no_targets.complete_proof.targets == no_targets.joint_only_coverage.targets == 0
    assert no_targets.complete_proof.rate is None and no_targets.joint_only_coverage.mean is None
    unobserved = _report([_planned(), empty], {'K1': _prediction()}).quality
    assert unobserved.state == 'provisional'
    assert unobserved.complete_proof.targets == unobserved.joint_only_coverage.targets == 1
    assert unobserved.observed_proof_targets == unobserved.observed_joint_targets == 0
    assert unobserved.complete_proof.rate is None and unobserved.joint_only_coverage.mean is None


def test_unannotated_correct_relationship_contributes_only_to_graph_metrics():
    planned = _planned('K0', proof=False)
    data = planned.frozen.saved.model_dump()
    data['truth']['relationships'] = [{
        'source': 'person', 'target': 'trust', 'type': 'trustee_of', 'approved_evidence': ['Evidence a.'],
    }]
    data['source_approval']['relationships'] = [{
        'source': 'person', 'target': 'trust', 'type': 'trustee_of', 'approved_evidence': [_pair('a')],
    }]
    frozen = replace(planned.frozen, saved=SavedIdeal.model_validate(data))
    report = _report([PlannedCondition('K', frozen)], {'K0': _prediction(_pair('a'))})
    assert report.quality.qualified_graph.f1 == 1.0
    assert report.quality.expected_relationships == 1
    assert report.quality.complete_proof.targets == 0
    assert report.quality.complete_proof.rate is None
    assert report.joint_targets == ()
