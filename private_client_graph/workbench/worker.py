"""Sequential worker; live dispatch requires durable invocation authority."""
import json
from functools import partial
import os
import sys
from pathlib import Path

from private_client_graph.research.demo import recorded_response
from private_client_graph.research.runner import execute
from .planning import open_executable, require_live
from .supervisor import command_lock, event


def run(root: Path, identity: str, invocation: str, parent: int) -> None:
    bundle, plan = open_executable(root, identity)
    def should_stop() -> bool:
        return (bundle.path / 'stops' / f'{invocation}.json').exists() or os.getppid() != parent
    try:
        records = json.loads((bundle.path / 'recorded-responses.json').read_text())
        live = bundle.plan.kind == 'live_experiment'
        provider = partial(recorded_response, records=records)
        if live:
            require_live(root)
            bundle.authorization_id = invocation
            from private_client_graph.research.provider import invoke_deepseek
            provider = partial(invoke_deepseek, api_key=os.getenv('DEEPSEEK_API_KEY', ''))
        session = execute(bundle, provider=provider, live=live,
            max_new_attempts=plan.preview.invocation_cap, should_stop=should_stop)
        state = 'complete' if session['stop_reason'] == 'matrix_complete' else 'stopped'
        message = 'Execution complete; inspect retained outcomes.' if state == 'complete' else session['stop_reason']
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
