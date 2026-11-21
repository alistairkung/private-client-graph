"""Benchmark v2 reporting over real frozen Workbench Run artifacts."""
from pathlib import Path

from benchmark_v2.report import ReportManifest, development_report
from private_client_graph.research.artifacts import Bundle
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.retained_inputs import input_digests, value_digest
from private_client_graph.research.runner import execute
from private_client_graph.workbench.case_catalog import repository_inputs
from private_client_graph.workbench.run_planning import freeze_run
from private_client_graph.workbench.workspace_contracts import (
    CreateExperiment,
    DraftUpdate,
    FreezeRun,
    RunConfiguration,
)
from private_client_graph.workbench.workspaces import create_experiment, update_draft


def _sample() -> ResearchInput:
    return next(
        sample for sample in repository_inputs()
        if sample.sample_id == 'benchmark_v1_aliases_dev_1_fixture'
    )


def _manifest(sample: ResearchInput, *, observations: int = 1, mode: str = 'replay',
              required: list | None = None) -> ReportManifest:
    labels = {
        'condition': 'D1',
        'input_id': sample.sample_id,
        'targets': {
            'required': [['Daniel Wu', 'beneficiary_of', 'Ashford Family Trust']] if required is None else required,
            'forbidden': [], 'unaffected': [], 'sufficiency': [],
        },
    }
    return ReportManifest.model_validate({
        'evaluator_version': 'semantic_edges_v1',
        'execution_mode': mode,
        'conditions': [{
            **labels, **input_digests(sample), 'annotation_digest': value_digest(labels),
            'matter_family': 'aliases', 'case_id': sample.case_id, 'observations': observations,
        }],
    })


def _freeze(root: Path, sample: ResearchInput, *, run_key: str | None = None, **configuration) -> Bundle:
    config = RunConfiguration.model_validate({"input_ids": [sample.sample_id], **configuration})
    experiment = create_experiment(root, CreateExperiment(request_id=run_key or root.name, name='Reporting test'))
    update_draft(root, experiment.id, DraftUpdate(request_id='draft', expected_revision=0, configuration=config))
    plan = freeze_run(root, experiment.id, FreezeRun(request_id='freeze', expected_revision=1))
    return Bundle.open(root / plan.id)


def test_development_report_preserves_individual_scores_and_unfrozen_slots(tmp_path):
    sample = _sample()
    run = _freeze(tmp_path, sample, input_mode='saved', execution_mode='replay', resolver='none')

    def unexpected_provider(_request):
        raise AssertionError('No calls for saved replay or reporting')

    execute(run, provider=unexpected_provider)
    report = development_report(_manifest(sample, observations=2), [run.path])
    baseline = report['baseline']
    assert baseline['coverage'] == {
        'planned': 2, 'scored': 1, 'failed': 0, 'uncertain': 0, 'pending': 0, 'unavailable': 1,
    }
    condition = baseline['conditions'][0]
    assert condition['condition'] == 'D1'
    observed, unfrozen = condition['observations']
    assert observed['graph']['exact_graph'] is True
    assert observed['graph']['f1'] == 1
    assert observed['quote_provenance']['accuracy'] == 1
    assert observed['source_attribution']['accuracy'] == 1
    assert observed['decisions']['required']['present'] == [
        ('Daniel Wu', 'beneficiary_of', 'Ashford Family Trust'),
    ]
    assert observed['decisions']['forbidden']['fraction'] is None
    assert observed['resources']['cost']['total'] == 0
    assert unfrozen['graph'] is None
    assert Bundle.open(run.path).attempt_count == 0


