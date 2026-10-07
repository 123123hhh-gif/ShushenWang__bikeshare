"""Unit tests for every function in rules.py."""

import json
import os
import tempfile
import unittest

from rules import breakages, completed_trips, load_days, parse_int, pence_to_pounds

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRIPS_PATH = os.path.join(PROJECT, "data", "trips.json")


class ParseIntTests(unittest.TestCase):
    def test_surrounding_spaces_are_ignored(self):
        self.assertEqual(parse_int(" 7 ", 1, 14), 7)

    def test_range_is_inclusive_at_both_ends(self):
        self.assertEqual(parse_int("1", 1, 14), 1)
        self.assertEqual(parse_int("14", 1, 14), 14)

    def test_value_outside_range_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_int("15", 1, 14)

    def test_blank_and_non_whole_numbers_are_rejected(self):
        for text in ("", "   ", "abc", "7.5"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_int(text)

    def test_non_string_is_a_type_error(self):
        with self.assertRaises(TypeError):
            parse_int(7)


class PenceToPoundsTests(unittest.TestCase):
    def test_formats_pounds_and_pence(self):
        self.assertEqual(pence_to_pounds(12345), "£123.45")
        self.assertEqual(pence_to_pounds(5), "£0.05")
        self.assertEqual(pence_to_pounds(-250), "-£2.50")

    def test_non_int_is_a_type_error(self):
        for pence in (1.5, "100", True):
            with self.subTest(pence=pence):
                with self.assertRaises(TypeError):
                    pence_to_pounds(pence)


class CompletedTripsTests(unittest.TestCase):
    def test_takes_the_smallest_limit(self):
        # Worked example: min(8, 15, 10) = 8 and min(15, 6, 3) = 3.
        self.assertEqual(completed_trips(8, 15, 10), 8)
        self.assertEqual(completed_trips(15, 6, 3), 3)

    def test_negative_value_is_rejected(self):
        with self.assertRaises(ValueError):
            completed_trips(5, -1, 5)

    def test_non_int_is_a_type_error(self):
        with self.assertRaises(TypeError):
            completed_trips(5, 5.0, 5)


class BreakagesTests(unittest.TestCase):
    def test_partial_bike_rounds_up(self):
        # 7 trips at 10% is 0.7 bikes, which rounds up to 1.
        self.assertEqual(breakages(7, 10), 1)

    def test_whole_number_of_bikes_is_not_rounded_further(self):
        # 10 trips at 10% is exactly 1 bike; 11 trips is 1.1, so 2.
        self.assertEqual(breakages(10, 10), 1)
        self.assertEqual(breakages(11, 10), 2)

    def test_rate_above_100_is_rejected(self):
        with self.assertRaises(ValueError):
            breakages(5, 101)

    def test_non_int_is_a_type_error(self):
        with self.assertRaises(TypeError):
            breakages("5", 10)


class LoadDaysTests(unittest.TestCase):
    def test_supplied_file_becomes_days_of_tuples(self):
        days = load_days(TRIPS_PATH)
        self.assertEqual(len(days), 14)
        self.assertEqual(days[0], [("A", "B", 8), ("C", "B", 15), ("B", "C", 4)])
        self.assertIsInstance(days[0][0], tuple)

    def test_missing_file_raises_file_not_found(self):
        missing = os.path.join(PROJECT, "data", "no_such_file.json")
        with self.assertRaises(FileNotFoundError):
            load_days(missing)

    def test_wrong_content_is_rejected(self):
        samples = {
            "empty list": [],
            "not a list": {"A": 1},
            "two items": [[["A", "B"]]],
            "non-string station": [[[1, "B", 2]]],
            "negative count": [[["A", "B", -1]]],
            "non-integer count": [[["A", "B", 1.5]]],
            "same origin and destination": [[["A", "A", 2]]],
        }
        for label, content in samples.items():
            with self.subTest(label=label):
                path = self._write(content)
                with self.assertRaises(ValueError):
                    load_days(path)

    def _write(self, content):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        with handle:
            json.dump(content, handle)
        self.addCleanup(os.remove, handle.name)
        return handle.name


if __name__ == "__main__":
    unittest.main()
