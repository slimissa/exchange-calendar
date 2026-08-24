#!/usr/bin/env python3
"""
validate.py — Multi-layer validator for the QuantOS exchange-calendar registry.

Validates every exchange file in exchanges/ against:
    1. JSON Schema (schema.json) — structural correctness
    2. Business logic — semantic correctness
    3. Cross-exchange consistency — no duplicate MICs, no duplicate dates

Usage:
    validate.py [exchanges_dir] [schema_path]

Defaults:
    exchanges_dir = "exchanges"
    schema_path   = "schema.json"

Exit codes:
    0 — All files valid
    1 — Validation errors found
    2 — Schema file missing or invalid
    3 — Exchanges directory missing
"""

import json
import sys
from datetime import date
from pathlib import Path

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"}
VALID_STATUSES = {"closed", "early_close", "delayed_open", "special_session"}
VALID_RULES = {"fixed_date", "fixed_with_weekend_adjustment", "nth_weekday", "last_weekday", "easter_offset"}
VALID_TIMEZONE_PREFIXES = {"Africa", "America", "Antarctica", "Arctic", "Asia", "Atlantic", "Australia", "Europe", "Indian", "Pacific", "Etc", "UTC", "GMT"}

def load_json(path: Path) -> dict:
    """Load and parse a JSON file. Returns None on failure."""
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: {path}: Invalid JSON: {e}")
        return None
    except FileNotFoundError:
        print(f"ERROR: {path}: File not found")
        return None


def validate_schema(exchange: dict, schema: dict, filename: str) -> list:
    """Validate exchange against JSON Schema. Returns list of error strings."""
    errors = []

    if not HAS_JSONSCHEMA:
        # Fallback: basic structural checks without jsonschema library
        required = schema.get("required", [])
        for field in required:
            if field not in exchange:
                errors.append(f"{filename}: Missing required field: {field}")
        return errors

    validator = jsonschema.Draft7Validator(schema)
    for error in validator.iter_errors(exchange):
        path = ".".join(str(p) for p in error.path) or "root"
        errors.append(f"{filename}: Schema violation at {path}: {error.message}")

    return errors


