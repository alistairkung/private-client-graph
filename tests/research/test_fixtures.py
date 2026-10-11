from private_client_graph.research.fixtures import load_inputs
from private_client_graph.graph import build_graph
from private_client_graph.evaluation import evaluate_graph


def test_six_reviewed_inputs_preserve_known_controls_and_opposite_identity_truth():
    samples = load_inputs()
    assert len(samples) == 6
    by_id = {s.sample_id: s for s in samples}
    merge, distinct = by_id['alias_merge'], by_id['alias_distinct']
    assert merge.extraction == distinct.extraction
    assert merge.source != distinct.source
    assert len(merge.truth.entities) == 2
    assert len(distinct.truth.entities) == 3
    assert merge.annotations[0].participant == merge.annotations[2].participant
    assert distinct.annotations[0].participant != distinct.annotations[2].participant
    for sample in samples:
        assert len(sample.annotations) == 2 * len(sample.extraction.relationships)
        graph = build_graph(sample.extraction.relationships, document='source.txt', source_text=sample.source)
        score = evaluate_graph(graph, sample.truth)
        if sample.sample_id == 'case_03_fixture':
            assert (score.tp, score.fp, score.fn) == (6, 1, 1)
        elif sample.sample_id == 'alias_merge':
            assert (score.tp, score.fp, score.fn) == (1, 1, 1)
        else:
            assert score.f1 == score.provenance_accuracy == 1
    assert by_id['case_03_historical'].cohort == 'historical'
    assert by_id['case_03_historical'].historical['metadata']['model'] == 'deepseek-flash'
