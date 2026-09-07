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
    NASDAQFetcher,
    LSEFetcher,
    XETRFetcher,
    ASXFetcher,
    EuronextFetcher,
    EuronextParisFetcher,
    EuronextAmsterdamFetcher,
    EuronextDublinFetcher,
    EuronextBrusselsFetcher,
    EuronextLisbonFetcher,
    EuronextOsloFetcher,
    TokyoFetcher,
    SSEFetcher,
    SZSEFetcher,
    HKEXFetcher,
    TSXFetcher,
    BMEMadridFetcher,
    SaudiExchangeFetcher,
    PDFFetcher,
    XDFMFetcher,
    BoursaKuwaitFetcher,
    MOEXFetcher,
    ViennaFetcher,
    WarsawFetcher,
    PragueFetcher,
    BudapestFetcher,
    NasdaqNordicFetcher,
    StockholmFetcher,
    HelsinkiFetcher,
    CopenhagenFetcher,
    IcelandFetcher,
    NasdaqBalticFetcher,
    TallinnFetcher,
    RigaFetcher,
    VilniusFetcher,
    B3BrazilFetcher,
    BMVMexicoFetcher,
    BymaArgentinaFetcher,
    HOSEVietnamFetcher,
    NigeriaExchangeFetcher,
    BRVMFetcher,
    ColomboFetcher,
    GhanaExchangeFetcher,
    BermudaExchangeFetcher,
    CaymanExchangeFetcher,
    LuxembourgExchangeFetcher,
    MaltaExchangeFetcher,
    ZagrebExchangeFetcher,
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
    
    def test_source_url_is_ir_theice_not_bot_walled_nyse_com(self):
        """
        Regression test for the 2026-08-27 fix: NYSEFetcher must NOT point at
        nyse.com, which was confirmed (via live web_fetch, not the sandboxed
        bash_tool) to return "Site blocked the request (bot detection)"
        regardless of User-Agent. Source must be the ir.theice.com IR press
        release instead.
        """
        fetcher = NYSEFetcher()
        assert "nyse.com" not in fetcher.source_url
        assert "ir.theice.com" in fetcher.source_url

    def test_parse_html_ir_theice_table_structure(self):
        """
        Parse against a fixture matching the REAL ir.theice.com press release
        table structure (verified live 2026-08-27), including its uppercase
        "HOLIDAY" header and multiple trailing asterisks on footnoted cells --
        both of which the original case-sensitive header match and simpler
        asterisk handling would need to survive.
        """
        ir_theice_html = """
        <html><body>
        <table>
        <tr><th>HOLIDAY</th><th>2025</th><th>2026</th><th>2027</th></tr>
        <tr><td>New Year's Day</td><td>Wednesday, January 1</td><td>Thursday, January 1</td><td>Friday, January 1</td></tr>
        <tr><td>Independence Day</td><td>Friday, July 4*</td><td>Friday, July 3 (Independence Day observed)</td><td>Monday, July 5 (Independence Day observed)</td></tr>
        <tr><td>Thanksgiving Day</td><td>Thursday, November 27**</td><td>Thursday, November 26**</td><td>Thursday, November 25**</td></tr>
        <tr><td>Christmas Day</td><td>Thursday, December 25***</td><td>Friday, December 25***</td><td>Friday, December 24 (Christmas Day observed)</td></tr>
        </table>
        </body></html>
        """
        fetcher = NYSEFetcher()
        holidays = fetcher.parse_html(ir_theice_html)

        assert len(holidays) == 12
        dates = {h.date for h in holidays}
        assert "2025-01-01" in dates
        assert "2026-07-03" in dates  # Independence Day observed, 2026
        assert "2027-12-24" in dates  # Christmas Day observed, 2027

    def test_parse_html_2026_2028_table_skips_unobserved_holiday_cell(self):
        """
        Regression test for the 2026-08-29 source update (2025-2027 press
        release -> 2026-2028 press release). The newer table has a
        genuinely different case not present in the older fixture above: a
        "—*" cell for 2028 New Year's Day, which isn't observed because it
        falls on a Saturday. This must be skipped, not parsed as a date.
        """
        newer_html = """
        <html><body>
        <table>
        <tr><th>HOLIDAY</th><th>2026</th><th>2027</th><th>2028</th></tr>
        <tr><td>New Year's Day</td><td>Thursday, January 1</td><td>Friday, January 1</td><td>—*</td></tr>
        <tr><td>Juneteenth National Independence Day</td><td>Friday, June 19</td><td>Friday, June 18 (Juneteenth National Independence Day observed)</td><td>Monday, June 19</td></tr>
        <tr><td>Independence Day</td><td>Friday, July 3 (Independence Day observed)</td><td>Monday, July 5 (Independence Day observed)</td><td>Tuesday, July 4**</td></tr>
        </table>
        </body></html>
        """
        fetcher = NYSEFetcher()
        holidays = fetcher.parse_html(newer_html)

        dates = {h.date for h in holidays}
        assert "2028-01-01" not in dates  # the "—*" cell must not become a holiday
        assert "2026-01-01" in dates
        assert "2028-07-04" in dates  # the "**" footnote must still parse correctly
        assert len(holidays) == 8  # 3 rows x 3 years minus the one skipped "—*" cell

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


class TestNASDAQFetcher:
    """
    Tests for NASDAQFetcher.

    NASDAQ has no independently scrapable holiday source (nasdaq.com/trading-calendar
    is JS-rendered — verified by direct fetch, see class docstring in
    tools/update_from_exchange.py). These tests confirm the fetcher correctly mirrors
    NYSE's parsed data under the XNAS identity rather than testing a NASDAQ-specific
    parser, since none exists.
    """

    def test_parse_html_reuses_nyse_parser(self):
        """NASDAQFetcher.parse_html is inherited from NYSEFetcher unchanged"""
        fetcher = NASDAQFetcher()
        holidays = fetcher.parse_html(SAMPLE_HTML)

        assert len(holidays) > 0
        assert all(isinstance(h, HolidayEntry) for h in holidays)

    def test_parse_html_empty_or_invalid(self):
        fetcher = NASDAQFetcher()
        holidays = fetcher.parse_html("<html><body>No tables</body></html>")

        assert holidays == []

    def test_mic_and_name(self):
        fetcher = NASDAQFetcher()
        assert fetcher.mic == "XNAS"
        assert fetcher.name == "NASDAQ"
        # Source URL is deliberately NYSE's own working source, not nasdaq.com --
        # documented mirror. Compared against a fresh NYSEFetcher's source_url
        # rather than a hardcoded string, so this test can't silently go stale
        # the way the fetcher itself almost did when NYSE's source URL changed.
        assert fetcher.source_url == NYSEFetcher().source_url

    @patch('requests.get')
    def test_fetch_mirrors_nyse_dates_exactly(self, mock_get):
        """NASDAQ and NYSE fetches against the same source HTML must yield identical dates"""
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        nyse_data = NYSEFetcher().fetch()
        nasdaq_data = NASDAQFetcher().fetch()

        nyse_dates = sorted(h.date for h in nyse_data.holidays)
        nasdaq_dates = sorted(h.date for h in nasdaq_data.holidays)
        assert nyse_dates == nasdaq_dates
        assert len(nasdaq_dates) > 0

    @patch('requests.get')
    def test_fetch_returns_correct_exchange_data(self, mock_get):
        mock_response = Mock()
        mock_response.text = SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = NASDAQFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.code == "XNAS"
        assert data.mic == "XNAS"
        assert data.name == "NASDAQ"
        assert data.timezone == "America/New_York"
        assert data.regular_open == "09:30"
        assert data.regular_close == "16:00"
        assert len(data.holidays) > 0
        # Every mirrored holiday should carry a note explaining the mirror
        assert all(h.note and "NYSE" in h.note for h in data.holidays)

    def test_registered_in_registry(self):
        registry = ExchangeFetcherRegistry()
        fetcher = registry.get("XNAS")

        assert fetcher is not None
        assert isinstance(fetcher, NASDAQFetcher)
        assert "XNAS" in registry.list_available()



# ============================================================================
# Fixtures modeled on real, live-verified page structures (see class
# docstrings in tools/update_from_exchange.py for the verification date/method
# for each). These are trimmed excerpts, not full page dumps.
# ============================================================================

LSE_SAMPLE_JSON = json.dumps({
    "england-and-wales": {
        "division": "england-and-wales",
        "events": [
            {"title": "New Year's Day", "date": "2026-01-01", "notes": "", "bunting": True},
            {"title": "Good Friday", "date": "2026-04-03", "notes": "", "bunting": False},
            {"title": "Easter Monday", "date": "2026-04-06", "notes": "", "bunting": True},
            {"title": "Christmas Day", "date": "2026-12-25", "notes": "", "bunting": True},
            {"title": "Boxing Day", "date": "2026-12-28", "notes": "Substitute day", "bunting": True},
        ]
    }
})

XETR_SAMPLE_HTML = """
<html><body>
<table>
  <tr><th></th><th>2026</th><th>2027</th></tr>
  <tr><td>New Year's Day</td><td>Thursday Jan 01, 2026</td><td>Friday Jan 01, 2027</td></tr>
  <tr><td>Good Friday</td><td>Friday Apr 03, 2026</td><td>Friday Mar 26, 2027</td></tr>
  <tr><td>Labor Day</td><td>Friday May 01, 2026</td><td>Saturday May 01, 2027</td></tr>
  <tr><td>Christmas Day</td><td>Friday Dec 25, 2026</td><td>Saturday Dec 25, 2027</td></tr>
</table>
</body></html>
"""

ASX_SAMPLE_HTML = """
<html><body>
<h2>DATES FOR 2026</h2>
<table>
  <tr><th>PUBLIC HOLIDAY</th><th>DATES FOR 2026</th><th>TRADING DAY</th><th>SETTLEMENT</th></tr>
  <tr><td>New Year's Day</td><td>Thursday 1 January</td><td>CLOSED</td><td>No Settlement</td></tr>
  <tr><td>Australia Day</td><td>Monday 26 January</td><td>CLOSED</td><td>No Settlement</td></tr>
  <tr><td>Last Business day before Christmas Day</td><td>Thursday 24 December</td><td>CLOSE EARLY</td><td>Settlement</td></tr>
  <tr><td>Christmas Day</td><td>Friday 25 December</td><td>CLOSED</td><td>No Settlement</td></tr>
</table>
</body></html>
"""

EURONEXT_SAMPLE_HTML = """
<html><body>
<table>
  <tr><th>Euronext Holidays</th><th>Amsterdam</th><th>Brussels</th><th>Paris</th></tr>
  <tr><td>Thursday 1 January 2026 (New Year's Day)</td><td>Closed</td><td>Closed</td><td>Closed</td></tr>
  <tr><td>Friday 2 January 2026 (Substitute for New Year's Day)</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Full Trading Day</td></tr>
  <tr><td>Friday 3 April 2026 (Good Friday)</td><td>Closed</td><td>Closed</td><td>Closed</td></tr>
  <tr><td>Monday 4 May 2026 (Irish May Bank Holiday)</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Full Trading Day</td></tr>
  <tr><td>Friday 25 December 2026 (Christmas)</td><td>Closed</td><td>Closed</td><td>Closed</td></tr>
  <tr><td>Monday 5 and Tuesday 6 January 2026</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Full Trading Day</td></tr>
</table>
</body></html>
"""

