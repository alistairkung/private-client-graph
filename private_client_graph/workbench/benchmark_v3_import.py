"""Verified, checksummed membership for the retained Benchmark v3 baseline."""

import argparse
import json
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from benchmark_v3.batch.artifacts import read_bytes, write_bytes
from benchmark_v3.retained_evaluation import (
    BASELINE_INVENTORY_SHA256, verify_first_live_baseline, verify_first_live_custody,
)
from private_client_graph.research.artifacts import checksum, utc_now
from .benchmark_contracts import BenchmarkRun
from .benchmark_contracts import condition_relationship_outcomes
from .execution_contracts import FrozenPlan
from .family_context import read_family_context
from .run_evaluation import evaluate_run
from .run_inspection import RunDetail, RunObservation
from .workspaces import read_record, read_experiment, write_record, workspace_lock


IMPORT_SCHEMA_VERSION = 1
EXPERIMENT_NAMESPACE = 'pcg-benchmark-v3-first-live-baseline'


def import_first_live_baseline(root: Path, archive: Path, admissions: Path) -> str:
    """Verify first, then publish stable read-only Run and Experiment membership."""
    root = root.resolve()
    verified = verify_first_live_baseline(archive, admissions)
    run_id = _source_run_id(archive)
    experiment_id = uuid5(NAMESPACE_URL, f'{EXPERIMENT_NAMESPACE}:{run_id}').hex
    benchmark = BenchmarkRun.from_verified(verified)
    record_path = _record_path(root, run_id)
    detail = _detail(experiment_id, run_id, verified, benchmark, archive)
    projection_path = _projection_path(root, run_id)
    projection_json = _json_bytes(detail.model_dump(mode='json', exclude={'family_context'}))
    record = {
        'schema_version': IMPORT_SCHEMA_VERSION,
        'run_id': run_id,
        'experiment_id': experiment_id,
        'archive_path': str(archive.resolve()),
        'admissions_path': str(admissions.resolve()),
        'admissions_sha256': checksum(admissions.read_bytes()),
        'inventory_sha256': BASELINE_INVENTORY_SHA256,
        'projection_path': projection_path.relative_to(root).as_posix(),
        'projection_sha256': checksum(projection_json),
        'artifact_digest': BASELINE_INVENTORY_SHA256,
        'imported_at': utc_now(),
        'source_created_at': _source_created_at(archive, run_id),
    }
    with workspace_lock(root):
        if projection_path.exists() and checksum(read_bytes(projection_path)) != record['projection_sha256']:
            raise ValueError('Imported Run projection already exists with different contents')
        if record_path.exists():
            previous = read_record(record_path)
            if {key: value for key, value in previous.items() if key != 'imported_at'} != {
                key: value for key, value in record.items() if key != 'imported_at'
            }:
                raise ValueError('Imported Run identity already has different custody or commitments')
            record = previous
        else:
            _write_projection(projection_path, projection_json)
            write_record(record_path, record)
        # Recheck custody while holding the lock, then publish record membership atomically.
        verify_first_live_custody(archive, admissions)
        _publish_workspace(root, experiment_id, run_id, record)
    return run_id


def read_imported_run(root: Path, experiment_id: str, run_id: str) -> RunDetail:
    """Re-verify authority records and custody before serving the inspection projection."""
    root = root.resolve()
    workspace = read_experiment(root, experiment_id)
    if not workspace.read_only_import:
        raise ValueError('Imported Run does not belong to a read-only Experiment')
    if run_id not in workspace.run_ids:
        raise ValueError('Run does not belong to this Experiment')
    membership_path = root / 'experiments' / experiment_id / 'runs' / f'{run_id}.json'
    membership = read_record(membership_path)
    expected_record = _record_path(root, run_id).relative_to(root).as_posix()
    if membership.get('import_record') != expected_record:
        raise ValueError('Imported Run membership points outside its verified record')
    record = read_record(root / expected_record)
    if (record.get('schema_version') != IMPORT_SCHEMA_VERSION
            or record.get('run_id') != run_id or record.get('experiment_id') != experiment_id
            or membership.get('read_only_import') is not True):
        raise ValueError('Imported Run membership is invalid')
    if record.get('origin') not in (None, 'live', 'offline_fixture'):
        raise ValueError('Imported Run origin is invalid')
    projection_path = root / record.get('projection_path', '')
    projection_bytes = read_bytes(projection_path)
    if (record.get('projection_path') != _projection_path(root, run_id).relative_to(root).as_posix()
            or checksum(projection_bytes) != record.get('projection_sha256')):
        raise ValueError('Imported Run inspection projection changed')
    detail = RunDetail.model_validate_json(projection_bytes)
    if (detail.id != run_id or detail.experiment_id != experiment_id or detail.benchmark is None
            or detail.benchmark.scope.observation_origin != ('offline_fixture' if record.get('origin') == 'offline_fixture' else 'live')):
        raise ValueError('Imported Run projection identity or origin is invalid')
    # Bind the actual bytes to both authorities: the import record itself and the
    # independently published workspace membership. This catches adjacent record edits.
    expected_projection = checksum(projection_bytes)
    if record.get('projection_sha256') != expected_projection:
        raise ValueError('Imported Run projection is not bound to its import record')
    if membership.get('projection_sha256') != expected_projection:
        raise ValueError('Imported Run projection is not bound to workspace membership')
    if membership.get('artifact_digest') != detail.artifact_digest:
        raise ValueError('Imported Run artifact digest differs from workspace membership')
    if record.get('artifact_digest') != detail.artifact_digest:
        raise ValueError('Imported Run artifact digest differs from its import record')
    if record.get('origin') == 'offline_fixture':
        return detail
    archive, admissions = Path(record['archive_path']), Path(record['admissions_path'])
    admission_bytes = read_bytes(admissions)
    if checksum(admission_bytes) != record['admissions_sha256']:
        raise ValueError('Imported admissions register commitment changed')
    verify_first_live_custody(archive, admissions)
    detail.family_context = read_family_context(detail.benchmark.scope, admission_bytes)
    return detail


