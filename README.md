# Bike-share simulation
This is a text-based day-by-day simulation for a small bike-share system. It has three docking stations, a workshop for damaged bikes, and cash stored as integer pence. 
Each day the operator can move bikes by van and pay to repair broken bikes. After that, trips run, some bikes break, and the day’s accounts are finalised. 
The simulation stops once the selected number of days finish, or if cash becomes negative.


## How to run

From the project root folder using Python 3.11 or newer:

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
Inside `BikeShare.step()`, I use `copy.deepcopy(self.stations)`. All changes are applied to this temporary draft state. The draft only replaces the live simulation state when all bike moves and repairs succeed.
If I use a simple reference like `draft = self.stations`, any changes will modify the live stations directly. `copy.copy()` (shallow copy) also does not work properly. It copies the outer dictionary, but both dictionaries still reference the same mutable `Station` objects.
With either of these incorrect approaches, partial changes can remain. For example, if the first bike move succeeds but a later operation fails and raises `ValueError`, the earlier successful change stays applied. This violates requirement C3.
I have written a test named `test_c3_later_failed_move_changes_nothing` in `tests/student/test_bikeshare.py`. It runs a valid bike move followed by an impossible operation. The test verifies that station bike counts, cash, day counter and history all remain unchanged after the error.