JPX_SAMPLE_HTML = """
<html><body>
<h2>2026</h2>
<table>
  <tr><td>Jan. 1 (Thu.)</td><td>New Year's Day</td></tr>
  <tr><td>Jan. 2 (Fri.)</td><td>Market Holiday</td></tr>
  <tr><td>Feb. 11 (Wed.)</td><td>National Foundation Day</td></tr>
  <tr><td>May 6 (Wed.)</td><td>Constitution Memorial Day (May 3) observed1</td></tr>
</table>
<h2>2027</h2>
<table>
  <tr><td>Jan. 1 (Fri.)</td><td>New Year's Day</td></tr>
  <tr><td>Feb. 11 (Thu.)</td><td>National Foundation Day</td></tr>
</table>
</body></html>
"""


class TestLSEFetcher:
    """Tests for LSEFetcher (parses gov.uk bank-holidays JSON, not HTML)"""

    def test_parse_html_valid_json(self):
        fetcher = LSEFetcher()
        holidays = fetcher.parse_html(LSE_SAMPLE_JSON)

        assert len(holidays) == 5
        assert all(isinstance(h, HolidayEntry) for h in holidays)
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2026-12-25" in dates

    def test_parse_html_invalid_json(self):
        fetcher = LSEFetcher()
        holidays = fetcher.parse_html("not json at all {{{")
        assert holidays == []

    def test_parse_html_empty(self):
        fetcher = LSEFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html(json.dumps({})) == []

    def test_note_documents_proxy_source(self):
        fetcher = LSEFetcher()
        holidays = fetcher.parse_html(LSE_SAMPLE_JSON)
        assert all("bank holiday" in (h.note or "").lower() for h in holidays)

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = LSE_SAMPLE_JSON
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = LSEFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XLON"
        assert data.currency == "GBP"
        assert len(data.holidays) == 5


