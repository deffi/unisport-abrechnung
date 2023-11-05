from collections.abc import Iterator
import calendar
import tomllib
from pathlib import Path
import re
from datetime import datetime

import pypdf
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


class Bill(BaseModel):
    configuration: Configuration
    year: int
    month: int
    participant_counts: list[int]

    def records(self) -> Iterator[Record]:
        weekday = WEEKDAYS[self.configuration.class_.weekday.lower()]

        for day, count in zip(days(self.year, self.month, weekday), self.participant_counts, strict=True):
            if count > 0:
                hours = self.configuration.class_.time.hours()
                fee = hours * self.configuration.trainer.hourly_fee

                yield Record(day=day, hours=hours, fee=fee, participant_count=count)


def days(year: int, month: int, weekday: int) -> Iterator[int]:
    cal = calendar.Calendar()
    for dom, dow in cal.itermonthdays2(year, month):
        if dom != 0 and dow == weekday:
            yield dom


def parse_month(month: str) -> tuple[int, int]:
    match = re.fullmatch(r"(\d\d?)/(\d\d\d\d)", month)
    month = int(match.group(1))
    year = int(match.group(2))
    return year, month


def format_number(value: float) -> str:
    return str(value).replace(".", ",")


def fill_pdf_fields(writer: pypdf.PdfWriter, bill: Bill):
    records = list(bill.records())

    # Global fields
    writer.update_page_form_field_values(writer.pages[0], {
        # Trainer data
        "Monat": bill.configuration.trainer.name,
        "1": bill.configuration.trainer.address[0],
        "2": bill.configuration.trainer.address[1],
        "3": bill.configuration.trainer.iban,

        # Bill data
        "sportart": bill.configuration.class_.name,  # Sportart
        "undefined": f"{bill.month}/{bill.year}",  # Monat

        # Totals
        "summe": format_number(sum(r.hours for r in records)),
        bill.configuration.template.total_fee_column: format_number(sum(r.fee for r in records)),

        # Signature
        "Braunschweig den": datetime.today().strftime("%d.%m.%Y"),
    })

    # Individual records
    for i, record in enumerate(records):
        writer.update_page_form_field_values(writer.pages[0], {
            f"DatumRow{i+1}": f"{record.day}.{bill.month}.{bill.year}",
            f"ArbeitszeitRow{i+1}": f"{bill.configuration.class_.time.start} - {bill.configuration.class_.time.end}",
            f"StdRow{i+1}": format_number(record.hours),
            f"{bill.configuration.template.fee_column_prefix}{i + 1}": format_number(record.fee),
            f"Teil nehmerRow{i + 1}": record.participant_count,
        })


def abrechnung(configuration_file: Path, year: int, month: int, participant_counts: list[int]):
    with open(configuration_file, "rb") as f:
        doc = tomllib.load(f)
        configuration = Configuration.model_validate(doc)

    bill = Bill(configuration=configuration, year=year, month=month, participant_counts=participant_counts)

    input_file = configuration_file.parent / configuration.template.file
    print(f"Reading {input_file}")
    reader = pdf.PdfReader(open(input_file, "rb"), strict=True)

    writer = pdf.PdfWriter()
    writer.add_page(reader.pages[0])
    fill_pdf_fields(writer, bill)

    output_file_name = f"Trainerabrechnung {configuration.trainer.name} {configuration.class_.name} {year}-{month:02d}.pdf"
    output_file = configuration_file.with_name(output_file_name)
    print(f"Writing {output_file}")
    with open(output_file, "wb") as f:
        writer.write(f)


def main(data_file: Path, month: str, participant_counts: list[int]):
    year, month = parse_month(month)
    abrechnung(data_file, year, month, participant_counts)


if __name__ == "__main__":
    typer.run(main)
