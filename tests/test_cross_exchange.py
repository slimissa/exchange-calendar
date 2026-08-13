#!/usr/bin/env python3
"""
test_cross_exchange.py — Cross-exchange consistency tests.

Verifies that all exchanges in the registry are consistent with each other:
    - No duplicate MIC codes
    - No duplicate exchange codes
    - Codes match filenames
    - All exchanges have valid structure
    - No overlapping holidays with conflicting statuses

Run:
    python3 -m pytest tests/test_cross_exchange.py -v
"""

import json
import sys
import pytest
from pathlib import Path


EXCHANGES_DIR = Path(__file__).parent.parent / "exchanges"


# ──────────────────────────────────────────────────────────────
# Load all exchanges
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def all_exchanges():
    """Load all exchange files from the exchanges directory."""
    exchanges = {}
    for path in sorted(EXCHANGES_DIR.glob("*.json")):
        with open(path) as f:
            exchanges[path.name] = json.load(f)
    return exchanges


@pytest.fixture(scope="module")
def exchange_list(all_exchanges):
    """Return a list of exchange dicts."""
    return list(all_exchanges.values())


@pytest.fixture(scope="module")
def codes_by_filename(all_exchanges):
    """Return dict of filename -> code."""
    return {
        filename: exchange["code"]
        for filename, exchange in all_exchanges.items()
    }


@pytest.fixture(scope="module")
def mics_by_filename(all_exchanges):
    """Return dict of filename -> mic."""
    return {
        filename: exchange["mic"]
        for filename, exchange in all_exchanges.items()
    }


# ──────────────────────────────────────────────────────────────
# Duplicate detection
# ──────────────────────────────────────────────────────────────

class TestDuplicates:
    def test_no_duplicate_codes(self, exchange_list):
        """No two exchanges may share the same code."""
        codes = [e["code"] for e in exchange_list]
        assert len(codes) == len(set(codes)), f"Duplicate codes: {[c for c in codes if codes.count(c) > 1]}"

    def test_no_duplicate_mics(self, exchange_list):
        """No two exchanges may share the same MIC."""
        mics = [e["mic"] for e in exchange_list]
        assert len(mics) == len(set(mics)), f"Duplicate MICs: {[m for m in mics if mics.count(m) > 1]}"

    def test_code_equals_mic(self, exchange_list):
        """Every exchange's code must equal its MIC."""
        for exchange in exchange_list:
            assert exchange["code"] == exchange["mic"], \
                f"{exchange['code']}: code '{exchange['code']}' != mic '{exchange['mic']}'"


# ──────────────────────────────────────────────────────────────
# Filename matching
# ──────────────────────────────────────────────────────────────

class TestFilenames:
    def test_code_matches_filename(self, codes_by_filename):
        """Every exchange's code must match its filename (without .json)."""
        for filename, code in codes_by_filename.items():
            expected = filename.replace(".json", "")
            assert code == expected, f"{filename}: code '{code}' != expected '{expected}'"

    def test_filenames_are_uppercase(self, all_exchanges):
        """All exchange filenames must be uppercase."""
        for filename in all_exchanges:
            stem = filename.replace(".json", "")
            assert stem == stem.upper(), f"Filename not uppercase: {filename}"

    def test_filenames_are_valid_mic_format(self, all_exchanges):
        """All exchange filenames must match MIC pattern (4 uppercase alphanumeric)."""
        import re
        for filename in all_exchanges:
            stem = filename.replace(".json", "")
            assert re.match(r"^[A-Z0-9]{4}$", stem), f"Invalid MIC filename: {filename}"


# ──────────────────────────────────────────────────────────────
# Structural consistency
# ──────────────────────────────────────────────────────────────

class TestStructure:
    def test_all_have_required_fields(self, exchange_list):
        """Every exchange has all required top-level fields."""
        required = ["code", "name", "mic", "timezone", "regular_hours", "holidays", "generation_range"]
        for exchange in exchange_list:
            for field in required:
                assert field in exchange, f"{exchange.get('code', '?')}: missing {field}"

    def test_all_have_regular_hours(self, exchange_list):
        """Every exchange has regular_hours with open and close."""
        for exchange in exchange_list:
            assert "open" in exchange["regular_hours"], f"{exchange['code']}: missing regular_hours.open"
            assert "close" in exchange["regular_hours"], f"{exchange['code']}: missing regular_hours.close"

    def test_all_have_explicit_holidays(self, exchange_list):
        """Every exchange has at least one explicit holiday."""
        for exchange in exchange_list:
            explicit = exchange["holidays"].get("explicit", [])
            assert len(explicit) > 0, f"{exchange['code']}: no explicit holidays"

    def test_all_have_generation_range(self, exchange_list):
        """Every exchange has a generation_range with exactly 2 dates."""
        for exchange in exchange_list:
            gen_range = exchange.get("generation_range", [])
            assert len(gen_range) == 2, f"{exchange['code']}: generation_range must have 2 dates"

    def test_generation_ranges_are_similar(self, exchange_list):
        """All exchanges have similar generation ranges (within 10 years)."""
        if len(exchange_list) < 2:
            pytest.skip("Need at least 2 exchanges to compare ranges")

        start_years = [int(e["generation_range"][0][:4]) for e in exchange_list]
        end_years = [int(e["generation_range"][1][:4]) for e in exchange_list]

        assert max(start_years) - min(start_years) <= 2, "Start years differ by more than 2"
        assert max(end_years) - min(end_years) <= 2, "End years differ by more than 2"


