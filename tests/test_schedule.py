"""Tester för schemalogiken. Kör: python -m unittest discover tests"""

from datetime import date
import importlib.util
from pathlib import Path
import sys
import types
import unittest

# Ladda const.py och schedule.py utan att importera Home Assistant.
PKG_DIR = Path(__file__).resolve().parent.parent / "custom_components" / "trelleborg_avfall"
pkg = types.ModuleType("trelleborg_avfall")
pkg.__path__ = [str(PKG_DIR)]
sys.modules["trelleborg_avfall"] = pkg
for name in ("const", "schedule"):
    spec = importlib.util.spec_from_file_location(f"trelleborg_avfall.{name}", PKG_DIR / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"trelleborg_avfall.{name}"] = module
    spec.loader.exec_module(module)

from trelleborg_avfall.schedule import BinSchedule, in_season, parse_date_list  # noqa: E402


class ScheduleTest(unittest.TestCase):
    def test_biweekly(self):
        s = BinSchedule(reference_date=date(2026, 1, 7), interval_weeks=2)
        self.assertEqual(s.next_collection(date(2026, 10, 29)), date(2026, 11, 11))
        self.assertEqual(s.next_collection(date(2026, 11, 11)), date(2026, 11, 11))
        self.assertEqual(
            s.upcoming(date(2026, 11, 12), 3),
            [date(2026, 11, 25), date(2026, 12, 9), date(2026, 12, 23)],
        )

    def test_reference_in_future(self):
        s = BinSchedule(reference_date=date(2027, 3, 3), interval_weeks=4)
        self.assertEqual(s.next_collection(date(2026, 10, 28)), date(2026, 11, 11))

    def test_season(self):
        s = BinSchedule(
            reference_date=date(2026, 3, 18), interval_weeks=2, season_start=12, season_end=47
        )
        # Sista tömning 11 nov (v.46), 25 nov är v.48 och utanför säsong.
        self.assertEqual(s.next_collection(date(2026, 11, 5)), date(2026, 11, 11))
        # Rytmen behålls över vintern: 17 mars är v.11, så första blir 31 mars (v.13).
        self.assertEqual(s.next_collection(date(2026, 11, 12)), date(2027, 3, 31))

    def test_trelleborg_hamtschema_2026(self):
        """Verkligt hämtschema för Östergatan 42, Anderslöv (utskrivet 2026-10-28)."""
        expected = {
            # Fyrfack 1, var 14:e dag
            (2, None, None): [
                date(2026, 11, 4), date(2026, 11, 18), date(2026, 12, 2),
                date(2026, 12, 16), date(2026, 12, 30),
            ],
            # Fyrfack 2, var 4:e vecka
            (4, None, None): [date(2026, 11, 19), date(2026, 12, 17)],
            # Trädgårdsavfall, var 14:e dag säsong v.12-47
            (2, 12, 47): [date(2026, 11, 9)],
        }
        for (interval, s_start, s_end), dates in expected.items():
            # Oavsett vilket av datumen användaren anger ska hela schemat stämma.
            for ref in dates:
                s = BinSchedule(
                    reference_date=ref, interval_weeks=interval,
                    season_start=s_start, season_end=s_end,
                )
                with self.subTest(interval=interval, ref=ref):
                    self.assertEqual(
                        s.occurrences(date(2026, 10, 28), date(2026, 12, 31)), dates
                    )
                    self.assertEqual(s.next_collection(date(2026, 10, 28)), dates[0])

    def test_season_wraps_year(self):
        self.assertTrue(in_season(date(2026, 1, 5), 45, 10))
        self.assertTrue(in_season(date(2026, 11, 20), 45, 10))
        self.assertFalse(in_season(date(2026, 6, 1), 45, 10))

    def test_exclude_and_extra(self):
        s = BinSchedule(
            reference_date=date(2026, 12, 23),
            interval_weeks=2,
            exclude_dates=parse_date_list("2027-01-06"),
            extra_dates=parse_date_list("2027-01-07, 2027-01-08"),
        )
        self.assertEqual(
            s.occurrences(date(2027, 1, 1), date(2027, 1, 31)),
            [date(2027, 1, 7), date(2027, 1, 8), date(2027, 1, 20)],
        )


if __name__ == "__main__":
    unittest.main()
