"""Single local subprocess, durable commands and explicit restart reconciliation."""
import fcntl
import json
import os
import subprocess
import sys
from threading import Thread
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, TextIO
from uuid import uuid4

from private_client_graph.research.artifacts import Bundle, utc_now, write_json_once
from private_client_graph.research.runner import validate_execution, validate_environment
from .evidence import digest_text
from .execution_contracts import Command, LiveApproval, RunStatus
from .planning import open_executable, live_budget, require_live
from .approval import authorize


def event(bundle: Bundle, state: str, message: str, invocation: str) -> None:
    write_json_once(bundle.path / 'lifecycle' / f'{uuid4().hex}.json',
        {'at': utc_now(), 'state': state, 'message': message, 'invocation': invocation})


def latest_event(bundle: Bundle) -> dict:
    events = [json.loads(p.read_text()) for p in (bundle.path / 'lifecycle').glob('*.json')]
    return max(events, key=lambda e: e['at']) if events else {
        'state': 'frozen', 'message': 'Frozen plan; execution has not started.', 'invocation': ''}


@contextmanager
def command_lock(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    with (root / '.commands.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def active_lock(root: Path) -> TextIO | None:
    stream = (root / '.active.lock').open('a')
    try:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        stream.close()
        return None
    return stream


def _active_plan(root: Path) -> str | None:
    lock = active_lock(root)
    if lock is not None:
        lock.close()
        return None
    record = root / '.active.json'
    return json.loads(record.read_text())['plan_id'] if record.exists() else None


def status(root: Path, identity: str) -> RunStatus:
    with command_lock(root):
        return _status(root, identity)


def _status(root: Path, identity: str) -> RunStatus:
    bundle, plan = open_executable(root, identity)
    latest = _reconciled_event(bundle)
    active = _active_plan(root)
    if latest['state'] in ('running', 'stopping') and active != identity:
        event(bundle, 'interrupted', 'Execution did not resume. Review remaining work before explicit continuation.', latest['invocation'])
        latest = latest_event(bundle)
    if bundle.plan.kind == 'live_experiment':
        from private_client_graph.research.live_accounting import recover_reservations
        recover_reservations(bundle)
    attempts = bundle.attempts()
    current_work = None
    if latest['state'] in ('running', 'stopping'):
        pending = [attempt for attempt in attempts if attempt['status'] == 'uncertain']
        current_work = max(pending, key=lambda attempt: attempt['started_at'])['attempt_id'] if pending else 'Processing frozen inputs and results'
    return RunStatus(plan=plan, state=latest['state'], message=latest['message'],
        completed_observations=len(bundle.results()), planned_observations=plan.preview.planned_observations,
        attempts=len(attempts), uncertain_attempts=sum(a['status'] == 'uncertain' for a in attempts),
        remaining_attempts=max(0, plan.preview.matrix_call_maximum - len(attempts)),
        result_id=digest_text(identity), active_plan_id=active, current_work=current_work,
        task_budget=live_budget(root) if bundle.plan.kind == 'live_experiment' else None)


def start(root: Path, identity: str, command: Command, *, continuation: bool = False,
          approval: LiveApproval | None = None, origin: str = '', preauthorized: bool = False) -> RunStatus:
    with command_lock(root):
        bundle, plan = open_executable(root, identity)
        if command.plan_digest != plan.digest:
            raise ValueError('Command does not match the frozen plan digest')
        validate_environment(bundle)
        live = bundle.plan.kind == 'live_experiment'
        if approval is not None and not live:
            raise ValueError('Live approval requires a live plan')
        if live:
            require_live(root)
            if approval is None:
                raise ValueError('Explicit live approval is required')
        request = bundle.path / 'commands' / f'{command.request_id}.json'
        value = {**command.model_dump(), 'continuation': continuation}
        if approval is not None:
            value['approval'] = approval.model_dump()
        if request.exists():
            if json.loads(request.read_text()) != value:
                raise ValueError('Idempotency key was already used for another command')
            return _status(root, identity)
        if preauthorized and approval is not None:
            if live_budget(root).used != approval.expected_task_usage:
                raise ValueError('Task budget changed after authorization; review a new approval')
        current = _status(root, identity)
        permitted = ('stopped', 'interrupted', 'failed') if continuation else ('frozen',)
        if current.state not in permitted:
            raise ValueError('This lifecycle requires explicit continuation or is already complete')
        lock = active_lock(root)
        if lock is None:
            raise ValueError(f'Another experiment is active: {current.active_plan_id}')
        try:
            if live:
                assert approval is not None
                authorize(bundle, plan, approval, origin)
                bundle.authorization_id = command.request_id
            write_json_once(request, value)
            validate_execution(bundle, live=live)
            event(bundle, 'running', 'Running live.' if live else 'Running offline.', command.request_id)
            _launch_worker(root, bundle, identity, command.request_id, lock)
        except Exception:
            if request.exists():
                event(bundle, 'interrupted', 'Worker could not start; explicit continuation required.', command.request_id)
            raise
        finally:
            # Close without LOCK_UN: the child owns the inherited open-file description.
            lock.close()
        return _status(root, identity)


def stop(root: Path, identity: str, command: Command) -> RunStatus:
    with command_lock(root):
        bundle, plan = open_executable(root, identity)
        if plan.digest != command.plan_digest:
            raise ValueError('Command does not match the frozen plan digest')
        current = _status(root, identity)
        if current.state == 'stopping':
            return current
        if current.state != 'running':
            raise ValueError('Only a running experiment can be stopped')
        invocation = latest_event(bundle)['invocation']
        write_json_once(bundle.path / 'stops' / f'{invocation}.json', command.model_dump())
        event(bundle, 'stopping', 'Stopping after the current attempt.', invocation)
        return _status(root, identity)


def reconcile(root: Path) -> None:
    """Reconcile abandoned commands at startup without dispatching any work."""
    with command_lock(root):
        active = _active_plan(root)
        for authority in root.glob('*/execution.json'):
            try:
                bundle = Bundle.open(authority.parent)
                latest = _reconciled_event(bundle)
                if latest['state'] in ('running', 'stopping') and active != bundle.path.name:
                    event(bundle, 'interrupted', 'Service restarted; explicit continuation required.', latest['invocation'])
            except (OSError, ValueError, KeyError, TypeError):
                # Corrupt artifacts remain inspectable as integrity failures in the read index.
                continue


def _launch_worker(root: Path, bundle: Bundle, identity: str, invocation: str, lock: TextIO) -> None:
    # This hidden pointer is advisory; immutable commands/lifecycle remain authoritative.
    pointer = root / '.active.json'
    temporary = root / '.active.pending'
    temporary.write_text(json.dumps({'plan_id': identity}))
    os.replace(temporary, pointer)
    with (bundle.path / '.worker.log').open('a') as log:
        child = subprocess.Popen([sys.executable, '-m', 'private_client_graph.workbench.worker',
            str(root.resolve()), identity, invocation, str(lock.fileno()), str(os.getpid())],
            pass_fds=(lock.fileno(),), stdout=log, stderr=log, start_new_session=True)
        Thread(target=child.wait, daemon=True).start()


def _reconciled_event(bundle: Bundle) -> dict:
    latest = latest_event(bundle)
    commands = sorted((bundle.path / 'commands').glob('*.json'))
    if latest['state'] == 'frozen' and commands:
        event(bundle, 'interrupted', 'Command publication was interrupted; explicit continuation required.', commands[0].stem)
        return latest_event(bundle)
    return latest