def test_paired_report_distinguishes_fixes_regressions_and_missing_pairs(tmp_path):
    from benchmark_v2.report import final_report
    from private_client_graph.research.provider import ModelResponse, TokenUsage

    sample = _sample()
    baseline = _freeze(tmp_path, sample, input_mode='fresh', execution_mode='recorded',
                       resolver='none', invocation_cap=1)
    final = _freeze(tmp_path / 'final', sample, input_mode='fresh', execution_mode='recorded',
                    resolver='none', invocation_cap=1)
    assert sample.sourced_extraction is not None
    ideal = sample.sourced_extraction.relationships
    spurious = ideal[-1].model_copy(update={'source_name': 'Danny'})

    execute(baseline, provider=lambda _: ModelResponse(
        payload={'relationships': [item.model_dump() for item in [*ideal[1:], spurious]]},
        usage=TokenUsage(input_tokens=100, output_tokens=60, cached_tokens=0),
        raw_response={'response_metadata': {'system_fingerprint': 'baseline-fp'}},
    ))
    execute(final, provider=lambda _: ModelResponse(
        payload={'relationships': [item.model_dump() for item in [*ideal[:1], *ideal[2:]]]},
        usage=TokenUsage(input_tokens=150, output_tokens=40, cached_tokens=10),
        raw_response={'response_metadata': {'system_fingerprint': 'final-fp'}},
    ))
    report = final_report(_manifest(sample, mode='recorded'), [baseline.path], [final.path])
    assert report['paired_coverage'] == {'planned': 1, 'scored': 1}
    pair = report['pairs'][0]
    assert pair['baseline']['graph']['f1'] == .8
    assert pair['final']['graph']['f1'] == 8 / 9
    assert pair['delta']['fp_fixed'] == [('Danny', 'beneficiary_of', 'Ashford Family Trust')]
    assert pair['delta']['fn_fixed'] == [('Margaret Wu', 'settlor_of', 'Ashford Family Trust')]
    assert pair['delta']['fn_regressed'] == [('Margaret Wu', 'spouse_of', 'Thomas Wu')]
    assert pair['delta']['tokens']['input_tokens'] == 50
    assert pair['delta']['tokens']['output_tokens'] == -20
    assert pair['delta']['quote_provenance']['passes_gained'] == [
        ('Margaret Wu', 'settlor_of', 'Ashford Family Trust'),
    ]
    assert pair['delta']['fingerprints_changed'] is True
    fingerprints = report['baseline']['historical_fingerprint']
    assert fingerprints['comparison'] == 'drift_observed'
    assert fingerprints['observed'] == ['baseline-fp']
    assert pair['delta']['provider_seconds'] is not None

    missing = final_report(_manifest(sample, mode='recorded'), [baseline.path], [])
    assert missing['paired_coverage'] == {'planned': 1, 'scored': 0}
    assert missing['final']['coverage']['unavailable'] == 1
    assert missing['pairs'][0]['delta'] is None
    assert missing['paired_graph']['baseline']['f1'] is None


def test_development_report_excludes_replays_from_fresh_baseline(tmp_path):
    sample = _sample()
    run = _freeze(tmp_path, sample, input_mode='saved', execution_mode='replay', resolver='none')
    execute(run, provider=lambda _: None)
    manifest = _approved_development(_manifest(sample, mode='live'), [run])
    report = development_report(manifest, [run.path])
    observed = report['baseline']['conditions'][0]['excluded_observations'][0]
    assert observed['state'] == 'unavailable'
    assert observed['graph'] is None
    assert 'execution mode' in observed['reason'].lower()


def test_paired_report_excludes_changed_ordered_source_commitment(tmp_path):
    from benchmark_v2.report import final_report
    from private_client_graph.research.provider import ModelResponse

    sample = next(
        sample for sample in repository_inputs()
        if sample.sample_id == 'benchmark_v1_cross_source_dev_1_fixture'
    )
    assert sample.sources and len(sample.sources) > 1 and sample.sourced_extraction
    run = _freeze(tmp_path, sample, input_mode='fresh', execution_mode='recorded',
                  resolver='none', invocation_cap=1)
    execute(run, provider=lambda _: ModelResponse(payload=sample.sourced_extraction.model_dump()))
    reversed_input = sample.model_copy(update={'sources': list(reversed(sample.sources))})
    manifest = _manifest(reversed_input, mode='recorded', required=[])
    report = final_report(manifest, [run.path], [])
    observed = report['pairs'][0]['baseline']
    assert observed['state'] == 'unavailable'
    excluded = report['baseline']['conditions'][0]['excluded_observations'][0]
    assert 'source_digest' in excluded['reason']
    assert report['pairs'][0]['delta'] is None


