import pytest
from pydantic import ValidationError

from benchmark_v3.exploratory_consensus import (
    PANEL, Citation, EvidenceReview, Opinion, Review, Route, Ruling, aggregate, verify_evidence_rulings,
)
from private_client_graph.models.source import Source


def sources():
    return [Source(id=f'd{i}', title=f'Title {i}', text=f'Body {i}.') for i in range(65)]


def claim(*, source='A', predicate='spouse_of', target='B', position='support',
          quote='Body 0.', complete=True):
    return Opinion(source=source, predicate=predicate, target=target, position=position,
                   confidence='high', timing='Held at cutoff.', reason='Interpretation.',
                   routes=[Route(complete=complete, members=[Citation(source_id='d0', quote=quote)])])


def panel(*opinions):
    return {reviewer: Review(relationships=list(rows), unresolved=[], contradictions=[])
            for reviewer, rows in zip(PANEL, [*opinions, *([()] * (10 - len(opinions)))], strict=True)}


def ruling(*routes, decision='supported', source='A', predicate='spouse_of', target='B'):
    return Ruling(source=source, predicate=predicate, target=target, decision=decision,
                  accepted_route_ids=list(routes), reason='A separate review considered the intact documentary proof.')


def test_voting_distinguishes_explicit_rejection_uncertainty_and_omission():
    votes = panel(*([(claim(),)] * 5), (claim(source='B', target='A'),),
                  (claim(position='reject'),), (claim(position='uncertain'),))
    result, = aggregate(votes, sources())
    assert result.edge == ('A', 'spouse_of', 'B')
    assert result.counts == {'support': 6, 'reject': 1, 'uncertain': 1, 'omitted': 2}
    assert result.votes['r09'] is None
    assert result.votes['r07'].position == 'reject'
    assert result.votes['r06'].source == 'B'
    assert aggregate(dict(reversed(votes.items())), sources()) == [result]


def test_directed_edges_and_cutoff_differences_stay_visible():
    original = claim(predicate='parent_of')
    reverse = claim(predicate='parent_of', source='B', target='A')
    temporal_return = claim(predicate='parent_of', position='reject').model_copy(
        update={'timing': 'Only after cutoff; previous appointment expressly expired.'})
    rows = aggregate(panel((original, reverse), (temporal_return,)), sources())
    assert [row.edge for row in rows] == [('A', 'parent_of', 'B'), ('B', 'parent_of', 'A')]
    assert rows[0].counts['reject'] == 1
    assert 'after cutoff' in rows[0].votes['r02'].timing


def test_exact_panel_and_source_count_are_required():
    votes = panel()
    with pytest.raises(ValueError, match='ten'):
        aggregate({name: value for name, value in votes.items() if name != 'r10'}, sources())
    with pytest.raises(ValueError, match='65'):
        aggregate(votes, sources()[:-1])
    with pytest.raises(ValidationError, match='one position'):
        panel((claim(), claim(source='B', target='A')))


def test_bad_body_member_invalidates_the_whole_route_and_votes_survive():
    wrong = claim(quote='Title 0.')
    invalid_joint = wrong.model_copy(update={'routes': [Route(complete=True, members=[
        Citation(source_id='d0', quote='Body 0.'),
        Citation(source_id='missing', quote='Body 1.'),
    ])]})
    result, = aggregate(panel(*([(wrong,)] * 5), (invalid_joint,)), sources())
    assert result.counts['support'] == 6
    assert result.eligible_routes == []
    assert any('missing' in issue for issue in result.citation_issues)
    verdict = EvidenceReview(rulings=[ruling(decision='unresolved')], limitations=[])
    assert verify_evidence_rulings([result], verdict) == []


def test_intact_routes_are_never_merged_and_incomplete_routes_cannot_pass():
    incomplete = claim(complete=False)
    other = incomplete.model_copy(update={'routes': [
        Route(complete=False, members=[Citation(source_id='d1', quote='Body 1.')]),
    ]})
    result, = aggregate(panel(*([(incomplete,)] * 5), (other,)), sources())
    assert len(result.eligible_routes) == 2
    assert all(len(route.members) == 1 for route in result.eligible_routes)
    with pytest.raises(ValueError, match='submitted as complete'):
        verify_evidence_rulings([result], EvidenceReview(
            rulings=[ruling(result.eligible_routes[0].route_id)], limitations=[]))


def test_only_majority_edges_and_their_own_intact_routes_may_be_adjudicated():
    joint = claim().model_copy(update={'routes': [Route(complete=True, members=[
        Citation(source_id='d0', quote='Body 0.'), Citation(source_id='d1', quote='Body 1.'),
    ])]})
    matrix = aggregate(panel(*([(joint,)] * 6), (claim(source='C', target='D'),)), sources())
    chosen = matrix[0].eligible_routes[0]
    assert [item.source_id for item in chosen.members] == ['d0', 'd1']
    verdict = EvidenceReview(rulings=[ruling(chosen.route_id)], limitations=[])
    assert verify_evidence_rulings(matrix, verdict) == [('A', 'spouse_of', 'B')]
    with pytest.raises(ValueError, match='exactly once'):
        verify_evidence_rulings(matrix, EvidenceReview(
            rulings=[*verdict.rulings, ruling(source='C', target='D', decision='unresolved')], limitations=[]))


def test_incompatible_endpoint_types_are_flagged_not_silently_resolved():
    votes = [(claim(), claim(source='A', predicate='trustee_of', target='B'))] * 6
    matrix = aggregate(panel(*votes), sources())
    assert [row.entity_type_conflicts for row in matrix] == [['B'], ['B']]
    claimant, trust = matrix
    assert trust.endpoint_types == ('person', 'trust')
    with pytest.raises(ValueError, match='consistent entity types'):
        verify_evidence_rulings(matrix, EvidenceReview(rulings=[
            ruling(claimant.eligible_routes[0].route_id),
            ruling(predicate='trustee_of', decision='unresolved'),
        ], limitations=[]))
