from pydantic import BaseModel, conlist, Field

from unisport_abrechnung.configuration import Instructor, Class, Template


class Configuration(BaseModel):
    instructor: Instructor
    class_: Class = Field(alias = "class")
    template: Template
