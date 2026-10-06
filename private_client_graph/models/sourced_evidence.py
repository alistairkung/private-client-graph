from .evidence import Evidence


class SourcedEvidence(Evidence):
    """Evidence attributed by Source identity, independently of its display label."""

    source_id: str
