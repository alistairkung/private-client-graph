"""Substituted live boundary; real runner, task authority and durable reservations."""
import json
import shutil

import pytest

from private_client_graph.research import live_accounting
from private_client_graph.research.artifacts import Bundle, write_json_once
from private_client_graph.research.demo import recorded_response
from private_client_graph.research.runner import execute
from private_client_graph.workbench.approval import authorize
from private_client_graph.workbench.artifacts import read_artifact
from private_client_graph.workbench.execution_contracts import Command, LiveApproval, Proposal
from private_client_graph.workbench.planning import freeze, live_budget, open_executable
from private_client_graph.workbench.supervisor import start


@pytest.fixture
def live_root(tmp_path, monkeypatch):
    live_accounting.initialize_task(tmp_path, 'Issue 103 substituted validation')
    monkeypatch.setenv('PCG_RESEARCH_LIVE_ENABLED', '1')
    return tmp_path


def frozen(root, **changes):
    values = dict(input_ids=['case_03_fixture'], execution_mode='live', resolver='generative',
                  resolver_repetitions=3, invocation_cap=1, task_call_cap=3)
    return freeze(root, Proposal(**(values | changes)))


def approval(root, plan, request_id='approve', **changes):
    budget = live_budget(root)
    return LiveApproval(**(dict(request_id=request_id, plan_digest=plan.digest, task_id=plan.task_id,
        expected_task_usage=budget.used, expected_task_cap=budget.cap,
        task_cap=plan.preview.proposal.task_call_cap, approved=True) | changes))


def approved_bundle(root, plan, request_id='approve'):
    bundle, _ = open_executable(root, plan.id)
    authorize(bundle, plan, approval(root, plan, request_id), 'http://localhost')
    bundle.authorization_id = request_id
    return bundle


def test_no_authority_from_freezing_or_free_text(live_root):
    plan = frozen(live_root)
    bundle, _ = open_executable(live_root, plan.id)
    calls = []
    with pytest.raises(ValueError, match='approval'):
        execute(bundle, live=True, provider=lambda request: calls.append(request))
    with pytest.raises(ValueError, match='approval'):
        start(live_root, plan.id, Command(request_id='no', plan_digest=plan.digest))
    assert not calls and live_budget(live_root).cap == 0
    with pytest.raises(ValueError, match='task identity'):
        authorize(bundle, plan, approval(live_root, plan, task_id='Issue 103'), 'http://localhost')


def test_cross_bundle_task_cap_and_immutable_invocation_limit(live_root):
    plan = frozen(live_root, task_call_cap=2)
    bundle = approved_bundle(live_root, plan)
    calls = []
    def provider(request):
        # Both authoritative and local records exist before the substituted dispatch.
        assert bundle.attempt_count == 1
        assert live_budget(live_root).used == 1
        calls.append(request)
        return recorded_response(request)
    execute(bundle, live=True, provider=provider)  # persistent approval bound applies without runner checkpoint
    execute(bundle, live=True, provider=lambda _: pytest.fail('Approval replay spent more'))
    assert len(calls) == 1
    other = frozen(live_root, task_call_cap=2)
    second = approved_bundle(live_root, other)
    execute(second, live=True, provider=recorded_response)
    assert live_budget(live_root).used == 2
    third = frozen(live_root, task_call_cap=2)
    with pytest.raises(ValueError, match='exhausted'):
        approved_bundle(live_root, third)
    assert read_artifact(bundle.path, plan.id).history.integrity == 'verified'
    with pytest.raises(ValueError, match='already provisioned'):
        live_accounting.initialize_task(live_root, 'reset')


@pytest.mark.parametrize('crash', ['before_reservation', 'between_reservations', 'after_dispatch', 'before_completion'])
def test_crash_boundaries_count_uncertain_and_never_retry(live_root, monkeypatch, crash):
    plan = frozen(live_root, invocation_cap=3)
    bundle = approved_bundle(live_root, plan)
    calls = []
    real_write = live_accounting.write_json_once
    def write(path, value):
        if crash == 'before_reservation' and path.parent.name == 'reservations':
            raise SystemExit('before reservation')
        if crash == 'between_reservations' and path.parent.name == 'attempts':
            raise SystemExit('between ledger and bundle')
        return real_write(path, value)
    monkeypatch.setattr(live_accounting, 'write_json_once', write)
    def provider(request):
        calls.append(request)
        if crash == 'after_dispatch':
            raise SystemExit('provider returned but completion not published')
        return recorded_response(request)
    real_complete = bundle.complete
    if crash == 'before_completion':
        monkeypatch.setattr(bundle, 'complete', lambda *a: (_ for _ in ()).throw(SystemExit()))
    with pytest.raises(SystemExit):
        execute(bundle, live=True, provider=provider)
    assert len(calls) == (1 if crash in ('after_dispatch', 'before_completion') else 0)
    assert live_budget(live_root).used == (0 if crash == 'before_reservation' else 1)
    monkeypatch.setattr(live_accounting, 'write_json_once', real_write)
    monkeypatch.setattr(bundle, 'complete', real_complete)
    bundle = approved_bundle(live_root, plan, 'explicit-continuation')
    resumed = []
    execute(bundle, live=True, provider=lambda request: (resumed.append(request), recorded_response(request))[1])
    assert len(resumed) == (3 if crash == 'before_reservation' else 2)
    assert live_budget(live_root).used == 3
    assert sum(a['status'] == 'uncertain' for a in bundle.attempts()) == (crash != 'before_reservation')