def register_offline_fixture_for_tests(root: Path, detail: RunDetail) -> None:
    """Publish a synthetic projection for deterministic read-path tests only."""
    if detail.benchmark is None or detail.benchmark.scope.observation_origin != 'offline_fixture':
        raise ValueError('Test fixtures must declare the offline_fixture origin')
    if len(detail.id) != 32 or len(detail.experiment_id) != 32:
        raise ValueError('Test fixture requires stable Run and Experiment identities')
    root = root.resolve()
    projection_path = _projection_path(root, detail.id)
    excluded = {'family_context'} if detail.family_context is None else set()
    content = _json_bytes(detail.model_dump(mode='json', exclude=excluded))
    record = {
        'schema_version': IMPORT_SCHEMA_VERSION,
        'origin': 'offline_fixture',
        'run_id': detail.id,
        'experiment_id': detail.experiment_id,
        'projection_path': projection_path.relative_to(root).as_posix(),
        'projection_sha256': checksum(content),
        'artifact_digest': detail.artifact_digest,
        'imported_at': utc_now(),
        'source_created_at': detail.plan.created_at if detail.plan else '2026-11-24T00:00:00+00:00',
    }
    record_path = _record_path(root, detail.id)
    if projection_path.exists() and checksum(read_bytes(projection_path)) != record['projection_sha256']:
        raise ValueError('Test fixture Run identity conflicts with existing projection')
    if not projection_path.exists():
        _write_projection(projection_path, content)
    if record_path.exists():
        previous = read_record(record_path)
        stable_keys = ('schema_version', 'origin', 'run_id', 'experiment_id',
                       'projection_path', 'projection_sha256')
        if any(previous.get(key) != record[key] for key in stable_keys):
            raise ValueError('Test fixture Run identity conflicts with existing membership')
        record = previous
    else:
        write_record(record_path, record)
    record['artifact_digest'] = detail.artifact_digest
    with workspace_lock(root):
        _publish_workspace(root, detail.experiment_id, detail.id, record)