def test_live_report_counts_failed_and_uncertain_attempts_without_pricing(tmp_path, monkeypatch):
    from private_client_graph.research.artifacts import write_json_once
    from private_client_graph.research.live_accounting import initialize_task
    from private_client_graph.research.run_plan import RunPlan

    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    initialize_task(tmp_path, 'Substituted retained reporting records')
    sample = _sample()
    runs = [_freeze(tmp_path, sample, run_key=f'batch-{index}', input_mode='fresh', execution_mode='live',
                    resolver='none', invocation_cap=1, task_call_cap=3) for index in range(3)]
    for index, (run, fields) in enumerate(zip(runs, [
        {'status': 'provider_error', 'provider_seconds': 2.5,
         'response': {'usage': {'input_tokens': 90, 'output_tokens': 0, 'cached_tokens': 0}}},
        {'status': 'uncertain'},
    ])):
        assert isinstance(run.plan, RunPlan)
        identity = run.plan.planned_slots[0].extraction_attempt_id
        record = {'attempt_id': identity, 'started_at': f'2026-11-21T00:00:0{1 - index}+00:00', **fields}
        prefix = run.manifest['experiment_id']
        write_json_once(run.path / 'attempts' / f'{identity}.started.json', record)
        write_json_once(run.task_ledger / 'reservations' / f'{prefix}-{identity}.json', record)

    manifest = _approved_development(_manifest(sample, observations=3, mode='live'), runs)
    baseline = development_report(manifest, [run.path for run in runs])['baseline']
    assert baseline['coverage'] == {
        'planned': 3, 'scored': 0, 'pending': 1, 'failed': 1, 'uncertain': 1, 'unavailable': 0,
    }
    assert baseline['chronology']['state'] == 'deviation'
    assert baseline['historical_fingerprint']['comparison'] == 'unknown'
    resources = baseline['resources']
    assert resources['retained_attempts'] == resources['cost']['attempts'] == 2
    assert resources['cost']['total'] is None
    assert resources['cost']['unpriced_attempts'] == 2
    assert resources['tokens']['input_tokens'] == {'known_subtotal': 90, 'measured_attempts': 1, 'total': None}
    assert resources['provider_seconds'] == {'known_subtotal': 2.5, 'measured_attempts': 1, 'total': None}
    assert all(row['graph'] is None for row in baseline['conditions'][0]['observations'])


def test_live_development_requires_approved_plans_with_frozen_batches(tmp_path, monkeypatch):
    from private_client_graph.research.live_accounting import initialize_task

    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    initialize_task(tmp_path, 'Reporting plan and batch test')
    sample = _sample()
    run = _freeze(tmp_path, sample, input_mode='fresh', execution_mode='live', resolver='none',
                  extraction_samples=2, task_call_cap=2, invocation_cap=2)
    manifest = _manifest(sample, observations=2, mode='live')
    approval = {'baseline_plan_digests': [_plan_digest(run), '0' * 64],
                'development_batches': [['D1'], ['D1']]}
    result = development_report(manifest.model_copy(update=approval), [run.path])
    baseline = result['baseline']
    assert baseline['coverage']['unavailable'] == 2
    assert baseline['coverage']['pending'] == 0
    assert 'allocation' in baseline['runs'][0]['protocol_mismatch'].lower()


def _plan_digest(run: Bundle) -> str:
    from private_client_graph.research.live_accounting import plan_digest
    return plan_digest(run)


def test_final_report_excludes_pair_run_in_reverse_protocol_order(tmp_path):
    from benchmark_v2.report import final_report
    from private_client_graph.research.provider import ModelResponse

    sample = _sample()
    baseline = _freeze(tmp_path, sample, input_mode='fresh', execution_mode='recorded',
                       resolver='none', invocation_cap=1)
    final = _freeze(tmp_path / 'final', sample, input_mode='fresh', execution_mode='recorded',
                    resolver='none', invocation_cap=1)
    assert sample.sourced_extraction is not None
    response = ModelResponse(payload=sample.sourced_extraction.model_dump())
    execute(final, provider=lambda _: response)
    execute(baseline, provider=lambda _: response)

    report = final_report(_manifest(sample, mode='recorded'), [baseline.path], [final.path])
    assert report['pairs'][0]['chronology']['state'] == 'deviation'
    assert report['paired_coverage']['scored'] == 0
    assert report['pairs'][0]['delta'] is None
    assert report['baseline']['coverage']['scored'] == report['final']['coverage']['scored'] == 1



def _approved_development(manifest: ReportManifest, runs: list[Bundle]) -> ReportManifest:
    return manifest.model_copy(update={
        'baseline_plan_digests': [_plan_digest(run) for run in runs],
        'development_batches': [['D1'] for run in runs],
    })


