"""Benchmark-only eligibility and protected-scorer boundaries."""
import json

import pytest

from benchmark_v2.evidence_policy import ordinary_evidence
from benchmark_v2.preflight import STUDY, quarantined_input
from private_client_graph.pipeline import Pipeline, PipelineConfig
from private_client_graph.research.benchmark_decisions import DecisionTargets
from private_client_graph.research.source_attribution import SourceEvidenceApproval


@pytest.fixture
def linked():
    sample = quarantined_input()
    row = next(r for r in json.loads((STUDY / 'development.json').read_bytes()) if r['condition'] == 'D13')
    labels = DecisionTargets.model_validate(row['targets'])
    state = Pipeline(PipelineConfig()).run_from_sourced_extraction(sample.sources, sample.sourced_extraction).state
    return state, sample.truth, labels


def test_exemption_requires_an_explicit_joint_label_and_no_standalone_approval(linked):
    state, truth, labels = linked
    with pytest.raises(ValueError, match='explicitly joint-only'):
        ordinary_evidence(state, truth, DecisionTargets(), None)
    # The historical scorer pools repeated appearances of a semantic edge.
    duplicate = truth.relationships[0].model_copy(update={
        'approved_evidence': [labels.sufficiency[0].alternatives[0][0].supporting_text]})
    truth.relationships.append(duplicate)
    with pytest.raises(ValueError, match='explicitly joint-only'):
        ordinary_evidence(state, truth, labels, None)


def test_joint_label_rejects_an_independently_sufficient_alternative(linked):
    _, _, labels = linked
    raw = labels.model_dump()
    raw['sufficiency'][0]['alternatives'].append(raw['sufficiency'][0]['alternatives'][0][:1])
    with pytest.raises(ValueError, match='multiple Sources'):
        DecisionTargets.model_validate(raw)


def test_eligible_source_approval_must_cover_all_remaining_edges(linked):
    state, truth, labels = linked
    labels.ordinary_source_approval.relationships.pop()
    with pytest.raises(ValueError, match='complete ground truth'):
        ordinary_evidence(state, truth, labels, None)


def test_all_joint_only_truth_has_no_ordinary_evidence_denominator(linked):
    state, truth, labels = linked
    truth.relationships = [r for r in truth.relationships if not r.approved_evidence]
    labels.ordinary_source_approval = SourceEvidenceApproval(relationships=[])
    evidence = ordinary_evidence(state, truth, labels, None)
    for name in ('quotation', 'source_attribution'):
        assert evidence[name]['accuracy'] is None
        assert evidence[name]['assessed'] == evidence[name]['failed'] == 0
