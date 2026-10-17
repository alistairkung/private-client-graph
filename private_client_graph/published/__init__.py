"""Versioned, curated public research artifacts; no research execution imports."""
import hashlib
import json


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def publication_digest(snapshot: dict) -> str:
    """Digest canonical UTF-8 JSON excluding the top-level integrity envelope."""
    return hashlib.sha256(canonical_bytes({key: value for key, value in snapshot.items()
                                         if key != 'integrity'})).hexdigest()