def _detail(experiment_id, run_id, verified, benchmark, archive: Path) -> RunDetail:
    from private_client_graph.research.artifacts import Bundle
    observations = []
    typed = {item.condition: item for item in benchmark.observations}
    for planned in verified.planned:
        frozen = planned.frozen
        original = verified.original_results[frozen.saved.condition]
        condition = frozen.saved.condition
        benchmark_condition = typed[condition]
        observations.append(RunObservation(
            id=condition, sample_id=frozen.sample_id, case_id=planned.family,
            configuration=original.configuration or 'benchmark_v3_live_baseline',
            repetition=original.repetition or 1,
            status=verified.protocol.conditions[condition].outcome,
            reason=verified.protocol.conditions[condition].failure_detail,
            source=frozen.sources[0].text, sources=frozen.sources, result=original,
            relationships=condition_relationship_outcomes(
                benchmark_condition, original.evaluation, original.state,
            ),
            benchmark=benchmark_condition,
        ))
    bundle = Bundle.open(archive / run_id)
    frozen = FrozenPlan.model_validate_json((bundle.path / 'execution.json').read_text())
    lifecycle_records = [json.loads(path.read_text()) for path in (bundle.path / 'lifecycle').glob('*.json')]
    lifecycle = max(lifecycle_records, key=lambda item: item['at'])['state'] if lifecycle_records else 'complete'
    compact_attempts = []
    for attempt in bundle.attempts():
        response = attempt.get('response', {})
        usage = response.get('usage') or response.get('raw_response', {}).get('usage')
        compact_attempts.append({key: attempt.get(key) for key in ('attempt_id', 'stage', 'status', 'case_id')})
        if usage is not None:
            compact_attempts[-1]['usage'] = usage
    provenance = bundle.manifest['provenance']
    return RunDetail(
        id=run_id, experiment_id=experiment_id, plan=frozen, lifecycle=lifecycle,
        evaluation=evaluate_run(bundle),
        benchmark=benchmark, observations=observations,
        provenance={'origin': 'live', 'benchmark_protocol': verified.protocol.scope.protocol_version,
                    'archive_inventory_sha256': BASELINE_INVENTORY_SHA256,
                    'git_sha': provenance.get('git_sha'), 'prompt_hashes': provenance.get('prompt_hashes'),
                    'dependencies': provenance.get('dependencies')},
        artifact_digest=BASELINE_INVENTORY_SHA256, authorized_invocations=[],
        attempts=compact_attempts, pricing=bundle.plan.pricing.model_dump() if bundle.plan.pricing else None,
    )


def _publish_workspace(root: Path, experiment_id: str, run_id: str, import_record: dict) -> None:
    workspace_path = root / 'experiments' / experiment_id / 'workspace.json'
    membership_path = root / 'experiments' / experiment_id / 'runs' / f'{run_id}.json'
    workspace = {
        'schema_version': 1,
        'id': experiment_id,
        'created_at': import_record['source_created_at'],
        'command': {
            'request_id': f'benchmark-v3-import-{experiment_id}',
            'name': 'Benchmark v3 Research',
            'hypothesis': None,
            'description': 'Read-only verified import of the retained first live baseline.',
        },
        'initial_draft': {},
        'read_only_import': True,
    }
    from .workspace_contracts import RunDraft
    workspace['initial_draft'] = RunDraft().model_dump(mode='json')
    previous_workspace = None
    if workspace_path.exists():
        previous_workspace = read_record(workspace_path)
        workspace['created_at'] = previous_workspace.get('created_at', workspace['created_at'])
        if previous_workspace != workspace:
            raise ValueError('Imported Experiment identity conflicts with existing workspace records')
    membership = {
        'experiment_id': experiment_id,
        'run_id': run_id,
        'created_at': import_record['source_created_at'],
        'import_record': _record_path(root, run_id).relative_to(root).as_posix(),
        'read_only_import': True,
        'projection_sha256': import_record['projection_sha256'],
        'artifact_digest': import_record.get('artifact_digest', BASELINE_INVENTORY_SHA256),
    }
    if membership_path.exists():
        if read_record(membership_path) != membership:
            raise ValueError('Imported Run identity conflicts with existing workspace membership')
    else:
        write_record(membership_path, membership)
    if previous_workspace is None:
        write_record(workspace_path, workspace)


def _record_path(root: Path, run_id: str) -> Path:
    return root / 'benchmark_v3' / 'imports' / run_id / 'record.json'


def _projection_path(root: Path, run_id: str) -> Path:
    return root / 'benchmark_v3' / 'imports' / run_id / 'projection.json'


def _write_projection(path: Path, content: bytes) -> None:
    write_bytes(path, content)


def _source_run_id(archive: Path) -> str:
    run = json.loads((archive / 'RUN.json').read_text())
    identity = run.get('id')
    if not isinstance(identity, str) or len(identity) != 32 or set(identity) - set('0123456789abcdef'):
        raise ValueError('Retained Run has an invalid stable identity')
    return identity


def _source_created_at(archive: Path, run_id: str) -> str:
    from private_client_graph.research.artifacts import Bundle
    return Bundle.open(archive / run_id).manifest['created_at']


def _json_bytes(value) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()


def main() -> None:
    parser = argparse.ArgumentParser(description='Verify and register the retained Benchmark v3 baseline')
    parser.add_argument('--artifacts', required=True, type=Path)
    parser.add_argument('--archive', required=True, type=Path)
    parser.add_argument('--admissions', required=True, type=Path)
    args = parser.parse_args()
    run_id = import_first_live_baseline(args.artifacts, args.archive, args.admissions)
    from private_client_graph.persistence.database import database_engine
    from .index import rebuild_index
    rebuild_index(database_engine(), args.artifacts)
    print(run_id)


if __name__ == '__main__':
    main()
