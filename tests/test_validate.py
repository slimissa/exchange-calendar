#!/usr/bin/env python3
"""
test_validate.py — Unit tests for the validator.

Tests that validate.py correctly:
    1. Accepts valid exchange files
    2. Rejects invalid JSON
    3. Rejects schema violations
    4. Rejects business logic errors
    5. Rejects cross-exchange duplicates

Run:
    python3 -m pytest tests/test_validate.py -v
"""

import json
import os
import sys
import pytest
from pathlib import Path

# Add tools/ to path
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import validate as validator


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def write_temp_exchange(tmp_path, filename, data):
    """Write an exchange dict to a temp file."""
    path = tmp_path / filename
    with open(path, "w") as f:
        json.dump(data, f)
    return path


def make_valid_exchange(code="TEST", mic="TEST"):
    """Return a minimal valid exchange dict."""
    return {
        "code": code,
        "name": f"Test Exchange {code}",
        "mic": mic,
        "timezone": "Europe/London",
        "weekend_days": [5, 6],
        "regular_hours": {"open": "09:00", "close": "17:00"},
        "holidays": {
            "explicit": [
                {
                    "date": "2025-01-01",
                    "name": "New Year's Day",
                    "status": "closed",
                }
            ],
            "recurrence_rules": [],
        },
        "ad_hoc_closures": [],
        "generation_range": ["2025-01-01", "2025-12-31"],
    }


# ──────────────────────────────────────────────────────────────
# Schema validation
# ──────────────────────────────────────────────────────────────

class TestSchemaValidation:
    def test_valid_exchange_passes(self, tmp_path):
        exchange = make_valid_exchange()
        path = write_temp_exchange(tmp_path, "TEST.json", exchange)

        schema = json.loads((Path(__file__).parent.parent / "schema.json").read_text())

        errors = validator.validate_schema(exchange, schema, path.name)
        assert errors == []

    def test_missing_required_field(self, tmp_path):
        exchange = make_valid_exchange()
        del exchange["timezone"]
        path = write_temp_exchange(tmp_path, "TEST.json", exchange)

        schema = json.loads((Path(__file__).parent.parent / "schema.json").read_text())

        errors = validator.validate_schema(exchange, schema, path.name)
        assert len(errors) > 0
        assert any("timezone" in e for e in errors)

    def test_invalid_code_pattern(self, tmp_path):
        exchange = make_valid_exchange(code="TOOLONG")
        path = write_temp_exchange(tmp_path, "TOOLONG.json", exchange)

        schema = json.loads((Path(__file__).parent.parent / "schema.json").read_text())

        errors = validator.validate_schema(exchange, schema, path.name)
        assert len(errors) > 0

    def test_invalid_timezone_pattern(self, tmp_path):
        exchange = make_valid_exchange()
        exchange["timezone"] = "invalid_timezone_no_slash"
        path = write_temp_exchange(tmp_path, "TEST.json", exchange)

        schema = json.loads((Path(__file__).parent.parent / "schema.json").read_text())

        errors = validator.validate_schema(exchange, schema, path.name)
        assert len(errors) > 0

    def test_invalid_hours_format(self, tmp_path):
        exchange = make_valid_exchange()
        exchange["regular_hours"] = {"open": "9am", "close": "5pm"}
        path = write_temp_exchange(tmp_path, "TEST.json", exchange)

        schema = json.loads((Path(__file__).parent.parent / "schema.json").read_text())

        errors = validator.validate_schema(exchange, schema, path.name)
        assert len(errors) > 0


# ──────────────────────────────────────────────────────────────
# Business logic validation
# ──────────────────────────────────────────────────────────────

