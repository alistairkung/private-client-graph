"""Workbench configuration for the private operational benchmark."""
import os
from pathlib import Path

from private_client_graph.research.benchmark_v4 import (
    BenchmarkRoster, BenchmarkWorkload, configured_custody, load_roster, load_workload,
)
from private_client_graph.research.case_metadata import CaseMetadata
from private_client_graph.research.plan import Pricing
from .workspace_contracts import RunConfiguration, RunDraft


def load_private_workload() -> BenchmarkWorkload:
    custody = configured_custody()
    if custody is None:
        raise ValueError('Benchmark v4 private custody is unavailable')
    try:
        return load_workload(custody)
    except (KeyError, OSError, ValueError):
        raise ValueError('Benchmark v4 private workload failed commitment verification') from None


def workload_metadata(roster: BenchmarkRoster) -> dict[str, CaseMetadata]:
    return {
        item.sample_id: CaseMetadata(id=item.sample_id, case_id=item.matter,
            name='U revision 8' if item.reference_methodology == 'consensus_adjudication' else f'Matter {item.matter}',
            description=None, fixture_name=item.id,
            fixture_description=(
                'Consensus adjudication' if item.reference_methodology == 'consensus_adjudication'
                else 'Originally qualified Environment Condition'
            ), kind='benchmark', metadata_available=True, split='dev', matter_family=item.matter)
        for item in roster.inputs
    }


def default_benchmark_draft(root: Path) -> RunDraft | None:
    if configured_custody() is None:
        return None
    from .planning import live_budget
    roster = load_roster()
    try:
        budget = live_budget(root)
    except (KeyError, OSError, ValueError):
        task_cap: int = roster.definition.input_count
    else:
        task_cap = max(roster.definition.input_count, budget.cap)
    return RunDraft(configuration=RunConfiguration(
        benchmark_v4_sha256=roster.sha256, input_ids=[item.sample_id for item in roster.inputs],
        input_mode='fresh', execution_mode='live', resolver='none',
        invocation_cap=roster.definition.input_count, task_call_cap=task_cap,
    ))


def run_pricing() -> Pricing | None:
    path = os.getenv('PCG_BENCHMARK_V4_PRICING_FILE')
    if path is None:
        return None
    try:
        return Pricing.model_validate_json(Path(path).read_bytes())
    except (OSError, ValueError):
        raise ValueError('Benchmark v4 pricing file is unavailable or invalid') from None
