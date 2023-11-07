from pydantic import BaseModel, conlist


class Instructor(BaseModel):
    name: str
    address: conlist(str, min_length = 1, max_length = 2)
    iban: str
