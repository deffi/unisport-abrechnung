import calendar
import tomllib
from pathlib import Path
import re
from datetime import datetime

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


def abrechnung(data_file: Path, year: int, month: int, participant_count: list[int]):
    with open(data_file, "rb") as f:
        data = tomllib.load(f)

    input_file = data_file.parent / data["template"]["file"]

    print(f"Reading {input_file}")
    reader = pdf.PdfReader(open(input_file, "rb"), strict=False)  # TODO strict?

    writer = pdf.PdfWriter()
    writer.add_page(reader.pages[0])

    writer.update_page_form_field_values(
        writer.pages[0], {"Monat": "Max Mustermann"}
    )

    trainer_name = data["trainer"]["name"]
    class_name = data["class"]["name"]

    writer.update_page_form_field_values(writer.pages[0], {
        "Monat": trainer_name,
        "1": data["trainer"]["address"][0],
        "2": data["trainer"]["address"][1],
        "3": data["trainer"]["iban"],
    })

    writer.update_page_form_field_values(writer.pages[0], {
        "sportart": class_name,  # Sportart
        "undefined": f"{month}/{year}",  # Monat
    })

    start_time = datetime.strptime(data['class']['time']['start'], "%H:%M")
    end_time = datetime.strptime(data['class']['time']['end'], "%H:%M")

    duration = end_time - start_time
    hourly_fee = data["trainer"]["hourly_fee"]

    weekday = data["class"]["weekday"]
    total_hours = 0
    total_fee = 0

    ds = days(year, month, WEEKDAYS[weekday.lower()])
    for i, (day, count) in enumerate((day, count) for day, count in zip(ds, participant_count) if count > 0):
        hours = duration.total_seconds() / 3600
        fee = hourly_fee * hours

        writer.update_page_form_field_values(writer.pages[0], {
            f"DatumRow{i+1}": f"{day}.{month}.{year}",
            f"ArbeitszeitRow{i+1}": f"{data['class']['time']['start']} - {data['class']['time']['end']}",
            f"StdRow{i+1}": format_number(duration.total_seconds() / 3600),
            f"{data['template']['fee_column_prefix']}{i + 1}": format_number(fee),
            f"Teil nehmerRow{i + 1}": count,
        })

        total_hours += hours
        total_fee += fee

    writer.update_page_form_field_values(writer.pages[0], {
        "summe": format_number(total_hours),
        data['template']['total_fee_column']: format_number(total_fee),
        "Braunschweig den": datetime.today().strftime("%d.%m.%Y"),
    })

    output_file_name = f"Trainerabrechnung {trainer_name} {class_name} {year}-{month:02d}.pdf"
    output_file = data_file.with_name(output_file_name)
    print(f"Writing {output_file}")
    with open(output_file, "wb") as f:
        writer.write(f)


def main(data_file: Path, month: str, participant_count: list[int]):
    year, month = parse_month(month)
    abrechnung(data_file, year, month, participant_count)


if __name__ == "__main__":
    typer.run(main)
