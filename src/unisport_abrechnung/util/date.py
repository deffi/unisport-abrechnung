import calendar
from collections.abc import Iterator
import re


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