def test_stale_approval_replay_and_cap_increase(live_root):
    plan = frozen(live_root, task_call_cap=1)
    stale = approval(live_root, plan)
    bundle = approved_bundle(live_root, plan)
    execute(bundle, live=True, provider=recorded_response)
    with pytest.raises(ValueError, match='budget changed'):
        authorize(bundle, plan, stale.model_copy(update={'request_id': 'stale'}), 'http://localhost')
    with pytest.raises(ValueError, match='replay differs'):
        authorize(bundle, plan, stale.model_copy(update={'expected_task_usage': 1}), 'http://localhost')
    with pytest.raises(ValueError, match='frozen task'):
        authorize(bundle, plan, approval(live_root, plan, 'increase', task_cap=2), 'http://localhost')
    larger = frozen(live_root, task_call_cap=2)
    assert live_budget(live_root).cap == 1  # preview/freeze never increase authority
    approved_bundle(live_root, larger)
    assert live_budget(live_root).cap == 2


def test_copies_missing_accounting_and_changed_plan(live_root, tmp_path):
    plan = frozen(live_root)
    bundle = approved_bundle(live_root, plan)
    copy = live_root / 'copied'
    shutil.copytree(bundle.path, copy / plan.id)
    with pytest.raises(ValueError, match='relocation'):
        open_executable(copy, plan.id)
    bundle.authorization_id = 'unapproved-invocation'
    with pytest.raises(FileNotFoundError):
        execute(bundle, live=True, provider=lambda _: pytest.fail('unapproved'))
    bundle.authorization_id = 'approve'
    binding = bundle.path / 'execution-binding.json'
    old = binding.read_text()
    binding.write_text(old + ' ')
    with pytest.raises(ValueError, match='does not match'):
        execute(bundle, live=True, provider=lambda _: pytest.fail('changed plan'))
    binding.write_text(old)
    (bundle.task_ledger / 'task.json').unlink()
    with pytest.raises(FileNotFoundError):
        execute(bundle, live=True, provider=lambda _: pytest.fail('missing ledger'))


def test_lost_other_bundle_reservation_is_not_a_budget_reset(live_root):
    plan = frozen(live_root)
    bundle = approved_bundle(live_root, plan)
    execute(bundle, live=True, provider=recorded_response)
    next((bundle.task_ledger / 'reservations').glob('*.json')).unlink()
    with pytest.raises(ValueError, match='incomplete'):
        frozen(live_root)


def test_missing_registry_cannot_be_reprovisioned_as_new_allowance(live_root):
    (live_root / 'live-task.json').unlink()
    with pytest.raises(ValueError, match='already provisioned'):
        live_accounting.initialize_task(live_root, 'new label cannot reset task')


def test_authorization_partial_publication_recovers_without_increasing_cap(live_root, monkeypatch):
    from private_client_graph.workbench import approval as module
    plan = frozen(live_root)
    bundle, _ = open_executable(live_root, plan.id)
    request = approval(live_root, plan)
    original = module.write_json_once
    def publish(path, value):
        if path.parent.parent == bundle.path:
            raise OSError('simulated bundle publication crash')
        original(path, value)
    monkeypatch.setattr(module, 'write_json_once', publish)
    with pytest.raises(OSError):
        authorize(bundle, plan, request, 'http://localhost')
    assert live_budget(live_root).cap == 3
    monkeypatch.setattr(module, 'write_json_once', original)
    authorize(bundle, plan, request, 'http://localhost')
    bundle.authorization_id = request.request_id
    execute(bundle, live=True, provider=recorded_response)
    assert bundle.attempt_count == 1


