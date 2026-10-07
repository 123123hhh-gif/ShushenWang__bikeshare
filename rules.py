"""Conversion helpers and trip rules for the bike-share simulation.

Author: Shushen Wang

Functions only: parse user text, format pence as pounds, load the trips file,
and work out completed trips and broken bikes for one route.
"""

import json


def _require_ints(*values):
    """Raise TypeError unless every value is an int. Booleans are rejected."""
    for value in values:
        if type(value) is not int:
            raise TypeError("arguments must be ints")


def parse_int(text, minimum=None, maximum=None):
    """Convert text typed by a user into an int.

    Surrounding spaces are ignored. minimum and maximum, when given, are
    inclusive bounds.
    """
    if not isinstance(text, str):
        raise TypeError("text must be a str")
    for bound in (minimum, maximum):
        if bound is not None:
            _require_ints(bound)
    stripped = text.strip()
    digits = stripped[1:] if stripped[:1] in "+-" else stripped
    if not digits or any(char not in "0123456789" for char in digits):
        raise ValueError(f"not a whole number: {text!r}")
    value = int(stripped)
    if minimum is not None and value < minimum:
        raise ValueError(f"{value} is below the minimum of {minimum}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{value} is above the maximum of {maximum}")
    return value


def pence_to_pounds(pence):
    """Return a display string for an amount in pence, such as £123.45."""
    _require_ints(pence)
    sign = "-" if pence < 0 else ""
    amount = abs(pence)
    return f"{sign}£{amount // 100}.{amount % 100:02d}"


def load_days(path):
    """Read a trips file and return days of (origin, destination, count)."""
    with open(path, encoding="utf-8") as trips_file:
        data = json.load(trips_file)
    if not isinstance(data, list) or not data:
        raise ValueError("trips file must contain a non-empty list of days")
    days = []
    for day in data:
        if not isinstance(day, list):
            raise ValueError("each day must be a list of trips")
        days.append([_convert_trip(trip) for trip in day])
    return days


def _convert_trip(trip):
    """Return one JSON trip as a (str, str, int) tuple, or raise ValueError."""
    if not isinstance(trip, list) or len(trip) != 3:
        raise ValueError("each trip must have exactly three items")
    origin, destination, count = trip
    if not isinstance(origin, str) or not isinstance(destination, str):
        raise ValueError("station ids must be strings")
    if type(count) is not int or count < 0:
        raise ValueError("trip count must be a non-negative integer")
    if origin == destination:
        raise ValueError("origin and destination must be different")
    return origin, destination, count


def completed_trips(requested, bikes, free_docks):
    """Return how many trips one route can complete.

    That is the smallest of the requested trips, the bikes at the origin and
    the free docks at the destination.
    """
    _require_ints(requested, bikes, free_docks)
    if min(requested, bikes, free_docks) < 0:
        raise ValueError("requested, bikes and free docks must be 0 or more")
    return min(requested, bikes, free_docks)


def breakages(completed, rate_percent):
    """Return bikes broken on a route, rounded up.

    rate_percent is the percentage of completed trips that break a bike,
    from 0 to 100.
    """
    _require_ints(completed, rate_percent)
    if completed < 0:
        raise ValueError("completed must be 0 or more")
    if not 0 <= rate_percent <= 100:
        raise ValueError("rate_percent must be from 0 to 100")
    return (completed * rate_percent + 99) // 100
