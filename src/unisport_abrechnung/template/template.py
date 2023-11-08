from datetime import datetime
from pathlib import Path

from pypdf import PdfWriter

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
    @staticmethod
    def format_number(value: float) -> str:
        return str(value).replace(".", ",")

    @staticmethod
    def fee_field(hourly_fee: float, index: int) -> str:
        return f"{_fee_field_prefix[hourly_fee]}{index + 1}"

    def fill(self, writer: PdfWriter, bill: Bill):
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
            "summe": self.format_number(bill.total_hours()),
            _total_fee_field[bill.configuration.class_.hourly_fee]: self.format_number(bill.total_fee()),

            # Signature
            "Braunschweig den": datetime.today().strftime("%d.%m.%Y"),
        })

        # Individual records
        for i, record in enumerate(records):
            writer.update_page_form_field_values(writer.pages[0], {
                f"DatumRow{i + 1}": f"{record.day}.{bill.month}.{bill.year}",
                f"ArbeitszeitRow{i + 1}": f"{bill.configuration.class_.start_time} - {bill.configuration.class_.end_time}",
                f"StdRow{i + 1}": self.format_number(record.hours),
                f"{_fee_field_prefix[bill.configuration.class_.hourly_fee]}{i + 1}": self.format_number(record.fee),
                f"Teil nehmerRow{i + 1}": record.participant_count,
            })
