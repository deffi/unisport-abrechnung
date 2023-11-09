from datetime import datetime
from pathlib import Path

from pypdf import PdfWriter, PdfReader

from unisport_abrechnung.bill import Bill


_fee_field_prefix = {
    6.5: "650Row",
    12.0: "900Row",
    14.5: "1150Row",
    16.5: "1350Row",
    18.0: "1500Row",
}

_total_fee_field = {
    6.5: "stunden1",
    12.0: "stunden2",
    14.5: "stunden3",
    16.5: "stunden4",
    18.0: "stunden5",
}


class Template:
    def __init__(self, file: Path):
        self._file = file

    @staticmethod
    def format_number(value: float) -> str:
        return str(value).replace(".", ",")

    @staticmethod
    def fee_field(hourly_fee: float, index: int) -> str:
        return f"{_fee_field_prefix[hourly_fee]}{index + 1}"

    def _create_reader(self) -> PdfReader:
        return PdfReader(open(self._file, "rb"), strict=True)

    @staticmethod
    def _create_writer(reader: PdfReader) -> PdfWriter:
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
        return writer

    def fill(self, bill: Bill) -> PdfWriter:
        writer = self._create_writer(self._create_reader())

        # Shortcuts
        instructor = bill.configuration.instructor
        class_ = bill.configuration.class_

        records = list(bill.records())

        # Global fields
        writer.update_page_form_field_values(writer.pages[0], {
            # Instructor data
            "Monat": instructor.name,
            "1": instructor.address[0],
            "2": instructor.address[1],
            "3": instructor.iban,

            # Bill data
            "sportart": class_.name,  # Sportart
            "undefined": f"{bill.month}/{bill.year}",  # Monat

            # Totals
            "summe": self.format_number(bill.total_hours()),
            _total_fee_field[class_.hourly_fee]: self.format_number(bill.total_fee()),

            # Signature
            "Braunschweig den": datetime.today().strftime("%d.%m.%Y"),
        })

        # Individual records
        for i, record in enumerate(records):
            writer.update_page_form_field_values(writer.pages[0], {
                f"DatumRow{i + 1}": f"{record.day}.{bill.month}.{bill.year}",
                f"ArbeitszeitRow{i + 1}": f"{class_.start_time} - {class_.end_time}",
                f"StdRow{i + 1}": self.format_number(record.hours),
                f"{_fee_field_prefix[class_.hourly_fee]}{i + 1}": self.format_number(record.fee),
                f"Teil nehmerRow{i + 1}": record.participant_count,
            })

        return writer