def validate_business_logic(exchange: dict, filename: str) -> list:
    """Validate semantic correctness beyond schema. Returns list of error strings."""
    errors = []

    code = exchange.get("code", "")
    mic = exchange.get("mic", "")
    timezone = exchange.get("timezone", "")

    # code must match filename
    expected_code = filename.replace(".json", "")
    if code != expected_code:
        errors.append(f"{filename}: code '{code}' does not match filename '{expected_code}'")

    # code must equal mic
    if code != mic:
        errors.append(f"{filename}: code '{code}' does not equal mic '{mic}'")

    # timezone must be plausible
    if timezone:
        prefix = timezone.split("/")[0]
        if prefix not in VALID_TIMEZONE_PREFIXES:
            errors.append(f"{filename}: Suspicious timezone: {timezone}")

    # regular_hours validation
    regular = exchange.get("regular_hours", {})
    if regular:
        open_time = regular.get("open", "")
        close_time = regular.get("close", "")
        if open_time and close_time and open_time >= close_time:
            errors.append(f"{filename}: regular_hours open ({open_time}) must be before close ({close_time})")

    # extended_hours validation
    extended = exchange.get("extended_hours", {})
    if extended:
        pre = extended.get("pre_market", {})
        after = extended.get("after_hours", {})
        if pre and pre.get("close", "") != regular.get("open", ""):
            errors.append(f"{filename}: pre_market close ({pre.get('close')}) should equal regular open ({regular.get('open')})")
        if after and after.get("open", "") != regular.get("close", ""):
            errors.append(f"{filename}: after_hours open ({after.get('open')}) should equal regular close ({regular.get('close')})")

    # sessions validation
    sessions = exchange.get("sessions", [])
    seen_session_times = set()
    for session in sessions:
        session_type = session.get("type", "")
        if session_type == "lunch_break":
            open_time = session.get("open", "")
            close_time = session.get("close", "")
            if open_time and close_time and open_time >= close_time:
                errors.append(f"{filename}: lunch_break open ({open_time}) must be before close ({close_time})")
            key = (session_type, open_time, close_time)
            if key in seen_session_times:
                errors.append(f"{filename}: Duplicate lunch_break session at {open_time}-{close_time}")
            seen_session_times.add(key)
        elif session_type == "auction":
            at_time = session.get("at", "")
            key = (session_type, at_time)
            if key in seen_session_times:
                errors.append(f"{filename}: Duplicate auction at {at_time}")
            seen_session_times.add(key)

    # holidays validation
    holidays = exchange.get("holidays", {})
    explicit = holidays.get("explicit", [])

    # Check for duplicate dates in explicit
    seen_dates = set()
    for entry in explicit:
        date_str = entry.get("date", "")
        if date_str in seen_dates:
            errors.append(f"{filename}: Duplicate explicit date: {date_str}")
        seen_dates.add(date_str)

        status = entry.get("status", "")
        if status == "early_close" and "early_close_time" not in entry:
            errors.append(f"{filename}: early_close entry {date_str} missing early_close_time")
        if status == "delayed_open" and "delayed_open_time" not in entry:
            errors.append(f"{filename}: delayed_open entry {date_str} missing delayed_open_time")

        # Check date format
        try:
            year = int(date_str[:4])
            month = int(date_str[5:7])
            day = int(date_str[8:10])
            if month < 1 or month > 12:
                errors.append(f"{filename}: Invalid month in date: {date_str}")
            if day < 1 or day > 31:
                errors.append(f"{filename}: Invalid day in date: {date_str}")
        except (ValueError, IndexError):
            errors.append(f"{filename}: Malformed date: {date_str}")

    # recurrence_rules validation
    rules = holidays.get("recurrence_rules", [])
    for rule in rules:
        rule_type = rule.get("rule", "")
        if rule_type not in VALID_RULES:
            errors.append(f"{filename}: Unknown rule type: {rule_type}")
            continue

        status = rule.get("status", "")
        if status == "early_close" and "early_close_time" not in rule:
            errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' with early_close status missing early_close_time")

        if rule_type == "fixed_date" or rule_type == "fixed_with_weekend_adjustment":
            if "month" not in rule or "day" not in rule:
                errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' missing month/day")
            else:
                month = rule["month"]
                day = rule["day"]
                if month < 1 or month > 12:
                    errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' has invalid month: {month}")
                if day < 1 or day > 31:
                    errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' has invalid day: {day}")

        elif rule_type == "nth_weekday":
            if "month" not in rule or "weekday" not in rule or "n" not in rule:
                errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' missing month/weekday/n")
            else:
                if rule["weekday"] not in WEEKDAYS:
                    errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' has invalid weekday: {rule['weekday']}")
                if rule["n"] < 1 or rule["n"] > 5:
                    errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' has invalid n: {rule['n']}")

        elif rule_type == "last_weekday":
            if "month" not in rule or "weekday" not in rule:
                errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' missing month/weekday")
            else:
                if rule["weekday"] not in WEEKDAYS:
                    errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' has invalid weekday: {rule['weekday']}")

        elif rule_type == "easter_offset":
            if "offset_days" not in rule:
                errors.append(f"{filename}: Recurrence rule '{rule.get('name')}' missing offset_days")

    # ad_hoc_closures validation
    ad_hoc = exchange.get("ad_hoc_closures", [])
    for entry in ad_hoc:
        date_str = entry.get("date", "")
        if date_str in seen_dates:
            errors.append(f"{filename}: Ad-hoc closure date duplicates explicit date: {date_str}")
        if entry.get("status") == "early_close" and "early_close_time" not in entry:
            errors.append(f"{filename}: Ad-hoc early_close entry {date_str} missing early_close_time")
        if "source_url" not in entry:
            errors.append(f"{filename}: Ad-hoc closure {date_str} missing source_url (required for auditability)")

    # generation_range validation
    gen_range = exchange.get("generation_range", [])
    if len(gen_range) != 2:
        errors.append(f"{filename}: generation_range must have exactly 2 dates")
    else:
        try:
            start = gen_range[0]
            end = gen_range[1]
            if start >= end:
                errors.append(f"{filename}: generation_range start ({start}) must be before end ({end})")
        except (IndexError, TypeError):
            errors.append(f"{filename}: generation_range dates malformed")

    return errors


def check_weekend_dates(exchange: dict, filename: str) -> list:
    """H1 check 1: no explicit holiday date should fall on this
    exchange's own weekend days. Uses weekend_days (added in C1)
    instead of assuming Saturday/Sunday for every exchange."""
    errors = []
    weekend = exchange.get("weekend_days", [5, 6])
    for holiday in exchange.get("holidays", {}).get("explicit", []):
        try:
            d = date.fromisoformat(holiday["date"])
        except (KeyError, ValueError):
            continue  # malformed date is caught by schema validation
        if holiday.get("weekend_exception"):
            continue  # deliberate, sourced exception -- see schema.json
        if d.weekday() in weekend:
            errors.append(
                f"{filename}: holiday on weekend day: {holiday['date']} ({holiday.get('name', '?')})"
            )
    return errors


def check_islamic_holidays(exchange: dict, filename: str) -> list:
    """H1 check 2: Friday/Saturday-weekend (Islamic-calendar) exchanges
    should have both Eid al-Fitr and Eid al-Adha somewhere in their
    explicit holidays. Would have caught C2/C3 (XSAU/XDFM shipping
    with zero Islamic holidays) automatically.

    Uses sorted(weekend_days) == [4, 5] rather than an exact-order
    list comparison, since weekend_days is a set of two days and
    should be compared as such -- [5, 4] means the same thing as
    [4, 5] and shouldn't silently skip this check.
    """
    errors = []
    weekend = exchange.get("weekend_days", [])
    if sorted(weekend) == [4, 5]:
        names = [h.get("name", "").lower() for h in exchange.get("holidays", {}).get("explicit", [])]
        if not any("eid al-fitr" in n for n in names):
            errors.append(f"{filename}: Islamic-weekend exchange missing Eid al-Fitr")
        if not any("eid al-adha" in n for n in names):
            errors.append(f"{filename}: Islamic-weekend exchange missing Eid al-Adha")
    return errors


