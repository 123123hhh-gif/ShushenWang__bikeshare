"""A docking station in the bike-share scheme.

Author: Shushen Wang

Defines Station, which tracks a fixed number of docks and the bikes in them.
"""


class Station:
    """One station with a fixed number of docks and the bikes docked there."""

    def __init__(self, station_id, name, capacity, bikes):
        """Create a station. Raise ValueError if any argument is invalid.

        station_id and name must be non-empty strings, capacity an int of 1 or
        more, and bikes an int from 0 to capacity.
        """
        if not isinstance(station_id, str) or not station_id:
            raise ValueError("station_id must be a non-empty string")
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string")
        if type(capacity) is not int or capacity < 1:
            raise ValueError("capacity must be an int of 1 or more")
        if type(bikes) is not int or not 0 <= bikes <= capacity:
            raise ValueError("bikes must be an int from 0 to capacity")
        self.station_id = station_id
        self.name = name
        self.capacity = capacity
        self.bikes = bikes

    def free_docks(self):
        """Return how many more bikes this station can accept."""
        return self.capacity - self.bikes

    def remove_bikes(self, count):
        """Remove count bikes. Raise ValueError if too few are docked."""
        self._check_count(count)
        if count > self.bikes:
            raise ValueError("not enough bikes to remove")
        self.bikes -= count

    def add_bikes(self, count):
        """Add count bikes. Raise ValueError if too few docks are free."""
        self._check_count(count)
        if count > self.free_docks():
            raise ValueError("not enough free docks")
        self.bikes += count

    @staticmethod
    def _check_count(count):
        """Raise ValueError unless count is an int of 0 or more."""
        if type(count) is not int or count < 0:
            raise ValueError("count must be an int of 0 or more")
