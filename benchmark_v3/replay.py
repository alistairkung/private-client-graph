"""Replay frozen Benchmark v3 ideals with no access to a provider."""

import argparse
import json
from pathlib import Path
from typing import Any, NoReturn

from private_client_graph.canonical_state import reconstruct_graph
from private_client_graph.evaluation import evaluate_graph
from private_client_graph.extraction.semantic import SOURCED_EXTRACTION_PROMPT
from private_client_graph.models import EvaluationResult, ExtractionResult
from private_client_graph.models.evaluation_result import SemanticEdge
from private_client_graph.research.artifacts import Bundle, checksum, write_json_once
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.provider import ModelRequest, request_messages
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.retained_inputs import value_digest
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.research.runner import execute
from private_client_graph.workbench.artifacts import artifact_digest
from private_client_graph.workbench.run_evaluation import evaluate_run

from .replay_evidence import assess_evidence
from .replay_manifest import VerifiedCondition, VerifiedFamily, load_family


# benchmark_v2/baseline.json at the protocol's frozen c4a21e5f revision.
FROZEN_SOURCED_PROMPT_SHA256 = 'd67afaeb19c26448a6779d9576800cc50ca399c634ad81a1a02b847be0a9dfae'


def preflight(manifest: Path, artifacts: Path) -> dict[str, Any]:
    """Verify the matched inputs, replay the saved ideals, and audit the reopened Run."""
    family = load_family(manifest)
    if artifacts.exists() and (not artifacts.is_dir() or any(artifacts.iterdir())):
        raise ValueError('Select a new or empty artifact directory for the offline replay')

    plan = _make_plan(family)
    preview = _make_preview(plan)
    write_json_once(artifacts / 'preview.json', preview)
    bundle = Bundle.create(artifacts / 'run', plan, task_ledger=artifacts / 'offline-ledger')
    execute(bundle, provider=_offline_only)
    aggregate, results, run_digest = _read_results(plan, bundle.path, preview['sourced_prompt_sha256'])

    conditions = []
    observed = {}
    for identity, condition in family.conditions.items():
        row, edges = _inspect_result(family, identity, results[condition.sample_id])
        conditions.append(row)
        observed[identity] = edges
    matches = _verify_matched_observations(family, observed)
    report = dict(schema_version=1, family=family.family, mode='saved_ideal_replay',
        manifest_sha256=family.manifest_sha256, freeze_sha256=family.freeze_sha256,
        preview=preview, paid_attempts=0, run_path='run',
        run_artifact_digest=run_digest, aggregate=aggregate, conditions=conditions, matches=matches)
    write_json_once(artifacts / 'preflight.json', report)
    return report


def _make_plan(family: VerifiedFamily) -> RunPlan:
    return RunPlan(task_id=f'benchmark-v3-family-{family.family.lower()}-offline', inputs=[
        _research_input(condition) for condition in family.conditions.values()
    ], input_mode='saved', execution_mode='replay', resolver='none', repetitions=1)


def _research_input(condition: VerifiedCondition) -> ResearchInput:
    saved = condition.saved
    # The saved Run contract also carries a legacy extraction projection.
    # Construction uses the Source-aware ideal and the complete Source array.
    projection = ExtractionResult.model_validate({'relationships': [
        item.model_dump(exclude={'source_id'}) for item in saved.ideal.relationships
    ]})
    joint_only = any(item.joint_only for item in saved.sufficient_evidence)
    return ResearchInput(sample_id=condition.sample_id, case_id=condition.sample_id, cohort='authored',
        source='', sources=condition.sources, truth=saved.truth, extraction=projection,
        sourced_extraction=saved.ideal, source_evidence=None if joint_only else saved.source_approval,
        origin_hashes={'condition': condition.case_sha256, 'ordered_sources': condition.sources_sha256})


