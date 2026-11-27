"""Owner-only inspection of the installed Benchmark v4 roster."""
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from private_client_graph.research.benchmark_v4 import BenchmarkRoster, configured_custody, load_roster
from .benchmark_v4 import load_private_workload
from .benchmark_v4_inspection import inspect_frozen_input
from .exploratory_workload import require_private_owner
from .run_inspection import RunObservation
from .semantic_evidence_api import mount_semantic_evidence


def mount_benchmark_v4(app: FastAPI, root: Path, prefix: str) -> bool:
    if configured_custody() is None:
        return False
    if not root.is_absolute() or root.resolve() != root or not root.is_dir() or root.stat().st_mode & 0o077:
        raise ValueError('Benchmark v4 requires a private absolute Research artifact directory')
    require_private_owner(app, os.getenv('PCG_BENCHMARK_V4_OWNER_TOKEN', ''))
    mount_semantic_evidence(app, root, prefix)

    @app.get(f'{prefix}/benchmark-v4', response_model=BenchmarkRoster)
    def roster() -> BenchmarkRoster:
        return load_roster()

    @app.get(f'{prefix}/benchmark-v4/inputs/{{identity}}', response_model=RunObservation)
    def inspect(identity: str) -> RunObservation:
        result = inspect_frozen_input(load_private_workload(), identity)
        if result is None:
            raise HTTPException(404, 'Input is outside the frozen Benchmark v4 roster')
        return result

    return True
