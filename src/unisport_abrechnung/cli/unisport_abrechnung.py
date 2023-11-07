from collections.abc import Iterator, Iterable
from datetime import datetime
from pathlib import Path
import tomllib

from pypdf import PdfReader, PdfWriter
import typer

from unisport_abrechnung.configuration import Configuration
from unisport_abrechnung.bill import Bill
from unisport_abrechnung.util.date import parse_month, days, WEEKDAYS
from unisport_abrechnung.util.file import find_free_file_name


def format_number(value: float) -> str:
    return str(value).replace(".", ",")


fee_field_prefix = {
    6.5: "650Row",
    12.0: "900Row",
    14.5: "1150Row",
    16.5: "1350Row",
    18.0: "1500Row",
}


total_fee_field = {
    6.5: "stunden1",
    12.0: "stunden2",
    14.5: "stunden3",
    16.5: "stunden4",
    18.0: "stunden5",
}


def fee_field(hourly_fee: float, index: int) -> str:
    return f"{fee_field_prefix[hourly_fee]}{index + 1}"


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
        total_fee_field[bill.configuration.class_.hourly_fee]: format_number(bill.total_fee()),

        # Signature
        "Braunschweig den": datetime.today().strftime("%d.%m.%Y"),
    })

    # Individual records
    for i, record in enumerate(records):
        writer.update_page_form_field_values(writer.pages[0], {
            f"DatumRow{i+1}": f"{record.day}.{bill.month}.{bill.year}",
            f"ArbeitszeitRow{i+1}": f"{bill.configuration.class_.start_time} - {bill.configuration.class_.end_time}",
            f"StdRow{i+1}": format_number(record.hours),
            f"{fee_field_prefix[bill.configuration.class_.hourly_fee]}{i + 1}": format_number(record.fee),
            f"Teil nehmerRow{i + 1}": record.participant_count,
        })


# Script #######################################################################

def abrechnung(configuration: Configuration, base: Path, year: int, month: int, participant_counts: list[int]):
    bill = Bill(configuration=configuration, year=year, month=month, participant_counts=participant_counts)

    input_file = base / configuration.template.file
    print(f"Reading {input_file}")
    reader = PdfReader(open(input_file, "rb"), strict=True)

    writer = PdfWriter()
    writer.add_page(reader.pages[0])
    fill_pdf_fields(writer, bill)

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


def main(month: str = typer.Argument(""),
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
