from pydantic import BaseModel


class Source(BaseModel):
    """Explicitly identified finalized text within one aggregate."""

    id: str
    title: str
    text: str
