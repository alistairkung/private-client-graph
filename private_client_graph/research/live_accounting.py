"""Durable local task authority and invocation reservations for schema-3 research.

The registry is provisioned explicitly once, not when a bundle is created or an
index is rebuilt. Authorization records are the task's append-only cap history.
"""
from contextlib import contextmanager
import fcntl
import json
from pathlib import Path
from typing import Iterator, TYPE_CHECKING
from uuid import uuid4

from .artifacts import BudgetExceeded, checksum, utc_now, write_json_once

if TYPE_CHECKING:
    from .artifacts import Bundle


def initialize_task(root: Path, label: str) -> dict:
    """Explicit operator action; never reset or replace an existing task."""
    root = root.resolve()
    if not label.strip() or len(label) > 120:
        raise ValueError('Provide a task label of 1–120 characters')
    if ((root / 'live-task.json').exists()
            or any((root / 'task-ledgers').glob('live-*'))
            or any(root.glob('*/authorizations/*.json'))):
        raise ValueError('A live task is already provisioned; retain its accounting')
    identity = f'live-{uuid4().hex}'
    ledger = root / 'task-ledgers' / identity
    record = {'version': 1, 'task_id': identity, 'label': label,
              'root': str(root), 'ledger': str(ledger), 'created_at': utc_now()}
    write_json_once(ledger / 'task.json', record)
    write_json_once(root / 'live-task.json', record)
    return record


def read_task(root: Path) -> dict:
    root = root.resolve()
    registry = root / 'live-task.json'
    if registry.is_symlink():
        raise ValueError('Live task registry cannot be relocated')
    task = json.loads(registry.read_text())
    ledger = root / 'task-ledgers' / task['task_id']
    if task['root'] != str(root) or task['ledger'] != str(ledger) or ledger.is_symlink():
        raise ValueError('Live task ledger relocation is unsafe')
    if json.loads((ledger / 'task.json').read_text()) != task:
        raise ValueError('Live task registry and ledger do not match')
    return task


@contextmanager
def task_lock(ledger: Path) -> Iterator[None]:
    # Opening the lock must not recreate a missing ledger.
    with (ledger / '.lock').open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield


def task_state(ledger: Path) -> dict:
    task = json.loads((ledger / 'task.json').read_text())
    if read_task(Path(task['root'])) != task:
        raise ValueError('Live task authority mismatch')
    approvals = [json.loads(p.read_text()) for p in (ledger / 'authorizations').glob('*.json')]
    reservations = list((ledger / 'reservations').glob('*.json'))
    _validate_retained_reservations(task, ledger)
    return {'task_id': task['task_id'], 'label': task['label'], 'used': len(reservations),
            'cap': max((a['task_cap'] for a in approvals), default=0)}


def _validate_retained_reservations(task: dict, ledger: Path) -> None:
    # Detect lost reservations even when the next experiment is a different bundle.
    for manifest in Path(task['root']).glob('*/manifest.json'):
        try:
            value = json.loads(manifest.read_text())
        except (ValueError, OSError):
            continue
        if not isinstance(value, dict):
            continue
        if value.get('plan', {}).get('task_id') != task['task_id']:
            continue
        for attempt in (manifest.parent / 'attempts').glob('*.started.json'):
            attempt_id = json.loads(attempt.read_text())['attempt_id']
            shared = ledger / 'reservations' / f"{value['experiment_id']}-{attempt_id}.json"
            if not shared.exists():
                raise ValueError('Task ledger is incomplete; restore before live execution')


def plan_digest(bundle: 'Bundle') -> str:
    return checksum((bundle.path / 'manifest.json').read_bytes()
                    + (bundle.path / 'execution-binding.json').read_bytes())


def validate_authorization(bundle: 'Bundle') -> dict:
    if not bundle.authorization_id:
        raise ValueError('Explicit invocation approval is required before live execution')
    task = read_task(bundle.path.parent)
    if str(bundle.task_ledger) != task['ledger'] or bundle.plan.task_id != task['task_id']:
        raise ValueError('Live task identity mismatch')
    key = f'{bundle.path.name}-{bundle.authorization_id}'
    record = json.loads((bundle.task_ledger / 'authorizations' / f'{key}.json').read_text())
    if (record['plan_digest'] != plan_digest(bundle)
            or record['bundle_path'] != str(bundle.path.resolve())
            or record['invocation'] != bundle.authorization_id
            or record['task_id'] != bundle.plan.task_id):
        raise ValueError('Approval does not match this plan, task and invocation')
    if record != json.loads((bundle.path / 'authorizations' / f'{bundle.authorization_id}.json').read_text()):
        raise ValueError('Approval publication is incomplete')
    return record


def recover_reservations(bundle: 'Bundle') -> None:
    """Expose task-first crash reservations as uncertain before continuation review."""
    with task_lock(bundle.task_ledger):
        task_state(bundle.task_ledger)
        prefix = bundle.manifest['experiment_id']
        for shared in (bundle.task_ledger / 'reservations').glob(f'{prefix}-*.json'):
            record = json.loads(shared.read_text())
            path = bundle.path / 'attempts' / f"{record['attempt_id']}.started.json"
            if not path.exists():
                write_json_once(path, record)


def reserve(bundle: 'Bundle', path: Path, record: dict) -> bool:
    """Task and invocation bounds are enforced under the same reservation lock."""
    with task_lock(bundle.task_ledger):
        authority = validate_authorization(bundle)
        reservations = bundle.task_ledger / 'reservations'
        prefix = bundle.manifest['experiment_id']
        for previous in bundle.attempts():
            if not (reservations / f"{prefix}-{previous['attempt_id']}.json").exists():
                raise ValueError('Task ledger is incomplete; restore before live execution')
        shared = reservations / f"{prefix}-{record['attempt_id']}.json"
        if shared.exists() and not path.exists():
            write_json_once(path, json.loads(shared.read_text()))
            return False
        if path.exists():
            raise FileExistsError(path)
        if bundle.attempt_count >= bundle.plan.max_calls:
            raise BudgetExceeded('Frozen matrix allowance exhausted')
        state = task_state(bundle.task_ledger)
        records = [json.loads(p.read_text()) for p in reservations.glob('*.json')]
        invocation_used = sum(r['authorization'] == authority['authorization'] for r in records)
        if invocation_used >= authority['invocation_cap']:
            raise BudgetExceeded('Approved invocation allowance exhausted; explicit continuation required')
        if state['used'] >= authority['task_cap']:
            raise BudgetExceeded('Shared task allowance exhausted; new explicit approval required')
        record = {**record, 'authorization': authority['authorization']}
        # A crash after the shared publication spends the slot, even if dispatch never happens.
        write_json_once(shared, record)
        write_json_once(path, record)
        return True
