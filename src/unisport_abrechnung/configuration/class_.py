import calendar
from collections.abc import Iterator
from datetime import datetime

from pydantic import BaseModel

from unisport_abrechnung.util.date import days


_weekdays = {
    "mon": calendar.MONDAY,
    "tue": calendar.TUESDAY,
    "wed": calendar.WEDNESDAY,
    "thu": calendar.THURSDAY,
    "fri": calendar.FRIDAY,
    "sat": calendar.SATURDAY,
    "sun": calendar.SUNDAY,
}


class Class(BaseModel):
    name: str
    weekday: str
    start_time: str
    end_time: str
    hourly_fee: float

    def days(self, year: int, month: int) -> Iterator[int]:
        weekday = _weekdays[self.weekday.lower()]
        return days(year, month, weekday)

    def hours(self):
        start_time = datetime.strptime(self.start_time, "%H:%M")
        end_time = datetime.strptime(self.end_time, "%H:%M")
        return (end_time - start_time).total_seconds() / 3600
