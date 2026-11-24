"""Replay the v2 development ideals and inspect the budget without enabling a provider."""
import argparse
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path

from pydantic import BaseModel, ConfigDict, TypeAdapter

from benchmark_v2.execution_environment import TRACED_LOCK_SHA256, baseline_configuration
from benchmark_v2.evidence_policy import VERSION, ordinary_evidence
from private_client_graph.extraction import sourced_extraction_messages
from private_client_graph.research.artifacts import Bundle, write_json_once
from private_client_graph.research.benchmark_admission import package_hashes, pending_semantic_review
from private_client_graph.research.benchmark_decisions import DecisionTargets, diagnose
from private_client_graph.research.fixtures import ROOT
from private_client_graph.research.inputs import ResearchInput
from private_client_graph.research.results import ResearchResult
from private_client_graph.research.retained_inputs import input_digests, value_digest
from private_client_graph.research.run_plan import RunPlan
from private_client_graph.research.runner import execute
from private_client_graph.research.source_attribution import SourceEvidenceApproval
from private_client_graph.workbench.case_catalog import frozen_case_metadata, repository_inputs
from private_client_graph.workbench.run_inspection import read_run
from private_client_graph.workbench.run_planning import freeze_run, preview_run
from private_client_graph.workbench.workspace_contracts import CreateExperiment, DraftUpdate, FreezeRun, RunConfiguration
from private_client_graph.workbench.workspaces import create_experiment, update_draft

STUDY = ROOT / 'benchmark_v2'


class Condition(BaseModel):
    model_config = ConfigDict(extra='forbid')
    condition: str
    input_id: str
    targets: DecisionTargets


def package_commitment(directory: Path) -> str:
    return value_digest(package_hashes(directory))


def verify_development_lock(rows: Sequence[Condition], catalog: dict[str, ResearchInput]) -> dict[str, str]:
    """Bind the declared cases to exact annotation, protocol and fixture bytes before replay."""
    metadata = frozen_case_metadata([catalog[r.input_id] for r in rows])
    families = {}
    packages = {}
    for row in rows:
        info = metadata[row.input_id]
        family = info.matter_family
        if row.condition == 'D13':
            directory = STUDY / 'candidates/D13'
        else:
            ordinal = info.case_id.rsplit('_', 1)[1]
            directory = ROOT / 'benchmark_v1' / str(info.axis) / 'dev' / f'case_{ordinal}'
        if not family:
            raise ValueError(f'Unknown matter family for {row.condition}')
        families[row.condition] = family
        packages[row.condition] = package_commitment(directory)
    lock = json.loads((STUDY / 'development.lock.json').read_bytes())
    documents = {name: hashlib.sha256((STUDY / name).read_bytes()).hexdigest()
                 for name in ('development.json', 'README.md', 'baseline.json', 'evidence-policy-v1.md', 'evidence_policy.py')}
    decisions_module = 'private_client_graph/research/benchmark_decisions.py'
    scorers = {decisions_module: hashlib.sha256((ROOT / decisions_module).read_bytes()).hexdigest()}
    if lock != {'documents': documents, 'packages': packages, 'scorers': scorers}:
        raise ValueError('Development package, annotation or protocol differs from its committed revision')
    return families


def offline_only(_request):
    raise AssertionError('An offline benchmark replay attempted a provider call')


def replay_catalog(root: Path, ids: list[str]) -> tuple[list[ResearchResult], RunPlan]:
    config = RunConfiguration(input_ids=ids, input_mode='saved', execution_mode='replay', resolver='none')
    preview = preview_run(config, root)
    if preview.matrix_call_maximum != 0:
        raise ValueError('Unexpected nonzero replay budget')
    workspace = create_experiment(root, CreateExperiment(request_id='benchmark-v2', name='Benchmark v2 offline review'))
    update_draft(root, workspace.id, DraftUpdate(request_id='ideals', expected_revision=0, configuration=config))
    frozen = freeze_run(root, workspace.id, FreezeRun(request_id='ideals', expected_revision=1))
    bundle = Bundle.open(root / frozen.id)
    execute(bundle, provider=offline_only)
    detail = read_run(root, workspace.id, frozen.id)
    if bundle.attempt_count or detail.evaluation.aggregate.coverage.scored != len(ids):
        raise ValueError('Incomplete offline Workbench replay')
    assert isinstance(bundle.plan, RunPlan)
    return [o.result for o in detail.observations if o.result is not None], bundle.plan


