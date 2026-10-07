"""Unit tests for every function in rules.py."""

import json
import os
import tempfile
import unittest

from rules import breakages, completed_trips, load_days, parse_int, pence_to_pounds


class ParseIntTests(unittest.TestCase):
    def test_strips_spaces_and_accepts_inclusive_bounds(self):
        self.assertEqual(parse_int(" 7 ", 1, 14), 7)
        self.assertEqual(parse_int("1", 1, 14), 1)
        self.assertEqual(parse_int("14", 1, 14), 14)

    def test_accepts_a_leading_sign(self):
        self.assertEqual(parse_int("+3"), 3)
        self.assertEqual(parse_int("-4", -10, 0), -4)

    def test_rejects_non_text(self):
        with self.assertRaises(TypeError):
            parse_int(7)

    def test_rejects_blank_and_non_integers(self):
        for text in ("", "   ", "abc", "7.5", "1_000"):
            with self.assertRaises(ValueError):
                parse_int(text)

    def test_rejects_values_outside_the_inclusive_range(self):
        with self.assertRaises(ValueError):
            parse_int("0", 1, 14)
        with self.assertRaises(ValueError):
            parse_int("15", 1, 14)


class PenceToPoundsTests(unittest.TestCase):
    def test_formats_positive_small_and_negative_amounts(self):
        self.assertEqual(pence_to_pounds(12345), "£123.45")
        self.assertEqual(pence_to_pounds(5), "£0.05")
        self.assertEqual(pence_to_pounds(-250), "-£2.50")
        self.assertEqual(pence_to_pounds(0), "£0.00")

    def test_rejects_non_integers(self):
        with self.assertRaises(TypeError):
            pence_to_pounds(1.5)
        with self.assertRaises(TypeError):
            pence_to_pounds(True)


class LoadDaysTests(unittest.TestCase):
    def test_loads_supplied_trips_as_tuples(self):
        days = load_days(os.path.join("data", "trips.json"))
        self.assertEqual(len(days), 14)
        self.assertEqual(days[0], [("A", "B", 8), ("C", "B", 15), ("B", "C", 4)])

    def test_missing_file_propagates(self):
        with self.assertRaises(FileNotFoundError):
            load_days("data/missing.json")

    def test_rejects_bad_content(self):
        samples = [
            [],
            {},
            [[["A", "B"]]],
            [[["A", "B", 1, 2]]],
            [[[1, "B", 1]]],
            [[["A", "B", -1]]],
            [[["A", "B", 1.5]]],
            [[["A", "A", 1]]],
            ["not-a-day"],
        ]
        for sample in samples:
            with self.subTest(sample=sample):
                self._assert_rejected(sample)

    def test_allows_an_empty_day_and_a_zero_count(self):
        days = self._write_and_load([[], [["A", "B", 0]]])
        self.assertEqual(days, [[], [("A", "B", 0)]])

    def _assert_rejected(self, sample):
        with self.assertRaises(ValueError):
            self._write_and_load(sample)

    def _write_and_load(self, sample):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as handle:
            json.dump(sample, handle)
            path = handle.name
        try:
            return load_days(path)
        finally:
            os.remove(path)


class CompletedTripsTests(unittest.TestCase):
    def test_takes_the_smallest_of_the_three_limits(self):
        self.assertEqual(completed_trips(8, 15, 10), 8)
        self.assertEqual(completed_trips(15, 6, 3), 3)
        self.assertEqual(completed_trips(4, 14, 9), 4)
        self.assertEqual(completed_trips(0, 5, 5), 0)

    def test_rejects_non_integers(self):
        with self.assertRaises(TypeError):
            completed_trips(1.5, 1, 1)
        with self.assertRaises(TypeError):
            completed_trips(1, True, 1)

    def test_rejects_negative_values(self):
        with self.assertRaises(ValueError):
            completed_trips(-1, 1, 1)
        with self.assertRaises(ValueError):
            completed_trips(1, -1, 1)
        with self.assertRaises(ValueError):
            completed_trips(1, 1, -1)


class BreakagesTests(unittest.TestCase):
    def test_rounds_up_the_break_percentage(self):
        self.assertEqual(breakages(8, 10), 1)
        self.assertEqual(breakages(3, 10), 1)
        self.assertEqual(breakages(4, 10), 1)
        self.assertEqual(breakages(10, 10), 1)
        self.assertEqual(breakages(1, 1), 1)
        self.assertEqual(breakages(7, 100), 7)

    def test_zero_completed_or_zero_rate_breaks_nothing(self):
        self.assertEqual(breakages(0, 10), 0)
        self.assertEqual(breakages(5, 0), 0)

    def test_rejects_non_integers(self):
        with self.assertRaises(TypeError):
            breakages("8", 10)
        with self.assertRaises(TypeError):
            breakages(8, 10.0)

    def test_rejects_negative_values_and_rates_above_100(self):
        with self.assertRaises(ValueError):
            breakages(-1, 10)
        with self.assertRaises(ValueError):
            breakages(1, -1)
        with self.assertRaises(ValueError):
            breakages(1, 101)


if __name__ == "__main__":
    unittest.main()
