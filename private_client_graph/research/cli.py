"""Plan, run, inspect, render and export the bounded alias-resolution experiment."""
import argparse
import json
import os
from functools import partial
from pathlib import Path

from dotenv import load_dotenv

from .artifacts import Bundle
from .demo import recorded_response
from .export import export_bundle, verify_export
from .fixtures import load_inputs
from .plan import ExperimentPlan, Pricing
from .provider import ModelSettings, invoke_deepseek
from .report import render_report
from .runner import Provider, execute
from .summary import summarize


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    plan = commands.add_parser('plan', help='Create a frozen manifest without making provider calls')
    plan.add_argument('bundle', type=Path)
    plan.add_argument('--kind', choices=['demonstration', 'task_a_diagnostic', 'task_b_pilot'], default='demonstration')
    plan.add_argument('--samples', help='Comma-separated frozen input IDs; default all six')
    plan.add_argument('--model')
    plan.add_argument('--effective-model', help='Provider-resolved model/version recorded during preflight')
    plan.add_argument('--repetitions', type=int, default=3)
    plan.add_argument('--fresh', type=int)
    plan.add_argument('--max-calls', type=int)
    plan.add_argument('--pricing', type=Path, help='Dated Pricing JSON; omit when unknown')
    plan.add_argument('--authorization-reference')
    plan.add_argument('--reviewed-commit')
    run = commands.add_parser('run', help='Resume attempts; live execution requires --live')
    run.add_argument('bundle', type=Path)
    run.add_argument('--live', action='store_true')
    run.add_argument('--checkpoint', type=int, help='Maximum new attempts this invocation; does not reset task budget')
    for command in ('inspect', 'render'):
        commands.add_parser(command).add_argument('bundle', type=Path)
    export = commands.add_parser('export')
    export.add_argument('bundle', type=Path)
    export.add_argument('destination', type=Path)
    args = parser.parse_args(argv)
    if args.command == 'plan':
        _plan(args)
        return
    bundle = Bundle.open(args.bundle)
    if args.command == 'run':
        _run(bundle, args)
    elif args.command == 'inspect':
        print(json.dumps(summarize(bundle), indent=2))
    elif args.command == 'render':
        with bundle.execution_lock():
            (bundle.path / 'report.html').write_text(render_report(bundle))
            (bundle.path / 'summary.json').write_text(json.dumps(summarize(bundle), indent=2) + '\n')
        print(bundle.path / 'report.html')
    else:
        export_bundle(bundle, args.destination)
        verify_export(args.destination)
        print(args.destination)


def _plan(args: argparse.Namespace) -> None:
    inputs = load_inputs()
    if args.samples:
        wanted = args.samples.split(',')
        if len(set(wanted)) != len(wanted) or set(wanted) - {s.sample_id for s in inputs}:
            raise ValueError('Unknown or duplicate sample selection')
        inputs = [s for s in inputs if s.sample_id in wanted]
    load_dotenv(Path('.env'))
    settings = ModelSettings(model=args.model or os.getenv('DEEPSEEK_MODEL', 'deepseek-flash'))
    plan = ExperimentPlan(
        kind=args.kind, task_id='92' if args.kind == 'task_b_pilot' else '91', inputs=inputs,
        settings=settings, effective_model=args.effective_model, repetitions=args.repetitions,
        fresh_extractions=args.fresh if args.fresh is not None else (5 if args.kind == 'task_b_pilot' else 0),
        max_calls=args.max_calls if args.max_calls is not None else (5 if args.kind == 'task_a_diagnostic' else 38),
        pricing=Pricing.model_validate_json(args.pricing.read_text()) if args.pricing else None,
        authorization_reference=args.authorization_reference, reviewed_commit=args.reviewed_commit)
    Bundle.create(args.bundle, plan)
    print(args.bundle / 'manifest.json')


def _run(bundle: Bundle, args: argparse.Namespace) -> None:
    if args.checkpoint is not None and args.checkpoint < 0:
        raise ValueError('Checkpoint must be nonnegative')
    provider: Provider
    if args.live:
        if bundle.plan.kind == 'demonstration':
            raise ValueError('Demonstration manifests cannot make live calls')
        load_dotenv(Path('.env'))
        key = os.getenv('DEEPSEEK_API_KEY')
        if not key:
            raise ValueError('DEEPSEEK_API_KEY is not configured')
        provider = partial(invoke_deepseek, api_key=key)
    else:
        provider = recorded_response
    checkpoint = args.checkpoint
    if bundle.plan.kind == 'task_b_pilot' and checkpoint is None:
        checkpoint = 6  # inspect the first matched challenge repetitions before continuing
    result = execute(bundle, provider=provider, live=args.live, max_new_attempts=checkpoint)
    print(json.dumps(result, indent=2))
