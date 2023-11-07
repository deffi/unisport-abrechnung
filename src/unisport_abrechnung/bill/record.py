from pydantic import BaseModel


class Record(BaseModel):
    day: int
    hours: float
    fee: float
    participant_count: int
