"""Restore checksum-verified historical exports into new directories only."""
import argparse
import zipfile
from tempfile import TemporaryDirectory
from pathlib import Path

from private_client_graph.research.export import verify_export


def restore_archive(archive: Path, destination: Path) -> None:
    verify_export(archive)
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix='.restore-', dir=destination.parent) as temporary:
        staged = Path(temporary) / 'bundle'
        staged.mkdir()
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(staged)
        # Publication is atomic; interrupted extraction never becomes retained history.
        if destination.exists():
            raise FileExistsError(destination)
        staged.rename(destination)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    restore_archive(args.archive, args.destination)


if __name__ == '__main__':
    main()
