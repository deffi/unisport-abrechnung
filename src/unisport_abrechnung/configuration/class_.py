from datetime import datetime

from pydantic import BaseModel


class Class(BaseModel):
    name: str
    weekday: str
    start_time: str
    end_time: str
    hourly_fee: float

    def hours(self):
        start_time = datetime.strptime(self.start_time, "%H:%M")
        end_time = datetime.strptime(self.end_time, "%H:%M")
        return (end_time - start_time).total_seconds() / 3600
