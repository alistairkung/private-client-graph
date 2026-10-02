from pydantic import BaseModel

from .entity import Entity
from .ground_truth_relationship import GroundTruthRelationship


class GroundTruth(BaseModel):
    entities: list[Entity]
    relationships: list[GroundTruthRelationship]
