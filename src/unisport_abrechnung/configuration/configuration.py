from pathlib import Path
import tomllib

from pydantic import BaseModel, Field

from unisport_abrechnung.configuration import Instructor, Class, Template


class Configuration(BaseModel):
    instructor: Instructor
    class_: Class = Field(alias = "class")
    template: Template

    @classmethod
    def load(cls, file: Path):
        with open(file, "rb") as f:
            doc = tomllib.load(f)
            return Configuration.model_validate(doc)
