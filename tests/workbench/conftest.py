from pathlib import Path

import pytest

from private_client_graph.workbench.restore import restore_archive


@pytest.fixture
def history_root(tmp_path):
    root = tmp_path / 'history'
    for name in ('issue-91-demonstration', 'issue-92-pilot'):
        restore_archive(Path('research/history') / f'{name}.zip', root / name)
    return root
