"""Day-by-day simulation of the bike-share scheme."""

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
        """Return the day about to be simulated, starting at 1."""
        return self._day

    def get_cash(self):
        """Return the current cash in pence."""
        return self._cash

    def get_workshop(self):
        """Return how many broken bikes are in the workshop."""
        return self.workshop

    def get_bikes(self):
        """Return a new {id: bikes} dictionary."""
        return {
            station_id: station.bikes for station_id, station in self.stations.items()
        }

    def get_history(self):
        """Return a list of copies of every record, oldest first."""
        return copy.deepcopy(self._history)

    def is_bankrupt(self):
        """Return whether closing cash has already fallen below zero."""
        return self._bankrupt

    def is_finished(self):
        """Return True after all days have run or the scheme is bankrupt."""
        return self._bankrupt or self._day > self.days

    def step(self, decision, trips):
        """Run one day. Return a copy of that day's record.

        Raise RuntimeError if the simulation has finished. An invalid decision
        or trip list raises ValueError and leaves the simulation unchanged.
        """
        if self.is_finished():
            raise RuntimeError("the simulation has finished")
        moves, repairs = self._parse_decision(decision)
        parsed_trips = self._parse_trips(trips)

        # Deepcopy so a failed later move or repair leaves the live stations alone.
        draft = copy.deepcopy(self.stations)
        workshop = self.workshop
        self._apply_moves(draft, moves)
        workshop = self._apply_repairs(draft, workshop, repairs)
        completed, lost, broken, workshop = self._apply_trips(
            draft, workshop, parsed_trips
        )

        revenue = completed * self.FARE
        van_cost = len(moves) * self.VAN_COST
        repair_cost = repairs * self.REPAIR_COST
        fixed_cost = self.DAILY_COST
        closing = self._cash + revenue - van_cost - repair_cost - fixed_cost
        record = {
            "day": self._day,
            "opening_cash": self._cash,
            "closing_cash": closing,
            "revenue": revenue,
            "van_cost": van_cost,
            "repair_cost": repair_cost,
            "fixed_cost": fixed_cost,
            "completed": completed,
            "lost": lost,
            "broken": broken,
            "bikes": {
                station_id: station.bikes for station_id, station in draft.items()
            },
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

    def _build_stations(self, stations):
        if not isinstance(stations, dict) or not stations:
            raise ValueError("stations must be a non-empty dict")
        if self.DEPOT not in stations:
            raise ValueError(f"stations must include the depot {self.DEPOT}")
        built = {}
        for station_id, info in stations.items():
            if not isinstance(station_id, str) or not station_id:
                raise ValueError("each station id must be a non-empty string")
            if isinstance(info, Station):
                if info.station_id != station_id:
                    raise ValueError("each Station must be stored under its own id")
                built[station_id] = copy.deepcopy(info)
                continue
            if not isinstance(info, dict):
                raise ValueError("each station must be a dict or Station")
            try:
                name = info["name"]
                capacity = info["capacity"]
                bikes = info["bikes"]
            except KeyError as error:
                raise ValueError("each station needs name, capacity and bikes") from error
            built[station_id] = Station(station_id, name, capacity, bikes)
        return built

    def _parse_decision(self, decision):
        if not isinstance(decision, dict) or "moves" not in decision or "repairs" not in decision:
            raise ValueError("decision must contain moves and repairs")
        moves = decision["moves"]
        repairs = decision["repairs"]
        if isinstance(moves, (str, bytes)) or not isinstance(moves, (list, tuple)):
            raise ValueError("moves must be a list")
        if len(moves) > self.MAX_MOVES:
            raise ValueError(f"a day can have at most {self.MAX_MOVES} van moves")
        if type(repairs) is not int or repairs < 0:
            raise ValueError("repairs must be a non-negative int")
        if repairs > self.workshop:
            raise ValueError("the workshop does not have that many bikes")
        parsed = []
        for move in moves:
            origin, destination, count = self._parse_triple(move, "move")
            self._require_station(origin)
            self._require_station(destination)
            if origin == destination:
                raise ValueError("a move must use two different stations")
            if type(count) is not int or not 1 <= count <= self.VAN_CAPACITY:
                raise ValueError(
                    f"a van move must carry 1 to {self.VAN_CAPACITY} bikes"
                )
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
        if (
            isinstance(value, (str, bytes))
            or not isinstance(value, (list, tuple))
            or len(value) != 3
        ):
            raise ValueError(
                f"each {label} must contain an origin, a destination and a count"
            )
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
            source.remove_bikes(count)
            target.add_bikes(count)

    def _apply_repairs(self, stations, workshop, repairs):
        depot = stations[self.DEPOT]
        if repairs > depot.free_docks():
            raise ValueError("repaired bikes do not fit at the depot")
        depot.add_bikes(repairs)
        return workshop - repairs

    def _apply_trips(self, stations, workshop, trips):
        completed_total = 0
        lost_total = 0
        broken_total = 0
        for origin, destination, requested in trips:
            source = stations[origin]
            target = stations[destination]
            completed = completed_trips(requested, source.bikes, target.free_docks())
            lost = requested - completed
            broken = breakages(completed, self.BREAK_RATE)
            source.remove_bikes(completed)
            target.add_bikes(completed)
            target.remove_bikes(broken)
            workshop += broken
            completed_total += completed
            lost_total += lost
            broken_total += broken
        return completed_total, lost_total, broken_total, workshop
