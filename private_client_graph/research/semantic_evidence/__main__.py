"""Plan, execute and report ground-truth-aligned Semantic Evidence."""
import argparse
import json
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from .assessment import MAX_USD, PRICING, execute, open_plan, prepare, upper_cost, frozen_rates
from .comparison import compare
from .reporting import report
from .store import entry, initialize, require, task_root


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    plan = commands.add_parser('plan', help='Freeze a Workbench Run assessment offline')
    plan.add_argument('artifact_root', type=Path)
    plan.add_argument('run_id')
    plan.add_argument('--reuse-from', action='append', default=[], metavar='RUN_ID')
    plan.add_argument('--peak-rates', nargs=2, type=Decimal, metavar=('INPUT', 'OUTPUT'), required=True)
    plan.add_argument('--usd-ceiling', type=Decimal, default=MAX_USD)
    plan.add_argument('--task-call-ceiling', type=int, required=True)
    commands.add_parser('initialize-task', help='Provision the shared Semantic Evidence ledger with zero authority'
                        ).add_argument('artifact_root', type=Path)
    run = commands.add_parser('run', help='Dispatch only the explicitly approved assessment')
    run.add_argument('directory', type=Path)
    run.add_argument('--approve-plan-sha256', required=True)
    run.add_argument('--approval-reference', required=True)
    run.add_argument('--verified-peak-rates', type=Decimal, nargs=2, metavar=('INPUT', 'OUTPUT'), required=True)
    commands.add_parser('report', help='Regenerate the private assessment report offline').add_argument('directory', type=Path)
    comparison = commands.add_parser('compare', help='Compare two Workbench Run assessments offline')
    comparison.add_argument('artifact_root', type=Path)
    comparison.add_argument('left')
    comparison.add_argument('right')
    args = parser.parse_args()

    if args.command == 'plan':
        _plan(args)
    elif args.command == 'initialize-task':
        print(initialize(args.artifact_root)['task_id'])
    elif args.command == 'run':
        input_rate, output_rate = args.verified_peak_rates
        execute(args.directory, approved_digest=args.approve_plan_sha256, approval_reference=args.approval_reference,
                verified_rates=(input_rate, output_rate), api_key=os.getenv('DEEPSEEK_API_KEY', ''))
    else:
        result = (compare(require(args.artifact_root, args.left), require(args.artifact_root, args.right))
                  if args.command == 'compare' else report(args.directory))
        print(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False))


def _plan(args: argparse.Namespace) -> None:
    root = args.artifact_root.resolve()
    directory = entry(root, args.run_id)
    input_rate, output_rate = args.peak_rates
    pricing = PRICING.model_copy(update={'input_per_million': float(input_rate),
        'output_per_million': float(output_rate), 'retrieved_at': datetime.now(timezone.utc).date().isoformat()})
    donors = [require(root, run_id) for run_id in args.reuse_from]
    digest = prepare(root / args.run_id, directory, task_root=task_root(root), task_call_ceiling=args.task_call_ceiling,
                     donors=donors, pricing=pricing, max_usd=args.usd_ceiling)
    plan, _, _ = open_plan(directory)
    print(json.dumps({'directory': str(directory), 'plan_sha256': digest, 'maximum_paid_attempts': plan.max_calls,
        'reused_judgments': len(plan.reused), 'usd_ceiling': str(plan.max_usd),
        'task_call_ceiling': plan.task_limit,
        'maximum_estimated_peak_usd': str(upper_cost(plan, frozen_rates(plan)))}, indent=2))


if __name__ == '__main__':
    main()
