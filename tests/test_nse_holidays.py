#!/usr/bin/env python3
"""
test_nse_holidays.py — Ground truth tests for XNSE (National Stock Exchange of India).

NSE and BSE share the identical holiday calendar (both in Mumbai, India).
These tests verify that XNSE has the same holidays as XBOM.

Run:
    python3 -m pytest tests/test_nse_holidays.py -v
"""

import json
import pytest
from datetime import date
from pathlib import Path


@pytest.fixture(scope="module")
def xnse():
    path = Path(__file__).parent.parent / "exchanges" / "XNSE.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def xbom():
    path = Path(__file__).parent.parent / "exchanges" / "XBOM.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def explicit_dates(xnse):
    return {e["date"]: e for e in xnse["holidays"]["explicit"]}


class TestXNSEProperties:
    def test_code(self, xnse):
        assert xnse["code"] == "XNSE"

    def test_mic(self, xnse):
        assert xnse["mic"] == "XNSE"

    def test_name(self, xnse):
        assert xnse["name"] == "National Stock Exchange of India"

    def test_timezone(self, xnse):
        assert xnse["timezone"] == "Asia/Kolkata"

    def test_regular_hours(self, xnse):
        assert xnse["regular_hours"]["open"] == "09:15"
        assert xnse["regular_hours"]["close"] == "15:30"

    def test_no_lunch_break(self, xnse):
        lunch = [s for s in xnse.get("sessions", []) if s["type"] == "lunch_break"]
        assert lunch == []


class TestXNSEMatchesXBOM:
    def test_same_explicit_dates(self, xnse, xbom):
        xnse_dates = {e["date"] for e in xnse["holidays"]["explicit"]}
        xbom_dates = {e["date"] for e in xbom["holidays"]["explicit"]}
        assert xnse_dates == xbom_dates

    def test_same_statuses(self, xnse, xbom):
        xnse_status = {e["date"]: e["status"] for e in xnse["holidays"]["explicit"]}
        xbom_status = {e["date"]: e["status"] for e in xbom["holidays"]["explicit"]}
        assert xnse_status == xbom_status

    def test_same_holiday_count(self, xnse, xbom):
        assert len(xnse["holidays"]["explicit"]) == len(xbom["holidays"]["explicit"])

    def test_same_recurrence_rules(self, xnse, xbom):
        xnse_rules = xnse["holidays"].get("recurrence_rules", [])
        xbom_rules = xbom["holidays"].get("recurrence_rules", [])
        assert len(xnse_rules) == len(xbom_rules)


class TestXNSEKeyHolidays:
    def test_republic_day_2026(self, explicit_dates):
        assert "2026-01-26" in explicit_dates

    def test_diwali_2025(self, explicit_dates):
        assert "2025-10-21" in explicit_dates
        assert "2025-10-22" in explicit_dates

    def test_holi_2025(self, explicit_dates):
        assert "2025-03-14" in explicit_dates

    def test_good_friday_2025(self, explicit_dates):
        assert "2025-04-18" in explicit_dates

    def test_independence_day_2025(self, explicit_dates):
        assert "2025-08-15" in explicit_dates


class TestXNSEStructure:
    def test_no_weekend_dates(self, explicit_dates):
        for date_str in explicit_dates:
            d = date.fromisoformat(date_str)
            assert d.weekday() < 5

    def test_no_duplicates(self, explicit_dates):
        dates = list(explicit_dates.keys())
        assert len(dates) == len(set(dates))

    def test_all_entries_have_source(self, explicit_dates):
        for entry in explicit_dates.values():
            assert "source_url" in entry

    def test_all_statuses_closed(self, explicit_dates):
        for entry in explicit_dates.values():
            assert entry["status"] == "closed"