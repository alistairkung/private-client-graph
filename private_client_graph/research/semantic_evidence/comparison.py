"""Compare aligned formal targets without dropping failed assessments."""
from pathlib import Path
from typing import Any

from .reporting import report


def compare(left: Path, right: Path) -> dict[str, Any]:
    first, second = report(left), report(right)
    if first['run_id'] == second['run_id']:
        raise ValueError('Select two different Benchmark v4 Runs')
    left_targets, right_targets = (_index(first), _index(second))
    if (_scope(first) != _scope(second) or left_targets.keys() != right_targets.keys()):
        raise ValueError('Semantic Evidence comparison requires the same frozen target scope and judge contract')
    transitions = [_transition(row, right_targets[identity]) for identity, row in left_targets.items()]
    return {
        'status': 'Exploratory and unverified',
        'temporal_limitation': first['temporal_limitation'],
        'evaluator': first['evaluator'],
        'formal_targets': len(transitions),
        'paired_valid_targets': sum(row['facts_comparable'] for row in transitions),
        'left': _side(first),
        'right': _side(second),
        'transitions': transitions,
    }


def _scope(data: dict[str, Any]) -> tuple:
    baseline = data['deterministic_baseline']
    return (baseline['benchmark_sha256'], baseline['qualified_reference_sha256'],
            baseline['scorer_sha256'], baseline['report_version'], data['evaluator'])


def _index(data: dict[str, Any]) -> dict:
    return {(row['condition'], tuple(row['edge'])): row for row in data['targets']}


def _side(data: dict[str, Any]) -> dict:
    return {key: data[key] for key in ('run_id', 'plan_sha256', 'target_summary', 'operations')}


def _transition(left: dict, right: dict) -> dict:
    comparable = left['status'] == right['status'] == 'judged'
    left_facts = _facts(left) if comparable else {}
    right_facts = _facts(right) if comparable else {}
    changed_facts = [{'fact': fact, 'left': left_facts[fact], 'right': right_facts[fact]}
                     for fact in left_facts if left_facts[fact] != right_facts[fact]]
    return {
        'id': left['id'], 'condition': left['condition'], 'edge': left['edge'],
        'left': _outcome(left), 'right': _outcome(right), 'facts_comparable': comparable,
        'changed_facts': changed_facts,
    }


def _facts(row: dict) -> dict:
    return {fact['fact']: fact['status'] for fact in row['judgment']['facts']}


def _outcome(row: dict) -> dict:
    return {
        'status': row['status'],
        'verdict': row.get('judgment', {}).get('verdict'),
        'exact_outcome': row['deterministic']['exact_outcome'],
        'potentially_sufficient': 'potentially_sufficient_overlooked_by_exact_matching' in row['flags'],
        'reused': 'reuse' in row,
    }