def check_generation_range(exchange: dict, filename: str) -> list:
    """H1 check 3: explicit holiday data should actually extend close
    to the end of the claimed generation_range, not just start within
    it. Would have caught C4 (XBKK/XCOL/XMOS/XSHE/XSTC claiming
    coverage through 2029 while data stopped years earlier)
    automatically. A gap under 90 days is tolerated since the last
    holiday of a range doesn't necessarily fall on the range's final
    day."""
    errors = []
    dates = [h["date"] for h in exchange.get("holidays", {}).get("explicit", []) if "date" in h]
    gen_range = exchange.get("generation_range", [])
    if not dates or len(gen_range) != 2:
        return errors
    latest = max(dates)
    range_end = gen_range[1]
    try:
        if latest < range_end:
            gap_days = (date.fromisoformat(range_end) - date.fromisoformat(latest)).days
            if gap_days > 90:
                errors.append(
                    f"{filename}: generation_range claims coverage through {range_end} "
                    f"but explicit data ends {latest} ({gap_days}d gap)"
                )
    except ValueError:
        pass  # malformed date is caught by schema validation
    return errors


def check_predicted_consistency(exchange: dict, filename: str) -> list:
    """M6: the structured `predicted` field and the legacy '(predicted)'
    name suffix should not contradict each other. Both forms are
    currently accepted (backward compatibility), but if an entry
    explicitly sets `predicted` one way while its name suggests the
    other, that's a real data inconsistency worth catching -- not
    every entry needs the field, so this only checks entries where
    `predicted` is explicitly present."""
    errors = []
    for holiday in exchange.get("holidays", {}).get("explicit", []):
        if "predicted" not in holiday:
            continue  # field is optional; absence is not an error
        name = holiday.get("name", "")
        name_says_predicted = "(predicted)" in name
        field_says_predicted = bool(holiday["predicted"])
        if field_says_predicted and not name_says_predicted:
            errors.append(
                f"{filename}: {holiday.get('date', '?')}: predicted=true but "
                f"name has no '(predicted)' suffix: {name!r}"
            )
        elif not field_says_predicted and name_says_predicted:
            errors.append(
                f"{filename}: {holiday.get('date', '?')}: predicted=false but "
                f"name still has '(predicted)' suffix: {name!r}"
            )
    return errors


def validate_cross_exchange(all_exchanges: dict, filenames: list) -> list:
    """Validate consistency across all exchange files. Returns list of error strings."""
    errors = []

    seen_codes = {}
    seen_mics = {}

    for filename in filenames:
        exchange = all_exchanges[filename]
        code = exchange.get("code", "")
        mic = exchange.get("mic", "")

        if code in seen_codes:
            errors.append(f"Duplicate code '{code}' in {seen_codes[code]} and {filename}")
        else:
            seen_codes[code] = filename

        if mic in seen_mics:
            errors.append(f"Duplicate mic '{mic}' in {seen_mics[mic]} and {filename}")
        else:
            seen_mics[mic] = filename

    return errors


def main():
    exchanges_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("exchanges")
    schema_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("schema.json")

    if not exchanges_dir.exists():
        print(f"ERROR: Exchanges directory not found: {exchanges_dir}")
        sys.exit(3)

    if not schema_path.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        sys.exit(2)

    schema = load_json(schema_path)
    if schema is None:
        print(f"ERROR: Schema file is invalid JSON: {schema_path}")
        sys.exit(2)

    all_errors = []
    all_exchanges = {}
    valid_filenames = []

    # Collect all exchange files
    exchange_files = sorted(exchanges_dir.glob("*.json"))

    if not exchange_files:
        print("ERROR: No exchange files found")
        sys.exit(1)

    # Validate each file
    for exchange_file in exchange_files:
        exchange = load_json(exchange_file)
        if exchange is None:
            all_errors.append(f"{exchange_file.name}: Failed to parse")
            continue

        all_exchanges[exchange_file.name] = exchange
        valid_filenames.append(exchange_file.name)

        errors = validate_schema(exchange, schema, exchange_file.name)
        errors.extend(validate_business_logic(exchange, exchange_file.name))
        errors.extend(check_weekend_dates(exchange, exchange_file.name))
        errors.extend(check_islamic_holidays(exchange, exchange_file.name))
        errors.extend(check_generation_range(exchange, exchange_file.name))
        errors.extend(check_predicted_consistency(exchange, exchange_file.name))
        all_errors.extend(errors)

    # Cross-exchange validation
    all_errors.extend(validate_cross_exchange(all_exchanges, valid_filenames))

    # Report
    if all_errors:
        print(f"Validation failed with {len(all_errors)} error(s):")
        for error in all_errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print(f"OK: {len(valid_filenames)} exchange file(s) validated successfully")
        sys.exit(0)


if __name__ == "__main__":
    main()