def inspect_ideal(row: Condition, sample: ResearchInput, result: ResearchResult) -> dict:
    score = result.evaluation
    if score is None or result.state is None or not sample.sources:
        raise ValueError(f'Unscored ideal for {row.condition}')
    if score.fp or score.fn or score.tp != len(sample.truth.relationships):
        raise ValueError(f'Ideal disagrees with complete truth for {row.condition}')
    decisions = diagnose(result.state, sample.truth, row.targets)
    if decisions['sufficiency']['incomplete']:
        raise ValueError(f'Ideal lacks an annotated sufficient set for {row.condition}')
    if row.condition == 'D13':
        packaged = SourceEvidenceApproval.model_validate_json((STUDY / 'candidates/D13/source_evidence.json').read_bytes())
        eligible = SourceEvidenceApproval(relationships=[r for r in packaged.relationships if r.approved_evidence])
        if eligible != row.targets.ordinary_source_approval:
            raise ValueError('Frozen eligible approvals differ from the D13 source-specific answer key')
    ordinary = ordinary_evidence(result.state, sample.truth, row.targets, sample.source_evidence)
    attribution = ordinary['source_attribution']
    if ordinary['quotation']['failed'] or attribution is None or attribution['failed']:
        raise ValueError(f'Ideal quotation or Source mismatch for {row.condition}')
    payload = sourced_extraction_messages(sample.sources)
    byte_count = sum(len(message.encode()) for _, message in payload)
    return dict(condition=row.condition, input_id=row.input_id, case_id=sample.case_id, **input_digests(sample),
                annotation_digest=value_digest(row.model_dump(mode='json')), source_count=len(sample.sources),
                message_bytes=byte_count, estimated_message_tokens=(byte_count + 3) // 4,
                graph=score.model_dump(mode='json'), decisions=decisions, ordinary_evidence=ordinary,
                legacy_source_attribution=result.source_attribution.model_dump() if result.source_attribution else None)


def preflight(root: Path) -> dict:
    pin = baseline_configuration()
    rows = TypeAdapter(list[Condition]).validate_json((STUDY / 'development.json').read_bytes())
    if [r.condition for r in rows] != [f'D{i}' for i in range(1, 15)] or len({r.input_id for r in rows}) != 14:
        raise ValueError('Invalid development selection')
    ids = [row.input_id for row in rows]
    catalog = {s.sample_id: s for s in repository_inputs(input_ids=ids)}
    families = verify_development_lock(rows, catalog)
    if root.exists() and any(root.iterdir()):
        raise ValueError('Select an empty artifact directory to retain this replay')
    root.mkdir(parents=True, exist_ok=True)
    write_json_once(root / 'development-targets.json', [r.model_dump(mode='json') for r in rows])
    results, plan = replay_catalog(root, ids)
    if any(input_digests(sample) != input_digests(catalog[sample.sample_id]) for sample in plan.inputs):
        raise ValueError('Workbench inputs changed between validation and freeze')
    samples = {s.sample_id: s for s in plan.inputs}
    scored = {r.sample_id: r for r in results}
    conditions = [inspect_ideal(row, samples[row.input_id], scored[row.input_id]) for row in rows]
    for item in conditions:
        item['matter_family'] = families[item['condition']]
    groups = [rows[:7], rows[7:9], rows[7:9], rows[7:9], rows[9:]]
    schedule = [row.condition for group in groups for row in group]
    proposed = [RunConfiguration(input_ids=[r.input_id for r in group], input_mode='fresh', execution_mode='live',
                                 resolver='none', invocation_cap=len(group), task_call_cap=len(schedule),
                                 model='deepseek-flash', timeout_seconds=90.0).model_dump(mode='json')
                for group in groups]
    pending = [row.condition for row in rows
               if pending_semantic_review(catalog[row.input_id])]
    provenance = Bundle.open(root / str(plan.run_id)).manifest['provenance']
    report = dict(execution_revision=provenance['git_sha'], execution_dirty=provenance['dirty'],
                  sourced_prompt_sha256=pin['prompt'], model_settings_sha256=pin['settings'],
                  pending_live_admission=pending, execution_lock_sha256=TRACED_LOCK_SHA256,
                  evidence_policy_version=VERSION, conditions=conditions, baseline_schedule=schedule, proposed_run_configurations=proposed,
                  workbench_run=plan.run_id,
                  protocol_sha256=hashlib.sha256((STUDY / 'README.md').read_bytes()).hexdigest(),
                  development_lock_sha256=hashlib.sha256((STUDY / 'development.lock.json').read_bytes()).hexdigest(),
                  paid_attempts=0, development_attempts_proposed=len(schedule), final_attempts_reserved=8,
                  baseline_reference=pin['revision'], corpus_status='pending independent human semantic review' if pending else 'development roster admitted',
                  estimate_method='ceil(UTF-8 bytes of sourced system and user message contents / 4); excludes schema and chat framing')
    write_json_once(root / 'preflight.json', report)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--artifacts', required=True, type=Path, help='New or empty directory for immutable replay artifacts')
    print(json.dumps(preflight(parser.parse_args().artifacts.resolve()), indent=2))
