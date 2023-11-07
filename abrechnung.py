#!/usr/bin/env python3

import calendar
from collections.abc import Iterator
from datetime import datetime
from itertools import count
from pathlib import Path
import re
import tomllib

from pydantic import BaseModel, conlist, Field
from pypdf import PdfReader, PdfWriter
import typer


# Utilities ####################################################################

WEEKDAYS = {
    "mon": calendar.MONDAY,
    "tue": calendar.TUESDAY,
    "wed": calendar.WEDNESDAY,
    "thu": calendar.THURSDAY,
    "fri": calendar.FRIDAY,
    "sat": calendar.SATURDAY,
    "sun": calendar.SUNDAY,
}


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


def find_free_file_name(file: Path):
    def candidates() -> Iterator[Path]:
        yield file
        for i in count(1):
            yield file.with_stem(file.stem + f"_{i}")

    for candidate in candidates():
        if not candidate.exists():
            return candidate


# Configuration ################################################################

class Instructor(BaseModel):
    name: str
    address: conlist(str, min_length = 1, max_length = 2)
    iban: str


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


class Template(BaseModel):
    file: str
    fee_column_prefix: str
    total_fee_column: str


class Configuration(BaseModel):
    instructor: Instructor
    class_: Class = Field(alias = "class")
    template: Template


# Bill #########################################################################

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
                hours = self.configuration.class_.hours()
                fee = hours * self.configuration.class_.hourly_fee

                yield Record(day=day, hours=hours, fee=fee, participant_count=count)

    def total_hours(self) -> float:
        return sum(r.hours for r in self.records())

    def total_fee(self) -> float:
        return sum(r.fee for r in self.records())


# PDF ##########################################################################

def fill_pdf_fields(writer: PdfWriter, bill: Bill):
    records = list(bill.records())

    # Global fields
    writer.update_page_form_field_values(writer.pages[0], {
        # Instructor data
        "Monat": bill.configuration.instructor.name,
        "1": bill.configuration.instructor.address[0],
        "2": bill.configuration.instructor.address[1],
        "3": bill.configuration.instructor.iban,

        # Bill data
        "sportart": bill.configuration.class_.name,  # Sportart
        "undefined": f"{bill.month}/{bill.year}",  # Monat

        # Totals
        "summe": format_number(bill.total_hours()),
        bill.configuration.template.total_fee_column: format_number(bill.total_fee()),

        # Signature
        "Braunschweig den": datetime.today().strftime("%d.%m.%Y"),
    })

    # Individual records
    for i, record in enumerate(records):
        writer.update_page_form_field_values(writer.pages[0], {
            f"DatumRow{i+1}": f"{record.day}.{bill.month}.{bill.year}",
            f"ArbeitszeitRow{i+1}": f"{bill.configuration.class_.start_time} - {bill.configuration.class_.end_time}",
            f"StdRow{i+1}": format_number(record.hours),
            f"{bill.configuration.template.fee_column_prefix}{i + 1}": format_number(record.fee),
            f"Teil nehmerRow{i + 1}": record.participant_count,
        })


# Script #######################################################################

def abrechnung(configuration_file: Path, year: int, month: int, participant_counts: list[int]):
    with open(configuration_file, "rb") as f:
        doc = tomllib.load(f)
        configuration = Configuration.model_validate(doc)

    bill = Bill(configuration=configuration, year=year, month=month, participant_counts=participant_counts)

    input_file = configuration_file.parent / configuration.template.file
    print(f"Reading {input_file}")
    reader = PdfReader(open(input_file, "rb"), strict=True)

    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    fill_pdf_fields(writer, bill)

    output_file_name = \
        f"Trainerabrechnung {configuration.instructor.name} {configuration.class_.name} {year}-{month:02d}.pdf"
    output_file = find_free_file_name(configuration_file.with_name(output_file_name))
    assert not output_file.exists()

    print(f"Writing {output_file}")
    with open(output_file, "wb") as f:
        writer.write(f)


def main(month: str, participant_counts: list[int]):
    """
    Supports the 2023-10-24 template. May have to be changed if the template is
    updated by Sportzentrum.
    """
    year, month = parse_month(month)
    abrechnung(Path("unisport-abrechnung.toml"), year, month, participant_counts)


if __name__ == "__main__":
    typer.run(main)
