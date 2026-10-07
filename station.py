"""A docking station in the bike-share scheme."""


class Station:
    """One station, with a fixed number of docks and the bikes currently there."""

    def __init__(self, station_id, name, capacity, bikes):
        if not isinstance(station_id, str) or not station_id:
            raise ValueError("station_id must be a non-empty string")
        if not isinstance(name, str) or not name:
            raise ValueError("name must be a non-empty string")
        if type(capacity) is not int or capacity < 1:
            raise ValueError("capacity must be an int of 1 or more")
        if type(bikes) is not int or bikes < 0 or bikes > capacity:
            raise ValueError("bikes must be an int from 0 to capacity")
        self.station_id = station_id
        self.name = name
        self.capacity = capacity
        self.bikes = bikes

    def free_docks(self):
        """Return how many more bikes this station can accept."""
        return self.capacity - self.bikes

    def remove_bikes(self, count):
        """Remove count bikes. count may be zero."""
        if type(count) is not int or count < 0:
            raise ValueError("count must be an int of 0 or more")
        if count > self.bikes:
            raise ValueError("not enough bikes to remove")
        self.bikes -= count

    def add_bikes(self, count):
        """Add count bikes. count may be zero."""
        if type(count) is not int or count < 0:
            raise ValueError("count must be an int of 0 or more")
        if count > self.free_docks():
            raise ValueError("not enough free docks")
        self.bikes += count