# ──────────────────────────────────────────────────────────────
# Timezone diversity
# ──────────────────────────────────────────────────────────────

class TestTimezones:
    def test_all_have_valid_timezone_format(self, exchange_list):
        """Every timezone has a slash (IANA format)."""
        for exchange in exchange_list:
            tz = exchange["timezone"]
            assert "/" in tz, f"{exchange['code']}: timezone '{tz}' has no slash"

    def test_different_exchanges_can_have_different_timezones(self, exchange_list):
        """If there are multiple exchanges, they may have different timezones."""
        if len(exchange_list) < 2:
            pytest.skip("Need at least 2 exchanges")

        timezones = {e["timezone"] for e in exchange_list}
        # Not all exchanges must have the same timezone
        assert len(timezones) >= 1

    def test_known_timezones(self, exchange_list):
        """Verify specific known timezones."""
        timezone_by_code = {e["code"]: e["timezone"] for e in exchange_list}

        if "XNYS" in timezone_by_code:
            assert timezone_by_code["XNYS"] == "America/New_York"
        if "XLON" in timezone_by_code:
            assert timezone_by_code["XLON"] == "Europe/London"


# ──────────────────────────────────────────────────────────────
# Holiday overlap
# ──────────────────────────────────────────────────────────────

class TestHolidayOverlap:
    def test_no_conflicting_status_on_same_date(self, all_exchanges):
        """If two exchanges have the same date, they should not conflict."""
        # Build date -> list of (exchange, status)
        date_statuses = {}

        for filename, exchange in all_exchanges.items():
            code = exchange["code"]
            for entry in exchange["holidays"].get("explicit", []):
                date_str = entry["date"]
                status = entry["status"]
                if date_str not in date_statuses:
                    date_statuses[date_str] = []
                date_statuses[date_str].append((code, status))

        # Check no date has both 'closed' and 'early_close' for the same exchange
        # (This is already tested per-exchange, but verify cross-exchange isn't confused)
        for date_str, statuses in date_statuses.items():
            codes = {code for code, _ in statuses}
            if len(codes) > 1:
                # Same date, multiple exchanges — each should have exactly one status per exchange
                for code in codes:
                    code_statuses = [s for c, s in statuses if c == code]
                    assert len(code_statuses) == 1, \
                        f"{code}: {date_str} has {len(code_statuses)} statuses: {code_statuses}"

    def test_shared_holidays_between_xnys_and_xlon(self, all_exchanges):
        """XNYS and XLON share New Year's Day and Christmas Day."""
        if "XNYS.json" not in all_exchanges or "XLON.json" not in all_exchanges:
            pytest.skip("Both XNYS and XLON required")

        xnys_dates = {e["date"] for e in all_exchanges["XNYS.json"]["holidays"]["explicit"]}
        xlon_dates = {e["date"] for e in all_exchanges["XLON.json"]["holidays"]["explicit"]}

        shared = xnys_dates & xlon_dates

        # At minimum, they share: New Year's Day, Good Friday, Christmas Day
        assert "2025-01-01" in shared
        assert "2025-04-18" in shared  # Good Friday
        assert "2025-12-25" in shared  # Christmas Day

    def test_us_only_holidays_not_in_xlon(self, all_exchanges):
        """XNYS has US-only holidays that XLON does not."""
        if "XNYS.json" not in all_exchanges or "XLON.json" not in all_exchanges:
            pytest.skip("Both XNYS and XLON required")

        xlon_dates = {e["date"] for e in all_exchanges["XLON.json"]["holidays"]["explicit"]}

        # Juneteenth, MLK Day, Presidents Day, Thanksgiving are US-only
        xnys = all_exchanges["XNYS.json"]
        for entry in xnys["holidays"]["explicit"]:
            if "Juneteenth" in entry["name"] or "Martin Luther King" in entry["name"] or \
               "Presidents" in entry["name"] or "Thanksgiving" in entry["name"]:
                assert entry["date"] not in xlon_dates, \
                    f"US-only holiday {entry['name']} ({entry['date']}) should not be in XLON"

    def test_uk_only_holiday_names_not_in_xnys(self, all_exchanges):
        """XLON has UK-only holiday names that XNYS does not use."""
        if "XNYS.json" not in all_exchanges or "XLON.json" not in all_exchanges:
            pytest.skip("Both XNYS and XLON required")

        xnys_names = {e["name"] for e in all_exchanges["XNYS.json"]["holidays"]["explicit"]}

        # Bank Holidays, Boxing Day, Easter Monday are UK-specific names
        xlon = all_exchanges["XLON.json"]
        for entry in xlon["holidays"]["explicit"]:
            if "Bank Holiday" in entry["name"] or "Boxing" in entry["name"] or "Easter Monday" in entry["name"]:
                assert entry["name"] not in xnys_names, \
                    f"UK-only holiday name '{entry['name']}' should not be in XNYS"