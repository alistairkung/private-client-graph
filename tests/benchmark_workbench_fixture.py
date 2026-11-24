"""Synthetic, offline retained records for Workbench browser and API tests."""

from benchmark_v3.evaluation_protocol import PlannedCondition, evaluate_protocol
from benchmark_v3.replay_manifest import SavedIdeal, VerifiedCondition, VerifiedFamily
from benchmark_v3.retained_evaluation import VerifiedBaseline
from private_client_graph.models import SourcedExtractionResult
from private_client_graph.models.source import Source
from private_client_graph.pipeline import Pipeline, PipelineConfig
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.retained_inputs import value_digest


_TERMS = {'source_id': 'terms', 'supporting_text': 'The document defines the office.'}
_REGISTER = {'source_id': 'register', 'supporting_text': 'Morgan is the current holder.'}
_ALTERNATE = {'source_id': 'audit', 'supporting_text': 'The audit confirms Morgan holds the office.'}
_WRONG = {'source_id': 'register', 'supporting_text': 'Morgan was nominated earlier.'}


def _condition(identity: str, *, empty: bool = False) -> PlannedCondition:
    sources = [
        Source(id='terms', title='Terms', text=_TERMS['supporting_text']),
        Source(id='register', title='Register', text=f"{_REGISTER['supporting_text']} {_WRONG['supporting_text']}"),
        Source(id='audit', title='Audit', text=_ALTERNATE['supporting_text']),
    ]
    entities = [
        {'id': 'person', 'name': 'Morgan Example', 'type': 'person'},
        {'id': 'trust', 'name': 'North Example Trust', 'type': 'trust'},
    ]
    relationship = {'source': 'person', 'target': 'trust', 'type': 'trustee_of', 'approved_evidence': []}
    proof = {
        'edge': ['Morgan Example', 'trustee_of', 'North Example Trust'],
        'joint_only': True, 'alternatives': [[_TERMS, _REGISTER], [_TERMS, _ALTERNATE]],
    }
    key = SavedIdeal.model_validate({
        'condition': identity,
        'truth': {'entities': entities, 'relationships': [] if empty else [relationship]},
        'source_approval': {'relationships': []}, 'ideal': {'relationships': []},
        'sufficient_evidence': [] if empty else [proof],
    })
    frozen = VerifiedCondition(
        key, sources, value_digest(key.model_dump(mode='json')),
        value_digest([row.model_dump(mode='json') for row in sources]), {},
    )
    return PlannedCondition(identity[0], frozen)


def _prediction(*quotes: dict[str, str]) -> SourcedExtractionResult:
    return SourcedExtractionResult.model_validate({
        'relationships': [
            {'source_name': 'Morgan Example', 'target_name': 'North Example Trust',
             'relationship_type': 'trustee_of', **quote}
            for quote in quotes
        ],
    })


def synthetic_verified_run(arm: str) -> VerifiedBaseline:
    roster = [_condition('F0'), _condition('F1'), _condition('G0', empty=True)]
    if arm == 'reordered':
        roster.reverse()
    predictions = {'F0': _prediction(_TERMS, _WRONG), 'F1': _prediction(), 'G0': _prediction()}
    if arm == 'control':
        predictions['F1'] = _prediction(_TERMS | {'supporting_text': 'Invalid quote absent from the Source.'})
    if arm == 'treatment':
        predictions['F0'] = _prediction(_TERMS, _REGISTER, _WRONG)
        # Explicit not-attempted outcome remains in the paired roster.
        del predictions['F1']

    report = evaluate_protocol(roster, predictions, benchmark_sha256='a' * 64,
                               observation_origin='offline_fixture')
    results = {}
    for item in roster:
        identity = item.frozen.saved.condition
        outcome = report.conditions[identity]
        prediction = predictions.get(identity)
        common = dict(sample_id=f'{item.frozen.sample_id}_fresh_01', case_id=item.family,
                      cohort='fresh', sourced_extraction=prediction, configuration='noop', repetition=1)
        if outcome.outcome == 'scored' and prediction is not None:
            built = Pipeline(PipelineConfig()).run_from_sourced_extraction(item.frozen.sources, prediction)
            results[identity] = ResearchResult.model_validate(dict(
                **common, state=built.state, graph=built.graph, evaluation=outcome.graph))
        else:
            status = 'graph_error' if outcome.outcome == 'validation_failure' else 'unavailable'
            results[identity] = ResearchResult.model_validate(dict(**common, status=status))

    families = {
        family: VerifiedFamily(family, 'b' * 64, 'c' * 64, {
            row.frozen.saved.condition: row.frozen for row in sorted(roster, key=lambda row: row.frozen.saved.condition)
            if row.family == family
        }, {}, {}, set(), set())
        for family in report.families
    }
    return VerifiedBaseline(report, tuple(roster), predictions, results, families)