def test_final_report_excludes_a_pair_with_different_source_attribution_code(tmp_path, monkeypatch):
    from benchmark_v2.report import final_report
    from private_client_graph.research.provider import ModelResponse

    sample = _sample()
    assert sample.sourced_extraction is not None
    response = ModelResponse(payload=sample.sourced_extraction.model_dump())
    baseline = _freeze(tmp_path, sample, input_mode='fresh', execution_mode='recorded',
                       resolver='none', invocation_cap=1)
    execute(baseline, provider=lambda _: response)

    original_read = Path.read_text

    def read_changed_source_attribution(path, *args, **kwargs):
        content = original_read(path, *args, **kwargs)
        return content + '\n# Different source scorer snapshot.\n' if path.name == 'source_attribution.py' else content

    with monkeypatch.context() as changed:
        changed.setattr(Path, 'read_text', read_changed_source_attribution)
        final = _freeze(tmp_path / 'final', sample, input_mode='fresh', execution_mode='recorded',
                        resolver='none', invocation_cap=1)
        execute(final, provider=lambda _: response)

    report = final_report(_manifest(sample, mode='recorded'), [baseline.path], [final.path])
    assert report['pairs'][0]['chronology']['state'] == 'verified'
    assert 'evaluator implementations' in report['pairs'][0]['exclusion_reason']
    assert report['pairs'][0]['delta'] is None


def test_unexpected_input_excludes_the_whole_run_from_scoring(tmp_path):
    sample = _sample()
    run = _freeze(tmp_path, sample, input_mode='saved', execution_mode='replay', resolver='none',
                  input_ids=[sample.sample_id, 'benchmark_v1_cross_source_dev_1_fixture'])
    execute(run, provider=lambda _: None)
    baseline = development_report(_manifest(sample), [run.path])['baseline']
    assert baseline['coverage']['scored'] == 0
    assert baseline['coverage']['unavailable'] == 1
    assert baseline['unexpected_inputs'][0]['input_id'] == 'benchmark_v1_cross_source_dev_1_fixture'


def test_live_development_excludes_approved_batches_spread_across_ledgers(tmp_path, monkeypatch):
    from private_client_graph.research.live_accounting import initialize_task

    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    sample = _sample()
    runs = []
    for name in ('first-ledger', 'second-ledger'):
        root = tmp_path / name
        initialize_task(root, 'Substituted study task')
        runs.append(_freeze(root, sample, input_mode='fresh', execution_mode='live',
                            resolver='none', task_call_cap=2, invocation_cap=1))
    manifest = _approved_development(_manifest(sample, observations=2, mode='live'), runs)
    baseline = development_report(manifest, [run.path for run in runs])['baseline']
    assert baseline['coverage']['unavailable'] == 2
    assert all('ledger' in run['protocol_mismatch'] for run in baseline['runs'])


def test_live_final_report_rejects_inconsistent_approved_task_caps(tmp_path, monkeypatch):
    from benchmark_v2.report import final_report
    from private_client_graph.research.live_accounting import initialize_task

    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    initialize_task(tmp_path, 'Substituted final task')
    sample = _sample()
    baseline = _freeze(tmp_path, sample, run_key='baseline', input_mode='fresh', execution_mode='live',
                       resolver='none', invocation_cap=1, task_call_cap=2)
    final = _freeze(tmp_path, sample, run_key='final', input_mode='fresh', execution_mode='live',
                    resolver='none', invocation_cap=1, task_call_cap=3)
    manifest = _manifest(sample, mode='live').model_copy(update={
        'baseline_plan_digests': [_plan_digest(baseline)], 'final_plan_digests': [_plan_digest(final)],
    })
    report = final_report(manifest, [baseline.path], [final.path])
    assert final_report(manifest, [baseline.path], [])['shared_task_mismatch'] == (
        'Run cap differs from the predeclared final attempt cap.')
    revised = manifest.model_copy(update={'final_attempt_cap': 2})
    assert final_report(revised, [baseline.path], [])['shared_task_mismatch'] is None
    assert 'different' in report['shared_task_mismatch']
    assert report['baseline']['coverage']['unavailable'] == report['final']['coverage']['unavailable'] == 1
