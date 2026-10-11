"""Compatibility imports and the existing ``python -m private_client_graph.extract`` CLI."""
from private_client_graph.extraction import (
    EXTRACTION_PROMPT,
    build_relationship_extraction_chain,
    extract_relationships_from_text,
    extraction_messages,
)
from private_client_graph.extraction.cli import extract_relationships, main

__all__ = [
    'EXTRACTION_PROMPT', 'build_relationship_extraction_chain',
    'extract_relationships_from_text', 'extraction_messages', 'extract_relationships', 'main',
]

if __name__ == '__main__':
    main()
