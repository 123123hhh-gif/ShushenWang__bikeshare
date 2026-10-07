"""Day-by-day simulation of the bike-share scheme."""

import copy

from rules import (
    BREAK_RATE,
    DAILY_COST,
    DEPOT,
    FARE,
    MAX_DAYS,
    MAX_MOVES,
    REPAIR_COST,
    VAN_CAPACITY,
    VAN_COST,
    breakages,
    completed_trips,
)
from station import Station

STARTING_CASH = 10000

DEFAULT_STATIONS = {
    "A": Station("A", "Temple Meads", 20, 12),
    "B": Station("B", "Harbourside", 15, 8),
    "C": Station("C", "Clifton", 12, 6),
}


class BikeShare:
    """The stations, workshop, cash and day-by-day history of one scheme."""

    def __init__(self, stations=None):
        # deepcopy, not copy.copy: a shallow copy would share the Station objects
        # stored in DEFAULT_STATIONS, so one simulation would change the other.
        source = DEFAULT_STATIONS if stations is None else stations
        self.stations = copy.deepcopy(source)
        self._check_stations(self.stations)
        self.workshop = 0
        self._cash = STARTING_CASH
        self._day = 1
        self._history = []
        self._bankrupt = False

    def get_day(self):
        """Return the day about to be simulated, starting at 1."""
        return self._day

    def get_cash(self):
        """Return the current cash in pence."""
        return self._cash

    def get_bikes(self):
        """Return a copy of the bikes docked at each station."""
        return {station_id: station.bikes for station_id, station in self.stations.items()}

    def get_workshop(self):
        """Return how many broken bikes are in the workshop."""
        return self.workshop

    def is_bankrupt(self):
        """Return whether closing cash has already fallen below zero."""
        return self._bankrupt

    def get_history(self):
        """Return a copy of the stored day records."""
        return copy.deepcopy(self._history)

    def step(self, decision, trips):
        """Run one day. Return a copy of that day's record.

        An invalid decision or trip list raises ValueError and leaves the
        simulation unchanged. The record is stored before the copy is returned.
        """
        if self._bankrupt:
            raise ValueError("the scheme is bankrupt")
        if self._day > MAX_DAYS:
            raise ValueError("the simulation has reached its last day")
        moves, repairs = self._parse_decision(decision)
        parsed_trips = self._parse_trips(trips)

        draft = copy.deepcopy(self.stations)
        workshop = self.workshop
        self._apply_moves(draft, moves)
        workshop = self._apply_repairs(draft, workshop, repairs)
        routes, workshop, completed, lost, broken = self._apply_trips(draft, workshop, parsed_trips)

        revenue = completed * FARE
        van_cost = len(moves) * VAN_COST
        repair_cost = repairs * REPAIR_COST
        closing = self._cash + revenue - van_cost - repair_cost - DAILY_COST
        record = {
            "day": self._day,
            "moves": [tuple(move) for move in moves],
            "repairs": repairs,
            "trips": routes,
            "completed": completed,
            "lost": lost,
            "broken": broken,
            "revenue": revenue,
            "van_cost": van_cost,
            "repair_cost": repair_cost,
            "daily_cost": DAILY_COST,
            "opening_cash": self._cash,
            "closing_cash": closing,
            "bikes": {station_id: station.bikes for station_id, station in draft.items()},
            "workshop": workshop,
            "bankrupt": closing < 0,
        }
        self.stations = draft
        self.workshop = workshop
        self._cash = closing
        self._bankrupt = closing < 0
        self._history.append(record)
        self._day += 1
        return copy.deepcopy(record)

    def _parse_decision(self, decision):
        if not isinstance(decision, dict) or set(decision) != {"moves", "repairs"}:
            raise ValueError("decision must contain moves and repairs")
        moves = decision["moves"]
        repairs = decision["repairs"]
        if isinstance(moves, (str, bytes)) or not isinstance(moves, (list, tuple)):
            raise ValueError("moves must be a list")
        if len(moves) > MAX_MOVES:
            raise ValueError(f"a day can have at most {MAX_MOVES} van moves")
        if type(repairs) is not int or repairs < 0:
            raise ValueError("repairs must be a non-negative int")
        parsed = []
        for move in moves:
            origin, destination, count = self._parse_triple(move, "move")
            self._require_station(origin)
            self._require_station(destination)
            if origin == destination:
                raise ValueError("a move must use two different stations")
            if type(count) is not int or not 1 <= count <= VAN_CAPACITY:
                raise ValueError(f"a van move must carry 1 to {VAN_CAPACITY} bikes")
            parsed.append((origin, destination, count))
        return parsed, repairs

    def _parse_trips(self, trips):
        if isinstance(trips, (str, bytes)) or not isinstance(trips, (list, tuple)):
            raise ValueError("trips must be a list")
        parsed = []
        for trip in trips:
            origin, destination, count = self._parse_triple(trip, "trip")
            self._require_station(origin)
            self._require_station(destination)
            if origin == destination:
                raise ValueError("a trip must use two different stations")
            if type(count) is not int or count < 0:
                raise ValueError("a trip count must be a non-negative int")
            parsed.append((origin, destination, count))
        return parsed

    def _parse_triple(self, value, label):
        if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)) or len(value) != 3:
            raise ValueError(f"each {label} must contain an origin, a destination and a count")
        return value[0], value[1], value[2]

    def _require_station(self, station_id):
        if not isinstance(station_id, str) or station_id not in self.stations:
            raise ValueError(f"unknown station: {station_id!r}")

    def _apply_moves(self, stations, moves):
        for origin, destination, count in moves:
            source = stations[origin]
            target = stations[destination]
            if count > source.bikes or count > target.free_docks():
                raise ValueError("that van move is not possible")
            source.undock(count)
            target.dock(count)

    def _apply_repairs(self, stations, workshop, repairs):
        if repairs > workshop:
            raise ValueError("the workshop does not have that many bikes")
        depot = stations[DEPOT]
        if repairs > depot.free_docks():
            raise ValueError("repaired bikes do not fit at the depot")
        depot.dock(repairs)
        return workshop - repairs

    def _apply_trips(self, stations, workshop, trips):
        routes = []
        completed_total = 0
        lost_total = 0
        broken_total = 0
        for origin, destination, requested in trips:
            source = stations[origin]
            target = stations[destination]
            completed = completed_trips(requested, source.bikes, target.free_docks())
            lost = requested - completed
            broken = breakages(completed, BREAK_RATE)
            source.undock(completed)
            target.dock(completed)
            target.undock(broken)
            workshop += broken
            completed_total += completed
            lost_total += lost
            broken_total += broken
            routes.append({
                "origin": origin,
                "destination": destination,
                "requested": requested,
                "completed": completed,
                "lost": lost,
                "broken": broken,
            })
        return routes, workshop, completed_total, lost_total, broken_total

    @staticmethod
    def _check_stations(stations):
        if not isinstance(stations, dict) or not stations:
            raise ValueError("stations must be a non-empty dict of Station objects")
        if DEPOT not in stations:
            raise ValueError(f"stations must include the depot {DEPOT}")
        for station_id, station in stations.items():
            if not isinstance(station, Station) or station.id != station_id:
                raise ValueError("each station must be a Station stored under its own id")
