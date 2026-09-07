#!/usr/bin/env python3
"""
generate_dates.py — Recurrence rule engine for the QuantOS exchange-calendar registry.

Expands recurrence rules from an exchange calendar file into explicit dated holidays.

Rules supported:
    fixed_date                     — Same date every year, no weekend adjustment
    fixed_with_weekend_adjustment  — Fixed date; Saturday -> Friday, Sunday -> Monday
    nth_weekday                    — Nth weekday of a month (1=first, 5=last)
    last_weekday                   — Last weekday of a month
    easter_offset                  — Easter Sunday + offset_days (negative = before)

Usage:
    generate_dates.py <exchange.json> [start_year] [end_year]

If start_year and end_year are omitted, the generation_range from the exchange file is used.

Exit codes:
    0 — Success
    1 — Invalid JSON
    2 — Schema violation (missing rule fields, invalid rule type)
    3 — Invalid date range
"""

import json
import sys
from datetime import date, timedelta
from pathlib import Path


WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def easter_sunday(year: int) -> date:
    """
    Anonymous Gregorian algorithm for Easter Sunday.

    Returns the date of Easter Sunday for the given year.

    Reference:
        Meeus, Jean. "Astronomical Algorithms." 2nd ed., 1998.
        Algorithm attributed to J. M. Oudin (1940).
    """
    if year < 1583:
        raise ValueError(f"Easter calculation not valid before 1583 (Gregorian calendar). Got {year}.")

    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    return date(year, month, day)


def adjust_weekend(d: date, rule: str) -> date:
    """
    Apply weekend adjustment to a fixed date.

    For fixed_with_weekend_adjustment:
        Saturday -> preceding Friday
        Sunday   -> following Monday

    For fixed_date:
        No adjustment.

    For fixed_with_weekend_adjustment, this follows NYSE Rule 7.2 and equivalent
    exchange conventions where applicable.
    """
    if rule == "fixed_with_weekend_adjustment":
        if d.weekday() == 5:  # Saturday
            return d - timedelta(days=1)
        if d.weekday() == 6:  # Sunday
            return d + timedelta(days=1)
    return d


def nth_weekday(year: int, month: int, weekday_name: str, n: int) -> date:
    """
    Return the date of the nth occurrence of a weekday in a month.

    n=1: first occurrence
    n=2: second occurrence
    n=3: third occurrence
    n=4: fourth occurrence
    n=5: fifth occurrence (last, even if it's the 4th — see note)

    Note: This function returns the nth occurrence, which may not be the last
    weekday of the month if the month has fewer than n occurrences. For "last
    weekday of month," use last_weekday().
    """
    if n < 1 or n > 5:
        raise ValueError(f"n must be between 1 and 5. Got {n}.")
    if month < 1 or month > 12:
        raise ValueError(f"month must be between 1 and 12. Got {month}.")
    if weekday_name not in WEEKDAYS:
        raise ValueError(f"Invalid weekday: {weekday_name}")

    target_weekday = WEEKDAYS[weekday_name]

    # First day of month
    first = date(year, month, 1)

    # Days until first occurrence of target weekday
    offset = (target_weekday - first.weekday()) % 7

    # Nth occurrence
    candidate = first + timedelta(days=offset + (n - 1) * 7)

    # Verify still in same month
    if candidate.month != month:
        raise ValueError(
            f"No {n}th {weekday_name} in {year}-{month:02d}. "
            f"Month has fewer occurrences."
        )

    return candidate


def last_weekday(year: int, month: int, weekday_name: str) -> date:
    """
    Return the date of the last occurrence of a weekday in a month.
    """
    if month < 1 or month > 12:
        raise ValueError(f"month must be between 1 and 12. Got {month}.")
    if weekday_name not in WEEKDAYS:
        raise ValueError(f"Invalid weekday: {weekday_name}")

    target_weekday = WEEKDAYS[weekday_name]

    # Last day of month
    if month == 12:
        last = date(year, month, 31)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)

    # Days since last occurrence of target weekday
    offset = (last.weekday() - target_weekday) % 7

    return last - timedelta(days=offset)


