"""A docking station in the bike-share scheme."""


class Station:
    """One station, with a fixed number of docks and the bikes currently there."""

    def __init__(self, station_id, name, capacity, bikes):
        if not isinstance(station_id, str) or not isinstance(name, str):
            raise TypeError("station id and name must be strings")
        if type(capacity) is not int or type(bikes) is not int:
            raise TypeError("capacity and bikes must be ints")
        if capacity < 0 or bikes < 0 or bikes > capacity:
            raise ValueError("bikes must be between 0 and the station capacity")
        self.id = station_id
        self.name = name
        self.capacity = capacity
        self.bikes = bikes

    def free_docks(self):
        """Return how many more bikes this station can accept."""
        return self.capacity - self.bikes

    def undock(self, count):
        """Remove count bikes. count may be zero."""
        if type(count) is not int:
            raise TypeError("count must be an int")
        if count < 0 or count > self.bikes:
            raise ValueError("not enough bikes to undock")
        self.bikes -= count

    def dock(self, count):
        """Add count bikes. count may be zero."""
        if type(count) is not int:
            raise TypeError("count must be an int")
        if count < 0 or count > self.free_docks():
            raise ValueError("not enough free docks")
        self.bikes += count
