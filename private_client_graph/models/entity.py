from pydantic import BaseModel

from .types import EntityType


class Entity(BaseModel):
    id: str
    type: EntityType
    name: str
