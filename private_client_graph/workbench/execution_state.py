"""Non-mutating local execution visibility, independent of command dispatch."""
import fcntl
import json
from pathlib import Path

from pydantic import BaseModel

from private_client_graph.research.live_accounting import read_task, task_state
from .execution_contracts import TaskBudget


class ExecutionAvailability(BaseModel):
    active_run_id: str | None = None
    task_budget: TaskBudget | None = None
    accounting_reason: str | None = None


def active_run_id(root: Path) -> str | None:
    path = root / '.active.lock'
    if not path.exists():
        return None
    # Do not create a lock or repair an advisory pointer on a read request.
    with path.open('r') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pointer = root / '.active.json'
            return json.loads(pointer.read_text())['plan_id'] if pointer.exists() else 'unknown'
    return None


def execution_availability(root: Path) -> ExecutionAvailability:
    result = ExecutionAvailability(active_run_id=active_run_id(root))
    if not (root / 'live-task.json').exists():
        result.accounting_reason = 'No local live task has been provisioned.'
        return result
    try:
        task = read_task(root)
        state = task_state(Path(task['ledger']))
        result.task_budget = TaskBudget(**state, remaining=max(0, state['cap'] - state['used']))
    except (OSError, ValueError, KeyError):
        result.accounting_reason = 'Task accounting is unavailable; restore it before execution.'
    return result
