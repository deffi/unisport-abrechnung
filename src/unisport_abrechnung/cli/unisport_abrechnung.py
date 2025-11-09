from pathlib import Path

import typer

from unisport_abrechnung.bill import Bill
from unisport_abrechnung.configuration import Configuration
from unisport_abrechnung.template import Template
from unisport_abrechnung.util.date import parse_month
from unisport_abrechnung.util.file import find_free_file_name


def _unisport_abrechnung(base: Path, configuration: Configuration,
                         year: int, month: int, participant_counts: list[int]):
    # Create the bill data
    bill = Bill(configuration=configuration, year=year, month=month, participant_counts=participant_counts)

    # Determine file paths
    input_file = base / configuration.template.file
    output_file = find_free_file_name(base / f"{bill.default_file_name_stem()}.pdf")

    # Fill the template
    print(f"Reading template from {input_file}")
    writer = Template(input_file).fill(bill)

    # Write the output
    print(f"Writing output to {output_file}")
    assert not output_file.exists()
    with open(output_file, "wb") as f:
        writer.write(f)


def unisport_abrechnung(period:             str       = typer.Argument(""),
                        participant_counts: list[int] = typer.Argument([])):

    # Load the configuration
    configuration_file = Path("unisport-abrechnung.toml")
    print(f"Loading configuration from {configuration_file}")
    configuration = Configuration.load(configuration_file)

    # If the period is not specified, query the user
    if not period:
        period = input("Billing period (mm/yyyy): ")

    # Parse the period
    year, month = parse_month(period)

    # If the participant counts are not specified, query the user (we need the
    # period for this)
    if not participant_counts:
        for day in configuration.class_.days(year, month):
            participant_count = int(input(f"Participant count for {year}-{month}-{day}: ") or "0")  # TODO day with fixed width
            participant_counts.append(participant_count)

    # Run with cleaned up parameters
    _unisport_abrechnung(configuration_file.parent, configuration, year, month, participant_counts)


def main():
    typer.run(unisport_abrechnung)