def generate_dates_for_rule(rule: dict, year: int) -> date:
    """
    Generate the date for a single recurrence rule in a given year.

    Returns a date object. Raises ValueError on invalid rule.
    """
    rule_type = rule.get("rule")
    if rule_type is None:
        raise ValueError("Rule missing 'rule' field.")

    if rule_type == "fixed_date":
        month = rule.get("month")
        day = rule.get("day")
        if month is None or day is None:
            raise ValueError(f"fixed_date rule missing month or day: {rule}")
        return date(year, month, day)

    elif rule_type == "fixed_with_weekend_adjustment":
        month = rule.get("month")
        day = rule.get("day")
        if month is None or day is None:
            raise ValueError(f"fixed_with_weekend_adjustment rule missing month or day: {rule}")
        d = date(year, month, day)
        return adjust_weekend(d, rule_type)

    elif rule_type == "nth_weekday":
        month = rule.get("month")
        weekday = rule.get("weekday")
        n = rule.get("n")
        if month is None or weekday is None or n is None:
            raise ValueError(f"nth_weekday rule missing month, weekday, or n: {rule}")
        return nth_weekday(year, month, weekday, n)

    elif rule_type == "last_weekday":
        month = rule.get("month")
        weekday = rule.get("weekday")
        if month is None or weekday is None:
            raise ValueError(f"last_weekday rule missing month or weekday: {rule}")
        return last_weekday(year, month, weekday)

    elif rule_type == "easter_offset":
        offset_days = rule.get("offset_days")
        if offset_days is None:
            raise ValueError(f"easter_offset rule missing offset_days: {rule}")
        return easter_sunday(year) + timedelta(days=offset_days)

    else:
        raise ValueError(f"Unknown rule type: {rule_type}")


def expand_exchange(exchange: dict, start_year: int = None, end_year: int = None) -> list:
    """
    Expand all recurrence rules in an exchange file into explicit holiday entries.

    Returns a list of holiday dicts (same structure as explicit array entries),
    with dates generated for each year in [start_year, end_year].

    Explicit dates already present in the exchange file are not duplicated.
    """
    holidays = exchange.get("holidays", {})
    recurrence_rules = holidays.get("recurrence_rules", [])
    explicit_dates = holidays.get("explicit", [])

    # Determine year range
    if start_year is None or end_year is None:
        gen_range = exchange.get("generation_range", [])
        if len(gen_range) != 2:
            raise ValueError("generation_range must be [start_date, end_date]")
        start_year = int(gen_range[0][:4])
        end_year = int(gen_range[1][:4])

    if start_year > end_year:
        raise ValueError(f"start_year ({start_year}) > end_year ({end_year})")

    # Build set of existing dates to avoid duplicates
    existing = set()
    for entry in explicit_dates:
        existing.add(entry["date"])

    generated = []

    for rule in recurrence_rules:
        rule_name = rule.get("name", "Unnamed rule")
        rule_status = rule.get("status", "closed")

        for year in range(start_year, end_year + 1):
            try:
                d = generate_dates_for_rule(rule, year)
            except ValueError as e:
                # Skip rules that don't apply in this year (e.g., nth_weekday where n=5 doesn't exist)
                print(f"WARN: {rule_name} ({rule['rule']}) failed for {year}: {e}", file=sys.stderr)
                continue

            date_str = d.isoformat()

            if date_str in existing:
                continue

            entry = {
                "date": date_str,
                "name": rule_name,
                "status": rule_status,
            }

            if rule_status == "early_close":
                early_close_time = rule.get("early_close_time")
                if early_close_time:
                    entry["early_close_time"] = early_close_time

            if rule.get("source_url"):
                entry["source_url"] = rule["source_url"]

            generated.append(entry)
            existing.add(date_str)

    # Sort by date
    generated.sort(key=lambda x: x["date"])

    return generated


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <exchange.json> [start_year] [end_year]", file=sys.stderr)
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(path) as f:
            exchange = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    start_year = None
    end_year = None
    if len(sys.argv) >= 4:
        try:
            start_year = int(sys.argv[2])
            end_year = int(sys.argv[3])
        except ValueError:
            print("Error: start_year and end_year must be integers", file=sys.stderr)
            sys.exit(3)

    try:
        generated = expand_exchange(exchange, start_year, end_year)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)

    # Output as JSON
    print(json.dumps(generated, indent=2))


if __name__ == "__main__":
    main()