def _make_preview(plan: RunPlan) -> dict[str, Any]:
    if plan.maximum_attempts or plan.max_calls or plan.invocation_cap or plan.task_call_cap:
        raise ValueError('The saved replay preview must authorize zero paid slots')
    prompt_digest = checksum(SOURCED_EXTRACTION_PROMPT.encode('utf-8'))
    if prompt_digest != FROZEN_SOURCED_PROMPT_SHA256:
        raise ValueError('Sourced extraction prompt differs from the frozen baseline')
    inputs = []
    for sample in plan.inputs:
        assert sample.sources is not None
        request = ModelRequest(stage='extraction', source=sample.source, sources=sample.sources, settings=plan.settings)
        messages = request_messages(request)
        source_array = [source.model_dump(mode='json') for source in sample.sources]
        expected = [
            ('system', SOURCED_EXTRACTION_PROMPT),
            ('human', json.dumps(source_array, ensure_ascii=False)),
        ]
        if messages != expected or value_digest(source_array) != sample.origin_hashes['ordered_sources']:
            raise ValueError(f'Unexpected extraction request contents for {sample.sample_id}')
        message_bytes = sum(len(content.encode('utf-8')) for _, content in messages)
        inputs.append(dict(id=sample.sample_id, source_count=len(source_array),
            ordered_sources_sha256=sample.origin_hashes['ordered_sources'],
            source_body_sha256={source.id: checksum(source.text.encode('utf-8')) for source in sample.sources},
            messages_sha256=value_digest(messages), message_bytes=message_bytes,
            estimated_message_tokens=(message_bytes + 3) // 4))
    return dict(input_mode=plan.input_mode, execution_mode=plan.execution_mode, resolver=plan.resolver,
        maximum_paid_slots=plan.maximum_attempts, planned_observations=len(plan.planned_slots),
        sourced_prompt_sha256=prompt_digest, inputs=inputs,
        token_estimate='Ceiling of UTF-8 message bytes divided by four, excluding schema and framing.')


def _offline_only(_request: ModelRequest) -> NoReturn:
    raise AssertionError('The saved replay attempted to call a provider')


def _read_results(plan: RunPlan, path: Path, prompt_digest: str
                  ) -> tuple[dict[str, Any], dict[str, ResearchResult], str]:
    digest = artifact_digest(path)
    bundle = Bundle.open(path)
    if bundle.plan != plan:
        raise ValueError('Saved replay inputs changed after the verified freeze')
    prompt = bundle.manifest['provenance']
    if (prompt['prompt_hashes']['sourced_extraction'] != prompt_digest
            or checksum(prompt['prompts']['sourced_extraction'].encode('utf-8')) != prompt_digest):
        raise ValueError('Retained sourced extraction prompt differs from the verified preview')
    retained = evaluate_run(bundle)
    aggregate = retained.aggregate
    if bundle.attempt_count or bundle.task_attempt_count or retained.cost.attempts:
        raise ValueError('Offline replay retained a provider attempt')
    results = [ResearchResult.model_validate(row) for row in bundle.results()]
    by_id = {row.sample_id: row for row in results}
    expected_ids = [slot.sample_id for slot in plan.planned_slots]
    if (set(by_id) != set(expected_ids) or len(results) != len(expected_ids)
            or aggregate.coverage.scored != len(expected_ids)):
        unscored = [slot.observation_id for slot in aggregate.observations if slot.state != 'scored']
        raise ValueError(f'Incomplete offline replay coverage; unscored slots: {", ".join(unscored) or "unknown"}')
    tp, fp, fn = aggregate.tp, aggregate.fp, aggregate.fn
    report = dict(coverage=aggregate.coverage.model_dump(mode='json'), tp=tp, fp=fp, fn=fn,
        micro_precision=tp / (tp + fp) if tp + fp else 0.0,
        micro_recall=tp / (tp + fn) if tp + fn else 0.0, micro_f1=aggregate.f1)
    if artifact_digest(path) != digest:
        raise ValueError('Retained Run artifacts changed during inspection')
    return report, by_id, digest


def _inspect_result(family: VerifiedFamily, identity: str, result: ResearchResult
                    ) -> tuple[dict[str, Any], set[SemanticEdge]]:
    condition = family.conditions[identity]
    saved = condition.saved
    if result.state is None or result.graph is None or result.evaluation is None:
        raise ValueError(f'Unscored saved ideal for {identity}')
    if result.state.sources != condition.sources or result.sourced_extraction != saved.ideal:
        raise ValueError(f'Retained result changed the frozen Sources or saved ideal for {identity}')
    if reconstruct_graph(result.state) != result.graph:
        raise ValueError(f'Retained canonical state disagrees with its Graph for {identity}')
    graph_score = evaluate_graph(result.graph, saved.truth)
    if graph_score != result.evaluation:
        raise ValueError(f'Retained Graph evaluation disagrees with the protected scorer for {identity}')

    required = family.required[identity]
    forbidden = sorted(family.candidates - set(required))
    graph_edges = set(graph_score.true_positive_edges) | set(graph_score.false_positive_edges)
    decisions = dict(required=required, forbidden=forbidden, unaffected=sorted(family.unaffected),
        required_present=sorted(graph_edges & set(required)), forbidden_present=sorted(graph_edges & set(forbidden)),
        unaffected_present=sorted(graph_edges & family.unaffected))
    evidence = assess_evidence(result.state, saved)
    _require_passing_ideal(identity, graph_score, decisions, evidence)
    report = dict(condition=identity, sample_id=condition.sample_id, condition_sha256=condition.case_sha256,
        ordered_sources_sha256=condition.sources_sha256, annotation_sha256=condition.annotation_sha256,
        planned=1, attempted=1, scored=1, exact_graph=True,
        graph=graph_score.model_dump(mode='json'), decisions=decisions, ordinary_evidence=evidence,
        legacy_source_attribution=(result.source_attribution.model_dump(mode='json')
                                   if result.source_attribution is not None else None),
        runtime_seconds=result.downstream_seconds, usage=result.usage.model_dump() if result.usage else None,
        incremental_cost=result.incremental_cost)
    return report, graph_edges


def _require_passing_ideal(identity: str, graph: EvaluationResult, decisions: dict[str, Any],
                           evidence: dict[str, Any]) -> None:
    if decisions['forbidden_present']:
        raise ValueError(f'{identity} retained a forbidden edge: {decisions["forbidden_present"]}')
    if decisions['required_present'] != decisions['required'] or evidence['sufficiency']['missed']:
        raise ValueError(f'{identity} missed a critical edge')
    if graph.fp or graph.fn:
        raise ValueError(f'{identity} Graph differs from complete truth: FP={graph.fp}, FN={graph.fn}')
    if evidence['sufficiency']['incomplete']:
        raise ValueError(f'{identity} has incomplete same-edge sufficient evidence')
    if evidence['quotation']['failed']:
        raise ValueError(f'{identity} has a failed ordinary quotation check')
    if evidence['source_attribution']['failed']:
        raise ValueError(f'{identity} has a failed ordinary Source attribution check')


def _verify_matched_observations(family: VerifiedFamily,
                                 observed: dict[str, set[SemanticEdge]]) -> dict[str, Any]:
    base, *variants = observed
    original = observed[base]
    matches = {}
    for identity in variants:
        current = observed[identity]
        if identity not in family.edits:
            if original != current:
                raise ValueError(f'{base}/{identity} observed Graphs fail exact invariance')
            label = 'invariance' if family.family == 'A' else identity
            matches[label] = dict(pair=[base, identity], passed=True, edges=sorted(original))
            continue
        removed, added = original - current, current - original
        prior, required = set(family.required[base]), set(family.required[identity])
        unchanged = family.unaffected | (prior & required)
        if removed != prior - required or added != required - prior or original & current != unchanged:
            raise ValueError(f'{base}/{identity} observed Graphs fail the exact predeclared contrast')
        label = 'sensitivity' if family.family == 'A' else identity
        matches[label] = dict(pair=[base, identity], passed=True, removed=sorted(removed),
            added=sorted(added), unaffected=sorted(family.unaffected), changed_source_id=family.edits[identity].source_id)
    return matches


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True, help='Explicit frozen Benchmark v3 replay manifest')
    parser.add_argument('--artifacts', type=Path, required=True, help='New or empty directory for retained replay')
    args = parser.parse_args()
    try:
        report = preflight(args.manifest.resolve(), args.artifacts.resolve())
    except (OSError, ValueError) as error:
        parser.exit(1, f'Benchmark v3 offline replay failed: {error}\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
