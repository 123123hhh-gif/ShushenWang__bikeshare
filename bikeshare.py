"""Day-by-day simulation of the bike-share scheme.

Author: Shushen Wang

Defines DEFAULT_STATIONS and BikeShare, which holds the stations, workshop,
cash and history, and runs one day at a time with step().
"""

import copy

from rules import breakages, completed_trips
from station import Station

DEFAULT_STATIONS = {
    "A": {"name": "Temple Meads", "capacity": 20, "bikes": 12},
    "B": {"name": "Harbourside", "capacity": 15, "bikes": 8},
    "C": {"name": "Clifton", "capacity": 12, "bikes": 6},
}


class BikeShare:
    """The stations, workshop, cash and day-by-day history of one scheme."""

    FARE = 200
    DAILY_COST = 2400
    VAN_COST = 500
    REPAIR_COST = 200
    BREAK_RATE = 10
    VAN_CAPACITY = 10
    MAX_MOVES = 3
    MAX_DAYS = 14
    DEPOT = "A"

    def __init__(self, days=7, cash=10000, stations=None, workshop=0):
        """Set up a new simulation starting on day 1.

        stations uses the DEFAULT_STATIONS format; None means the defaults.
        Raise ValueError for invalid days, cash, workshop or stations.
        """
        if type(days) is not int or not 1 <= days <= self.MAX_DAYS:
            raise ValueError(f"days must be an int from 1 to {self.MAX_DAYS}")
        if type(cash) is not int or cash < 0:
            raise ValueError("cash must be an int of 0 or more")
        if type(workshop) is not int or workshop < 0:
            raise ValueError("workshop must be an int of 0 or more")
        source = DEFAULT_STATIONS if stations is None else stations
        self.stations = self._build_stations(source)
        self.days = days
        self.workshop = workshop
        self._cash = cash
        self._day = 1
        self._history = []
        self._bankrupt = False

    def get_day(self):
        """Return the number of the next day to run, starting at 1."""
        return self._day

    def get_cash(self):
        """Return the current cash in pence."""
        return self._cash

    def get_workshop(self):
        """Return how many broken bikes are in the workshop."""
        return self.workshop

    def get_bikes(self):
        """Return a new {id: bikes} dictionary."""
        return self._bike_counts(self.stations)

    def get_history(self):
        """Return a list of copies of every record, oldest first."""
        return copy.deepcopy(self._history)

    def is_bankrupt(self):
        """Return whether closing cash has fallen below zero."""
        return self._bankrupt

    def is_finished(self):
        """Return True after all days have run or the scheme is bankrupt."""
        return self._bankrupt or self._day > self.days

    def step(self, decision, trips):
        """Run one day and return a copy of its record.

        Raise RuntimeError if the simulation has finished. An invalid
        decision or trip list raises ValueError and changes nothing.
        """
        if self.is_finished():
            raise RuntimeError("the simulation has finished")
        moves, repairs = self._parse_decision(decision)
        parsed_trips = self._parse_trips(trips)

        # Work on deep copies of the Station objects so that a later failed
        # move or repair leaves the live stations unchanged.
        draft = copy.deepcopy(self.stations)
        self._apply_moves(draft, moves)
        self._apply_repairs(draft, repairs)
        completed, lost, broken = self._apply_trips(draft, parsed_trips)

        revenue = completed * self.FARE
        van_cost = len(moves) * self.VAN_COST
        repair_cost = repairs * self.REPAIR_COST
        closing = (self._cash + revenue - van_cost - repair_cost
                   - self.DAILY_COST)
        workshop = self.workshop - repairs + broken
        record = {
            "day": self._day,
            "opening_cash": self._cash,
            "closing_cash": closing,
            "revenue": revenue,
            "van_cost": van_cost,
            "repair_cost": repair_cost,
            "fixed_cost": self.DAILY_COST,
            "completed": completed,
            "lost": lost,
            "broken": broken,
            "bikes": self._bike_counts(draft),
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

    @staticmethod
    def _bike_counts(stations):
        """Return a new {id: bikes} dictionary for a dict of stations."""
        return {sid: station.bikes for sid, station in stations.items()}

    def _build_stations(self, stations):
        """Return a new dict of Station objects, or raise ValueError."""
        if not isinstance(stations, dict) or self.DEPOT not in stations:
            raise ValueError(
                f"stations must be a dict that includes {self.DEPOT!r}"
            )
        built = {}
        for station_id, info in stations.items():
            if not isinstance(info, dict):
                raise ValueError("each station must be a dict")
            try:
                built[station_id] = Station(
                    station_id, info["name"], info["capacity"], info["bikes"]
                )
            except KeyError as error:
                raise ValueError(
                    "each station needs name, capacity and bikes"
                ) from error
        return built

    def _parse_decision(self, decision):
        """Check a decision and return (moves, repairs)."""
        if (not isinstance(decision, dict) or "moves" not in decision
                or "repairs" not in decision):
            raise ValueError("decision must contain moves and repairs")
        moves = self._require_sequence(decision["moves"], "moves")
        if len(moves) > self.MAX_MOVES:
            raise ValueError(
                f"a day can have at most {self.MAX_MOVES} van moves"
            )
        repairs = decision["repairs"]
        if type(repairs) is not int or repairs < 0:
            raise ValueError("repairs must be a non-negative int")
        if repairs > self.workshop:
            raise ValueError("the workshop does not have that many bikes")
        parsed = []
        for move in moves:
            origin, destination, count = self._parse_route(move, "move")
            if type(count) is not int or not 1 <= count <= self.VAN_CAPACITY:
                raise ValueError(
                    f"a van move must carry 1 to {self.VAN_CAPACITY} bikes"
                )
            parsed.append((origin, destination, count))
        return parsed, repairs

    def _parse_trips(self, trips):
        """Check one day of trips and return them as tuples."""
        parsed = []
        for trip in self._require_sequence(trips, "trips"):
            origin, destination, count = self._parse_route(trip, "trip")
            if type(count) is not int or count < 0:
                raise ValueError("a trip count must be a non-negative int")
            parsed.append((origin, destination, count))
        return parsed

    def _parse_route(self, route, label):
        """Return (origin, destination, count) from a move or trip.

        Raise ValueError unless route has three items, both stations are
        known, and the origin and destination differ.
        """
        route = self._require_sequence(route, label)
        if len(route) != 3:
            raise ValueError(f"each {label} must have exactly three items")
        origin, destination, count = route
        for station_id in (origin, destination):
            if (not isinstance(station_id, str)
                    or station_id not in self.stations):
                raise ValueError(f"unknown station: {station_id!r}")
        if origin == destination:
            raise ValueError(f"a {label} must use two different stations")
        return origin, destination, count

    @staticmethod
    def _require_sequence(value, label):
        """Return value if it is a list or tuple, else raise ValueError."""
        if not isinstance(value, (list, tuple)):
            raise ValueError(f"{label} must be a list or tuple")
        return value

    @staticmethod
    def _apply_moves(stations, moves):
        """Apply van moves in order; raise ValueError if one is impossible."""
        for origin, destination, count in moves:
            source = stations[origin]
            target = stations[destination]
            if count > source.bikes or count > target.free_docks():
                raise ValueError(
                    f"move {origin}->{destination} {count} is not possible now"
                )
            source.remove_bikes(count)
            target.add_bikes(count)

    def _apply_repairs(self, stations, repairs):
        """Dock repaired bikes at the depot, or raise ValueError."""
        depot = stations[self.DEPOT]
        if repairs > depot.free_docks():
            raise ValueError("repaired bikes do not fit at the depot")
        depot.add_bikes(repairs)

    def _apply_trips(self, stations, trips):
        """Run trips route by route and return (completed, lost, broken)."""
        total_completed = total_lost = total_broken = 0
        for origin, destination, requested in trips:
            source = stations[origin]
            target = stations[destination]
            completed = completed_trips(
                requested, source.bikes, target.free_docks()
            )
            broken = breakages(completed, self.BREAK_RATE)
            source.remove_bikes(completed)
            target.add_bikes(completed)
            target.remove_bikes(broken)
            total_completed += completed
            total_lost += requested - completed
            total_broken += broken
        return total_completed, total_lost, total_broken
