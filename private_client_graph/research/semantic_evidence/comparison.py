"""Compare the same approved proof routes with fixed target populations."""
from pathlib import Path
from typing import Any

from .reporting import report


def compare(left: Path, right: Path) -> dict[str, Any]:
    return compare_reports(report(left), report(right))


def compare_reports(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    if first['run_id'] == second['run_id']:
        raise ValueError('Select two different Benchmark v4 Runs')
    left_targets, right_targets = _index(first), _index(second)
    if (_scope(first) != _scope(second) or left_targets.keys() != right_targets.keys()
            or any(_reference(row) != _reference(right_targets[identity]) for identity, row in left_targets.items())):
        raise ValueError('Semantic Evidence comparison requires the same frozen target scope and judge contract')
    paired = [(row, right_targets[identity]) for identity, row in left_targets.items()]
    comparable = first['state'] == second['state'] == 'complete'
    return {
        'methodology': first['methodology'],
        'scope_note': first['scope_note'],
        'evaluator': first['evaluator'],
        'formal_targets': len(paired),
        'comparable': comparable,
        'paired_valid_targets': sum(left['status'] == right['status'] == 'judged' for left, right in paired),
        'left': _side(first),
        'right': _side(second),
        'transitions': [_transition(left, right) for left, right in paired] if comparable else [],
    }


def _scope(data: dict[str, Any]) -> tuple:
    baseline = data['deterministic_baseline']
    return (baseline['benchmark_sha256'], baseline['qualified_reference_sha256'],
            baseline['scorer_sha256'], baseline['report_version'], data['evaluator'])


def _index(data: dict[str, Any]) -> dict:
    return {(row['condition'], tuple(row['edge'])): row for row in data['targets']}


def _reference(row: dict) -> tuple:
    members = {member['id']: (member['source_id'], member['text']) for member in row['members']}
    routes = tuple(tuple(members[identity] for identity in route['members']) for route in row['routes'])
    return row['deterministic']['joint_only'], routes


def _side(data: dict[str, Any]) -> dict:
    return {key: data[key] for key in ('run_id', 'plan_sha256', 'state', 'graph_f1', 'evidence_adjusted_f1',
                                      'target_summary', 'operations')}


def _transition(left: dict, right: dict) -> dict:
    changed_members = []
    right_ids = {(member['source_id'], member['text']): member['id'] for member in right['members']}
    for member in left['members']:
        key = (member['source_id'], member['text'])
        before, after = _match(left, member['id']), _match(right, right_ids[key])
        if before != after:
            changed_members.append({'member_id': member['id'], 'source_id': key[0], 'quotation': key[1],
                                    'left': before, 'right': after})
    return {
        'id': left['id'], 'condition': left['condition'], 'edge': left['edge'],
        'left': _outcome(left), 'right': _outcome(right),
        'changed_members': changed_members,
    }


def _match(row: dict, member_id: str) -> str:
    if member_id in row['exact_matches']:
        return 'exact'
    if member_id in row['semantic_members']:
        return 'semantic'
    return 'unmatched'


def _outcome(row: dict) -> dict:
    return {
        'status': row['status'],
        'exact_outcome': row['deterministic']['exact_outcome'],
        'complete': any(route['complete'] for route in row['routes']),
        'reused': 'reuse' in row,
    }
