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


class Configuration(BaseModel):
    trainer: Trainer
    class_: Class = Field(alias = "class")
    template: Template


class Record(BaseModel):
    day: int
    hours: float
    fee: float
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


def create_records(configuration: Configuration, year: int, month: int, weekday: int, participant_count: list[int]) -> Iterator[Record]:
    for day, count in zip(days(year, month, weekday), participant_count, strict=True):
        if count > 0:
            hours = configuration.class_.time.hours()
            fee = hours * configuration.trainer.hourly_fee

            yield Record(day=day, hours=hours, fee=fee, participant_count=count)


def abrechnung(configuration_file: Path, year: int, month: int, participant_count: list[int]):
    with open(configuration_file, "rb") as f:
        doc = tomllib.load(f)
        configuration = Configuration.model_validate(doc)

    input_file = configuration_file.parent / configuration.template.file

    print(f"Reading {input_file}")
    reader = pdf.PdfReader(open(input_file, "rb"), strict=False)  # TODO strict?

    writer = pdf.PdfWriter()
    writer.add_page(reader.pages[0])

    writer.update_page_form_field_values(writer.pages[0], {
        "Monat": configuration.trainer.name,
        "1": configuration.trainer.address[0],
        "2": configuration.trainer.address[1],
        "3": configuration.trainer.iban,
    })

    writer.update_page_form_field_values(writer.pages[0], {
        "sportart": configuration.class_.name,  # Sportart
        "undefined": f"{month}/{year}",  # Monat
    })

    records = list(create_records(configuration, year, month, WEEKDAYS[configuration.class_.weekday.lower()], participant_count))

    for i, record in enumerate(records):
        writer.update_page_form_field_values(writer.pages[0], {
            f"DatumRow{i+1}": f"{record.day}.{month}.{year}",
            f"ArbeitszeitRow{i+1}": f"{configuration.class_.time.start} - {configuration.class_.time.end}",
            f"StdRow{i+1}": format_number(record.hours),
            f"{configuration.template.fee_column_prefix}{i + 1}": format_number(record.fee),
            f"Teil nehmerRow{i + 1}": record.participant_count,
        })

    writer.update_page_form_field_values(writer.pages[0], {
        "summe": format_number(sum(r.hours for r in records)),
        configuration.template.total_fee_column: format_number(sum(r.fee for r in records)),
        "Braunschweig den": datetime.today().strftime("%d.%m.%Y"),
    })

    output_file_name = f"Trainerabrechnung {configuration.trainer.name} {configuration.class_.name} {year}-{month:02d}.pdf"
    output_file = configuration_file.with_name(output_file_name)
    print(f"Writing {output_file}")
    with open(output_file, "wb") as f:
        writer.write(f)


def main(data_file: Path, month: str, participant_count: list[int]):
    year, month = parse_month(month)
    abrechnung(data_file, year, month, participant_count)


if __name__ == "__main__":
    typer.run(main)
