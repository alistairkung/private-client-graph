from pydantic import BaseModel


class Evidence(BaseModel):
    id: str
    document: str
    supporting_text: str
