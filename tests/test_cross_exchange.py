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
        """Most exchanges share a similar generation range, but a small
        number of lunar/lunisolar-calendar exchanges (XBKK, XCOL, XMOS,
        XSHE, XSTC) intentionally have shorter ranges reflecting actual
        researched data coverage, since the recurrence-rule engine
        doesn't support lunar/lunisolar holidays (see C4). Allow up to
        a 4-year spread rather than 2 to accommodate that gap without
        masking a genuinely wrong far-outlier."""
        if len(exchange_list) < 2:
            pytest.skip("Need at least 2 exchanges to compare ranges")

        start_years = [int(e["generation_range"][0][:4]) for e in exchange_list]
        end_years = [int(e["generation_range"][1][:4]) for e in exchange_list]

        assert max(start_years) - min(start_years) <= 2, "Start years differ by more than 2"
        assert max(end_years) - min(end_years) <= 4, "End years differ by more than 4"


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

# ──────────────────────────────────────────────────────────────
# Islamic holiday date divergence (C6)
# ──────────────────────────────────────────────────────────────

class TestIslamicDateDivergence:
    """Regression coverage for C6: all 6 Islamic-weekend exchanges with
    Islamic holidays previously had byte-for-byte identical dates,
    which is what let the wrapper's uniform-Saudi-date generation go
    undetected. Egypt (XCAI) and Oman (XMUS) use their own
    moon-sighting committees and can legitimately diverge from Saudi
    (and from each other) by +/-1 day. This does NOT mean they must
    always diverge -- Eid al-Adha 2025 actually matched Saudi's date
    for both countries, confirmed independently -- so these tests
    check for the specific, sourced divergence that exists, not for
    divergence in general."""

    ISLAMIC_EXCHANGES = ("XBAH", "XCAI", "XDFM", "XKUW", "XMUS", "XQSE", "XSAU", "XTAD")

    def _islamic_dates(self, all_exchanges, code):
        """Identify Islamic-calendar holiday entries by name keyword,
        NOT by the '(predicted)' suffix -- that conflates "is this an
        Islamic holiday" with "is this still unconfirmed", and breaks
        the moment an entry gets reconciled (M7) and loses the
        suffix. Use the structured `predicted` field or the legacy
        suffix separately if you specifically need confirmed-vs-
        pending status."""
        data = all_exchanges[f"{code}.json"]
        keywords = ("Eid al-Fitr", "Eid al-Adha", "Islamic New Year", "Prophet's Birthday", "Ashura")
        return {
            h["date"] for h in data["holidays"]["explicit"]
            if any(k in h["name"] for k in keywords)
        }

    def test_islamic_dates_not_assumed_uniform(self, all_exchanges):
        """The 6+ Islamic-holiday-bearing exchanges should not all be
        byte-for-byte identical -- that was the C6 bug. At least one
        pair should differ, since XCAI/XMUS's 2025 Eid al-Fitr dates
        are now confirmed to differ from XSAU/XBAH/XKUW/XQSE/XTAD."""
        present = [c for c in self.ISLAMIC_EXCHANGES if f"{c}.json" in all_exchanges]
        date_sets = {c: self._islamic_dates(all_exchanges, c) for c in present}

        distinct_sets = {frozenset(s) for s in date_sets.values() if s}
        assert len(distinct_sets) > 1, (
            "All Islamic-holiday exchanges have identical date sets -- "
            "this is the exact uniform-Saudi-date bug C6 fixed"
        )

    def test_xcai_xmus_eid_al_fitr_2025_diverges_from_saudi(self, all_exchanges):
        """Confirmed via Dar al-Ifta / MERA: Egypt and Oman's Eid
        al-Fitr 2025 fell on 2025-03-31, one day after Saudi's
        2025-03-30 (Umm al-Qura). M7: both dates are now reconciled
        (predicted=false, no '(predicted)' suffix)."""
        if "XSAU.json" not in all_exchanges:
            pytest.skip("XSAU required")
        xsau_dates = self._islamic_dates(all_exchanges, "XSAU")
        assert "2025-03-30" in xsau_dates

        for code in ("XCAI", "XMUS"):
            if f"{code}.json" not in all_exchanges:
                continue
            dates = self._islamic_dates(all_exchanges, code)
            assert "2025-03-31" in dates, f"{code} should have Eid al-Fitr on 2025-03-31"
            assert "2025-03-30" not in dates, f"{code} should NOT have the Saudi-only 2025-03-30 date"

    def test_xcai_xmus_eid_al_adha_2025_matches_saudi(self, all_exchanges):
        """Confirmed via Ahram Online / Gulf News: unlike Eid al-Fitr,
        Egypt and Oman's Eid al-Adha 2025 DID match Saudi's date
        (civil day 1 = 2025-06-06, a Friday). Divergence is not
        automatic or uniform -- this guards against 'fixing' C6 by
        blindly shifting every Islamic date by a day, which would have
        broken this case.

        XCAI, XMUS, and XSAU all observe a Friday/Saturday weekend, so
        2025-06-06 (Friday) itself is correctly absent from `explicit`
        (weekend already covers it, per the C2 convention) -- what
        should match across all three is the first surviving day,
        2025-06-08 (Sunday), carrying the 'Holiday' suffix rather than
        the bare name since civil day 1 was dropped for the weekend."""
        for code in ("XCAI", "XMUS", "XSAU"):
            if f"{code}.json" not in all_exchanges:
                continue
            dates = self._islamic_dates(all_exchanges, code)
            assert "2025-06-06" not in dates, f"{code}: Friday should be excluded (weekend)"
            assert "2025-06-08" in dates, f"{code} should have Eid al-Adha on 2025-06-08 (first non-weekend day)"

    def test_xbah_xqse_xkuw_follow_saudi_2025(self, all_exchanges):
        """Confirmed via Gulf News: Bahrain, Qatar, and Kuwait all
        announced Eid al-Fitr 2025 for 2025-03-30, matching Saudi --
        unlike Egypt and Oman. These 3 should NOT be changed.

        XTAD is deliberately excluded here (unlike the original
        version of this test): 2025-03-30 is a Sunday, XTAD's own
        weekend day, so it's correctly absent from XTAD's explicit
        data regardless of whether UAE's civil announcement matched
        Saudi -- the weekend exclusion and the moon-sighting
        divergence question are two independent things, and this
        test previously conflated them for XTAD specifically."""
        for code in ("XBAH", "XQSE", "XKUW"):
            if f"{code}.json" not in all_exchanges:
                continue
            dates = self._islamic_dates(all_exchanges, code)
            assert "2025-03-30" in dates, f"{code} should have Eid al-Fitr on 2025-03-30 (matches Saudi)"