FIXTURE_EXPERIMENT = 'e' * 32
FIXTURE_RUNS = {'control': '1' * 32, 'treatment': '2' * 32, 'reordered': '3' * 32}


def _fixture_context(benchmark):
    """Research context authored only for the synthetic demonstration records."""
    from private_client_graph.workbench.family_context import FamilyResearchContext, RunFamilyContext

    families = {}
    for family, description, intent, conditions in [
        ('F', 'Identify the current trustee from the office records.',
         'An earlier nomination can be mistaken for evidence of current office.',
         {'F0': 'Read the register alongside the terms that define the office.',
          'F1': 'Check whether the office record and its defining terms support the same relationship.'}),
        ('G', 'Determine whether the file establishes any relationship.',
         'A mention of an office can be mistaken for an established relationship.',
         {'G0': 'Inspect a constructed graph with no relationships.'}),
    ]:
        families[family] = FamilyResearchContext(
            revision='synthetic-demo', dossier_sha256=value_digest(family),
            description=description, shortcuts=intent, hypothesis_text=intent,
            hypothesis_basis='historical_admission', hypothesis=None,
            primary_axis='evidence-sufficiency', secondary_axes=[],
            condition_intents=conditions, verified_findings=[], incidental_challenges=[],
            scope_limits='Synthetic demonstration file.',
        )
    return RunFamilyContext(
        benchmark_sha256=benchmark.scope.benchmark_sha256, families=families,
        axis_definitions={'evidence-sufficiency': 'Whether the cited records jointly establish the relationship.'},
    )


def register_benchmark_browser_fixture(root):
    from private_client_graph.workbench.benchmark_contracts import BenchmarkRun, condition_relationship_outcomes
    from private_client_graph.workbench.benchmark_v3_import import register_offline_fixture_for_tests
    from private_client_graph.workbench.execution_contracts import FrozenPlan, Preview, Proposal
    from private_client_graph.workbench.run_evaluation_contracts import RunAggregate, RunCost, RunEvaluation
    from private_client_graph.workbench.run_inspection import RunDetail, RunObservation

    for arm, identity in FIXTURE_RUNS.items():
        verified = synthetic_verified_run(arm)
        benchmark = BenchmarkRun.from_verified(verified)
        observations = []
        for condition, planned in zip(benchmark.observations, verified.planned, strict=True):
            frozen = planned.frozen
            result = verified.original_results[condition.condition]
            observations.append(RunObservation(
                id=condition.condition, sample_id=frozen.sample_id, case_id=condition.family,
                configuration='noop', repetition=1, status=condition.outcome, reason=condition.failure_detail,
                sources=frozen.sources, result=result, benchmark=condition,
                relationships=condition_relationship_outcomes(condition, result.evaluation, result.state),
            ))
        plan = FrozenPlan(
            id=identity, digest=value_digest(arm), task_id='synthetic',
            created_at='2026-11-24T00:00:00+00:00',
            preview=Preview(proposal=Proposal(input_ids=['synthetic']), inputs=[],
                extraction_call_maximum=0, resolution_call_maximum=0, matrix_call_maximum=0,
                planned_observations=len(observations), invocation_cap=0),
        )
        register_offline_fixture_for_tests(root, RunDetail(
            id=identity, experiment_id=FIXTURE_EXPERIMENT, plan=plan,
            lifecycle='incomplete' if arm == 'treatment' else 'complete',
            evaluation=RunEvaluation(run_id=identity, aggregate=RunAggregate(), cost=RunCost()), benchmark=benchmark, observations=observations,
            family_context=_fixture_context(benchmark), provenance={'fixture_arm': arm}, artifact_digest=value_digest(arm),
            authorized_invocations=[], attempts=[],
        ))
