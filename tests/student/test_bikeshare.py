"""Tests for Station, BikeShare.step(), and the C1–C3 copy requirements."""

import unittest
from unittest.mock import patch

from bikeshare import DEFAULT_STATIONS, BikeShare
from rules import DAILY_COST, FARE, MAX_DAYS, REPAIR_COST, VAN_COST
from station import Station


DAY_ONE = {
    "moves": [("B", "A", 3)],
    "repairs": 0,
}
DAY_ONE_TRIPS = [("A", "B", 8), ("C", "B", 15), ("B", "C", 4)]
START_BIKES = {"A": 12, "B": 8, "C": 6}


class StationTests(unittest.TestCase):
    def test_free_docks_are_capacity_minus_bikes(self):
        self.assertEqual(Station("A", "Temple Meads", 20, 12).free_docks(), 8)
        self.assertEqual(Station("C", "Clifton", 12, 0).free_docks(), 12)
        self.assertEqual(Station("B", "Harbourside", 15, 15).free_docks(), 0)

    def test_dock_and_undock_change_the_bike_count(self):
        station = Station("B", "Harbourside", 15, 8)
        station.undock(3)
        self.assertEqual(station.bikes, 5)
        self.assertEqual(station.free_docks(), 10)
        station.dock(4)
        self.assertEqual(station.bikes, 9)
        station.undock(0)
        station.dock(0)
        self.assertEqual(station.bikes, 9)

    def test_rejects_more_bikes_than_docks(self):
        with self.assertRaises(ValueError):
            Station("A", "Temple Meads", 20, 21)
        with self.assertRaises(ValueError):
            Station("A", "Temple Meads", 20, -1)

    def test_rejects_bad_types_and_overfull_or_empty_moves(self):
        with self.assertRaises(TypeError):
            Station(1, "Temple Meads", 20, 12)
        with self.assertRaises(TypeError):
            Station("A", "Temple Meads", 20.0, 12)
        station = Station("A", "Temple Meads", 20, 12)
        with self.assertRaises(ValueError):
            station.undock(13)
        with self.assertRaises(ValueError):
            station.dock(9)
        with self.assertRaises(TypeError):
            station.dock(True)


class OrderOfOperationsTests(unittest.TestCase):
    def test_moves_happen_before_repairs_and_trips(self):
        sim = BikeShare()
        record = sim.step(DAY_ONE, DAY_ONE_TRIPS)
        self.assertEqual(record["moves"], [("B", "A", 3)])
        self.assertEqual(record["trips"][0]["completed"], 8)
        self.assertEqual(record["trips"][1]["completed"], 3)
        self.assertEqual(record["trips"][1]["lost"], 12)
        self.assertEqual(record["trips"][2]["completed"], 4)
        self.assertEqual(record["bikes"], {"A": 7, "B": 10, "C": 6})
        self.assertEqual(record["workshop"], 3)

    def test_repairs_use_space_left_after_moves_and_before_trips(self):
        sim = BikeShare()
        sim.step(DAY_ONE, DAY_ONE_TRIPS)
        before = sim.get_bikes()
        self.assertEqual(before["A"], 7)
        record = sim.step(
            {"moves": [], "repairs": 2},
            [("A", "B", 10), ("A", "C", 4), ("C", "B", 6), ("B", "A", 5)],
        )
        self.assertEqual(record["repairs"], 2)
        self.assertEqual(record["bikes"], {"A": 4, "B": 9, "C": 8})
        self.assertEqual(record["workshop"], 5)
        self.assertEqual(sum(record["bikes"].values()) + record["workshop"], 26)

    def test_chained_moves_are_applied_in_order(self):
        sim = BikeShare()
        record = sim.step(
            {"moves": [("B", "A", 5), ("A", "C", 4)], "repairs": 0},
            [],
        )
        self.assertEqual(record["bikes"], {"A": 13, "B": 3, "C": 10})
        self.assertEqual(record["van_cost"], 2 * VAN_COST)


class MoneyTests(unittest.TestCase):
    def test_itemised_costs_match_the_worked_example(self):
        sim = BikeShare()
        record = sim.step(DAY_ONE, DAY_ONE_TRIPS)
        self.assertEqual(record["revenue"], 15 * FARE)
        self.assertEqual(record["van_cost"], 1 * VAN_COST)
        self.assertEqual(record["repair_cost"], 0)
        self.assertEqual(record["daily_cost"], DAILY_COST)
        self.assertEqual(record["opening_cash"], 10000)
        self.assertEqual(
            record["closing_cash"],
            10000 + 15 * FARE - VAN_COST - DAILY_COST,
        )
        self.assertEqual(sim.get_cash(), 10100)

    def test_repair_and_van_costs_are_subtracted(self):
        sim = BikeShare()
        sim.step(DAY_ONE, DAY_ONE_TRIPS)
        record = sim.step({"moves": [("C", "B", 1)], "repairs": 2}, [])
        self.assertEqual(record["revenue"], 0)
        self.assertEqual(record["van_cost"], VAN_COST)
        self.assertEqual(record["repair_cost"], 2 * REPAIR_COST)
        self.assertEqual(
            record["closing_cash"],
            10100 - VAN_COST - 2 * REPAIR_COST - DAILY_COST,
        )
        self.assertEqual(record["bikes"], {"A": 9, "B": 11, "C": 5})
        self.assertEqual(record["workshop"], 1)


