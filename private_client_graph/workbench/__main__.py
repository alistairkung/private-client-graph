"""Explicit local index maintenance, never an HTTP command or experiment runner."""
import argparse
from pathlib import Path

from private_client_graph.persistence.database import database_engine
from .index import rebuild_index


def main() -> None:
    parser = argparse.ArgumentParser(description='Rebuild the read-only research index from retained artifacts')
    parser.add_argument('artifacts', type=Path)
    args = parser.parse_args()
    print(f'Indexed {rebuild_index(database_engine(), args.artifacts)} retained experiments.')


if __name__ == '__main__':
    main()
