from pydantic import BaseModel


class StreamEventEnvelope(BaseModel):
    event: str
    id: str
    data: dict