class TestBusinessLogic:
    def test_code_matches_filename(self):
        exchange = make_valid_exchange(code="XNYS", mic="XNYS")
        errors = validator.validate_business_logic(exchange, "XNYS.json")
        assert errors == []

    def test_code_mismatch_filename(self):
        exchange = make_valid_exchange(code="XNYS", mic="XNYS")
        errors = validator.validate_business_logic(exchange, "XLON.json")
        assert any("code" in e and "filename" in e for e in errors)

    def test_code_mismatch_mic(self):
        exchange = make_valid_exchange(code="XNYS", mic="XLON")
        errors = validator.validate_business_logic(exchange, "XNYS.json")
        assert any("code" in e and "mic" in e for e in errors)

    def test_regular_hours_open_after_close(self):
        exchange = make_valid_exchange()
        exchange["regular_hours"] = {"open": "17:00", "close": "09:00"}
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("open" in e and "close" in e for e in errors)

    def test_extended_hours_mismatch_regular_open(self):
        exchange = make_valid_exchange()
        exchange["extended_hours"] = {
            "pre_market": {"open": "04:00", "close": "10:00"},
        }
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("pre_market" in e for e in errors)

    def test_duplicate_explicit_dates(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-01-01",
            "name": "Duplicate",
            "status": "closed",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("Duplicate" in e for e in errors)

    def test_early_close_missing_time(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-12-24",
            "name": "Christmas Eve",
            "status": "early_close",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("early_close" in e for e in errors)

    def test_delayed_open_missing_time(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-01-02",
            "name": "Delayed Open",
            "status": "delayed_open",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("delayed_open" in e for e in errors)

    def test_unknown_rule_type(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["recurrence_rules"].append({
            "rule": "not_a_rule",
            "name": "Bogus",
            "status": "closed",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("Unknown rule type" in e for e in errors)

    def test_nth_weekday_missing_fields(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["recurrence_rules"].append({
            "rule": "nth_weekday",
            "name": "Incomplete",
            "status": "closed",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("nth_weekday" in e or "Incomplete" in e for e in errors)

    def test_invalid_month(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["recurrence_rules"].append({
            "rule": "fixed_date",
            "month": 13,
            "day": 1,
            "name": "Invalid Month",
            "status": "closed",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("month" in e for e in errors)

    def test_invalid_weekday(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["recurrence_rules"].append({
            "rule": "nth_weekday",
            "month": 1,
            "weekday": "funday",
            "n": 1,
            "name": "Invalid Weekday",
            "status": "closed",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("weekday" in e for e in errors)

    def test_ad_hoc_missing_source_url(self):
        exchange = make_valid_exchange()
        exchange["ad_hoc_closures"].append({
            "date": "2025-01-09",
            "name": "Unplanned Closure",
            "status": "closed",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("source_url" in e for e in errors)

    def test_ad_hoc_duplicates_explicit(self):
        exchange = make_valid_exchange()
        exchange["ad_hoc_closures"].append({
            "date": "2025-01-01",
            "name": "Duplicate",
            "status": "closed",
            "source_url": "https://example.com",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("duplicates explicit" in e for e in errors)

    def test_generation_range_invalid(self):
        exchange = make_valid_exchange()
        exchange["generation_range"] = ["2025-12-31", "2025-01-01"]
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("generation_range" in e for e in errors)

    def test_generation_range_single_date(self):
        exchange = make_valid_exchange()
        exchange["generation_range"] = ["2025-01-01"]
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("generation_range" in e for e in errors)

    def test_suspicious_timezone(self):
        exchange = make_valid_exchange()
        exchange["timezone"] = "NotAReal/Zone"
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("timezone" in e for e in errors)

    def test_lunch_break_open_after_close(self):
        exchange = make_valid_exchange()
        exchange["sessions"] = [
            {"type": "lunch_break", "open": "14:00", "close": "12:00"}
        ]
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("lunch_break" in e for e in errors)

    def test_duplicate_lunch_break(self):
        exchange = make_valid_exchange()
        exchange["sessions"] = [
            {"type": "lunch_break", "open": "12:00", "close": "13:00"},
            {"type": "lunch_break", "open": "12:00", "close": "13:00"},
        ]
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("Duplicate lunch_break" in e for e in errors)

    def test_duplicate_auction(self):
        exchange = make_valid_exchange()
        exchange["sessions"] = [
            {"type": "auction", "at": "09:00"},
            {"type": "auction", "at": "09:00"},
        ]
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("Duplicate auction" in e for e in errors)

    def test_malformed_date(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-13-45",
            "name": "Malformed",
            "status": "closed",
        })
        errors = validator.validate_business_logic(exchange, "TEST.json")
        assert any("Invalid month" in e or "Invalid day" in e for e in errors)


# ──────────────────────────────────────────────────────────────
# Cross-exchange validation
# ──────────────────────────────────────────────────────────────

class TestCrossExchange:
    def test_no_duplicates(self):
        exchanges = {
            "TEST1.json": make_valid_exchange("TEST1", "TEST1"),
            "TEST2.json": make_valid_exchange("TEST2", "TEST2"),
        }
        errors = validator.validate_cross_exchange(exchanges, list(exchanges.keys()))
        assert errors == []

    def test_duplicate_code(self):
        exchanges = {
            "TEST1.json": make_valid_exchange("SAME", "MIC1"),
            "TEST2.json": make_valid_exchange("SAME", "MIC2"),
        }
        errors = validator.validate_cross_exchange(exchanges, list(exchanges.keys()))
        assert any("Duplicate code" in e for e in errors)

    def test_duplicate_mic(self):
        exchanges = {
            "TEST1.json": make_valid_exchange("CODE1", "SAME"),
            "TEST2.json": make_valid_exchange("CODE2", "SAME"),
        }
        errors = validator.validate_cross_exchange(exchanges, list(exchanges.keys()))
        assert any("Duplicate mic" in e for e in errors)


# ──────────────────────────────────────────────────────────────
# Integration with real fixture files
# ──────────────────────────────────────────────────────────────

class TestWeekendDateCheck:
    """H1 check 1: no explicit holiday should fall on the exchange's
    own weekend days."""

    def test_clean_exchange_passes(self):
        exchange = make_valid_exchange()  # 2025-01-01 is a Wednesday
        errors = validator.check_weekend_dates(exchange, "TEST.json")
        assert errors == []

    def test_saturday_holiday_flagged_for_western_weekend(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-01-04",  # Saturday
            "name": "Bad Entry",
            "status": "closed",
        })
        errors = validator.check_weekend_dates(exchange, "TEST.json")
        assert any("2025-01-04" in e and "weekend" in e for e in errors)

    def test_friday_ok_for_islamic_weekend_but_not_western(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-01-03",  # Friday
            "name": "Friday Entry",
            "status": "closed",
        })
        # Western weekend (default [5, 6]): Friday is fine.
        errors = validator.check_weekend_dates(exchange, "TEST.json")
        assert errors == []

        # Islamic weekend ([4, 5]): the same Friday date is now a
        # weekend violation.
        exchange["weekend_days"] = [4, 5]
        errors = validator.check_weekend_dates(exchange, "TEST.json")
        assert any("2025-01-03" in e for e in errors)

    def test_missing_weekend_days_defaults_to_western(self):
        exchange = make_valid_exchange()
        del exchange["weekend_days"]
        exchange["holidays"]["explicit"].append({
            "date": "2025-01-04",  # Saturday
            "name": "Bad Entry",
            "status": "closed",
        })
        errors = validator.check_weekend_dates(exchange, "TEST.json")
        assert any("2025-01-04" in e for e in errors)

    def test_weekend_exception_flag_suppresses_the_check(self):
        """H3: a real, sourced, exchange-gazetted holiday that
        legitimately falls on the exchange's own weekend (e.g. NSE's
        Diwali Laxmi Pujan 2026, a Sunday) should not be flagged, if
        and only if explicitly marked weekend_exception."""
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-01-04",  # Saturday
            "name": "Gazetted Exception",
            "status": "closed",
            "weekend_exception": True,
        })
        errors = validator.check_weekend_dates(exchange, "TEST.json")
        assert errors == []

    def test_weekend_exception_false_still_flagged(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-01-04",  # Saturday
            "name": "Not Actually Excepted",
            "status": "closed",
            "weekend_exception": False,
        })
        errors = validator.check_weekend_dates(exchange, "TEST.json")
        assert any("2025-01-04" in e for e in errors)


class TestIslamicHolidayCompletenessCheck:
    """H1 check 2: Islamic-weekend (Friday/Saturday) exchanges should
    have both Eid al-Fitr and Eid al-Adha present. Regression coverage
    for C2/C3, which this check would have caught automatically."""

    def _islamic_exchange(self, explicit_extra=None):
        exchange = make_valid_exchange()
        exchange["weekend_days"] = [4, 5]
        if explicit_extra:
            exchange["holidays"]["explicit"].extend(explicit_extra)
        return exchange

    def test_western_weekend_exchange_not_checked(self):
        """A Western-weekend exchange has no Eid entries and should
        not be flagged -- the check only applies to [4, 5]."""
        exchange = make_valid_exchange()
        errors = validator.check_islamic_holidays(exchange, "TEST.json")
        assert errors == []

    def test_islamic_exchange_missing_both_eids(self):
        exchange = self._islamic_exchange()
        errors = validator.check_islamic_holidays(exchange, "TEST.json")
        assert any("Eid al-Fitr" in e for e in errors)
        assert any("Eid al-Adha" in e for e in errors)

    def test_islamic_exchange_missing_eid_al_adha_only(self):
        exchange = self._islamic_exchange([
            {"date": "2025-03-30", "name": "Eid al-Fitr (predicted)", "status": "closed"},
        ])
        errors = validator.check_islamic_holidays(exchange, "TEST.json")
        assert not any("Eid al-Fitr" in e for e in errors)
        assert any("Eid al-Adha" in e for e in errors)

    def test_islamic_exchange_with_both_eids_passes(self):
        exchange = self._islamic_exchange([
            {"date": "2025-03-30", "name": "Eid al-Fitr (predicted)", "status": "closed"},
            {"date": "2025-06-08", "name": "Eid al-Adha Holiday (predicted)", "status": "closed"},
        ])
        errors = validator.check_islamic_holidays(exchange, "TEST.json")
        assert errors == []

    def test_reversed_weekend_days_order_still_detected(self):
        """[5, 4] means the same weekend as [4, 5] and should not
        silently skip this check due to list-order sensitivity."""
        exchange = make_valid_exchange()
        exchange["weekend_days"] = [5, 4]
        errors = validator.check_islamic_holidays(exchange, "TEST.json")
        assert any("Eid al-Fitr" in e for e in errors)


class TestGenerationRangeCoverageCheck:
    """H1 check 3: explicit data should actually extend close to the
    end of the claimed generation_range. Regression coverage for C4,
    which this check would have caught automatically."""

    def test_data_covering_full_range_passes(self):
        exchange = make_valid_exchange()
        exchange["generation_range"] = ["2025-01-01", "2025-01-01"]
        errors = validator.check_generation_range(exchange, "TEST.json")
        assert errors == []

    def test_small_gap_under_90_days_tolerated(self):
        exchange = make_valid_exchange()
        exchange["generation_range"] = ["2025-01-01", "2025-03-01"]
        errors = validator.check_generation_range(exchange, "TEST.json")
        assert errors == []

    def test_large_gap_over_90_days_flagged(self):
        exchange = make_valid_exchange()
        exchange["generation_range"] = ["2025-01-01", "2029-12-31"]
        errors = validator.check_generation_range(exchange, "TEST.json")
        assert any("gap" in e and "2029-12-31" in e for e in errors)

    def test_no_explicit_dates_skipped(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"] = []
        exchange["generation_range"] = ["2025-01-01", "2029-12-31"]
        errors = validator.check_generation_range(exchange, "TEST.json")
        assert errors == []


class TestPredictedConsistencyCheck:
    """M6: the structured `predicted` field and legacy '(predicted)'
    name suffix should not contradict each other."""

    def test_no_predicted_field_skipped(self):
        """Absence of the field is not an error -- most existing
        entries don't have it yet (backward compatibility)."""
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-06-01", "name": "Eid al-Fitr (predicted)", "status": "closed",
        })
        errors = validator.check_predicted_consistency(exchange, "TEST.json")
        assert errors == []

    def test_predicted_true_with_suffix_passes(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-06-01", "name": "Eid al-Fitr (predicted)", "status": "closed", "predicted": True,
        })
        errors = validator.check_predicted_consistency(exchange, "TEST.json")
        assert errors == []

    def test_predicted_false_without_suffix_passes(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-06-01", "name": "Eid al-Fitr", "status": "closed", "predicted": False,
        })
        errors = validator.check_predicted_consistency(exchange, "TEST.json")
        assert errors == []

    def test_predicted_true_without_suffix_flagged(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-06-01", "name": "Eid al-Fitr", "status": "closed", "predicted": True,
        })
        errors = validator.check_predicted_consistency(exchange, "TEST.json")
        assert any("2025-06-01" in e for e in errors)

    def test_predicted_false_with_suffix_flagged(self):
        exchange = make_valid_exchange()
        exchange["holidays"]["explicit"].append({
            "date": "2025-06-01", "name": "Eid al-Fitr (predicted)", "status": "closed", "predicted": False,
        })
        errors = validator.check_predicted_consistency(exchange, "TEST.json")
        assert any("2025-06-01" in e for e in errors)


# ──────────────────────────────────────────────────────────────

class TestFixtures:
    def test_valid_exchange_fixture(self):
        fixture_path = Path(__file__).parent / "fixtures" / "valid_exchange.json"
        with open(fixture_path) as f:
            exchange = json.load(f)

        schema_path = Path(__file__).parent.parent / "schema.json"
        with open(schema_path) as f:
            schema = json.load(f)

        errors = validator.validate_schema(exchange, schema, fixture_path.name)
        assert errors == []

    def test_invalid_bad_timezone_fixture(self):
        fixture_path = Path(__file__).parent / "fixtures" / "invalid_bad_timezone.json"
        with open(fixture_path) as f:
            exchange = json.load(f)

        schema_path = Path(__file__).parent.parent / "schema.json"
        with open(schema_path) as f:
            schema = json.load(f)

        errors = validator.validate_schema(exchange, schema, fixture_path.name)
        assert len(errors) > 0

    def test_invalid_duplicate_dates_fixture(self):
        fixture_path = Path(__file__).parent / "fixtures" / "invalid_duplicate_dates.json"
        with open(fixture_path) as f:
            exchange = json.load(f)

        schema_path = Path(__file__).parent.parent / "schema.json"
        with open(schema_path) as f:
            schema = json.load(f)

        errors = validator.validate_schema(exchange, schema, fixture_path.name)
        errors.extend(validator.validate_business_logic(exchange, fixture_path.name))
        assert len(errors) > 0

    def test_invalid_missing_hours_fixture(self):
        fixture_path = Path(__file__).parent / "fixtures" / "invalid_missing_hours.json"
        with open(fixture_path) as f:
            exchange = json.load(f)

        schema_path = Path(__file__).parent.parent / "schema.json"
        with open(schema_path) as f:
            schema = json.load(f)

        errors = validator.validate_schema(exchange, schema, fixture_path.name)
        assert len(errors) > 0


# ──────────────────────────────────────────────────────────────
# Real exchange files
# ──────────────────────────────────────────────────────────────

class TestRealExchanges:
    def test_xnys_valid(self):
        """XNYS.json passes validation with zero errors."""
        exchange_path = Path(__file__).parent.parent / "exchanges" / "XNYS.json"
        with open(exchange_path) as f:
            exchange = json.load(f)

        schema_path = Path(__file__).parent.parent / "schema.json"
        with open(schema_path) as f:
            schema = json.load(f)

        errors = validator.validate_schema(exchange, schema, "XNYS.json")
        errors.extend(validator.validate_business_logic(exchange, "XNYS.json"))
        assert errors == []

    def test_xlon_valid(self):
        """XLON.json passes validation with zero errors."""
        exchange_path = Path(__file__).parent.parent / "exchanges" / "XLON.json"
        with open(exchange_path) as f:
            exchange = json.load(f)

        schema_path = Path(__file__).parent.parent / "schema.json"
        with open(schema_path) as f:
            schema = json.load(f)

        errors = validator.validate_schema(exchange, schema, "XLON.json")
        errors.extend(validator.validate_business_logic(exchange, "XLON.json"))
        assert errors == []


# ──────────────────────────────────────────────────────────────
# Fixture file creation (run once to generate fixtures if missing)
# ──────────────────────────────────────────────────────────────

def create_fixtures_if_missing():
    """Create fixture files if they don't exist. Run manually, not as a test."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    fixtures = {
        "valid_exchange.json": make_valid_exchange("TEST", "TEST"),
        "invalid_bad_timezone.json": {
            **make_valid_exchange("TEST", "TEST"),
            "timezone": "invalid_timezone_no_slash",
        },
        "invalid_duplicate_dates.json": {
            **make_valid_exchange("TEST", "TEST"),
            "holidays": {
                "explicit": [
                    {
                        "date": "2025-01-01",
                        "name": "New Year's Day",
                        "status": "closed",
                    },
                    {
                        "date": "2025-01-01",
                        "name": "Duplicate",
                        "status": "closed",
                    },
                ],
                "recurrence_rules": [],
            },
        },
        "invalid_missing_hours.json": {
            **make_valid_exchange("TEST", "TEST"),
            "regular_hours": {},
        },
    }

    for filename, data in fixtures.items():
        path = fixtures_dir / filename
        if not path.exists():
            with open(path, "w") as f:
                json.dump(data, f, indent=2)


if __name__ == "__main__":
    create_fixtures_if_missing()
    print("Fixtures ensured.")