from collections.abc import Iterator

from pydantic import BaseModel

from unisport_abrechnung.bill import Record
from unisport_abrechnung.configuration import Configuration
from unisport_abrechnung.util.date import WEEKDAYS, days


class Bill(BaseModel):
    configuration: Configuration
    year: int
    month: int
    participant_counts: list[int]

    def records(self) -> Iterator[Record]:
        weekday = WEEKDAYS[self.configuration.class_.weekday.lower()]

        for day, count in zip(days(self.year, self.month, weekday), self.participant_counts, strict=True):
            if count > 0:
                hours = self.configuration.class_.hours()
                fee = hours * self.configuration.class_.hourly_fee

                yield Record(day=day, hours=hours, fee=fee, participant_count=count)

    def total_hours(self) -> float:
        return sum(r.hours for r in self.records())

    def total_fee(self) -> float:
        return sum(r.fee for r in self.records())

    def default_file_name_stem(self) -> str:
        instructor = self.configuration.instructor.name
        class_ = self.configuration.class_.name

        return f"Trainerabrechnung {instructor} {class_} {self.year}-{self.month:02d}"
