from pydantic import BaseModel

from .entity import Entity
from .relationship import Relationship
from .source import Source
from .sourced_evidence import SourcedEvidence


class CanonicalState(BaseModel):
    """Facts scoped to one Matter or proposal, without graph or aggregate identity.

    References resolve only within this state. Sequence order and graph-local IDs
    carry the reviewed representation; they are not database key conventions.
    """

    sources: list[Source]
    entities: list[Entity]
    relationships: list[Relationship]
    evidence: list[SourcedEvidence]