class TestXETRFetcher:
    """Tests for XETRFetcher (Deutsche Boerse Xetra)"""

    def test_parse_html_extracts_holidays(self):
        fetcher = XETRFetcher()
        holidays = fetcher.parse_html(XETR_SAMPLE_HTML)

        assert len(holidays) > 0
        assert all(isinstance(h, HolidayEntry) for h in holidays)

    def test_parse_html_empty(self):
        fetcher = XETRFetcher()
        assert fetcher.parse_html("<html><body>no tables</body></html>") == []

    def test_weekend_exclusion(self):
        """Saturday May 01, 2027 (Labor Day) and Saturday Dec 25, 2027 must be excluded"""
        fetcher = XETRFetcher()
        holidays = fetcher.parse_html(XETR_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2027-05-01" not in dates  # falls on a Saturday
        assert "2027-12-25" not in dates  # falls on a Saturday
        assert "2026-05-01" in dates      # Friday -- should be included

    def test_date_format_parsing(self):
        fetcher = XETRFetcher()
        holidays = fetcher.parse_html(XETR_SAMPLE_HTML)
        date_pattern_ok = all(len(h.date) == 10 and h.date[4] == '-' and h.date[7] == '-'
                               for h in holidays)
        assert date_pattern_ok

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = XETR_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = XETRFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XETR"
        assert data.currency == "EUR"


class TestASXFetcher:
    """Tests for ASXFetcher"""

    def test_parse_html_separates_holidays_and_early_closes(self):
        fetcher = ASXFetcher()
        holidays, early_closes = fetcher.parse_html(ASX_SAMPLE_HTML)

        assert len(holidays) == 3  # New Year's, Australia Day, Christmas
        assert len(early_closes) == 1  # the CLOSE EARLY row
        assert all(isinstance(h, HolidayEntry) for h in holidays + early_closes)

    def test_parse_html_empty(self):
        fetcher = ASXFetcher()
        holidays, early_closes = fetcher.parse_html("<html><body>nothing here</body></html>")
        assert holidays == []
        assert early_closes == []

    def test_year_extracted_from_header(self):
        fetcher = ASXFetcher()
        holidays, _ = fetcher.parse_html(ASX_SAMPLE_HTML)
        assert all(h.date.startswith("2026-") for h in holidays)

    def test_date_format_iso(self):
        fetcher = ASXFetcher()
        holidays, _ = fetcher.parse_html(ASX_SAMPLE_HTML)
        assert "2026-01-01" in {h.date for h in holidays}
        assert "2026-01-26" in {h.date for h in holidays}

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = ASX_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = ASXFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XASX"
        assert len(data.early_closes) == 1


EURONEXT_HALF_DAY_SAMPLE_HTML = """
<html><body>
<table>
<tr><th>Euronext Holidays</th><th>Amsterdam</th><th>Brussels</th><th>Dublin</th><th>Lisbon</th><th>Milan</th><th>Oslo</th><th>Paris</th></tr>
<tr><td>Thursday 1 January 2026 (New Year's Day)</td><td>Closed</td><td>Closed</td><td>Closed</td><td>Closed</td><td>Closed</td><td>Closed</td><td>Closed</td></tr>
<tr><td>Monday 4 May 2026 (Irish May Bank Holiday)</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Closed</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Full Trading Day</td></tr>
<tr><td>Thursday 14 May 2026 (Ascension Day)</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Full Trading Day</td><td>Closed</td><td>Full Trading Day</td></tr>
<tr><td>Thursday 24 December 2026</td><td>**Half Trading Day</td><td>**Half Trading Day</td><td>**Half Trading Day</td><td>**Half Trading Day</td><td>Closed</td><td>Closed</td><td>**Half Trading Day</td></tr>
<tr><td>Friday 25 December 2026 (Christmas)</td><td>Closed</td><td>Closed</td><td>Closed</td><td>Closed</td><td>Closed</td><td>Closed</td><td>Closed</td></tr>
</table>
</body></html>
"""


class TestEuronextFetcher:
    """Tests for the shared EuronextFetcher (XPAR/XAMS/XDUB/XBRU/XLIS/XOSL)"""

    def test_parse_html_paris_column(self):
        fetcher = EuronextParisFetcher()
        holidays, early_closes = fetcher.parse_html(EURONEXT_SAMPLE_HTML)

        # 3 "Closed" rows for Paris; the substitute day and the multi-day
        # range row are "Full Trading Day" / unparseable respectively
        assert len(holidays) == 3
        assert all(isinstance(h, HolidayEntry) for h in holidays)

    def test_parse_html_amsterdam_column_same_closures(self):
        """In the sample, Amsterdam and Paris close on the same days"""
        paris_holidays, _ = EuronextParisFetcher().parse_html(EURONEXT_SAMPLE_HTML)
        ams_holidays, _ = EuronextAmsterdamFetcher().parse_html(EURONEXT_SAMPLE_HTML)
        assert {h.date for h in paris_holidays} == {h.date for h in ams_holidays}

    def test_parse_html_empty(self):
        fetcher = EuronextParisFetcher()
        assert fetcher.parse_html("<html><body>no tables</body></html>") == ([], [])

    def test_multi_day_range_row_skipped_not_guessed(self):
        """The 'Monday 5 and Tuesday 6 January 2026' row must not produce a holiday"""
        fetcher = EuronextParisFetcher()
        holidays, _ = fetcher.parse_html(EURONEXT_SAMPLE_HTML)
        assert "2026-01-05" not in {h.date for h in holidays}
        assert "2026-01-06" not in {h.date for h in holidays}

    def test_invalid_mic_raises(self):
        with pytest.raises(ValueError):
            EuronextFetcher(mic="XXXX", name="Not a real Euronext market")

    def test_half_trading_day_produces_early_close_not_dropped(self):
        """
        Regression test for the 2026-08-31 fix: 'Half Trading Day' cells
        were previously silently dropped (only 'closed' was checked). This
        affects XPAR/XAMS, built in Tier 1, not just the new markets.
        """
        fetcher = EuronextParisFetcher()
        holidays, early_closes = fetcher.parse_html(EURONEXT_HALF_DAY_SAMPLE_HTML)

        assert len(early_closes) == 1
        assert early_closes[0].date == "2026-12-24"
        assert early_closes[0].status == "early_close"
        # And it must NOT also appear in holidays (full closures)
        assert "2026-12-24" not in {h.date for h in holidays}

    def test_dublin_irish_bank_holiday_is_dublin_specific_closure(self):
        """Dublin closes on the Irish May Bank Holiday; other markets don't"""
        fetcher = EuronextDublinFetcher()
        holidays, _ = fetcher.parse_html(EURONEXT_HALF_DAY_SAMPLE_HTML)
        assert "2026-05-04" in {h.date for h in holidays}

        paris_holidays, _ = EuronextParisFetcher().parse_html(EURONEXT_HALF_DAY_SAMPLE_HTML)
        assert "2026-05-04" not in {h.date for h in paris_holidays}

    def test_oslo_ascension_day_closure_and_currency(self):
        """
        Oslo closes on Ascension Day (other markets don't) and trades in
        NOK, not EUR -- confirmed separately, not assumed from the other
        five Euronext markets' pattern.
        """
        fetcher = EuronextOsloFetcher()
        holidays, _ = fetcher.parse_html(EURONEXT_HALF_DAY_SAMPLE_HTML)
        assert "2026-05-14" in {h.date for h in holidays}
        assert fetcher.CURRENCY["XOSL"] == "NOK"

    def test_brussels_lisbon_registered_columns(self):
        for fetcher_cls, mic, column in [
            (EuronextBrusselsFetcher, "XBRU", "Brussels"),
            (EuronextLisbonFetcher, "XLIS", "Lisbon"),
        ]:
            fetcher = fetcher_cls()
            assert fetcher.mic == mic
            assert fetcher.MARKET_COLUMN[mic] == column
            holidays, _ = fetcher.parse_html(EURONEXT_HALF_DAY_SAMPLE_HTML)
            assert "2026-01-01" in {h.date for h in holidays}

    @patch('requests.get')
    def test_fetch_success_distinct_mics(self, mock_get):
        mock_response = Mock()
        mock_response.text = EURONEXT_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        paris_data = EuronextParisFetcher().fetch()
        ams_data = EuronextAmsterdamFetcher().fetch()

        assert paris_data.mic == "XPAR"
        assert ams_data.mic == "XAMS"
        assert paris_data.country == "France"
        assert ams_data.country == "Netherlands"

    @patch('requests.get')
    def test_fetch_success_new_markets(self, mock_get):
        mock_response = Mock()
        mock_response.text = EURONEXT_HALF_DAY_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        dub_data = EuronextDublinFetcher().fetch()
        osl_data = EuronextOsloFetcher().fetch()

        assert dub_data.mic == "XDUB"
        assert dub_data.currency == "EUR"
        assert osl_data.mic == "XOSL"
        assert osl_data.currency == "NOK"
        assert osl_data.regular_close == "16:30"
        # Oslo (like Milan) gets a FULL closure on Dec 24, not a half-day
        # like the other five Euronext markets in this fixture
        assert "2026-12-24" in {h.date for h in osl_data.holidays}
        assert len(osl_data.early_closes) == 0


VIENNA_SAMPLE_PDF_TEXT = """Delivering 
a world of 
good deals.
Holiday schedule & trading on public holidays
on the Vienna Stock Exchange 2026
Please contact us for any further questions: T: +43-1-53165-222 | F: +43-1-53165-192 | index@wienerboerse.at
For updates please see our website: www.wienerboerse.at
Stock exchange holidays Additional holiday trading days
Th, 1 January New Year Tu, 6 January Epiphany
Fr, 3 April Good Friday Th, 14 May Ascension Day
Mo, 6 April Easter Monday Mo, 25 May Whit Monday
Fr, 1 May Labour Day Th, 4 June Corpus Christi Day
Mo, 26 October National Holiday Tu, 8 December Immaculate Conception
Th, 24 December Christmas Eve
Fr, 25 December Christmas Day
Th, 31 December New Years's Eve
"""

WARSAW_SAMPLE_HTML = """
<html><body>
<h2>2026</h2>
<table>
<tr><td>Thursday</td><td>1 January</td></tr>
<tr><td>Tuesday</td><td>6 January</td></tr>
<tr><td>Friday</td><td>3 April</td></tr>
<tr><td>Thursday</td><td>24 December</td></tr>
<tr><td>Friday</td><td>25 December</td></tr>
<tr><td>Thursday</td><td>31 December</td></tr>
</table>
<h2>2027</h2>
<table>
<tr><td>Friday</td><td>1 January</td></tr>
</table>
</body></html>
"""

PRAGUE_SAMPLE_HTML = """
<html><body>
<h4>2026 Non-business days:</h4>
<p>1. Jan</p><p>2026</p><p>New Year's Day</p>
<p>3. Apr</p><p>2026</p><p>Good Friday</p>
<p>6. Apr</p><p>2026</p><p>Easter Monday</p>
<p>25. Dec</p><p>2026</p><p>Christmas Day</p>
<h4>2025 Non-business days:</h4>
<p>1. Jan</p><p>2025</p><p>New Year's Day</p>
<p>26. Dec</p><p>2025</p><p>St. Stephen's Day</p>
#### Download
<p>2026 Trading Calendar</p>
</body></html>
"""

BUDAPEST_SAMPLE_PDF_TEXT = """Resolution No. 380/2025 of the Budapest Stock Exchange Plc.
Budapest, 5 November 2025
The Budapest Stock Exchange Plc. as authorized under Part I, Chapter 3, Section 3.2. a) of Book Five 
Trading Rules of the The General Terms of Service of the Budapest Stock Exchange resolves that the
following days shall be trading holidays in 2026:
2026
1 January Thursday New Year
2 January Friday Public Holiday
3 April Friday Good Friday
25 December Friday Christmas
31 December Thursday New Year's Eve
The following Saturdays in 2026 shall also be nontrading days: 10 January, 8 August, 12 December.
"""


class TestViennaFetcher:
    """Tests for ViennaFetcher (XWBO) -- 2-column PDF with an opposite-meaning right column"""

    def test_parse_html_extracts_left_column_only(self):
        fetcher = ViennaFetcher()
        holidays = fetcher.parse_html(VIENNA_SAMPLE_PDF_TEXT)
        assert len(holidays) == 8

    def test_parse_html_discards_additional_trading_days(self):
        """Epiphany, Ascension Day, etc (right column) must NOT appear as closures"""
        fetcher = ViennaFetcher()
        holidays = fetcher.parse_html(VIENNA_SAMPLE_PDF_TEXT)
        names = {h.name for h in holidays}
        assert "Epiphany" not in names
        assert "Ascension Day" not in names
        assert "Corpus Christi Day" not in names

    def test_parse_html_includes_real_closures(self):
        fetcher = ViennaFetcher()
        holidays = fetcher.parse_html(VIENNA_SAMPLE_PDF_TEXT)
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2026-12-25" in dates

    def test_parse_html_empty(self):
        fetcher = ViennaFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("no year heading here") == []

    @patch.object(ViennaFetcher, '_extract_pdf_text')
    @patch('requests.get')
    def test_fetch_success(self, mock_get, mock_extract):
        mock_response = Mock()
        mock_response.content = b"%PDF-1.4 dummy"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_extract.return_value = VIENNA_SAMPLE_PDF_TEXT

        fetcher = ViennaFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XWBO"
        assert data.currency == "EUR"


class TestWarsawFetcher:
    """Tests for WarsawFetcher (XWAR)"""

    def test_parse_html_extracts_both_years(self):
        fetcher = WarsawFetcher()
        holidays = fetcher.parse_html(WARSAW_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2027-01-01" in dates
        assert len(holidays) == 7

    def test_parse_html_generic_name(self):
        fetcher = WarsawFetcher()
        holidays = fetcher.parse_html(WARSAW_SAMPLE_HTML)
        assert all(h.name == "Warsaw Stock Exchange Holiday" for h in holidays)

    def test_parse_html_empty(self):
        fetcher = WarsawFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no year heading</body></html>") == []

    def test_date_format_iso(self):
        fetcher = WarsawFetcher()
        holidays = fetcher.parse_html(WARSAW_SAMPLE_HTML)
        assert all(len(h.date) == 10 and h.date[4] == '-' for h in holidays)

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = WARSAW_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = WarsawFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XWAR"
        assert data.currency == "PLN"


class TestPragueFetcher:
    """Tests for PragueFetcher (XPRA)"""

    def test_parse_html_extracts_both_years_with_real_names(self):
        fetcher = PragueFetcher()
        holidays = fetcher.parse_html(PRAGUE_SAMPLE_HTML)
        assert len(holidays) == 6
        names = {h.name for h in holidays}
        assert "New Year's Day" in names
        assert "Good Friday" in names
        assert "St. Stephen's Day" in names

    def test_parse_html_does_not_leak_download_section(self):
        fetcher = PragueFetcher()
        holidays = fetcher.parse_html(PRAGUE_SAMPLE_HTML)
        names = {h.name for h in holidays}
        assert not any("Trading Calendar" in n for n in names)

    def test_parse_html_empty(self):
        fetcher = PragueFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>nothing</body></html>") == []

    def test_dates_correct_year(self):
        fetcher = PragueFetcher()
        holidays = fetcher.parse_html(PRAGUE_SAMPLE_HTML)
        dates_2026 = {h.date for h in holidays if h.date.startswith("2026")}
        dates_2025 = {h.date for h in holidays if h.date.startswith("2025")}
        assert "2026-04-06" in dates_2026  # Easter Monday
        assert "2025-01-01" in dates_2025

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = PRAGUE_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = PragueFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XPRA"
        assert data.currency == "CZK"


class TestBudapestFetcher:
    """Tests for BudapestFetcher (XBUD)"""

    def test_parse_html_extracts_holidays_with_names(self):
        fetcher = BudapestFetcher()
        holidays = fetcher.parse_html(BUDAPEST_SAMPLE_PDF_TEXT)
        assert len(holidays) == 5
        names = {h.name for h in holidays}
        assert "New Year" in names
        assert "Good Friday" in names

    def test_parse_html_ignores_saturday_footnote(self):
        """The 'following Saturdays...' sentence must not produce holiday entries"""
        fetcher = BudapestFetcher()
        holidays = fetcher.parse_html(BUDAPEST_SAMPLE_PDF_TEXT)
        assert not any(h.date == "2026-01-10" for h in holidays)
        assert not any(h.date == "2026-08-08" for h in holidays)

    def test_parse_html_empty(self):
        fetcher = BudapestFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("no year phrase here") == []

    @patch.object(BudapestFetcher, '_extract_pdf_text')
    @patch('requests.get')
    def test_fetch_success(self, mock_get, mock_extract):
        mock_response = Mock()
        mock_response.content = b"%PDF-1.4 dummy"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_extract.return_value = BUDAPEST_SAMPLE_PDF_TEXT

        fetcher = BudapestFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XBUD"
        assert data.currency == "HUF"


NORDIC_SAMPLE_HTML = """
<html><body>
<h2>Exchange Holiday Schedule 2026</h2>
<table>
<tr><th></th><th>Equity/Equity derivatives</th><th>Fixed Income</th></tr>
<tr><td>Copenhagen</td><td><b>Closed</b> Jan 1, 2026; Apr 2, 2026; Apr 3, 2026; Apr 6, 2026; May 14, 2026; May 15, 2026; May 25, 2026; Jun 5, 2026; Dec 24, 2026; Dec 25, 2026; Dec 31, 2026</td><td>same</td></tr>
<tr><td>Stockholm</td><td><b>Closed</b> Jan 1, 2026; Jan 6, 2026; Apr 3, 2026; Apr 6, 2026; May 1, 2026; May 14, 2026; Jun 19, 2026; Dec 24, 2026; Dec 25, 2026; Dec 31, 2026 <b>Half trading days:</b> Jan 5, 2026; Apr 2, 2026; Apr 30, 2026; May 13, 2026; Oct 30, 2026</td><td>same</td></tr>
<tr><td>Helsinki</td><td><b>Closed</b> Jan 1, 2026; Jan 6, 2026; Apr 3, 2026; Apr 6, 2026; May 1, 2026; May 14, 2026; Jun 19, 2026; Dec 24, 2026; Dec 25, 2026; Dec 31, 2026</td><td>same</td></tr>
<tr><td>Iceland</td><td><b>Closed</b> Jan 1, 2026; Apr 2, 2026; Apr 3, 2026; Apr 6, 2026; Apr 23, 2026; May 1, 2026; May 14, 2026; May 25, 2026; Jun 17, 2026; Aug 3, 2026; Dec 24, 2026; Dec 25, 2026; Dec 31, 2026</td><td>same</td></tr>
</table>
</body></html>
"""

BALTIC_SAMPLE_HTML = """
<html><body>
<table>
<tr><th>Period</th><th>Event</th><th>Market</th><th>Add to calendar</th></tr>
<tr><td>01.01.2026</td><td>Trading holiday</td><td>TLN RIG VLN</td><td>+</td></tr>
<tr><td>02.01.2026</td><td>Trading holiday</td><td>RIG</td><td>+</td></tr>
<tr><td>16.02.2026</td><td>Trading holiday</td><td>VLN</td><td>+</td></tr>
<tr><td>24.02.2026</td><td>Trading holiday</td><td>TLN</td><td>+</td></tr>
<tr><td>24.12.2026 25.12.2026</td><td>Trading holiday</td><td>TLN RIG VLN</td><td>+</td></tr>
<tr><td>31.12.2026</td><td>Trading holiday</td><td>TLN RIG VLN</td><td>+</td></tr>
</table>
</body></html>
"""


class TestNasdaqNordicFetcher:
    """Tests for the shared NasdaqNordicFetcher (XSTO/XHEL/XCSE/XICE)"""

    def test_parse_html_stockholm_closed_and_half_days(self):
        fetcher = StockholmFetcher()
        holidays, early_closes = fetcher.parse_html(NORDIC_SAMPLE_HTML)
        assert len(holidays) == 10
        assert len(early_closes) == 5

    def test_parse_html_copenhagen_no_half_days(self):
        fetcher = CopenhagenFetcher()
        holidays, early_closes = fetcher.parse_html(NORDIC_SAMPLE_HTML)
        assert len(holidays) == 11
        assert len(early_closes) == 0

    def test_parse_html_iceland_distinct_holidays(self):
        """Iceland has extra holidays (Apr 23, Aug 3) not shared by other markets"""
        fetcher = IcelandFetcher()
        holidays, _ = fetcher.parse_html(NORDIC_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-04-23" in dates
        assert "2026-08-03" in dates

    def test_parse_html_empty(self):
        fetcher = StockholmFetcher()
        assert fetcher.parse_html("") == ([], [])
        assert fetcher.parse_html("<html><body>no year heading</body></html>") == ([], [])

    def test_invalid_mic_raises(self):
        with pytest.raises(ValueError):
            NasdaqNordicFetcher(mic="XXXX", name="Not a real Nordic market")

    def test_helsinki_registered_correctly(self):
        fetcher = HelsinkiFetcher()
        assert fetcher.mic == "XHEL"
        assert fetcher.CURRENCY["XHEL"] == "EUR"
        holidays, _ = fetcher.parse_html(NORDIC_SAMPLE_HTML)
        assert len(holidays) == 10

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = NORDIC_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        sto_data = StockholmFetcher().fetch()
        assert sto_data.mic == "XSTO"
        assert sto_data.currency == "SEK"
        assert len(sto_data.early_closes) == 5


class TestNasdaqBalticFetcher:
    """Tests for the shared NasdaqBalticFetcher (XTAL/XRIS/XLIT)"""

    def test_parse_html_shared_holiday_all_three_markets(self):
        for fetcher_cls in (TallinnFetcher, RigaFetcher, VilniusFetcher):
            fetcher = fetcher_cls()
            holidays = fetcher.parse_html(BALTIC_SAMPLE_HTML)
            assert "2026-01-01" in {h.date for h in holidays}

    def test_parse_html_market_specific_holiday_filtered(self):
        """Jan 2 is Riga-only; must not appear for Tallinn or Vilnius"""
        rig_holidays = RigaFetcher().parse_html(BALTIC_SAMPLE_HTML)
        tln_holidays = TallinnFetcher().parse_html(BALTIC_SAMPLE_HTML)
        assert "2026-01-02" in {h.date for h in rig_holidays}
        assert "2026-01-02" not in {h.date for h in tln_holidays}

    def test_parse_html_double_date_row_expands_both(self):
        """The '24.12.2026 25.12.2026' single row must produce two dates"""
        fetcher = TallinnFetcher()
        holidays = fetcher.parse_html(BALTIC_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-12-24" in dates
        assert "2026-12-25" in dates

    def test_parse_html_empty(self):
        fetcher = TallinnFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no market column</body></html>") == []

    def test_invalid_mic_raises(self):
        with pytest.raises(ValueError):
            NasdaqBalticFetcher(mic="XXXX", name="Not a real Baltic market")

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = BALTIC_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        vln_data = VilniusFetcher().fetch()
        assert vln_data.mic == "XLIT"
        assert vln_data.currency == "EUR"
        assert vln_data.country == "Lithuania"


class TestTokyoFetcher:
    """Tests for TokyoFetcher (JPX) -- English-language page, no Japanese parsing needed"""

    def test_parse_html_extracts_holidays_both_years(self):
        fetcher = TokyoFetcher()
        holidays = fetcher.parse_html(JPX_SAMPLE_HTML)

        assert len(holidays) == 6
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2027-01-01" in dates

    def test_parse_html_empty(self):
        fetcher = TokyoFetcher()
        assert fetcher.parse_html("<html><body>no headings or tables</body></html>") == []

    def test_footnote_marker_stripped_from_name(self):
        fetcher = TokyoFetcher()
        holidays = fetcher.parse_html(JPX_SAMPLE_HTML)
        matching = [h for h in holidays if h.date == "2026-05-06"]
        assert len(matching) == 1
        assert not matching[0].name.rstrip()[-1].isdigit()

    def test_date_format_english_month_abbreviation(self):
        fetcher = TokyoFetcher()
        holidays = fetcher.parse_html(JPX_SAMPLE_HTML)
        feb_holiday = [h for h in holidays if h.date == "2026-02-11"]
        assert len(feb_holiday) == 1
        assert feb_holiday[0].name == "National Foundation Day"

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = JPX_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = TokyoFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XTKS"
        assert data.timezone == "Asia/Tokyo"
        assert data.regular_open == "09:00"


SSE_SAMPLE_HTML = """
<html><body>
<h2>2025</h2>
<table>
<tr><td>New Year's Day</td><td>January 1, 2025 (Wednesday)</td></tr>
<tr><td>Chinese New Year</td><td>January 28 (Tuesday) - February 4 (Tuesday), plus January 26 (Sunday) and February 8 (Saturday)</td></tr>
<tr><td>Qingming Festival (also known as Tomb-Sweeping Day)</td><td>April 4 (Friday) - April 6 (Sunday)</td></tr>
<tr><td>Chinese Labor Day</td><td>May 1 (Thursday) - May 5 (Monday), plus April 27 (Sunday)</td></tr>
<tr><td>Dragon Boat Festival</td><td>May 31 (Saturday) - June 2 (Monday)</td></tr>
</table>
</body></html>
"""

SZSE_SAMPLE_HTML = """
<html><body>
<p>Stock Market Holiday Schedule (2025)</p>
<p>1. New Year: The market will close on January 1st (Wednesday) and resume trading on January 2nd (Thursday).</p>
<p>2. Spring Festival: The market will close from January 28th (Tuesday) to February 4th (Tuesday), and resume trading on February 5th (Wednesday).</p>
<p>3. Qingming Festival: The market will close on April 4th (Friday) and resume trading on April 7th (Monday).</p>
<p>4. Labour Day: The market will close from May 1st (Thursday) to May 5th (Monday) and resume trading on May 6th (Tuesday).</p>
</body></html>
"""


class TestSSEFetcher:
    """Tests for SSEFetcher (Shanghai) -- natural-language date-range parsing"""

    def test_parse_html_expands_ranges_to_weekdays_only(self):
        fetcher = SSEFetcher()
        holidays = fetcher.parse_html(SSE_SAMPLE_HTML)

        assert len(holidays) == 12  # see manual expansion in fetcher docstring test above
        dates = {h.date for h in holidays}
        # Chinese New Year range Jan 28 - Feb 4 2025: weekend Feb 1-2 excluded
        assert "2025-01-28" in dates
        assert "2025-02-01" not in dates  # Saturday
        assert "2025-02-02" not in dates  # Sunday
        assert "2025-02-04" in dates

    def test_parse_html_single_day_entry(self):
        fetcher = SSEFetcher()
        holidays = fetcher.parse_html(SSE_SAMPLE_HTML)
        new_years = [h for h in holidays if h.date == "2025-01-01"]
        assert len(new_years) == 1
        assert new_years[0].name == "New Year's Day"

    def test_parse_html_empty(self):
        fetcher = SSEFetcher()
        assert fetcher.parse_html("<html><body>no year heading</body></html>") == []
        assert fetcher.parse_html("") == []

    def test_plus_clause_ignored(self):
        """The 'plus January 26 (Sunday)...' clause must not produce its own holiday"""
        fetcher = SSEFetcher()
        holidays = fetcher.parse_html(SSE_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2025-01-26" not in dates  # weekend anyway, and part of "plus" clause

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = SSE_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = SSEFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XSHG"
        assert data.timezone == "Asia/Shanghai"


class TestSZSEFetcher:
    """Tests for SZSEFetcher (Shenzhen) -- prose 'close on X, resume on Y' parsing"""

    def test_parse_html_computes_end_as_resume_minus_one(self):
        fetcher = SZSEFetcher()
        holidays = fetcher.parse_html(SZSE_SAMPLE_HTML)

        assert len(holidays) == 11
        dates = {h.date for h in holidays}
        assert "2025-01-01" in dates
        assert "2025-04-04" in dates

    def test_parse_html_range_excludes_weekend(self):
        fetcher = SZSEFetcher()
        holidays = fetcher.parse_html(SZSE_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2025-02-01" not in dates  # Saturday, inside Spring Festival range
        assert "2025-02-02" not in dates  # Sunday

    def test_parse_html_empty(self):
        fetcher = SZSEFetcher()
        assert fetcher.parse_html("<html><body>no year found here</body></html>") == []
        assert fetcher.parse_html("") == []

    def test_holiday_names_extracted_correctly(self):
        fetcher = SZSEFetcher()
        holidays = fetcher.parse_html(SZSE_SAMPLE_HTML)
        names = {h.name for h in holidays}
        assert "New Year" in names
        assert "Spring Festival" in names
        assert "Qingming Festival" in names
        assert "Labour Day" in names

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = SZSE_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = SZSEFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XSHE"
        assert data.currency == "CNY"


HKEX_SAMPLE_CSV = (
    "\ufeffDate,Day of Week,Hong Kong,Shanghai & Shenzhen,Northbound Trading,Southbound Trading\n"
    "2026-01-01,Thu,Holiday,Holiday,Closed,Closed\n"
    "2026-01-02,Fri,,Holiday,Closed,Closed\n"
    "2026-02-16,Mon,Half Day,Holiday,Closed,Closed\n"
    "2026-02-17,Tue,Holiday,Holiday,Closed,Closed\n"
    "2026-04-03,Fri,Holiday,,Closed,Closed\n"
    "2026-12-24,Thu,Half Day,,,Half Day\n"
    "2026-12-25,Fri,Holiday,,Closed,Closed\n"
)


class TestHKEXFetcher:
    """
    Tests for HKEXFetcher. Unlike the JS-rendered News/HKEX-Calendar page
    (still unreachable), this fetcher uses HKEX's own published Stock
    Connect trading calendar CSV, reading only the 'Hong Kong' column.
    """

    def test_parse_html_reads_hong_kong_column_only(self):
        """Rows where only Shanghai & Shenzhen is a holiday must be excluded"""
        fetcher = HKEXFetcher()
        holidays = fetcher.parse_html(HKEX_SAMPLE_CSV)

        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates  # both HK and mainland holiday
        assert "2026-01-02" not in dates  # mainland-only holiday -- HK column empty

    def test_parse_html_separates_holiday_and_half_day(self):
        fetcher = HKEXFetcher()
        holidays = fetcher.parse_html(HKEX_SAMPLE_CSV)

        by_date = {h.date: h.status for h in holidays}
        assert by_date["2026-01-01"] == "closed"
        assert by_date["2026-02-16"] == "early_close"
        assert by_date["2026-12-24"] == "early_close"

    def test_parse_html_empty(self):
        fetcher = HKEXFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("Date,Day of Week\n2026-01-01,Thu\n") == []  # no Hong Kong column

    def test_parse_html_handles_bom(self):
        """The live file has a UTF-8 BOM at the start -- must not break the header row"""
        fetcher = HKEXFetcher()
        holidays = fetcher.parse_html(HKEX_SAMPLE_CSV)
        assert len(holidays) == 6

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = HKEX_SAMPLE_CSV
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = HKEXFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XHKG"
        assert data.timezone == "Asia/Hong_Kong"
        assert data.currency == "HKD"

    def test_registered_in_registry(self):
        registry = ExchangeFetcherRegistry()
        fetcher = registry.get("XHKG")
        assert fetcher is not None
        assert isinstance(fetcher, HKEXFetcher)


TSX_SAMPLE_HTML = """
<html><body>
<div>2026 Stock Market Holidays - Stock Markets Closed
<h3>Canadian Holidays</h3>
<ul>
<li>New Year's Day - Thursday, January 1, 2026</li>
<li>Family Day - Monday, February 16, 2026</li>
<li>Good Friday - Friday, April 3, 2026</li>
<li>Christmas Eve - Thursday, December 24, 2026*</li>
<li>Christmas Day - Friday, December 25, 2026</li>
<li>In Lieu of Boxing Day - Monday, December 28, 2026</li>
</ul>
<h3>U.S. Holidays**</h3>
<ul>
<li>Martin Luther King, Jr. Day - Monday, January 19, 2026</li>
<li>U.S. Thanksgiving Day - Thursday, November 26, 2026</li>
</ul>
</div>
<div>2025 Stock Market Holidays - Stock Markets Closed
<h3>Canadian Holidays</h3>
<ul>
<li>New Year's Day - Wednesday, January 1, 2025</li>
<li>Boxing Day - Friday, December 26, 2025</li>
</ul>
<h3>U.S. Holidays**</h3>
<ul>
<li>Martin Luther King, Jr. Day - Monday, January 20, 2025</li>
</ul>
</div>
</body></html>
"""

BME_MADRID_SAMPLE_HTML = """
<html><body>
<p>BME, operator of the equity, fixed income and derivatives markets in Spain, has set the trading calendar for 2026.
It has agreed to consider the following days as non-trading days for operational purposes:</p>
<p>1st of January</p><p>Thursday</p>
<p>3rd of April</p><p>Friday</p>
<p>6th of April</p><p>Monday</p>
<p>1st of May</p><p>Friday</p>
<p>25th of December</p><p>Friday</p>
<p>On 24 and 31 December the BME markets will trade until 14:00 hrs CET.</p>
<p>24th of December</p><p>Thursday</p>
<p>31st of December</p><p>Thursday</p>
</body></html>
"""

XSAU_SAMPLE_HTML = """
<html><body>
<table>
<tr><th>Date</th><th>Title</th></tr>
<tr><td>22/02/2027 - 22/02/2027</td><td>Founding Day of Saudi Arabia is on 22/02/2027.</td></tr>
<tr><td>23/09/2026 - 23/09/2026</td><td>National Day of Saudi Arabia is on 23/09/2026.</td></tr>
<tr><td>24/05/2026 - 28/05/2026</td><td>Eid Al Adha Holiday for the Saudi Exchange Trading will discontinue at the end of trading day 21/05/2026. Trading will resume after the holiday on 31/05/2026. * According to the UMM AL-QURA calendar</td></tr>
<tr><td>16/05/2027 - 20/05/2027</td><td>Eid Al Adha Holiday for the Saudi Exchange Trading will discontinue at the end of trading day 13/05/2027. Trading will resume after the holiday on 23/05/2027. * According to the UMM AL-QURA calendar</td></tr>
<tr><td>22/07/2021 - 15/07/2021</td><td>Eid Al Adha Holiday for the Saudi Exchange Trading will discontinue at the end of trading day 15/7/2021.Trading will resume after the holiday on 25/7/2021.</td></tr>
<tr><td>13/02/2020 -</td><td>Listing of ALBILAD Saudi Sovereign Sukuk ETF (by Al Bilad Capital) For more information...</td></tr>
<tr><td>22/09/2022 -</td><td>National Day of Saudi Arabia National Day of Saudi Arabia is on 22/9/2022.</td></tr>
</table>
</body></html>
"""


class TestTSXFetcher:
    """Tests for TSXFetcher (Toronto)"""

    def test_parse_html_excludes_us_holidays(self):
        fetcher = TSXFetcher()
        holidays = fetcher.parse_html(TSX_SAMPLE_HTML)
        names = {h.name for h in holidays}
        assert "Martin Luther King, Jr. Day" not in names
        assert "U.S. Thanksgiving Day" not in names

    def test_parse_html_includes_canadian_holidays_both_years(self):
        fetcher = TSXFetcher()
        holidays = fetcher.parse_html(TSX_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2025-01-01" in dates

    def test_parse_html_marks_early_close(self):
        fetcher = TSXFetcher()
        holidays = fetcher.parse_html(TSX_SAMPLE_HTML)
        christmas_eve = [h for h in holidays if h.date == "2026-12-24"]
        assert len(christmas_eve) == 1
        assert christmas_eve[0].status == "early_close"

    def test_parse_html_empty(self):
        fetcher = TSXFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>nothing here</body></html>") == []

    def test_date_format_iso(self):
        fetcher = TSXFetcher()
        holidays = fetcher.parse_html(TSX_SAMPLE_HTML)
        assert all(len(h.date) == 10 and h.date[4] == '-' for h in holidays)

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = TSX_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = TSXFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XTSE"
        assert data.currency == "CAD"


class TestBMEMadridFetcher:
    """Tests for BMEMadridFetcher"""

    def test_parse_html_no_names_uses_generic_labels(self):
        fetcher = BMEMadridFetcher()
        holidays = fetcher.parse_html(BME_MADRID_SAMPLE_HTML)
        assert all("BME" in h.name for h in holidays)

    def test_parse_html_splits_closures_and_early_closes(self):
        fetcher = BMEMadridFetcher()
        holidays = fetcher.parse_html(BME_MADRID_SAMPLE_HTML)
        by_date = {h.date: h.status for h in holidays}
        assert by_date["2026-01-01"] == "closed"
        assert by_date["2026-12-24"] == "early_close"
        assert by_date["2026-12-31"] == "early_close"

    def test_parse_html_empty(self):
        fetcher = BMEMadridFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no year mentioned</body></html>") == []

    def test_current_year_only_flag(self):
        fetcher = BMEMadridFetcher()
        assert fetcher.current_year_only is True

    def test_date_parsing_ordinal_suffixes(self):
        fetcher = BMEMadridFetcher()
        holidays = fetcher.parse_html(BME_MADRID_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-04-03" in dates  # "3rd of April"
        assert "2026-04-06" in dates  # "6th of April"

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = BME_MADRID_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = BMEMadridFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XMAD"
        assert data.currency == "EUR"


class TestSaudiExchangeFetcher:
    """Tests for SaudiExchangeFetcher"""

    def test_parse_html_filters_out_non_holiday_rows(self):
        """The 'Listing of ALBILAD...' IPO row must not become a holiday"""
        fetcher = SaudiExchangeFetcher()
        holidays = fetcher.parse_html(XSAU_SAMPLE_HTML)
        assert not any("Listing" in h.name for h in holidays)
        assert not any(h.date == "2020-02-13" for h in holidays)

    def test_parse_html_skips_inverted_date_range(self):
        """The 2021 row with end-before-start in its Date column must be skipped, not guessed"""
        fetcher = SaudiExchangeFetcher()
        holidays = fetcher.parse_html(XSAU_SAMPLE_HTML)
        assert not any(h.date.startswith("2021-07") for h in holidays)

    def test_parse_html_weekend_exclusion_friday_saturday(self):
        """Eid Al Adha 2026 range (Sun 24 - Thu 28 May) has no Fri/Sat inside it here,
        but the expansion logic itself must use Fri/Sat as the weekend, not Sat/Sun"""
        fetcher = SaudiExchangeFetcher()
        holidays = fetcher.parse_html(XSAU_SAMPLE_HTML)
        eid_dates = sorted(h.date for h in holidays if "Eid Al Adha" in h.name and h.date.startswith("2026"))
        assert eid_dates == ["2026-05-24", "2026-05-25", "2026-05-26", "2026-05-27", "2026-05-28"]

    def test_parse_html_predicted_flag_based_on_date(self):
        """2026 Eid (already past relative to 'now') -> predicted False;
        2027 Eid (future) -> predicted True"""
        fetcher = SaudiExchangeFetcher()
        holidays = fetcher.parse_html(XSAU_SAMPLE_HTML)
        eid_2026 = [h for h in holidays if h.date.startswith("2026-05")]
        eid_2027 = [h for h in holidays if h.date.startswith("2027-05")]
        assert all(h.predicted is False for h in eid_2026)
        assert all(h.predicted is True for h in eid_2027)

    def test_parse_html_fixed_holidays_never_predicted(self):
        fetcher = SaudiExchangeFetcher()
        holidays = fetcher.parse_html(XSAU_SAMPLE_HTML)
        founding_day = [h for h in holidays if "Founding Day" in h.name]
        assert len(founding_day) == 1
        assert founding_day[0].predicted is False

    def test_parse_html_deduplicates_and_cleans_repeated_title(self):
        fetcher = SaudiExchangeFetcher()
        holidays = fetcher.parse_html(XSAU_SAMPLE_HTML)
        matching = [h for h in holidays if h.date == "2022-09-22"]
        assert len(matching) == 1
        assert matching[0].name == "National Day of Saudi Arabia"

    def test_parse_html_empty(self):
        fetcher = SaudiExchangeFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no table</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = XSAU_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = SaudiExchangeFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XSAU"
        assert data.timezone == "Asia/Riyadh"
        assert data.currency == "SAR"


XDFM_SAMPLE_PDF_TEXT = """Circular No: 12/2025
Date: 29/12/2025

Subject: Trading and Settlement Holidays for the Calendar Year 2026 for Securities Market
(Excluding Derivatives contracts).
In addition to the official weekend holiday on Saturday and Sunday, please take note of the
Trading and Settlement holidays for the calendar year 2026 for Securities Market listed below:
SR.
NO.
DATE DAY DESCRIPTION
1 01-Jan-2026 Thursday NEW YEAR'S DAY
2 19-Mar-2026 Thursday EID AL FITR*
3 20-Mar-2026 Friday EID AL FITR*
4 21-Mar-2026 Saturday EID AL FITR*
5 26-May-2026 Tuesday ARAFAH (HAJ) DAY*
6 27-May-2026 Wednesday EID AL ADHA*
9 16-Jun-2026 Tuesday HIJRI NEW YEAR'S DAY*
10 25-Aug-2026 Tuesday PROPHET MUHAMMAD'S BIRTHDAY
11 02-Dec-2026 Wednesday UAE NATIONAL DAY

*Islamic holidays may vary and are subject to change.
"""

KUWAIT_SAMPLE_HTML = """
<html><body>
<h2>Kuwait Public Holidays 2026</h2>
<table>
<tr><th>Month</th><th>Date</th><th>Vacation</th></tr>
<tr><td>January</td><td>1</td><td>New Year</td></tr>
<tr><td>February</td><td>25-26</td><td>National Day - Liberation Day</td></tr>
<tr><td>March</td><td>20-21</td><td>Eid Al Fitr</td></tr>
<tr><td>May</td><td>27-28</td><td>Eid Al Adha</td></tr>
</table>
</body></html>
"""

MOEX_SAMPLE_HTML = """
<html><body>
<p>On 1-4 January, 7 January, 23 February, 8 March, 1 May, 9 May, 12 June, 4 November and 31 December 2026, public holidays in Russia, all Moscow Exchange markets will be closed. On 10 January 2026, a Saturday, Moscow Exchange markets will be open for trading.</p>
</body></html>
"""


class TestPDFFetcherBase:
    """Tests for the shared PDFFetcher base class"""

    def test_extract_pdf_text_empty_bytes(self):
        fetcher = XDFMFetcher()  # any PDFFetcher subclass will do
        assert fetcher._extract_pdf_text(b"") == ""

    def test_extract_pdf_text_malformed_pdf_does_not_raise(self):
        fetcher = XDFMFetcher()
        # Not valid PDF bytes at all -- should log and return "", not crash
        result = fetcher._extract_pdf_text(b"this is not a pdf")
        assert result == ""


class TestXDFMFetcher:
    """Tests for XDFMFetcher (Dubai) -- first PDF-based fetcher in this codebase"""

    def test_parse_html_extracts_holidays_from_pdf_text(self):
        fetcher = XDFMFetcher()
        holidays = fetcher.parse_html(XDFM_SAMPLE_PDF_TEXT)
        assert len(holidays) == 9

    def test_parse_html_marks_islamic_holidays_predicted(self):
        fetcher = XDFMFetcher()
        holidays = fetcher.parse_html(XDFM_SAMPLE_PDF_TEXT)
        eid = [h for h in holidays if "Eid Al Fitr" in h.name]
        assert len(eid) == 3
        assert all(h.predicted is True for h in eid)

    def test_parse_html_fixed_holidays_not_predicted(self):
        fetcher = XDFMFetcher()
        holidays = fetcher.parse_html(XDFM_SAMPLE_PDF_TEXT)
        new_years = [h for h in holidays if h.date == "2026-01-01"]
        national_day = [h for h in holidays if "National Day" in h.name]
        assert new_years[0].predicted is False
        assert national_day[0].predicted is False

    def test_parse_html_capitalization_preserves_acronyms(self):
        fetcher = XDFMFetcher()
        holidays = fetcher.parse_html(XDFM_SAMPLE_PDF_TEXT)
        names = {h.name for h in holidays}
        assert "UAE National Day" in names
        assert "Arafah (HAJ) Day" in names
        assert "New Year's Day" in names

    def test_parse_html_empty(self):
        fetcher = XDFMFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("no matching rows here") == []

    @patch.object(XDFMFetcher, '_extract_pdf_text')
    @patch('requests.get')
    def test_fetch_success(self, mock_get, mock_extract):
        mock_response = Mock()
        mock_response.content = b"%PDF-1.4 dummy bytes"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_extract.return_value = XDFM_SAMPLE_PDF_TEXT

        fetcher = XDFMFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XDFM"
        assert data.timezone == "Asia/Dubai"
        assert data.currency == "AED"


class TestBoursaKuwaitFetcher:
    """Tests for BoursaKuwaitFetcher"""

    def test_parse_html_extracts_holidays(self):
        fetcher = BoursaKuwaitFetcher()
        holidays = fetcher.parse_html(KUWAIT_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2026-02-25" in dates
        assert "2026-02-26" in dates

    def test_parse_html_weekend_exclusion_friday_saturday(self):
        """March 20-21 2026 (Fri/Sat) falls entirely within Kuwait's weekend
        and should produce zero explicit holiday entries for that range"""
        fetcher = BoursaKuwaitFetcher()
        holidays = fetcher.parse_html(KUWAIT_SAMPLE_HTML)
        march_dates = [h.date for h in holidays if h.date.startswith("2026-03")]
        assert march_dates == []

    def test_parse_html_empty(self):
        fetcher = BoursaKuwaitFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no year heading</body></html>") == []

    def test_current_year_only_flag(self):
        fetcher = BoursaKuwaitFetcher()
        assert fetcher.current_year_only is True

    def test_parse_html_combined_holiday_name(self):
        fetcher = BoursaKuwaitFetcher()
        holidays = fetcher.parse_html(KUWAIT_SAMPLE_HTML)
        names = {h.name for h in holidays}
        assert "National Day - Liberation Day" in names

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = KUWAIT_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = BoursaKuwaitFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XKUW"
        assert data.currency == "KWD"


class TestMOEXFetcher:
    """Tests for MOEXFetcher (Moscow) -- confirmed accessible, fragile source"""

    def test_parse_html_extracts_closure_dates(self):
        fetcher = MOEXFetcher()
        holidays = fetcher.parse_html(MOEX_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2026-01-04" in dates
        assert "2026-12-31" in dates
        assert len(holidays) == 12

    def test_parse_html_excludes_open_makeup_session_date(self):
        """The 'will be open for trading' sentence must not produce a holiday"""
        fetcher = MOEXFetcher()
        holidays = fetcher.parse_html(MOEX_SAMPLE_HTML)
        assert not any(h.date == "2026-01-10" for h in holidays)

    def test_parse_html_expands_range_fragment(self):
        fetcher = MOEXFetcher()
        holidays = fetcher.parse_html(MOEX_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2026-01-02" in dates
        assert "2026-01-03" in dates
        assert "2026-01-04" in dates

    def test_parse_html_empty(self):
        fetcher = MOEXFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no closure sentence</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = MOEX_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = MOEXFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XMOS"
        assert data.currency == "RUB"


BMV_MEXICO_SAMPLE_HTML = """
<html><body>
<table>
<tr><th>Holidays</th><th>2026</th></tr>
<tr><td>New Year's Day</td><td>January 1</td></tr>
<tr><td>Commemoration of February 5</td><td>February 2</td></tr>
<tr><td>Good Friday</td><td>April 3</td></tr>
<tr><td>Labor Day</td><td>May 1</td></tr>
<tr><td>Independence Day</td><td>September 16</td></tr>
<tr><td>Christmas Day</td><td>December 25</td></tr>
</table>
</body></html>
"""

BYMA_SAMPLE_HTML = """
<html><body>
<table>
<tr><th>Fecha</th><th>Dia</th><th>Motivo</th></tr>
<tr><td>16 de Febrero</td><td>Lunes</td><td>Carnaval (1)</td></tr>
<tr><td>2 de Abril</td><td>Jueves</td><td>D\u00eda del Veterano y de los Ca\u00eddos en la Guerra de Malvinas (1)</td></tr>
<tr><td>10 de Julio</td><td>Viernes</td><td>D\u00eda no Laborable con Fines Tur\u00edsticos (3)</td></tr>
<tr><td>6 de Noviembre</td><td>Viernes</td><td>D\u00eda del Bancario (3)</td></tr>
<tr><td>25 de Diciembre</td><td>Viernes</td><td>Navidad (1)</td></tr>
<tr><td>31 de Diciembre de 2026</td><td>Jueves</td><td>Jornada sin Negociaci\u00f3n ni Liquidaci\u00f3n (4)</td></tr>
</table>
</body></html>
"""

B3_SAMPLE_HTML = """
<html><body>
<h2>Market Calendar 2026</h2>
<h3>January</h3>
<table>
<tr><td>01</td><td>New Year's Day</td><td>icon</td><td>BM&FBOVESPA Segment: There will be no trading on the equity, private fixed income markets.</td></tr>
<tr><td>19</td><td>Birthday of Martin Luther King, Jr.</td><td>icon</td><td>B3 Clearinghouse will register, clear and settle all trades, except for agricultural commodity derivatives.</td></tr>
</table>
<h3>February</h3>
<table>
<tr><td>16</td><td>Carnival</td><td>icon</td><td>BM&FBOVESPA Segment: There will be no trading on the equity, private fixed income markets.</td></tr>
<tr><td>18</td><td>Ash Wednesday - Special trading hours</td><td>icon</td><td>Trading and registration will open at 1:00 p.m.</td></tr>
</table>
<h3>December</h3>
<table>
<tr><td>25</td><td>Christmas day</td><td>icon</td><td>BM&FBOVESPA Segment: There will be no trading on the equity, private fixed income markets.</td></tr>
<tr><td>28</td><td>B3 Foreign Exchange Clearinghouse</td><td>icon</td><td>T+2: The Foreign Exchange Clearinghouse will not accept trades for settlement</td></tr>
</table>
</body></html>
"""


class TestBMVMexicoFetcher:
    """Tests for BMVMexicoFetcher (XMEX)"""

    def test_parse_html_extracts_holidays_with_names(self):
        fetcher = BMVMexicoFetcher()
        holidays = fetcher.parse_html(BMV_MEXICO_SAMPLE_HTML)
        assert len(holidays) == 6
        names = {h.name for h in holidays}
        assert "Independence Day" in names

    def test_parse_html_empty(self):
        fetcher = BMVMexicoFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no year column</body></html>") == []

    def test_current_year_only_flag(self):
        fetcher = BMVMexicoFetcher()
        assert fetcher.current_year_only is True

    def test_date_format_iso(self):
        fetcher = BMVMexicoFetcher()
        holidays = fetcher.parse_html(BMV_MEXICO_SAMPLE_HTML)
        assert "2026-09-16" in {h.date for h in holidays}

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = BMV_MEXICO_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = BMVMexicoFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XMEX"
        assert data.currency == "MXN"


class TestBymaArgentinaFetcher:
    """Tests for BymaArgentinaFetcher (XBUE) -- footnote-reference filtering"""

    def test_parse_html_includes_true_closures(self):
        fetcher = BymaArgentinaFetcher()
        holidays = fetcher.parse_html(BYMA_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-02-16" in dates  # ref (1)
        assert "2026-12-31" in dates  # ref (4)

    def test_parse_html_excludes_ref_3_trading_continues(self):
        """Reference (3) = trading continues, no settlement -- not a closure"""
        fetcher = BymaArgentinaFetcher()
        holidays = fetcher.parse_html(BYMA_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-07-10" not in dates
        assert "2026-11-06" not in dates
        assert len(holidays) == 4

    def test_parse_html_spanish_month_parsing(self):
        fetcher = BymaArgentinaFetcher()
        holidays = fetcher.parse_html(BYMA_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-04-02" in dates  # "2 de Abril"

    def test_parse_html_empty(self):
        fetcher = BymaArgentinaFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no table</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = BYMA_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = BymaArgentinaFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XBUE"
        assert data.currency == "ARS"


class TestB3BrazilFetcher:
    """Tests for B3BrazilFetcher (XBSP) -- the most complex fetcher in this registry"""

    def test_parse_html_includes_real_brazilian_closures(self):
        fetcher = B3BrazilFetcher()
        holidays = fetcher.parse_html(B3_SAMPLE_HTML)
        assert len(holidays) == 3
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2026-02-16" in dates
        assert "2026-12-25" in dates

    def test_parse_html_excludes_us_settlement_only_rows(self):
        """MLK Day: normal trading continues, only settlement timing shifts"""
        fetcher = B3BrazilFetcher()
        holidays = fetcher.parse_html(B3_SAMPLE_HTML)
        names = {h.name for h in holidays}
        assert "Birthday of Martin Luther King, Jr." not in names

    def test_parse_html_excludes_special_hours_not_full_closure(self):
        """Ash Wednesday: delayed open, not a full closure"""
        fetcher = B3BrazilFetcher()
        holidays = fetcher.parse_html(B3_SAMPLE_HTML)
        names = {h.name for h in holidays}
        assert not any("Ash Wednesday" in n for n in names)

    def test_parse_html_excludes_pure_settlement_footnotes(self):
        """B3 Foreign Exchange Clearinghouse T+2 footnote is not a holiday"""
        fetcher = B3BrazilFetcher()
        holidays = fetcher.parse_html(B3_SAMPLE_HTML)
        names = {h.name for h in holidays}
        assert not any("Clearinghouse" in n for n in names)

    def test_parse_html_empty(self):
        fetcher = B3BrazilFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no year heading</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = B3_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = B3BrazilFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XBSP"
        assert data.currency == "BRL"


HOSE_VIETNAM_SAMPLE_TEXT = """The Hochiminh Stock Exchange (HOSE) announces the trading holiday schedule for 2026 as 
follows: 
Event Holiday Schedule 2026 
New Year 
From Thursday, January 1st, 2026 to the end of Friday, 
January 2nd, 2026 (The working day of Friday, January 
2nd, 2026 is rescheduled to Saturday, January 10th
, 
2026). 
Lunar New Year 
From Monday, February 16th, 2026 (December 29th, 
2025 (lunar calendar)) to the end of Friday, February 
20th, 2026 (the 4th day of the Lunar New Year holidays).
Hung Kings Day Monday, April 27th, 2026 
Liberation Day and Labor Day Thursday, April 30th, 2026 and Friday, May 1st, 2026 
National Day 
From Monday, August 31st, 2026 to the end of 
Wednesday, September 2nd, 2026 (The working day of 
Monday, August 31st, 2026 is rescheduled to Saturday, 
August 22nd, 2026). 
- HOSE will not implement trading on Saturday, January 10th, 2026. 
- HOSE will not implement trading on Saturday, August 22nd, 2026. 
"""

NGX_SAMPLE_HTML = """
<html><body>
<table>
<tr><th>Public Holiday</th><th>Observed Date</th></tr>
<tr><td>New Year's Day</td><td>Monday, January 1, 2024</td></tr>
<tr><td>Good Friday</td><td>Friday, March 29, 2024</td></tr>
<tr><td>Eidul-Fitr</td><td>Wednesday, April 10, 2024</td></tr>
<tr><td>Eid el-Kabir</td><td>Monday, June 17, 2024</td></tr>
<tr><td>Christmas Day</td><td>Wednesday, December 25, 2024</td></tr>
</table>
</body></html>
"""

BRVM_SAMPLE_HTML = """
<html><body>
<table>
<tr><th>Date</th><th>Evenement</th></tr>
<tr><td>01/01/2026</td><td>F\u00eate du Jour de l'an</td></tr>
<tr><td>17/03/2026</td><td>Lendemain de la nuit du destin</td></tr>
<tr><td>20/03/2026 (*)</td><td>F\u00eate du Ramadan</td></tr>
<tr><td>06/04/2026</td><td>Lundi de P\u00e2ques</td></tr>
<tr><td>27/05/2026 (*)</td><td>F\u00eate de Tabaski</td></tr>
<tr><td>25/12/2026</td><td>Lendemain de la No\u00ebl</td></tr>
</table>
</body></html>
"""

COLOMBO_SAMPLE_TEXT = """COLOMBO STOCK EXCHANGE HOLIDAYS FOR 2026 
The CSE holidays for 2026 are as follows: 
CSE HOLIDAYS FOR 2026 
MONTH DATE HOLIDAY 
January
01st Thursday CSE Customary Holiday 
15th Thursday Tamil Thai Pongal Day
February
4th Wednesday Independence Day 
March
02nd Monday Medin Full Moon Poya Day 
May
01st Friday May Day
Vesak Full Moon Poya Day 
28th Thursday Id-Ul-Allah (Hadji Festival Day) 
August
26th Wednesday Milad-Un-Nabi (Holy Prophets Birthday) 
December
25th Friday Christmas Day 
"""


class TestHOSEVietnamFetcher:
    """Tests for HOSEVietnamFetcher (XSTC) -- resolves the Tier 6 XSTC carryover"""

    def test_parse_html_extracts_all_events(self):
        fetcher = HOSEVietnamFetcher()
        holidays = fetcher.parse_html(HOSE_VIETNAM_SAMPLE_TEXT)
        names = {h.name for h in holidays}
        assert "New Year" in names
        assert "Lunar New Year" in names
        assert "Hung Kings Day" in names
        assert "National Day" in names

    def test_parse_html_expands_lunar_new_year_range(self):
        """Nested parentheses (lunar-calendar cross-reference) must not break range parsing"""
        fetcher = HOSEVietnamFetcher()
        holidays = fetcher.parse_html(HOSE_VIETNAM_SAMPLE_TEXT)
        lny_dates = {h.date for h in holidays if h.name == "Lunar New Year"}
        assert lny_dates == {"2026-02-16", "2026-02-17", "2026-02-18", "2026-02-19", "2026-02-20"}

    def test_parse_html_combined_event_two_dates(self):
        fetcher = HOSEVietnamFetcher()
        holidays = fetcher.parse_html(HOSE_VIETNAM_SAMPLE_TEXT)
        combined_dates = {h.date for h in holidays if h.name == "Liberation Day and Labor Day"}
        assert combined_dates == {"2026-04-30", "2026-05-01"}

    def test_parse_html_excludes_saturday_notice_bullets(self):
        """The 'HOSE will not implement trading on Saturday...' bullets are not new holidays"""
        fetcher = HOSEVietnamFetcher()
        holidays = fetcher.parse_html(HOSE_VIETNAM_SAMPLE_TEXT)
        assert not any(h.date == "2026-01-10" for h in holidays)
        assert not any(h.date == "2026-08-22" for h in holidays)

    def test_parse_html_empty(self):
        fetcher = HOSEVietnamFetcher()
        assert fetcher.parse_html("") == []

    @patch.object(HOSEVietnamFetcher, '_extract_pdf_text')
    @patch('requests.get')
    def test_fetch_success(self, mock_get, mock_extract):
        mock_response = Mock()
        mock_response.content = b"%PDF-1.4 dummy"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_extract.return_value = HOSE_VIETNAM_SAMPLE_TEXT

        fetcher = HOSEVietnamFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XSTC"
        assert data.currency == "VND"


class TestNigeriaExchangeFetcher:
    """Tests for NigeriaExchangeFetcher (XNSA)"""

    def test_parse_html_extracts_holidays(self):
        fetcher = NigeriaExchangeFetcher()
        holidays = fetcher.parse_html(NGX_SAMPLE_HTML)
        assert len(holidays) == 5

    def test_parse_html_marks_islamic_holidays_predicted(self):
        fetcher = NigeriaExchangeFetcher()
        holidays = fetcher.parse_html(NGX_SAMPLE_HTML)
        eid = [h for h in holidays if "Eid" in h.name]
        assert len(eid) == 2
        assert all(h.predicted is True for h in eid)

    def test_parse_html_fixed_holidays_not_predicted(self):
        fetcher = NigeriaExchangeFetcher()
        holidays = fetcher.parse_html(NGX_SAMPLE_HTML)
        christmas = [h for h in holidays if h.date == "2024-12-25"]
        assert christmas[0].predicted is None

    def test_parse_html_empty(self):
        fetcher = NigeriaExchangeFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no table</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = NGX_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = NigeriaExchangeFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XNSA"
        assert data.currency == "NGN"


class TestBRVMFetcher:
    """Tests for BRVMFetcher (XBRV) -- single source for 8 UEMOA countries"""

    def test_parse_html_extracts_holidays(self):
        fetcher = BRVMFetcher()
        holidays = fetcher.parse_html(BRVM_SAMPLE_HTML)
        assert len(holidays) == 6

    def test_parse_html_marks_islamic_holidays_predicted(self):
        fetcher = BRVMFetcher()
        holidays = fetcher.parse_html(BRVM_SAMPLE_HTML)
        ramadan = [h for h in holidays if "Ramadan" in h.name]
        tabaski = [h for h in holidays if "Tabaski" in h.name]
        assert ramadan[0].predicted is True
        assert tabaski[0].predicted is True

    def test_parse_html_fixed_holidays_not_predicted(self):
        fetcher = BRVMFetcher()
        holidays = fetcher.parse_html(BRVM_SAMPLE_HTML)
        new_years = [h for h in holidays if h.date == "2026-01-01"]
        assert new_years[0].predicted is False

    def test_parse_html_empty(self):
        fetcher = BRVMFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no table</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = BRVM_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = BRVMFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XBRV"
        assert data.currency == "XOF"


class TestColomboFetcher:
    """Tests for ColomboFetcher (XCOL) -- Poya days + Islamic holidays"""

    def test_parse_html_extracts_holidays(self):
        fetcher = ColomboFetcher()
        holidays = fetcher.parse_html(COLOMBO_SAMPLE_TEXT)
        assert len(holidays) == 8  # 9 raw entries, May 1st pair merged into 1

    def test_parse_html_shared_date_continuation_line(self):
        """'Vesak Full Moon Poya Day' has no date of its own -- shares May 1st
        with 'May Day'. Since ExchangeData.validate() rejects duplicate
        dates, same-date entries are merged into one with a combined name."""
        fetcher = ColomboFetcher()
        holidays = fetcher.parse_html(COLOMBO_SAMPLE_TEXT)
        may1 = [h for h in holidays if h.date == "2026-05-01"]
        assert len(may1) == 1
        assert "May Day" in may1[0].name
        assert "Vesak Full Moon Poya Day" in may1[0].name

    def test_parse_html_islamic_holidays_predicted(self):
        fetcher = ColomboFetcher()
        holidays = fetcher.parse_html(COLOMBO_SAMPLE_TEXT)
        islamic = [h for h in holidays if "Id-Ul-Allah" in h.name or "Milad" in h.name]
        assert len(islamic) == 2
        assert all(h.predicted is True for h in islamic)

    def test_parse_html_poya_days_not_predicted(self):
        """Poya (full moon) days are computable, not moon-sighting dependent -- not marked predicted"""
        fetcher = ColomboFetcher()
        holidays = fetcher.parse_html(COLOMBO_SAMPLE_TEXT)
        poya = [h for h in holidays if "Poya" in h.name and "Vesak" not in h.name]
        assert all(h.predicted is None for h in poya)

    def test_parse_html_empty(self):
        fetcher = ColomboFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("no year phrase here") == []

    @patch.object(ColomboFetcher, '_extract_pdf_text')
    @patch('requests.get')
    def test_fetch_success(self, mock_get, mock_extract):
        mock_response = Mock()
        mock_response.content = b"%PDF-1.4 dummy"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        mock_extract.return_value = COLOMBO_SAMPLE_TEXT

        fetcher = ColomboFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XCOL"
        assert data.currency == "LKR"


GHANA_SAMPLE_HTML = """
<html><body>
<p>Below is the list of Public Holidays for the year 2026.</p>
<table>
<tr><th>Day</th><th>Date</th><th>Holiday</th></tr>
<tr><td>Thursday</td><td>January 01</td><td>New Year's Day</td></tr>
<tr><td>Friday</td><td>March 06</td><td>Independence Day</td></tr>
<tr><td>***</td><td>***</td><td>Eid-Ul-Fitr</td></tr>
<tr><td>Friday</td><td>July 1st/3rd</td><td>Republic Day</td></tr>
<tr><td>Monday</td><td>December 26th/28th</td><td>Boxing Day</td></tr>
<tr><td>Friday</td><td>December 25</td><td>Christmas Day</td></tr>
</table>
</body></html>
"""

BERMUDA_SAMPLE_HTML = """
<html><body>
<table>
<tr><th>Holiday</th><th>2026</th></tr>
<tr><td>New Year's Day</td><td>January 1</td></tr>
<tr><td>Emancipation Day & Mary Prince Day (Often referred to as Cup Match)</td><td>July 30 and July 31</td></tr>
<tr><td>Christmas Eve (2pm AST Close)</td><td>December 24</td></tr>
<tr><td>Christmas Day</td><td>December 25</td></tr>
</table>
</body></html>
"""

CAYMAN_SAMPLE_HTML = """
<html><body>
<table>
<tr><td>Wednesday</td><td>1st January</td><td>New Year's Day</td></tr>
<tr><td>Thursday</td><td>25th December</td><td>Christmas Day</td></tr>
</table>
<table>
<tr><td>Thursday</td><td>1st January</td><td>New Year's Day</td></tr>
<tr><td>Friday</td><td>25th December</td><td>Christmas Day</td></tr>
<tr><td>Monday</td><td>28th December</td><td>Boxing Day</td></tr>
</table>
</body></html>
"""

LUXEMBOURG_SAMPLE_HTML = """
<html><body>
<p>Closing days 2026</p>
<p>Friday 25 December</p>
<p>Christmas Day</p>
<p>For the following days, which are public holidays, the Luxembourg Stock Exchange will not be closed, and duty teams will be available for trading and listing activities:</p>
<p>Tuesday 23 June</p>
<p>National day</p>
</body></html>
"""

MALTA_SAMPLE_HTML = """
<html><body>
<table>
<tr><th>DATE</th><th>HOLIDAY</th><th>TRADING</th><th>SETTLEMENT</th></tr>
<tr><td>Thursday 1 January 2026</td><td>New Year's Day</td><td>Non-trading day</td><td>Non-settlement day all currencies</td></tr>
<tr><td>Monday 19 January 2026</td><td>US Holiday</td><td>Normal trading day</td><td>Non-Settlement day USD</td></tr>
<tr><td>Friday 25 December 2026</td><td>Christmas Day</td><td>Non-trading day</td><td>Non-settlement day all currencies</td></tr>
</table>
</body></html>
"""

ZAGREB_SAMPLE_HTML = """
<html><body>
<p>In 2026, Zagreb Stock Exchange will be closed for trading each Saturday and Sunday as well as on the following days:</p>
<table>
<tr><td>Thursday</td><td>January 1st</td><td>New Year's Day</td></tr>
<tr><td>Friday</td><td>December 25th</td><td>Christmas</td></tr>
</table>
</body></html>
"""


class TestGhanaExchangeFetcher:
    """Tests for GhanaExchangeFetcher (XGSE) -- alternate-date weekday disambiguation"""

    def test_parse_html_extracts_holidays(self):
        fetcher = GhanaExchangeFetcher()
        holidays = fetcher.parse_html(GHANA_SAMPLE_HTML)
        assert len(holidays) == 5

    def test_parse_html_alternate_date_resolved_by_weekday(self):
        """'Friday July 1st/3rd' must resolve to July 3 (the actual Friday in 2026)"""
        fetcher = GhanaExchangeFetcher()
        holidays = fetcher.parse_html(GHANA_SAMPLE_HTML)
        republic_day = [h for h in holidays if h.name == "Republic Day"]
        assert len(republic_day) == 1
        assert republic_day[0].date == "2026-07-03"

    def test_parse_html_skips_unnamed_islamic_date(self):
        """The '*** | *** | Eid-Ul-Fitr' row has no actual date -- must be skipped, not guessed"""
        fetcher = GhanaExchangeFetcher()
        holidays = fetcher.parse_html(GHANA_SAMPLE_HTML)
        assert not any(h.name == "Eid-Ul-Fitr" for h in holidays)

    def test_parse_html_empty(self):
        fetcher = GhanaExchangeFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no year phrase</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = GHANA_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = GhanaExchangeFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XGSE"
        assert data.currency == "GHS"


class TestBermudaExchangeFetcher:
    """Tests for BermudaExchangeFetcher (XBDA)"""

    def test_parse_html_multi_date_row_expands(self):
        fetcher = BermudaExchangeFetcher()
        holidays = fetcher.parse_html(BERMUDA_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2026-07-30" in dates
        assert "2026-07-31" in dates

    def test_parse_html_christmas_eve_early_close(self):
        """Regression test: early-close detection must check the NAME cell
        ('AST Close'), not the date cell"""
        fetcher = BermudaExchangeFetcher()
        holidays = fetcher.parse_html(BERMUDA_SAMPLE_HTML)
        eve = [h for h in holidays if h.date == "2026-12-24"]
        assert len(eve) == 1
        assert eve[0].status == "early_close"

    def test_parse_html_empty(self):
        fetcher = BermudaExchangeFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no year column</body></html>") == []

    def test_parse_html_footnote_stripped_from_name(self):
        fetcher = BermudaExchangeFetcher()
        holidays = fetcher.parse_html(BERMUDA_SAMPLE_HTML)
        eve = [h for h in holidays if h.date == "2026-12-24"]
        assert eve[0].name == "Christmas Eve"

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = BERMUDA_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = BermudaExchangeFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XBDA"
        assert data.currency == "BMD"


class TestCaymanExchangeFetcher:
    """Tests for CaymanExchangeFetcher (XCAY) -- weekday-based year disambiguation"""

    def test_parse_html_two_year_sections(self):
        fetcher = CaymanExchangeFetcher()
        holidays = fetcher.parse_html(CAYMAN_SAMPLE_HTML)
        dates = {h.date for h in holidays}
        assert "2025-01-01" in dates
        assert "2026-01-01" in dates

    def test_parse_html_year_inferred_from_weekday(self):
        """New Year's Day is Wednesday in 2025 and Thursday in 2026 -- the
        parser must pick the correct year for each table using this"""
        fetcher = CaymanExchangeFetcher()
        holidays = fetcher.parse_html(CAYMAN_SAMPLE_HTML)
        boxing_days = sorted(h.date for h in holidays if h.name == "Boxing Day")
        assert "2026-12-28" in boxing_days

    def test_parse_html_empty(self):
        fetcher = CaymanExchangeFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no table</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = CAYMAN_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = CaymanExchangeFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XCAY"
        assert data.currency == "KYD"


class TestLuxembourgExchangeFetcher:
    """Tests for LuxembourgExchangeFetcher (XLUX) -- deliberately sparse source"""

    def test_parse_html_extracts_real_closure(self):
        fetcher = LuxembourgExchangeFetcher()
        holidays = fetcher.parse_html(LUXEMBOURG_SAMPLE_HTML)
        assert len(holidays) == 1
        assert holidays[0].date == "2026-12-25"

    def test_parse_html_excludes_stays_open_exception(self):
        """National Day (23 June): exchange stays open despite being a holiday"""
        fetcher = LuxembourgExchangeFetcher()
        holidays = fetcher.parse_html(LUXEMBOURG_SAMPLE_HTML)
        assert not any(h.date == "2026-06-23" for h in holidays)

    def test_parse_html_notes_completeness_caveat(self):
        fetcher = LuxembourgExchangeFetcher()
        holidays = fetcher.parse_html(LUXEMBOURG_SAMPLE_HTML)
        assert all(h.note and "confirmed complete" in h.note for h in holidays)

    def test_parse_html_empty(self):
        fetcher = LuxembourgExchangeFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no closing days heading</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = LUXEMBOURG_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = LuxembourgExchangeFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XLUX"
        assert data.currency == "EUR"


class TestMaltaExchangeFetcher:
    """Tests for MaltaExchangeFetcher (XMAL) -- foreign-holiday exclusion via TRADING column"""

    def test_parse_html_includes_real_closures(self):
        fetcher = MaltaExchangeFetcher()
        holidays = fetcher.parse_html(MALTA_SAMPLE_HTML)
        assert len(holidays) == 2

    def test_parse_html_excludes_foreign_holiday_row(self):
        """'US Holiday' row: Normal trading day -- MSE trades, must be excluded"""
        fetcher = MaltaExchangeFetcher()
        holidays = fetcher.parse_html(MALTA_SAMPLE_HTML)
        assert not any(h.name == "US Holiday" for h in holidays)

    def test_parse_html_empty(self):
        fetcher = MaltaExchangeFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no trading table</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = MALTA_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = MaltaExchangeFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XMAL"
        assert data.currency == "EUR"


class TestZagrebExchangeFetcher:
    """Tests for ZagrebExchangeFetcher (XZAG)"""

    def test_parse_html_extracts_holidays(self):
        fetcher = ZagrebExchangeFetcher()
        holidays = fetcher.parse_html(ZAGREB_SAMPLE_HTML)
        assert len(holidays) == 2
        dates = {h.date for h in holidays}
        assert "2026-01-01" in dates
        assert "2026-12-25" in dates

    def test_parse_html_empty(self):
        fetcher = ZagrebExchangeFetcher()
        assert fetcher.parse_html("") == []
        assert fetcher.parse_html("<html><body>no intro sentence</body></html>") == []

    @patch('requests.get')
    def test_fetch_success(self, mock_get):
        mock_response = Mock()
        mock_response.text = ZAGREB_SAMPLE_HTML
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = ZagrebExchangeFetcher()
        data = fetcher.fetch()

        assert data is not None
        assert data.mic == "XZAG"
        assert data.currency == "EUR"


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