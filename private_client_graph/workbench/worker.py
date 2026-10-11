"""Offline worker. Provider dispatch is exclusively the recorded boundary."""
import json
from functools import partial
import os
import sys
from pathlib import Path

from private_client_graph.research.demo import recorded_response
from private_client_graph.research.runner import execute
from .planning import open_executable
from .supervisor import command_lock, event


def run(root: Path, identity: str, invocation: str, parent: int) -> None:
    bundle, plan = open_executable(root, identity)
    def should_stop() -> bool:
        return (bundle.path / 'stops' / f'{invocation}.json').exists() or os.getppid() != parent
    try:
        records = json.loads((bundle.path / 'recorded-responses.json').read_text())
        session = execute(bundle, provider=partial(recorded_response, records=records), live=False,
            max_new_attempts=plan.preview.invocation_cap, should_stop=should_stop)
        state = 'complete' if session['stop_reason'] == 'matrix_complete' else 'stopped'
        message = 'Offline execution complete; inspect recorded outcomes.' if state == 'complete' else session['stop_reason']
    except Exception as error:
        state, message = 'failed', f'Execution stopped: {type(error).__name__}. Inspect retained artifacts.'
    with command_lock(root):
        event(bundle, state, message, invocation)
    # Indexing failure cannot erase execution or trigger a retry of the experiment.
    from private_client_graph.persistence.database import database_engine
    from .index import rebuild_index
    rebuild_index(database_engine(), root)


if __name__ == '__main__':
    root, identity, invocation, inherited_lock, parent = sys.argv[1:]
    try:
        run(Path(root), identity, invocation, int(parent))
    finally:
        os.close(int(inherited_lock))
