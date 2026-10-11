"""Real stored-history browser server; never invokes a stochastic boundary."""
import os
import sys
import tempfile
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from private_client_graph.persistence.database import database_engine
from private_client_graph.workbench.index import rebuild_index
from private_client_graph.workbench.restore import restore_archive

with tempfile.TemporaryDirectory(prefix='pcg-research-browser-') as directory:
    root = Path(directory)
    for name in ('issue-91-demonstration', 'issue-92-pilot'):
        restore_archive(ROOT / 'research/history' / f'{name}.zip', root / name)
    # Explicit exceptional-state fixtures derived from retained history, in a temporary directory only.
    restore_archive(ROOT / 'research/history/issue-92-pilot.zip', root / 'incomplete-history')
    (root / 'incomplete-history/CHECKSUMS.json').unlink()
    (root / 'incomplete-history/results/case_03_fixture-resolve-3.json').unlink()
    (root / 'corrupt-history').mkdir()
    (root / 'corrupt-history/manifest.json').write_text('{invalid')
    os.environ['PCG_RESEARCH_ARTIFACTS'] = str(root)
    rebuild_index(database_engine(), root)
    from private_client_graph.workbench.api import create_app
    uvicorn.run(create_app(), host='127.0.0.1', port=4175)
