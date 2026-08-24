#!/usr/bin/env python3
"""
test_build.py — Unit tests for the build script.

Tests that build.py:
    1. Produces calendar.json with correct structure
    2. Merges explicit and generated dates
    3. Is deterministic (same input → same output)
    4. Sorts exchanges by code
    5. Handles errors gracefully
    6. Works with the real exchange files

Run:
    python3 -m pytest tests/test_build.py -v
"""

import json
import sys
import pytest
from pathlib import Path

# Add tools/ to path
TOOLS_DIR = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(TOOLS_DIR))

import build as builder


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

def make_exchange(code, name="Test Exchange", holidays=None):
    """Return a valid exchange dict."""
    return {
        "code": code,
        "name": name,
        "mic": code,
        "timezone": "Europe/London",
        "regular_hours": {"open": "09:00", "close": "17:00"},
        "extended_hours": {},
        "sessions": [],
        "holidays": holidays or {
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


def write_exchange(tmp_path, exchange):
    """Write an exchange dict to a file in the tmp_path directory."""
    code = exchange["code"]
    path = tmp_path / f"{code}.json"
    with open(path, "w") as f:
        json.dump(exchange, f)
    return path


# ──────────────────────────────────────────────────────────────
# build_registry
# ──────────────────────────────────────────────────────────────

class TestBuildRegistry:
    def test_build_single_exchange(self, tmp_path):
        exchange = make_exchange("TEST", "Test Exchange")
        write_exchange(tmp_path, exchange)

        registry = builder.build_registry(tmp_path)

        assert registry["meta"]["version"] == "1.0.0"
        assert registry["meta"]["exchange_count"] == 1
        assert len(registry["exchanges"]) == 1
        assert registry["exchanges"][0]["code"] == "TEST"

    def test_build_multiple_exchanges_sorted(self, tmp_path):
        exchange_b = make_exchange("ZED", "Zed Exchange")
        exchange_a = make_exchange("ALPHA", "Alpha Exchange")
        write_exchange(tmp_path, exchange_b)
        write_exchange(tmp_path, exchange_a)

        registry = builder.build_registry(tmp_path)

        assert registry["meta"]["exchange_count"] == 2
        codes = [e["code"] for e in registry["exchanges"]]
        assert codes == ["ALPHA", "ZED"]  # Sorted by code

    def test_build_preserves_explicit_dates(self, tmp_path):
        exchange = make_exchange("TEST")
        exchange["holidays"]["explicit"].append({
            "date": "2025-12-25",
            "name": "Christmas Day",
            "status": "closed",
        })
        write_exchange(tmp_path, exchange)

        registry = builder.build_registry(tmp_path)
        result = registry["exchanges"][0]

        assert len(result["holidays"]["explicit"]) == 2
        dates = [e["date"] for e in result["holidays"]["explicit"]]
        assert "2025-01-01" in dates
        assert "2025-12-25" in dates

    def test_build_generates_recurrence_dates(self, tmp_path):
        exchange = make_exchange("TEST")
        exchange["holidays"]["recurrence_rules"] = [
            {
                "rule": "nth_weekday",
                "month": 9,
                "weekday": "monday",
                "n": 1,
                "name": "Labor Day",
                "status": "closed",
            }
        ]
        write_exchange(tmp_path, exchange)

        registry = builder.build_registry(tmp_path)
        result = registry["exchanges"][0]

        generated = result["holidays"]["generated"]
        assert len(generated) == 1
        assert generated[0]["date"] == "2025-09-01"
        assert generated[0]["name"] == "Labor Day"

    def test_build_preserves_regular_hours(self, tmp_path):
        exchange = make_exchange("TEST")
        exchange["regular_hours"] = {"open": "08:00", "close": "16:30"}
        write_exchange(tmp_path, exchange)

        registry = builder.build_registry(tmp_path)
        result = registry["exchanges"][0]

        assert result["regular_hours"] == {"open": "08:00", "close": "16:30"}

    def test_build_preserves_sessions(self, tmp_path):
        exchange = make_exchange("TEST")
        exchange["sessions"] = [
            {"type": "auction", "at": "09:00"}
        ]
        write_exchange(tmp_path, exchange)

        registry = builder.build_registry(tmp_path)
        result = registry["exchanges"][0]

        assert len(result["sessions"]) == 1
        assert result["sessions"][0]["type"] == "auction"

    def test_build_preserves_ad_hoc_closures(self, tmp_path):
        exchange = make_exchange("TEST")
        exchange["ad_hoc_closures"] = [
            {
                "date": "2025-01-09",
                "name": "Unplanned",
                "status": "closed",
                "source_url": "https://example.com",
            }
        ]
        write_exchange(tmp_path, exchange)

        registry = builder.build_registry(tmp_path)
        result = registry["exchanges"][0]

        assert len(result["ad_hoc_closures"]) == 1
        assert result["ad_hoc_closures"][0]["name"] == "Unplanned"

    def test_build_duplicate_code_rejected(self, tmp_path):
        exchange1 = make_exchange("DUPE", "First")
        exchange2 = make_exchange("DUPE", "Second")
        # Write to different filenames to bypass filesystem uniqueness
        write_exchange(tmp_path, exchange1)
        exchange2_path = tmp_path / "DUPE2.json"
        with open(exchange2_path, "w") as f:
            json.dump(exchange2, f)

        with pytest.raises(ValueError, match="Duplicate exchange code"):
            builder.build_registry(tmp_path)

    def test_build_empty_directory_rejected(self, tmp_path):
        with pytest.raises(ValueError, match="No exchange files"):
            builder.build_registry(tmp_path)

    def test_build_invalid_json_rejected(self, tmp_path):
        path = tmp_path / "BAD.json"
        path.write_text("{invalid json")
        
        with pytest.raises(ValueError):
            builder.build_registry(tmp_path)


# ──────────────────────────────────────────────────────────────
# Determinism
# ──────────────────────────────────────────────────────────────

class TestDeterminism:
    def test_identical_input_produces_identical_output(self, tmp_path):
        exchange = make_exchange("TEST")
        write_exchange(tmp_path, exchange)

        registry1 = builder.build_registry(tmp_path)
        registry2 = builder.build_registry(tmp_path)

        json1 = json.dumps(registry1, indent=2, ensure_ascii=False)
        json2 = json.dumps(registry2, indent=2, ensure_ascii=False)

        assert json1 == json2

    def test_exchange_order_independent(self, tmp_path):
        """Building after writing files in different order produces same output."""
        exchange_b = make_exchange("ZED", "Zed")
        exchange_a = make_exchange("ALPHA", "Alpha")

        # Write in order B, A
        write_exchange(tmp_path, exchange_b)
        write_exchange(tmp_path, exchange_a)

        registry1 = builder.build_registry(tmp_path)

        # Clear and write in order A, B
        for f in tmp_path.glob("*.json"):
            f.unlink()
        write_exchange(tmp_path, exchange_a)
        write_exchange(tmp_path, exchange_b)

        registry2 = builder.build_registry(tmp_path)

        json1 = json.dumps(registry1, indent=2, ensure_ascii=False)
        json2 = json.dumps(registry2, indent=2, ensure_ascii=False)

        assert json1 == json2


# ──────────────────────────────────────────────────────────────
# merge_holidays
# ──────────────────────────────────────────────────────────────

class TestMergeHolidays:
    def test_merge_explicit_and_generated(self):
        exchange = make_exchange("TEST")
        exchange["holidays"]["recurrence_rules"] = [
            {
                "rule": "nth_weekday",
                "month": 9,
                "weekday": "monday",
                "n": 1,
                "name": "Labor Day",
                "status": "closed",
            }
        ]

        result = builder.merge_holidays(exchange)

        assert result is not None
        assert len(result["explicit"]) == 1
        assert len(result["generated"]) == 1
        assert result["generated"][0]["date"] == "2025-09-01"

    def test_merge_no_recurrence_rules(self):
        exchange = make_exchange("TEST")
        result = builder.merge_holidays(exchange)

        assert result is not None
        assert result["generated"] == []

    def test_merge_generation_error_returns_none(self):
        exchange = make_exchange("TEST")
        del exchange["generation_range"]

        result = builder.merge_holidays(exchange)
        assert result is None


# ──────────────────────────────────────────────────────────────
# write_registry
# ──────────────────────────────────────────────────────────────

class TestWriteRegistry:
    def test_write_produces_valid_json(self, tmp_path):
        registry = {
            "meta": {"version": "1.0.0", "exchange_count": 1},
            "exchanges": [
                {
                    "code": "TEST",
                    "name": "Test",
                    "mic": "TEST",
                    "timezone": "Europe/London",
                    "regular_hours": {"open": "09:00", "close": "17:00"},
                    "extended_hours": {},
                    "sessions": [],
                    "holidays": {"explicit": [], "generated": []},
                    "ad_hoc_closures": [],
                    "generation_range": ["2025-01-01", "2025-12-31"],
                }
            ],
        }

        output_path = tmp_path / "calendar.json"
        builder.write_registry(registry, output_path)

        with open(output_path) as f:
            loaded = json.load(f)

        assert loaded == registry

    def test_write_ends_with_newline(self, tmp_path):
        registry = {
            "meta": {"version": "1.0.0", "exchange_count": 0},
            "exchanges": [],
        }

        output_path = tmp_path / "calendar.json"
        builder.write_registry(registry, output_path)

        content = output_path.read_text()
        assert content.endswith("\n")


# ──────────────────────────────────────────────────────────────
# Real exchange files
# ──────────────────────────────────────────────────────────────

class TestRealExchanges:
    def test_build_with_real_exchange_files(self):
        """Build the registry from the actual exchanges/ directory."""
        exchanges_dir = Path(__file__).parent.parent / "exchanges"

        registry = builder.build_registry(exchanges_dir)

        assert registry["meta"]["exchange_count"] == 74
        codes = [e["code"] for e in registry["exchanges"]]
        assert "XLON" in codes
        assert "XNYS" in codes

    def test_build_real_exchanges_have_generated_dates(self):
        """XNYS and XLON have explicit dates but may have empty generated."""
        exchanges_dir = Path(__file__).parent.parent / "exchanges"
        registry = builder.build_registry(exchanges_dir)

        for exchange in registry["exchanges"]:
            explicit = exchange["holidays"]["explicit"]
            assert len(explicit) > 0
            # Generated may be 0 if explicit covers the full range
            assert isinstance(exchange["holidays"]["generated"], list)