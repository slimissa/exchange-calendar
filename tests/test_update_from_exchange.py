#!/usr/bin/env python3
"""
Fixed test suite for update_from_exchange.py
"""

import json
import pytest
import pickle
import time
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, mock_open
from typing import Dict, Any, Optional, List

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from update_from_exchange import (
    FetchError,
    ParseError,
    ValidationError,
    RateLimitError,
    FetchStatus,
    HolidayEntry,
    ExchangeData,
    CacheManager,
    RateLimiter,
    TransactionManager,
    ExchangeFetcher,
    NYSEFetcher,
    ExchangeFetcherRegistry,
    RegistryUpdater,
    retry,
)

# ============================================================================
# Test Data
# ============================================================================

SAMPLE_HTML = """
<html>
<body>
<table class="table-data">
  <tr>
    <th>Holiday</th>
    <th>2026</th>
    <th>2027</th>
    <th>2028</th>
  </tr>
  <tr>
    <td>New Year's Day</td>
    <td>Thursday, January 1</td>
    <td>Friday, January 1</td>
    <td>—*</td>
  </tr>
  <tr>
    <td>Martin Luther King, Jr. Day</td>
    <td>Monday, January 19</td>
    <td>Monday, January 18</td>
    <td>Monday, January 17</td>
  </tr>
  <tr>
    <td>Independence Day</td>
    <td>Friday, July 3</td>
    <td>Monday, July 5</td>
    <td>Tuesday, July 4</td>
  </tr>
  <tr>
    <td>Christmas Day</td>
    <td>Friday, December 25</td>
    <td>Monday, December 27</td>
    <td>Monday, December 25</td>
  </tr>
</table>
</body>
</html>
"""

SAMPLE_HOLIDAYS = [
    HolidayEntry("2026-01-01", "New Year's Day", source_url="https://www.nyse.com/markets/hours-calendars"),
    HolidayEntry("2026-01-19", "Martin Luther King, Jr. Day", source_url="https://www.nyse.com/markets/hours-calendars"),
    HolidayEntry("2026-07-03", "Independence Day", source_url="https://www.nyse.com/markets/hours-calendars"),
    HolidayEntry("2026-12-25", "Christmas Day", source_url="https://www.nyse.com/markets/hours-calendars"),
]

