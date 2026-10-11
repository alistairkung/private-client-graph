"""Local container bootstrap: restore retained history once, then rebuild projections."""
import os
from pathlib import Path

from private_client_graph.persistence.database import database_engine
from .index import rebuild_index
from .restore import restore_archive


def main() -> None:
    root = Path(os.environ['PCG_RESEARCH_ARTIFACTS'])
    root.mkdir(parents=True, exist_ok=True)
    for archive in sorted(Path('research/history').glob('*.zip')):
        destination = root / archive.stem
        if not destination.exists():
            restore_archive(archive, destination)
    rebuild_index(database_engine(), root)


if __name__ == '__main__':
    main()
