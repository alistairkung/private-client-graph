"""Read the single packaged publication; no private research runtime dependency."""
import json
from pathlib import Path

from private_client_graph.published import publication_digest

PUBLISHED_SNAPSHOT = Path(__file__).resolve().parents[1] / 'published' / 'research-results.v1.json'


def read_public_research() -> bytes:
    """Return the exact artifact bytes after checking its public integrity envelope."""
    content = PUBLISHED_SNAPSHOT.read_bytes()
    snapshot = json.loads(content)
    integrity = snapshot['integrity']
    if (snapshot['schema_version'] != 1 or integrity['algorithm'] != 'sha256'
            or integrity['scope'] != 'canonical-json-excluding-integrity'
            or integrity['digest'] != publication_digest(snapshot)):
        raise ValueError('Invalid published research snapshot')
    return content