class BankruptcyAndFinishTests(unittest.TestCase):
    def test_exactly_zero_cash_is_not_bankrupt(self):
        sim = BikeShare()
        for _ in range(4):
            sim.step({"moves": [], "repairs": 0}, [])
        self.assertEqual(sim.get_cash(), 400)
        record = sim.step({"moves": [], "repairs": 0}, [("A", "B", 7), ("C", "A", 3)])
        self.assertEqual(record["closing_cash"], 0)
        self.assertFalse(record["bankrupt"])
        self.assertFalse(sim.is_bankrupt())

    def test_negative_closing_cash_ends_the_scheme(self):
        sim = BikeShare()
        for _ in range(4):
            sim.step({"moves": [], "repairs": 0}, [])
        sim.step({"moves": [], "repairs": 0}, [("A", "B", 7), ("C", "A", 3)])
        bankrupt = sim.step({"moves": [], "repairs": 0}, [])
        self.assertEqual(bankrupt["closing_cash"], -2400)
        self.assertTrue(bankrupt["bankrupt"])
        self.assertTrue(sim.is_bankrupt())
        bikes = sim.get_bikes()
        with self.assertRaises(ValueError):
            sim.step({"moves": [], "repairs": 0}, [])
        self.assertEqual(sim.get_cash(), -2400)
        self.assertEqual(sim.get_bikes(), bikes)
        self.assertEqual(len(sim.get_history()), 6)

    def test_simulation_stops_after_the_maximum_number_of_days(self):
        # Extra starting cash keeps empty days solvent until MAX_DAYS is reached.
        with patch("bikeshare.STARTING_CASH", 100000):
            sim = BikeShare()
        for day in range(MAX_DAYS):
            record = sim.step({"moves": [], "repairs": 0}, [])
            self.assertEqual(record["day"], day + 1)
            self.assertFalse(sim.is_bankrupt())
        self.assertEqual(sim.get_day(), MAX_DAYS + 1)
        self.assertEqual(len(sim.get_history()), MAX_DAYS)
        with self.assertRaises(ValueError):
            sim.step({"moves": [], "repairs": 0}, [])
        self.assertEqual(len(sim.get_history()), MAX_DAYS)


class CopyTests(unittest.TestCase):
    def test_c1_default_stations_and_simulations_stay_independent(self):
        original_bikes = {
            station_id: station.bikes for station_id, station in DEFAULT_STATIONS.items()
        }
        original_ids = {
            station_id: id(station) for station_id, station in DEFAULT_STATIONS.items()
        }
        first = BikeShare()
        second = BikeShare()
        first.step(DAY_ONE, DAY_ONE_TRIPS)
        self.assertEqual(second.get_bikes(), START_BIKES)
        self.assertEqual(second.get_cash(), 10000)
        self.assertEqual(second.get_day(), 1)
        self.assertEqual(
            {station_id: station.bikes for station_id, station in DEFAULT_STATIONS.items()},
            original_bikes,
        )
        self.assertEqual(
            {station_id: id(station) for station_id, station in DEFAULT_STATIONS.items()},
            original_ids,
        )
        self.assertIsNot(first.stations["A"], second.stations["A"])
        self.assertIsNot(first.stations["A"], DEFAULT_STATIONS["A"])

    def test_c2_returned_records_and_bike_counts_are_copies(self):
        sim = BikeShare()
        record = sim.step(DAY_ONE, DAY_ONE_TRIPS)
        record["closing_cash"] = 0
        record["bikes"]["A"] = 0
        record["moves"].append(("A", "B", 1))
        record["trips"].clear()
        bikes = sim.get_bikes()
        bikes["A"] = 0
        history = sim.get_history()
        history.clear()
        self.assertEqual(sim.get_bikes(), {"A": 7, "B": 10, "C": 6})
        self.assertEqual(len(sim.get_history()), 1)
        stored = sim.get_history()[0]
        self.assertEqual(stored["closing_cash"], 10100)
        self.assertEqual(stored["bikes"]["A"], 7)
        self.assertEqual(stored["moves"], [("B", "A", 3)])
        self.assertEqual(len(stored["trips"]), 3)
        sim.step({"moves": [], "repairs": 0}, [])
        self.assertEqual(sim.get_history()[0]["bikes"], {"A": 7, "B": 10, "C": 6})
        self.assertEqual(sim.get_history()[0]["closing_cash"], 10100)

    def test_c3_a_later_failed_move_rolls_back_the_whole_day(self):
        sim = BikeShare()
        with self.assertRaises(ValueError):
            sim.step(
                {"moves": [("B", "A", 3), ("B", "A", 8)], "repairs": 0},
                DAY_ONE_TRIPS,
            )
        self.assertEqual(sim.get_day(), 1)
        self.assertEqual(sim.get_cash(), 10000)
        self.assertEqual(sim.get_bikes(), START_BIKES)
        self.assertEqual(sim.get_workshop(), 0)
        self.assertEqual(sim.get_history(), [])

    def test_c3_failed_repairs_after_valid_moves_change_nothing(self):
        sim = BikeShare()
        sim.step(DAY_ONE, DAY_ONE_TRIPS)
        before = (
            sim.get_day(),
            sim.get_cash(),
            sim.get_bikes(),
            sim.get_workshop(),
            sim.get_history(),
        )
        with self.assertRaises(ValueError):
            sim.step({"moves": [("B", "A", 10), ("C", "A", 3)], "repairs": 1}, [])
        self.assertEqual(
            (
                sim.get_day(),
                sim.get_cash(),
                sim.get_bikes(),
                sim.get_workshop(),
                sim.get_history(),
            ),
            before,
        )

    def test_invalid_trips_are_rejected_before_any_move(self):
        sim = BikeShare()
        with self.assertRaises(ValueError):
            sim.step(DAY_ONE, [("A", "A", 1)])
        self.assertEqual(sim.get_bikes(), START_BIKES)
        self.assertEqual(sim.get_history(), [])


if __name__ == "__main__":
    unittest.main()
