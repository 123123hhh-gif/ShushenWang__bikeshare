"""Supplied public tests. Do not change this file.

These check that your files and names match the specification. They do not
check all the required behaviour: write your own tests in tests/student/.
"""
import unittest

from bikeshare import BikeShare
from rules import parse_int, pence_to_pounds
from station import Station


class PublicTests(unittest.TestCase):
    def test_parse_int_converts_text(self):
        self.assertEqual(parse_int(" 7 ", 1, 14), 7)

    def test_pence_to_pounds_formats_money(self):
        self.assertEqual(pence_to_pounds(12345), "£123.45")

    def test_station_reports_free_docks(self):
        self.assertEqual(Station("A", "Temple Meads", 20, 12).free_docks(), 8)

    def test_new_simulation_starts_on_day_one(self):
        sim = BikeShare()
        self.assertEqual(sim.get_day(), 1)
        self.assertEqual(sim.get_cash(), 10000)
        self.assertEqual(sim.get_bikes(), {"A": 12, "B": 8, "C": 6})

    def test_worked_example_closing_cash(self):
        sim = BikeShare()
        record = sim.step({"moves": [("B", "A", 3)], "repairs": 0},
                          [("A", "B", 8), ("C", "B", 15), ("B", "C", 4)])
        self.assertEqual(record["closing_cash"], 10100)
