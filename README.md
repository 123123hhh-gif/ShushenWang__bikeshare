# Bike-share simulation

A day-by-day text simulation of a small bike-share scheme with three docking
stations, a workshop for broken bikes, and cash tracked as integer pence. Each
day the operator may move bikes by van and pay for repairs; then expected trips
run, some bikes break, and the books are closed. The run ends after the chosen
number of days or if closing cash falls below zero.

## How to run

From the project root, with Python 3:

```text
python main.py
```

Invalid typing is re-prompted. Ctrl-C and end of input exit cleanly. If the
trips file cannot be loaded, the program prints a short message and stops
without a traceback.

Run the public checks and student tests:

```text
python -m unittest discover -s tests -v
```

Student tests only:

```text
python -m unittest discover -s tests/student -v
```

## Files

| File | Contents |
| --- | --- |
| `rules.py` | Functions only: `parse_int`, `pence_to_pounds`, `load_days`, `completed_trips`, `breakages`. |
| `station.py` | `Station` with `station_id`, `free_docks`, `add_bikes`, and `remove_bikes`. |
| `bikeshare.py` | `DEFAULT_STATIONS`, `BikeShare` class attributes/constants, and `step()`. |
| `main.py` | Text interface (no classes): load trips, ask for decisions, print summaries. |
| `data/trips.json` | Expected trips for up to 14 days. |
| `tests/test_public.py` | Staff public tests (do not change). |
| `tests/student/` | Student tests for `rules.py`, `Station`, and `BikeShare`. |

## Copying note

`BikeShare.__init__` builds each `Station` from a deep copy of
`DEFAULT_STATIONS` (a dict of plain dicts) or from a caller-supplied map. The
live state holds mutable `Station` objects. A shared reference to those nested
dicts, or later sharing the same `Station` between two simulations, would let
one van move rewrite another run or the module defaults. The test
`test_c1_default_stations_and_simulations_stay_independent` in
`tests/student/test_bikeshare.py` steps one `BikeShare()` and checks that a
second instance and `DEFAULT_STATIONS` still hold the starting bike counts.
