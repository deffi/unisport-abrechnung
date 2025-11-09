import calendar
from calendar import MONDAY

from unisport_abrechnung.util.date import days


class TestDate:
    def test_days(self):
        assert list(days(2023, 12, MONDAY)) == [4, 11, 18, 25]
