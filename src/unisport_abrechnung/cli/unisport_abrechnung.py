from collections.abc import Iterator, Iterable
from pathlib import Path
import tomllib

import typer

from unisport_abrechnung.configuration import Configuration
from unisport_abrechnung.bill import Bill
from unisport_abrechnung.template import Template
from unisport_abrechnung.util.date import parse_month, days, WEEKDAYS
from unisport_abrechnung.util.file import find_free_file_name


def query_period() -> str:
    return input("Billing period (mm/yyyy): ")


def query_participant_counts(year: int, month: int, days: Iterable[int]) -> Iterator[int]:
    for day in days:
        yield int(input(f"Participant count for {day}.{month}.{year}: ") or "0")


def unisport_abrechnung(period:             str       = typer.Argument(""),
                        participant_counts: list[int] = typer.Argument(None)):

    configuration_file = Path("unisport-abrechnung.toml")
    with open(configuration_file, "rb") as f:
        doc = tomllib.load(f)
        configuration = Configuration.model_validate(doc)

    if not period:
        period = query_period()

    year, month = parse_month(period)

    if not participant_counts:
        participant_counts = list(query_participant_counts(year, month, days(year, month, WEEKDAYS[configuration.class_.weekday.lower()])))

    bill = Bill(configuration=configuration, year=year, month=month, participant_counts=participant_counts)

    base = configuration_file.parent
    input_file = base / configuration.template.file
    output_file = find_free_file_name(base / f"{bill.default_file_name_stem()}.pdf")

    print(f"Reading {input_file}")
    writer = Template(input_file).fill(bill)

    print(f"Writing {output_file}")
    assert not output_file.exists()
    with open(output_file, "wb") as f:
        writer.write(f)


def main():
    typer.run(unisport_abrechnung)
