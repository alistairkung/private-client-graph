"""Explicit local-browser authorization, bound to one immutable invocation."""
import json
from pathlib import Path

from private_client_graph.research.artifacts import Bundle, utc_now, write_json_once
from private_client_graph.research.live_accounting import task_lock, task_state
from .execution_contracts import FrozenPlan, LiveApproval


def authorize(bundle: Bundle, plan: FrozenPlan, approval: LiveApproval, origin: str) -> None:
    if approval.plan_digest != plan.digest:
        raise ValueError('Approval does not match the frozen plan digest')
    if approval.task_id != plan.task_id or approval.task_cap != plan.preview.proposal.task_call_cap:
        raise ValueError('Approval does not match the frozen task identity and proposed cap')
    from .replay_gate import require_replay_control
    replay_gate_digest = require_replay_control(bundle, approval.request_id)
    key = f'{plan.id}-{approval.request_id}'
    shared = bundle.task_ledger / 'authorizations' / f'{key}.json'
    local = bundle.path / 'authorizations' / f'{approval.request_id}.json'
    with task_lock(bundle.task_ledger):
        if shared.exists():
            record = json.loads(shared.read_text())
            if record.get('replay_gate_digest') != replay_gate_digest:
                raise ValueError('Replay control differs from the original authorization')
            if record['request'] != approval.model_dump() or record['origin'] != origin:
                raise ValueError('Approval replay differs from the original authorization')
        else:
            state = task_state(bundle.task_ledger)
            if state['used'] != approval.expected_task_usage or state['cap'] != approval.expected_task_cap:
                raise ValueError('Task budget changed; refresh status and review a new approval')
            if approval.task_cap < state['cap']:
                raise ValueError('Task cap cannot be reduced; freeze a new plan')
            if approval.task_cap <= state['used']:
                raise ValueError('Task allowance exhausted; freeze and explicitly approve a larger cap')
            record = {'version': 1, 'authorization': key, 'at': utc_now(),
                'origin': origin, 'actor': 'explicit-local-browser',
                'task_id': plan.task_id, 'task_cap': approval.task_cap,
                'plan_digest': plan.digest, 'bundle_path': str(bundle.path.resolve()),
                'invocation': approval.request_id, 'invocation_cap': plan.preview.invocation_cap,
                'request': approval.model_dump()}
            if replay_gate_digest is not None:
                record['replay_gate_digest'] = replay_gate_digest
            write_json_once(shared, record)
        # Recover publication interrupted between the authoritative ledger and bundle copy.
        if not local.exists():
            write_json_once(local, record)
        elif json.loads(local.read_text()) != record:
            raise ValueError('Local approval differs from task authority')


def main() -> None:
    import argparse
    from private_client_graph.research.live_accounting import initialize_task
    parser = argparse.ArgumentParser(description='Provision one persistent local research task, with zero initial paid allowance.')
    parser.add_argument('root', type=Path)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    task = initialize_task(args.root, args.label)
    print(f"Provisioned {task['task_id']}; no calls authorized.")


if __name__ == '__main__':
    main()
