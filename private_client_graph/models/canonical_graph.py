from pydantic import BaseModel

from .entity import Entity
from .evidence import Evidence
from .relationship import Relationship


class CanonicalGraph(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]
    evidence: list[Evidence]
