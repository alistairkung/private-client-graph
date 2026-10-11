"""Test-only stochastic boundary pause; the worker/runner/pipeline remain real."""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from private_client_graph.workbench import worker
from private_client_graph.research.demo import recorded_response

root, identity, invocation, lock, parent = sys.argv[1:]
marker = Path(root) / '.boundary-entered'
release = Path(root) / '.boundary-release'


def boundary(request, **kwargs):
    marker.touch()
    for _ in range(200):
        if release.exists():
            return recorded_response(request, **kwargs)
        time.sleep(.05)
    raise RuntimeError('Test boundary was not released')


worker.recorded_response = boundary
try:
    worker.run(Path(root), identity, invocation, int(parent))
finally:
    os.close(int(lock))
