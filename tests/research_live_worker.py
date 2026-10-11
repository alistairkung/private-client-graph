"""Test-only subprocess: substitute only DeepSeek, never select a paid boundary."""
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from private_client_graph.research import provider
from private_client_graph.research.demo import recorded_response
from private_client_graph.workbench.worker import run


def substitute(request, **kwargs):
    response = recorded_response(request)
    response.returned_model = 'substituted-test-provider'
    return response


provider.invoke_deepseek = substitute
root, identity, invocation, inherited_lock, parent = sys.argv[1:]
try:
    run(Path(root), identity, invocation, int(parent))
finally:
    os.close(int(inherited_lock))
