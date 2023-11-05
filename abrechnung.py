from collections.abc import Iterator
import calendar
import tomllib
from pathlib import Path
import re
from datetime import datetime

from pydantic import BaseModel, conlist, Field
import pypdf as pdf
import typer


WEEKDAYS = {
    "mon": calendar.MONDAY,
    "tue": calendar.TUESDAY,
    "wed": calendar.WEDNESDAY,
    "thu": calendar.THURSDAY,
    "fri": calendar.FRIDAY,
    "sat": calendar.SATURDAY,
    "sun": calendar.SUNDAY,
}


class Trainer(BaseModel):
    name: str
    address: conlist(str, min_length = 1, max_length = 2)
    iban: str
    hourly_fee: float


class TimeRange(BaseModel):
    start: str
    end: str

    def hours(self):
        return (datetime.strptime(self.end, "%H:%M") - datetime.strptime(self.start, "%H:%M")).total_seconds() / 3600


class Class(BaseModel):
    name: str
    weekday: str
    time: TimeRange


class Template(BaseModel):
    file: str
    fee_column_prefix: str
    total_fee_column: str


class Data(BaseModel):
    trainer: Trainer
    class_: Class = Field(alias = "class")
    template: Template


class Record(BaseModel):
    day: int
    participant_count: int


def days(year: int, month: int, weekday: int) -> list[int]:
    cal = calendar.Calendar()
    return [dom for dom, dow in cal.itermonthdays2(year, month) if dom != 0 and dow == weekday]


def parse_month(month: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d\d?)/(\d\d\d\d)", month)
    month = int(match.group(1))
    year = int(match.group(2))
    return year, month


def format_number(value: float) -> str:
    return str(value).replace(".", ",")


def records(year: int, month: int, weekday: int, participant_count: list[int]) -> Iterator[Record]:
    for day, count in zip(days(year, month, weekday), participant_count, strict=True):
        if count > 0:
            yield Record(day=day, participant_count=count)


def abrechnung(data_file: Path, year: int, month: int, participant_count: list[int]):
    with open(data_file, "rb") as f:
        doc = tomllib.load(f)
        data = Data.model_validate(doc)

    input_file = data_file.parent / data.template.file

    print(f"Reading {input_file}")
    reader = pdf.PdfReader(open(input_file, "rb"), strict=False)  # TODO strict?

    writer = pdf.PdfWriter()
    writer.add_page(reader.pages[0])

    writer.update_page_form_field_values(writer.pages[0], {
        "Monat": data.trainer.name,
        "1": data.trainer.address[0],
        "2": data.trainer.address[1],
        "3": data.trainer.iban,
    })

    writer.update_page_form_field_values(writer.pages[0], {
        "sportart": data.class_.name,  # Sportart
        "undefined": f"{month}/{year}",  # Monat
    })

    recs = list(records(year, month, WEEKDAYS[data.class_.weekday.lower()], participant_count))

    for i, record in enumerate(recs):
        fee = data.trainer.hourly_fee * data.class_.time.hours()

        writer.update_page_form_field_values(writer.pages[0], {
            f"DatumRow{i+1}": f"{record.day}.{month}.{year}",
            f"ArbeitszeitRow{i+1}": f"{data.class_.time.start} - {data.class_.time.end}",
            f"StdRow{i+1}": format_number(data.class_.time.hours()),
            f"{data.template.fee_column_prefix}{i + 1}": format_number(fee),
            f"Teil nehmerRow{i + 1}": record.participant_count,
        })

    writer.update_page_form_field_values(writer.pages[0], {
        "summe": format_number(len(recs) * data.class_.time.hours()),
        data.template.total_fee_column: format_number(len(recs) * data.class_.time.hours() * data.trainer.hourly_fee),
        "Braunschweig den": datetime.today().strftime("%d.%m.%Y"),
    })

    output_file_name = f"Trainerabrechnung {data.trainer.name} {data.class_.name} {year}-{month:02d}.pdf"
    output_file = data_file.with_name(output_file_name)
    print(f"Writing {output_file}")
    with open(output_file, "wb") as f:
        writer.write(f)


def main(data_file: Path, month: str, participant_count: list[int]):
    year, month = parse_month(month)
    abrechnung(data_file, year, month, participant_count)


if __name__ == "__main__":
    typer.run(main)
