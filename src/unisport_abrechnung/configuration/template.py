from pydantic import BaseModel


class Template(BaseModel):
    file: str