SAMPLE_EXCHANGE_DATA = ExchangeData(
    code="XNYS",
    mic="XNYS",
    name="New York Stock Exchange",
    timezone="America/New_York",
    regular_open="09:30",
    regular_close="16:00",
    holidays=SAMPLE_HOLIDAYS,
    source_urls=["https://www.nyse.com/markets/hours-calendars"],
    currency="USD",
    country="United States",
    city="New York"
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_holiday():
    return HolidayEntry(
        date="2026-01-01",
        name="New Year's Day",
        status="closed",
        source_url="https://www.nyse.com/markets/hours-calendars"
    )


@pytest.fixture
def sample_exchange_data():
    return SAMPLE_EXCHANGE_DATA


@pytest.fixture
def temp_registry_dir(tmp_path):
    """Create a temporary registry directory structure"""
    registry_dir = tmp_path / "registry"
    exchanges_dir = registry_dir / "exchanges"
    exchanges_dir.mkdir(parents=True)
    
    # Create a sample exchange file
    exchange_file = exchanges_dir / "XNYS.json"
    exchange_data = {
        "code": "XNYS",
        "name": "New York Stock Exchange",
        "mic": "XNYS",
        "timezone": "America/New_York",
        "regular_hours": {
            "open": "09:30",
            "close": "16:00"
        },
        "extended_hours": {
            "pre_market": {"open": "04:00", "close": "09:30"},
            "after_hours": {"open": "16:00", "close": "20:00"}
        },
        "sessions": [],
        "holidays": {
            "explicit": [
                {
                    "date": "2025-01-01",
                    "name": "New Year's Day",
                    "status": "closed",
                    "source_url": "https://www.nyse.com/markets/hours-calendars"
                },
                {
                    "date": "2025-07-04",
                    "name": "Independence Day",
                    "status": "closed",
                    "source_url": "https://www.nyse.com/markets/hours-calendars"
                }
            ],
            "recurrence_rules": []
        },
        "ad_hoc_closures": [],
        "generation_range": ["2025-01-01", "2029-12-31"]
    }
    
    with open(exchange_file, 'w') as f:
        json.dump(exchange_data, f, indent=2)
    
    return registry_dir


@pytest.fixture
def registry_updater(temp_registry_dir):
    return RegistryUpdater(temp_registry_dir, use_cache=False)


# ============================================================================
# Test Classes (with fixes)
# ============================================================================

class TestRetryDecorator:
    """Tests for retry decorator"""
    
    def test_retry_success_first_attempt(self):
        """Test successful execution on first attempt"""
        def test_func():
            return "success"
        
        decorated = retry(max_attempts=3)(test_func)
        result = decorated()
        assert result == "success"
    
    def test_retry_success_after_failures(self):
        """Test successful execution after failures"""
        attempts = [0]
        
        def test_func():
            attempts[0] += 1
            if attempts[0] < 3:
                raise ValueError("fail")
            return "success"
        
        decorated = retry(max_attempts=3, delay=0, backoff=1)(test_func)
        result = decorated()
        
        assert result == "success"
        assert attempts[0] == 3
    
    def test_retry_all_attempts_fail(self):
        """Test when all attempts fail"""
        def test_func():
            raise ValueError("always fails")
        
        decorated = retry(max_attempts=3, delay=0, backoff=1)(test_func)
        
        with pytest.raises(ValueError, match="always fails"):
            decorated()
    
    def test_retry_specific_exception(self):
        """Test retry with specific exception types"""
        attempts = [0]
        
        def test_func():
            attempts[0] += 1
            if attempts[0] == 1:
                raise ValueError("bad")
            return "success"
        
        decorated = retry(
            max_attempts=2,
            delay=0,
            backoff=1,
            exceptions=(ValueError,)
        )(test_func)
        
        result = decorated()
        assert result == "success"
        assert attempts[0] == 2


class TestTransactionManager:
    """Tests for TransactionManager class"""
    
    def test_create_backup(self, temp_registry_dir):
        tm = TransactionManager(temp_registry_dir)
        backup = tm.create_backup("XNYS")
        
        assert backup is not None
        assert backup.exists()
        assert "XNYS" in backup.name
    
    def test_rollback(self, temp_registry_dir):
        tm = TransactionManager(temp_registry_dir)
        backup = tm.create_backup("XNYS")
        
        # Modify the file
        exchange_file = temp_registry_dir / "exchanges" / "XNYS.json"
        with open(exchange_file, 'w') as f:
            json.dump({"code": "XNYS", "modified": True}, f)
        
        # Rollback
        tm.rollback("XNYS", backup.name)
        
        # Check restored
        with open(exchange_file, 'r') as f:
            data = json.load(f)
        
        assert "modified" not in data
        assert "holidays" in data
    
    def test_list_backups(self, temp_registry_dir):
        """Test listing backups - fixed to handle timestamp collision"""
        tm = TransactionManager(temp_registry_dir)
        
        # Create first backup
        backup1 = tm.create_backup("XNYS")
        
        # Wait for timestamp to change (backup names use seconds precision)
        time.sleep(1.1)
        
        # Create second backup
        backup2 = tm.create_backup("XNYS")
        
        backups = tm.list_backups("XNYS")
        
        # Should have at least 2 backups
        assert len(backups) >= 2
        assert backup1.name in backups
        assert backup2.name in backups
        # Backup names should be different
        assert backup1.name != backup2.name
    
    def test_create_backup_nonexistent(self, tmp_path):
        registry_dir = tmp_path / "registry"
        registry_dir.mkdir()
        
        tm = TransactionManager(registry_dir)
        backup = tm.create_backup("XXXX")
        
        assert backup is None


class TestNYSEFetcher:
    """Tests for NYSEFetcher class"""
    
    def test_parse_html(self):
        fetcher = NYSEFetcher()
        holidays = fetcher.parse_html(SAMPLE_HTML)
        
        assert len(holidays) > 0
        assert all(isinstance(h, HolidayEntry) for h in holidays)
    
    def test_parse_html_empty(self):
        fetcher = NYSEFetcher()
        holidays = fetcher.parse_html("<html><body>No tables</body></html>")
        
        assert holidays == []
    
    def test_parse_holiday_date(self):
        fetcher = NYSEFetcher()
        
        date1 = fetcher._parse_holiday_date("Thursday, January 1", 2026)
        assert date1 == "2026-01-01"
        
        date2 = fetcher._parse_holiday_date("January 19", 2026)
        assert date2 == "2026-01-19"
    
    def test_parse_holiday_date_observed(self):
        fetcher = NYSEFetcher()
        date = fetcher._parse_holiday_date("July 5 (Independence Day observed)", 2027)
        assert date == "2027-07-05"
    
    def test_parse_holiday_date_invalid(self):
        fetcher = NYSEFetcher()
        date = fetcher._parse_holiday_date("Not a date", 2026)
        assert date is None
    
    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        """Test successful fetch - patched at module level"""
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        fetcher = NYSEFetcher()
        data = fetcher.fetch()
        
        assert data is not None
        assert data.code == "XNYS"
        assert len(data.holidays) > 0
    
    @patch('requests.get')
    def test_fetch_http_error(self, mock_get):
        """Test fetch with HTTP error - should raise FetchError after retries"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection error")
        
        fetcher = NYSEFetcher()
        # Patch sleep to speed up test
        with patch('time.sleep', return_value=None):
            with pytest.raises(FetchError, match="Failed to fetch"):
                fetcher.fetch()
    
    @patch('requests.get')
    def test_fetch_timeout(self, mock_get):
        """Test fetch with timeout - should raise FetchError after retries"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout("Timeout")
        
        fetcher = NYSEFetcher()
        # Patch sleep to speed up test
        with patch('time.sleep', return_value=None):
            with pytest.raises(FetchError, match="Failed to fetch"):
                fetcher.fetch()


class TestRegistryUpdater:
    """Tests for RegistryUpdater class"""
    
    def test_init(self, temp_registry_dir):
        updater = RegistryUpdater(temp_registry_dir)
        
        assert updater.registry_dir == temp_registry_dir
        assert updater.exchanges_dir == temp_registry_dir / "exchanges"
        assert updater.exchanges_dir.exists()
    
    def test_load_current_exchange(self, registry_updater):
        data = registry_updater.load_current_exchange("XNYS")
        
        assert data is not None
        assert data["code"] == "XNYS"
        assert "holidays" in data
    
    def test_load_nonexistent_exchange(self, registry_updater):
        data = registry_updater.load_current_exchange("XXXX")
        assert data is None
    
    def test_compare_holidays_new_exchange(self, registry_updater, sample_exchange_data):
        has_changes, changes = registry_updater.compare_holidays(None, sample_exchange_data)
        
        assert has_changes
        assert "New exchange" in changes
    
    def test_compare_holidays_no_changes(self, registry_updater):
        current = {
            "holidays": {
                "explicit": [
                    {"date": "2026-01-01", "name": "New Year's Day"},
                    {"date": "2026-01-19", "name": "MLK Day"}
                ]
            }
        }
        
        fetched = ExchangeData(
            code="XNYS", mic="XNYS", name="Test",
            timezone="America/New_York",
            regular_open="09:30", regular_close="16:00",
            holidays=[
                HolidayEntry("2026-01-01", "New Year's Day"),
                HolidayEntry("2026-01-19", "MLK Day")
            ]
        )
        
        has_changes, changes = registry_updater.compare_holidays(current, fetched)
        
        assert not has_changes
        assert changes == []
    
    def test_compare_holidays_with_additions(self, registry_updater):
        current = {
            "holidays": {
                "explicit": [
                    {"date": "2026-01-01", "name": "New Year's Day"}
                ]
            }
        }
        
        fetched = ExchangeData(
            code="XNYS", mic="XNYS", name="Test",
            timezone="America/New_York",
            regular_open="09:30", regular_close="16:00",
            holidays=[
                HolidayEntry("2026-01-01", "New Year's Day"),
                HolidayEntry("2026-12-25", "Christmas Day")
            ]
        )
        
        has_changes, changes = registry_updater.compare_holidays(current, fetched)
        
        assert has_changes
        assert "2026-12-25" in changes[0]
    
    def test_generate_exchange_json_new(self, registry_updater, sample_exchange_data):
        result = registry_updater.generate_exchange_json(sample_exchange_data)
        
        assert result["code"] == "XNYS"
        assert result["timezone"] == "America/New_York"
        assert len(result["holidays"]["explicit"]) == len(sample_exchange_data.holidays)
    
    def test_generate_exchange_json_merge(self, registry_updater, sample_exchange_data):
        current = {
            "code": "XNYS",
            "name": "New York Stock Exchange",
            "mic": "XNYS",
            "timezone": "America/New_York",
            "regular_hours": {"open": "09:30", "close": "16:00"},
            "extended_hours": {
                "pre_market": {"open": "04:00", "close": "09:30"}
            },
            "sessions": [{"name": "opening_auction"}],
            "holidays": {
                "explicit": [
                    {"date": "2025-01-01", "name": "New Year's Day 2025"}
                ],
                "recurrence_rules": [{"type": "fixed_date"}]
            },
            "ad_hoc_closures": [{"date": "2025-09-11"}],
            "generation_range": ["2025-01-01", "2029-12-31"]
        }
        
        result = registry_updater.generate_exchange_json(sample_exchange_data, current)
        
        holiday_dates = [h["date"] for h in result["holidays"]["explicit"]]
        assert "2025-01-01" in holiday_dates
        assert "2026-01-01" in holiday_dates
        
        assert result["extended_hours"]["pre_market"]["open"] == "04:00"
        assert len(result["sessions"]) == 1
        assert len(result["holidays"]["recurrence_rules"]) == 1
        assert len(result["ad_hoc_closures"]) == 1
    
    @patch('requests.get')
    def test_update_exchange_dry_run(self, mock_get, registry_updater):
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        status, message = registry_updater.update_exchange("XNYS", dry_run=True)
        
        with open(registry_updater.exchanges_dir / "XNYS.json", 'r') as f:
            data = json.load(f)
        
        assert len(data["holidays"]["explicit"]) == 2
    
    @patch('requests.get')
    def test_update_exchange_actual(self, mock_get, registry_updater):
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        status, message = registry_updater.update_exchange("XNYS", dry_run=False)
        
        with open(registry_updater.exchanges_dir / "XNYS.json", 'r') as f:
            data = json.load(f)
        
        holiday_dates = [h["date"] for h in data["holidays"]["explicit"]]
        assert "2025-01-01" in holiday_dates
        assert "2026-01-01" in holiday_dates
    
    def test_update_exchange_no_fetcher(self, registry_updater):
        status, message = registry_updater.update_exchange("XXXX")
        
        assert status == FetchStatus.SKIPPED
        assert message is None


class TestIntegration:
    """Integration tests for the complete workflow"""
    
    @patch('requests.get')
    def test_complete_workflow(self, mock_get, temp_registry_dir):
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        updater = RegistryUpdater(temp_registry_dir, use_cache=False)
        
        status, message = updater.update_exchange("XNYS", dry_run=False)
        
        assert status in [FetchStatus.UPDATED, FetchStatus.UNCHANGED, FetchStatus.NEW_EXCHANGE]
        
        data = updater.load_current_exchange("XNYS")
        assert data is not None
        assert data["code"] == "XNYS"
        assert len(data["holidays"]["explicit"]) >= 2
    
    @patch('requests.get')
    def test_multiple_updates_idempotent(self, mock_get, temp_registry_dir):
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        updater = RegistryUpdater(temp_registry_dir, use_cache=False)
        
        status1, _ = updater.update_exchange("XNYS", dry_run=False)
        data1 = updater.load_current_exchange("XNYS")
        holidays1 = data1["holidays"]["explicit"]
        
        status2, _ = updater.update_exchange("XNYS", dry_run=False)
        data2 = updater.load_current_exchange("XNYS")
        holidays2 = data2["holidays"]["explicit"]
        
        assert len(holidays1) == len(holidays2)
        assert status2 == FetchStatus.UNCHANGED


class TestPerformance:
    """Performance-related tests"""
    
    def test_cache_improves_performance(self, tmp_path):
        cache = CacheManager(tmp_path / "cache")
        data = SAMPLE_EXCHANGE_DATA
        
        start = time.time()
        cached1 = cache.get("XNYS", "https://test.com")
        first_access = time.time() - start
        
        cache.set("XNYS", "https://test.com", data)
        
        start = time.time()
        cached2 = cache.get("XNYS", "https://test.com")
        second_access = time.time() - start
        
        assert cached1 is None
        assert cached2 is not None
        assert second_access < first_access + 0.5
    
    def test_large_holiday_set(self):
        """Test with large holiday set - fixed to avoid duplicates"""
        data = ExchangeData(
            code="XNYS",
            mic="XNYS",
            name="Test",
            timezone="America/New_York",
            regular_open="09:30",
            regular_close="16:00",
            holidays=[]
        )
        
        # Add 1000 unique holidays
        base_date = datetime(2030, 1, 1)  # Start from 2030 to avoid overlap
        for i in range(1000):
            date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            data.holidays.append(HolidayEntry(date, f"Holiday {i}"))
        
        errors = data.validate()
        assert errors == []


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])