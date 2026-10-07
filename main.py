"""Text interface for the bike-share simulation."""

import json
import sys

from bikeshare import BikeShare
from rules import MAX_DAYS, MAX_MOVES, VAN_CAPACITY, load_days, parse_int, pence_to_pounds

TRIPS_PATH = "data/trips.json"


def main():
    """Load the trips, ask for each day's decision, and print the results."""
    use_utf8_output()
    try:
        all_days = load_days(TRIPS_PATH)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"Could not load {TRIPS_PATH}: {error}")
        return

    day_count = ask_day_count(len(all_days))
    scheme = BikeShare()
    for trips in all_days[:day_count]:
        print_status(scheme, trips)
        record = run_day(scheme, trips)
        print_summary(record)
        if scheme.is_bankrupt():
            break
    print_final(scheme)


def use_utf8_output():
    """Let the pound sign print on Windows consoles without crashing."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass


def read_line(prompt):
    """Read one line. Ctrl-C and end of input leave the program quietly."""
    try:
        return input(prompt)
    except EOFError:
        print("\nInput ended.")
        raise SystemExit(0)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        raise SystemExit(0)


def ask_day_count(available):
    """Ask for 1 to 14 days. Enter selects 7 when that many trips exist."""
    while True:
        text = read_line(f"How many days to simulate? (1-{MAX_DAYS}, Enter for 7): ")
        if text.strip() == "":
            chosen = 7
        else:
            try:
                chosen = parse_int(text, 1, MAX_DAYS)
            except ValueError:
                print(f"Enter a whole number from 1 to {MAX_DAYS}, or press Enter for 7.")
                continue
        if chosen > available:
            print(f"The trips file has {available} days. Choose 1 to {available}.")
            continue
        return chosen


def print_status(scheme, trips):
    """Show the state at the start of the day and the trips about to run."""
    print()
    print(f"Day {scheme.get_day()}")
    print(f"Cash: {pence_to_pounds(scheme.get_cash())}")
    print(f"Workshop: {scheme.get_workshop()}")
    print("Stations:")
    for station in scheme.stations.values():
        print(
            f"  {station.id} {station.name}: "
            f"{station.bikes} bikes, capacity {station.capacity}, "
            f"{station.free_docks()} free docks"
        )
    print("Expected trips:")
    if not trips:
        print("  none")
    for origin, destination, count in trips:
        print(f"  {origin} -> {destination}: {count}")


def run_day(scheme, trips):
    """Ask for moves and repairs until step() accepts the decision."""
    while True:
        decision = ask_decision(scheme)
        try:
            return scheme.step(decision, trips)
        except ValueError as error:
            print(f"That decision is not possible: {error}")
            print("Please enter this day's decision again.")


def ask_decision(scheme):
    """Read a valid number of moves, each move, and the repair count."""
    station_ids = set(scheme.stations)
    move_count = ask_int(f"How many van moves? (0-{MAX_MOVES}): ", 0, MAX_MOVES)
    moves = []
    for number in range(1, move_count + 1):
        moves.append(ask_move(number, station_ids))
    repairs = ask_int("How many bikes to repair? (0 or more): ", 0)
    return {"moves": moves, "repairs": repairs}


def ask_move(number, station_ids):
    """Read one move such as 'B A 5'."""
    names = ", ".join(sorted(station_ids))
    while True:
        text = read_line(f"Move {number} (origin destination bikes, for example B A 5): ")
        try:
            return parse_move(text, station_ids)
        except ValueError as error:
            print(f"{error} Stations: {names}.")


def parse_move(text, station_ids):
    """Turn 'B A 5' into a move tuple, or raise ValueError."""
    parts = text.split()
    if len(parts) != 3:
        raise ValueError("Enter the origin, destination and number of bikes, for example B A 5.")
    origin = match_station(parts[0], station_ids)
    destination = match_station(parts[1], station_ids)
    if origin == destination:
        raise ValueError("Origin and destination must be different.")
    try:
        count = parse_int(parts[2], 1, VAN_CAPACITY)
    except ValueError:
        raise ValueError(f"The number of bikes must be a whole number from 1 to {VAN_CAPACITY}.")
    return origin, destination, count


def match_station(token, station_ids):
    """Accept a station id in any case."""
    if token in station_ids:
        return token
    upper = token.upper()
    if upper in station_ids:
        return upper
    raise ValueError(f"Unknown station {token!r}.")


def ask_int(prompt, minimum, maximum=None):
    """Keep asking until the user types a whole number in range.

    maximum is omitted when the upper bound is a simulation rule. step()
    decides those cases and run_day asks for the whole day again.
    """
    while True:
        text = read_line(prompt)
        try:
            return parse_int(text, minimum, maximum)
        except ValueError:
            if maximum is None:
                print(f"Enter a whole number of {minimum} or more.")
            elif minimum == maximum:
                print(f"Enter {minimum}.")
            else:
                print(f"Enter a whole number from {minimum} to {maximum}.")


def print_summary(record):
    """Print completed trips, losses, breakages, costs and cash."""
    print()
    print(f"Day {record['day']} summary")
    print(f"Trips completed: {record['completed']}")
    print(f"Trips lost: {record['lost']}")
    print(f"Bikes broken: {record['broken']}")
    print(f"Revenue: {pence_to_pounds(record['revenue'])}")
    print(f"Van cost: {pence_to_pounds(record['van_cost'])}")
    print(f"Repair cost: {pence_to_pounds(record['repair_cost'])}")
    print(f"Daily cost: {pence_to_pounds(record['daily_cost'])}")
    print(f"Cash at start: {pence_to_pounds(record['opening_cash'])}")
    print(f"Cash at end: {pence_to_pounds(record['closing_cash'])}")


def print_final(scheme):
    """Print totals after the last day or bankruptcy."""
    history = scheme.get_history()
    completed = sum(record["completed"] for record in history)
    lost = sum(record["lost"] for record in history)
    print()
    print("End of simulation")
    print(f"Total trips completed: {completed}")
    print(f"Total trips lost: {lost}")
    print(f"Final cash: {pence_to_pounds(scheme.get_cash())}")
    if scheme.is_bankrupt():
        print("The scheme went bankrupt.")
    else:
        print("The scheme did not go bankrupt.")


if __name__ == "__main__":
    main()
