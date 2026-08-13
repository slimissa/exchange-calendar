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