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
| `rules.py` | Constants, `parse_int`, `pence_to_pounds`, `load_days`, `completed_trips`, `breakages`. |
| `station.py` | `Station` with docks, bikes, `free_docks`, `dock`, and `undock`. |
| `bikeshare.py` | `DEFAULT_STATIONS` and `BikeShare`, including `step()` and getters. |
| `main.py` | Text interface (no classes): load trips, ask for decisions, print summaries. |
| `data/trips.json` | Expected trips for up to 14 days. |
| `tests/test_public.py` | Staff public tests (do not change). |
| `tests/student/` | Student tests for rules, stations, simulation, and the CLI. |

## Copying note

`BikeShare.__init__` builds `self.stations` with `copy.deepcopy` of
`DEFAULT_STATIONS` (or a supplied map). Each value is a mutable `Station`. A
plain assignment, or `copy.copy` of the dict alone, would leave simulations
sharing the same `Station` objects, so a van move in one run would change bikes
in another and rewrite the module defaults. The test
`test_c1_default_stations_and_simulations_stay_independent` in
`tests/student/test_bikeshare.py` steps one `BikeShare()` and checks that a
second instance and `DEFAULT_STATIONS` still hold the starting bike counts.
