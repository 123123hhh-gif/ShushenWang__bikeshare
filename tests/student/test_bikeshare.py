"""Tests for Station, BikeShare.step(), and the C1-C3 copy requirements.

Expected values are worked out by hand from the rules: revenue 200 per trip,
van 500 per move, repair 200 per bike, fixed cost 2400 per day, and
broken = ceil(completed * 10 / 100) taken from the destination.
"""

import unittest

from bikeshare import DEFAULT_STATIONS, BikeShare
from station import Station


def no_action():
    return {"moves": [], "repairs": 0}


def worked_example_decision():
    return {"moves": [("B", "A", 3)], "repairs": 0}


def worked_example_trips():
    return [("A", "B", 8), ("C", "B", 15), ("B", "C", 4)]


def two_stations(a_capacity, a_bikes, b_capacity, b_bikes):
    return {
        "A": {"name": "Depot", "capacity": a_capacity, "bikes": a_bikes},
        "B": {"name": "Other", "capacity": b_capacity, "bikes": b_bikes},
    }


class StationTests(unittest.TestCase):
    def test_free_docks_follow_added_and_removed_bikes(self):
        station = Station("B", "Harbourside", 15, 8)
        station.remove_bikes(3)
        station.add_bikes(4)
        self.assertEqual(station.bikes, 9)
        self.assertEqual(station.free_docks(), 6)

    def test_invalid_constructor_values_are_rejected(self):
        cases = {
            "empty id": ("", "Temple Meads", 20, 12),
            "empty name": ("A", "", 20, 12),
            "zero capacity": ("A", "Temple Meads", 0, 0),
            "more bikes than docks": ("A", "Temple Meads", 20, 21),
            "bool bikes": ("A", "Temple Meads", 20, True),
        }
        for label, arguments in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    Station(*arguments)

    def test_cannot_remove_more_bikes_than_present(self):
        station = Station("C", "Clifton", 12, 6)
        with self.assertRaises(ValueError):
            station.remove_bikes(7)

    def test_cannot_add_bikes_to_a_full_station(self):
        station = Station("B", "Harbourside", 15, 15)
        with self.assertRaises(ValueError):
            station.add_bikes(1)


class ConstructorTests(unittest.TestCase):
    def test_invalid_arguments_are_rejected(self):
        cases = {
            "zero days": {"days": 0},
            "fifteen days": {"days": 15},
            "negative cash": {"cash": -1},
            "negative workshop": {"workshop": -1},
            "no depot": {"stations": {"B": {"name": "Harbourside", "capacity": 15, "bikes": 8}}},
        }
        for label, arguments in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    BikeShare(**arguments)


class StepTests(unittest.TestCase):
    def test_worked_example_day_one(self):
        sim = BikeShare()
        record = sim.step(worked_example_decision(), worked_example_trips())
        self.assertEqual(record["day"], 1)
        self.assertEqual(record["completed"], 15)
        self.assertEqual(record["lost"], 12)
        self.assertEqual(record["broken"], 3)
        self.assertEqual(record["revenue"], 3000)
        self.assertEqual(record["van_cost"], 500)
        self.assertEqual(record["repair_cost"], 0)
        self.assertEqual(record["fixed_cost"], 2400)
        self.assertEqual(record["opening_cash"], 10000)
        self.assertEqual(record["closing_cash"], 10100)
        self.assertEqual(record["bikes"], {"A": 7, "B": 10, "C": 6})
        self.assertEqual(record["workshop"], 3)
        self.assertFalse(record["bankrupt"])

    def test_van_moves_happen_before_trips(self):
        # Move B->A 3 gives A 3 bikes, so A->B 3 completes 3 (not 0).
        sim = BikeShare(stations=two_stations(10, 0, 10, 5))
        record = sim.step({"moves": [("B", "A", 3)], "repairs": 0}, [("A", "B", 3)])
        self.assertEqual(record["completed"], 3)

    def test_repaired_bikes_are_docked_at_depot_before_trips(self):
        # Repair 2 -> A has 2; A->B 2 completes 2; ceil(0.2) = 1 broken from B.
        sim = BikeShare(stations=two_stations(10, 0, 10, 0), workshop=2)
        record = sim.step({"moves": [], "repairs": 2}, [("A", "B", 2)])
        self.assertEqual(record["completed"], 2)
        self.assertEqual(record["repair_cost"], 400)
        self.assertEqual(record["bikes"], {"A": 0, "B": 1})
        self.assertEqual(record["workshop"], 1)

    def test_moves_can_chain_through_a_station(self):
        stations = two_stations(10, 0, 10, 6)
        stations["C"] = {"name": "Third", "capacity": 10, "bikes": 0}
        sim = BikeShare(stations=stations)
        record = sim.step({"moves": [("B", "A", 4), ("A", "C", 4)], "repairs": 0}, [])
        self.assertEqual(record["bikes"], {"A": 0, "B": 2, "C": 4})
        self.assertEqual(record["van_cost"], 1000)

    def test_full_van_of_ten_bikes_is_allowed(self):
        sim = BikeShare(stations=two_stations(20, 10, 10, 0))
        record = sim.step({"moves": [("A", "B", 10)], "repairs": 0}, [])
        self.assertEqual(record["bikes"], {"A": 0, "B": 10})

    def test_trips_to_a_full_station_are_all_lost(self):
        sim = BikeShare(stations=two_stations(5, 5, 5, 5))
        record = sim.step(no_action(), [("A", "B", 3)])
        self.assertEqual(record["completed"], 0)
        self.assertEqual(record["lost"], 3)
        self.assertEqual(record["broken"], 0)
        self.assertEqual(record["closing_cash"], 7600)