def test_published_command_crash_needs_new_explicit_continuation(live_root, monkeypatch):
    from private_client_graph.workbench import supervisor
    plan = frozen(live_root)
    requested = approval(live_root, plan)
    calls = []
    def crash(*args):
        calls.append('launch')
        raise SystemExit('process crash before worker')
    monkeypatch.setattr(supervisor, '_launch_worker', crash)
    command = Command(request_id=requested.request_id, plan_digest=plan.digest)
    with pytest.raises(SystemExit):
        supervisor.start(live_root, plan.id, command, approval=requested, origin='http://localhost')
    supervisor.reconcile(live_root)
    assert supervisor.status(live_root, plan.id).state == 'interrupted'
    assert live_budget(live_root).used == 0
    supervisor.start(live_root, plan.id, command, approval=requested, origin='http://localhost')
    assert calls == ['launch']  # same approval command never dispatches again
    fresh = approval(live_root, plan, 'new')
    with pytest.raises(ValueError, match='continuation'):
        supervisor.start(live_root, plan.id, Command(request_id='new', plan_digest=plan.digest),
                         approval=fresh, origin='http://localhost')


def test_live_failure_retains_unknown_usage_and_redacts_exception(live_root):
    plan = frozen(live_root)
    bundle = approved_bundle(live_root, plan)
    def failed(request):
        raise RuntimeError('secret-credential-should-never-be-persisted')
    execute(bundle, live=True, provider=failed)
    detail = read_artifact(bundle.path, plan.id)
    assert detail.operations['paid_attempts'] == 1
    assert detail.operations['provider_failed_attempts'] == 1
    assert detail.operations['estimated_spend'] is None
    assert detail.operations['unpriced_attempts'] == 1
    assert detail.operations['tokens']['input_tokens']['unknown_attempts'] == 1
    assert 'secret-credential' not in ''.join(p.read_text() for p in bundle.path.rglob('*.json'))


def test_schema2_pre_live_preview_remains_inspectable(live_root):
    from private_client_graph.research.artifacts import checksum
    plan = freeze(live_root, Proposal(input_ids=['case_03_fixture']))
    path = live_root / plan.id
    binding = json.loads((path / 'execution-binding.json').read_text())
    frozen_value = json.loads((path / 'execution.json').read_text())
    for value in (binding['preview'], frozen_value['preview']):
        value.pop('task_id')
        value.pop('task_label')
        value['proposal'].pop('task_call_cap')
    (path / 'execution-binding.json').write_text(json.dumps(binding))
    frozen_value['digest'] = checksum((path / 'manifest.json').read_bytes() + (path / 'execution-binding.json').read_bytes())
    (path / 'execution.json').write_text(json.dumps(frozen_value))
    assert read_artifact(path, plan.id).history.integrity == 'verified'


def test_status_recovers_task_first_crash_before_continuation_review(live_root):
    from private_client_graph.research.artifacts import utc_now
    from private_client_graph.workbench.supervisor import status
    plan = frozen(live_root)
    bundle = approved_bundle(live_root, plan)
    attempt_id = 'case_03_fixture-resolve-1'
    write_json_once(bundle.task_ledger / 'reservations' / f"{bundle.manifest['experiment_id']}-{attempt_id}.json",
        {'attempt_id': attempt_id, 'started_at': utc_now(), 'status': 'uncertain',
         'request': {}, 'authorization': f'{plan.id}-approve'})
    result = status(live_root, plan.id)
    assert result.task_budget.used == result.uncertain_attempts == result.attempts == 1
    assert result.remaining_attempts == 2


def test_rejected_approval_or_concurrent_start_preserves_frozen_state(live_root, monkeypatch):
    from private_client_graph.workbench import supervisor
    plan = frozen(live_root)
    requested = approval(live_root, plan, expected_task_usage=1)
    command = Command(request_id=requested.request_id, plan_digest=plan.digest)
    monkeypatch.setattr(supervisor, '_launch_worker', lambda *args: pytest.fail('Rejected start launched worker'))
    with pytest.raises(ValueError, match='budget changed'):
        start(live_root, plan.id, command, approval=requested, origin='http://localhost')
    assert supervisor.status(live_root, plan.id).state == 'frozen'
    requested = approval(live_root, plan)
    active = supervisor.active_lock(live_root)
    assert active is not None
    try:
        with pytest.raises(ValueError, match='Another experiment'):
            start(live_root, plan.id, command, approval=requested, origin='http://localhost')
    finally:
        active.close()
    assert supervisor.status(live_root, plan.id).state == 'frozen'
    assert live_budget(live_root).cap == 0
    assert not list((live_root / plan.id / 'authorizations').glob('*.json'))
