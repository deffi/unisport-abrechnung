from collections.abc import Iterator, Iterable
from pathlib import Path
import tomllib

from pypdf import PdfReader, PdfWriter
import typer

from unisport_abrechnung.configuration import Configuration
from unisport_abrechnung.bill import Bill
from unisport_abrechnung.template import Template
from unisport_abrechnung.util.date import parse_month, days, WEEKDAYS
from unisport_abrechnung.util.file import find_free_file_name


def abrechnung(configuration: Configuration, base: Path, year: int, month: int, participant_counts: list[int]):
    bill = Bill(configuration=configuration, year=year, month=month, participant_counts=participant_counts)

    input_file = base / configuration.template.file
    print(f"Reading {input_file}")
    reader = PdfReader(open(input_file, "rb"), strict=True)

    writer = PdfWriter()
    writer.add_page(reader.pages[0])

    Template().fill(writer, bill)

    output_file_name = \
        f"Trainerabrechnung {configuration.instructor.name} {configuration.class_.name} {year}-{month:02d}.pdf"
    output_file = find_free_file_name(base / output_file_name)
    assert not output_file.exists()

    print(f"Writing {output_file}")
    with open(output_file, "wb") as f:
        writer.write(f)


def query_month() -> str:
    return input("Billing period (mm/yyyy): ")


def query_participant_counts(year: int, month: int, days: Iterable[int]) -> Iterator[int]:
    for day in days:
        yield int(input(f"Participant count for {day}.{month}.{year}: ") or "0")


def unisport_abrechnung(month: str = typer.Argument(""),
         participant_counts: list[int] = typer.Argument(None)):

    configuration_file = Path("unisport-abrechnung.toml")
    with open(configuration_file, "rb") as f:
        doc = tomllib.load(f)
        configuration = Configuration.model_validate(doc)

    if not month:
        month = query_month()

    year, month = parse_month(month)

    if not participant_counts:
        participant_counts = list(query_participant_counts(year, month, days(year, month, WEEKDAYS[configuration.class_.weekday.lower()])))

    abrechnung(configuration, configuration_file.parent, year, month, participant_counts)


def main():
    typer.run(unisport_abrechnung)
