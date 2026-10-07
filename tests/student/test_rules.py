"""Unit tests for the functions in rules.py.

Author: Shushen Wang

Covers parse_int, pence_to_pounds, completed_trips, breakages and load_days:
normal cases, boundaries and errors. Expected values are worked out by hand
from the rules, not copied from running the code.
"""

import json
import os
import tempfile
import unittest

from rules import (
    breakages,
    completed_trips,
    load_days,
    parse_int,
    pence_to_pounds,
)

TESTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT = os.path.dirname(TESTS_DIR)
TRIPS_PATH = os.path.join(PROJECT, "data", "trips.json")


class ParseIntTests(unittest.TestCase):
    """Tests for parse_int(text, minimum, maximum)."""

    def test_surrounding_spaces_are_ignored(self):
        """Spaces around the digits do not stop the conversion."""
        self.assertEqual(parse_int(" 7 ", 1, 14), 7)

    def test_range_is_inclusive(self):
        """Both bounds are allowed; one past either bound is rejected."""
        self.assertEqual(parse_int("1", 1, 14), 1)
        self.assertEqual(parse_int("14", 1, 14), 14)
        with self.assertRaises(ValueError):
            parse_int("0", 1, 14)
        with self.assertRaises(ValueError):
            parse_int("15", 1, 14)

    def test_blank_and_non_whole_numbers_are_rejected(self):
        """Blank text, letters and decimals raise ValueError."""
        for text in ("", "   ", "abc", "7.5"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_int(text)

    def test_non_string_is_a_type_error(self):
        """Passing an int instead of text raises TypeError."""
        with self.assertRaises(TypeError):
            parse_int(7)


class PenceToPoundsTests(unittest.TestCase):
    """Tests for pence_to_pounds(pence)."""

    def test_formats_pounds_and_pence(self):
        """Large, small and negative amounts use the £x.yy format."""
        self.assertEqual(pence_to_pounds(12345), "£123.45")
        self.assertEqual(pence_to_pounds(5), "£0.05")
        self.assertEqual(pence_to_pounds(-250), "-£2.50")

    def test_non_int_is_a_type_error(self):
        """Floats, strings and booleans are not accepted as pence."""
        for pence in (1.5, "100", True):
            with self.subTest(pence=pence):
                with self.assertRaises(TypeError):
                    pence_to_pounds(pence)


class CompletedTripsTests(unittest.TestCase):
    """Tests for completed_trips(requested, bikes, free_docks)."""

    def test_takes_the_smallest_limit(self):
        """Worked example: min(8, 15, 10) = 8 and min(15, 6, 3) = 3."""
        self.assertEqual(completed_trips(8, 15, 10), 8)
        self.assertEqual(completed_trips(15, 6, 3), 3)

    def test_invalid_arguments_are_rejected(self):
        """A negative value is a ValueError; a non-int is a TypeError."""
        with self.assertRaises(ValueError):
            completed_trips(5, -1, 5)
        with self.assertRaises(TypeError):
            completed_trips(5, 5.0, 5)


class BreakagesTests(unittest.TestCase):
    """Tests for breakages(completed, rate_percent)."""

    def test_only_partial_bikes_round_up(self):
        """0.7 bikes becomes 1, exactly 1.0 stays 1, and 1.1 becomes 2."""
        self.assertEqual(breakages(7, 10), 1)
        self.assertEqual(breakages(10, 10), 1)
        self.assertEqual(breakages(11, 10), 2)

    def test_invalid_arguments_are_rejected(self):
        """A rate above 100 is a ValueError; a non-int is a TypeError."""
        with self.assertRaises(ValueError):
            breakages(5, 101)
        with self.assertRaises(TypeError):
            breakages("5", 10)


class LoadDaysTests(unittest.TestCase):
    """Tests for load_days(path)."""

    def test_supplied_file_becomes_days_of_tuples(self):
        """The supplied file has 14 days; day 1 matches the worked example."""
        days = load_days(TRIPS_PATH)
        self.assertEqual(len(days), 14)
        self.assertEqual(
            days[0], [("A", "B", 8), ("C", "B", 15), ("B", "C", 4)]
        )
        self.assertIsInstance(days[0][0], tuple)

    def test_missing_file_raises_file_not_found(self):
        """A path that does not exist lets FileNotFoundError propagate."""
        missing = os.path.join(PROJECT, "data", "no_such_file.json")
        with self.assertRaises(FileNotFoundError):
            load_days(missing)

    def test_wrong_content_is_rejected(self):
        """Each kind of badly formatted content raises ValueError."""
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
        """Write content to a temporary JSON file and return its path."""
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        )
        with handle:
            json.dump(content, handle)
        self.addCleanup(os.remove, handle.name)
        return handle.name


if __name__ == "__main__":
    unittest.main()