class BankruptcyAndFinishTests(unittest.TestCase):
    def test_exactly_zero_closing_cash_is_not_bankrupt(self):
        sim = BikeShare(cash=2400)
        record = sim.step(no_action(), [])
        self.assertEqual(record["closing_cash"], 0)
        self.assertFalse(record["bankrupt"])
        self.assertFalse(sim.is_finished())

    def test_closing_cash_below_zero_is_bankrupt_and_finished(self):
        sim = BikeShare(cash=2399)
        record = sim.step(no_action(), [])
        self.assertEqual(record["closing_cash"], -1)
        self.assertTrue(sim.is_bankrupt())
        self.assertTrue(sim.is_finished())

    def test_step_after_last_day_raises_runtime_error(self):
        sim = BikeShare(days=1)
        sim.step(no_action(), [])
        self.assertTrue(sim.is_finished())
        with self.assertRaises(RuntimeError):
            sim.step(no_action(), [])


class RejectedDecisionTests(unittest.TestCase):
    def test_invalid_decision_shapes_are_rejected(self):
        cases = {
            "not a dict": [("B", "A", 3)],
            "missing repairs": {"moves": []},
            "four moves": {"moves": [("A", "B", 1)] * 4, "repairs": 0},
            "two-item move": {"moves": [("A", "B")], "repairs": 0},
            "unknown station": {"moves": [("A", "Z", 1)], "repairs": 0},
            "same origin and destination": {"moves": [("A", "A", 1)], "repairs": 0},
            "zero bikes": {"moves": [("A", "B", 0)], "repairs": 0},
            "negative repairs": {"moves": [], "repairs": -1},
        }
        for label, decision in cases.items():
            with self.subTest(label=label):
                sim = BikeShare()
                with self.assertRaises(ValueError):
                    sim.step(decision, [])

    def test_eleven_bikes_is_more_than_the_van_holds(self):
        sim = BikeShare(stations=two_stations(20, 12, 15, 0))
        with self.assertRaises(ValueError):
            sim.step({"moves": [("A", "B", 11)], "repairs": 0}, [])

    def test_move_needs_enough_bikes_at_origin(self):
        # C has 6 bikes, B has 7 free docks, so only the origin is short.
        sim = BikeShare()
        with self.assertRaises(ValueError):
            sim.step({"moves": [("C", "B", 7)], "repairs": 0}, [])

    def test_cannot_repair_more_than_the_workshop_holds(self):
        sim = BikeShare(workshop=1)
        with self.assertRaises(ValueError):
            sim.step({"moves": [], "repairs": 2}, [])

    def test_repairs_must_fit_at_depot_after_moves(self):
        # A has 2 free docks, but moving 2 bikes in fills it before repairs.
        sim = BikeShare(stations=two_stations(10, 8, 10, 5), workshop=2)
        with self.assertRaises(ValueError):
            sim.step({"moves": [("B", "A", 2)], "repairs": 1}, [])

    def test_invalid_trips_are_rejected(self):
        cases = {
            "negative count": [("A", "B", -1)],
            "unknown station": [("A", "Z", 1)],
            "two items": [("A", "B")],
        }
        for label, trips in cases.items():
            with self.subTest(label=label):
                sim = BikeShare()
                with self.assertRaises(ValueError):
                    sim.step(no_action(), trips)


class CopyTests(unittest.TestCase):
    def test_c1_default_stations_and_simulations_stay_independent(self):
        first = BikeShare()
        second = BikeShare()
        first.step(worked_example_decision(), worked_example_trips())
        self.assertEqual(second.get_bikes(), {"A": 12, "B": 8, "C": 6})
        self.assertEqual(second.get_cash(), 10000)
        self.assertEqual(
            DEFAULT_STATIONS,
            {
                "A": {"name": "Temple Meads", "capacity": 20, "bikes": 12},
                "B": {"name": "Harbourside", "capacity": 15, "bikes": 8},
                "C": {"name": "Clifton", "capacity": 12, "bikes": 6},
            },
        )

    def test_c2_changing_returned_data_does_not_change_simulation(self):
        sim = BikeShare()
        record = sim.step(worked_example_decision(), worked_example_trips())
        record["bikes"]["A"] = 0
        sim.get_bikes()["B"] = 0
        sim.get_history()[0]["closing_cash"] = 0
        self.assertEqual(sim.get_bikes(), {"A": 7, "B": 10, "C": 6})
        self.assertEqual(sim.get_history()[0]["bikes"], {"A": 7, "B": 10, "C": 6})
        self.assertEqual(sim.get_history()[0]["closing_cash"], 10100)

    def test_c2_stored_record_is_unchanged_by_later_days(self):
        sim = BikeShare()
        sim.step(worked_example_decision(), worked_example_trips())
        sim.step({"moves": [("B", "A", 3)], "repairs": 3}, [])
        self.assertEqual(sim.get_history()[0]["bikes"], {"A": 7, "B": 10, "C": 6})
        self.assertEqual(sim.get_history()[0]["workshop"], 3)

    def test_c3_later_failed_move_changes_nothing(self):
        # B->A 3 is valid, then C->B 7 fails because C has only 6 bikes.
        sim = BikeShare()
        with self.assertRaises(ValueError):
            sim.step({"moves": [("B", "A", 3), ("C", "B", 7)], "repairs": 0}, [])
        self.assertEqual(sim.get_bikes(), {"A": 12, "B": 8, "C": 6})
        self.assertEqual(sim.get_cash(), 10000)
        self.assertEqual(sim.get_day(), 1)
        self.assertEqual(sim.get_workshop(), 0)
        self.assertEqual(sim.get_history(), [])


if __name__ == "__main__":
    unittest.main()
