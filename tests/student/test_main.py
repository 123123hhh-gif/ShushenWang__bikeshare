"""Tests for the text interface in main.py."""

import os
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from main import parse_move, read_line

PROJECT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MAIN = os.path.join(PROJECT, "main.py")


def run_main(stdin, cwd=None):
    """Run main.py and capture its text output."""
    env = os.environ.copy()
    env["PYTHONPATH"] = PROJECT
    env["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, MAIN],
        input=stdin,
        text=True,
        encoding="utf-8",
        capture_output=True,
        cwd=cwd or PROJECT,
        env=env,
        check=False,
    )


class MainTests(unittest.TestCase):
    def test_importing_main_does_not_start_the_program(self):
        result = subprocess.run(
            [sys.executable, "-c", "import main; print('imported')"],
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=PROJECT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "imported")

    def test_worked_example_day(self):
        result = run_main("1\n1\nB A 3\n0\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        output = result.stdout
        self.assertIn("Day 1", output)
        self.assertIn("£100.00", output)
        self.assertIn("Temple Meads", output)
        self.assertIn("12 bikes, capacity 20, 8 free docks", output)
        self.assertIn("Workshop: 0", output)
        self.assertIn("A -> B: 8", output)
        self.assertIn("Trips completed: 15", output)
        self.assertIn("Trips lost: 12", output)
        self.assertIn("Bikes broken: 3", output)
        self.assertIn("Van cost: £5.00", output)
        self.assertIn("Repair cost: £0.00", output)
        self.assertIn("Daily cost: £24.00", output)
        self.assertIn("Cash at start: £100.00", output)
        self.assertIn("Cash at end: £101.00", output)
        self.assertIn("Total trips completed: 15", output)
        self.assertIn("Total trips lost: 12", output)
        self.assertIn("Final cash: £101.00", output)
        self.assertIn("The scheme did not go bankrupt.", output)

    def test_too_many_repairs_are_rejected_by_step(self):
        stdin = "\n".join([
            "1",
            "1",
            "B A 3",
            "-1",
            "abc",
            "10",
            "1",
            "B A 3",
            "0",
        ]) + "\n"
        result = run_main(stdin)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("Enter a whole number of 0 or more.", result.stdout)
        self.assertIn(
            "That decision is not possible: the workshop does not have that many bikes",
            result.stdout,
        )
        self.assertIn("Cash at end: £101.00", result.stdout)
        self.assertIn("The scheme did not go bankrupt.", result.stdout)

    def test_repairs_that_do_not_fit_at_the_depot_are_rejected_by_step(self):
        stdin = "\n".join([
            "2",
            "1",
            "B A 3",
            "0",
            "2",
            "B A 10",
            "C A 3",
            "1",
            "0",
            "0",
        ]) + "\n"
        result = run_main(stdin)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("Cash at end: £101.00", result.stdout)
        self.assertIn(
            "That decision is not possible: repaired bikes do not fit at the depot",
            result.stdout,
        )
        self.assertIn("Cash at end: £103.00", result.stdout)

    def test_invalid_typing_is_requested_again(self):
        stdin = "\n".join([
            "abc",
            "1",
            "no",
            "2",
            "Z A 3",
            "B A 3.5",
            "B A 8",
            "B A 1",
            "0",
            "0",
            "0",
        ]) + "\n"
        result = run_main(stdin)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("That decision is not possible", result.stdout)
        self.assertIn("Cash at end: £100.00", result.stdout)
        self.assertIn("The scheme did not go bankrupt.", result.stdout)

    def test_enter_selects_seven_days(self):
        result = run_main("\n" + "0\n0\n" * 7)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Day 7 summary", result.stdout)
        self.assertNotIn("Day 8", result.stdout)

    def test_missing_trips_file_stops_without_a_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_main("", cwd=directory)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("Traceback", result.stderr)
        self.assertIn("Could not load data/trips.json", result.stdout)

    def test_end_of_input_exits_cleanly(self):
        result = run_main("")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Input ended.", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_ctrl_c_exits_cleanly(self):
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            with self.assertRaises(SystemExit) as caught:
                read_line("prompt: ")
        self.assertEqual(caught.exception.code, 0)

    def test_parse_move_accepts_lowercase_and_rejects_bad_text(self):
        self.assertEqual(parse_move(" b a 5 ", {"A", "B", "C"}), ("B", "A", 5))
        with self.assertRaises(ValueError):
            parse_move("B B 5", {"A", "B", "C"})
        with self.assertRaises(ValueError):
            parse_move("", {"A", "B", "C"})


if __name__ == "__main__":
    unittest.main()
