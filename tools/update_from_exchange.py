#!/usr/bin/env python3
"""
update_from_exchange.py — Production-grade exchange data updater
Phase 4: Automated data fetching with retry, caching, and validation

Features:
- Retry logic with exponential backoff
- Request caching
- Schema validation
- Transaction support with rollback
- Rate limiting
- Concurrent fetching
- Progress reporting
- Comprehensive error handling
- Delta updates
"""

import asyncio
import argparse
import csv
import hashlib
import json
import logging
import pickle
import re
import shutil
import sys
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import (Any, Callable, Dict, List, Optional, Tuple)
from urllib.parse import urlparse
import urllib.robotparser as robotparser

# Try imports with fallbacks
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    tqdm = None

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


class FetchError(Exception):
    """Base exception for fetch errors"""
    pass


class ParseError(FetchError):
    """Raised when HTML parsing fails"""
    pass


class ValidationError(FetchError):
    """Raised when data validation fails"""
    pass


class RateLimitError(FetchError):
    """Raised when rate limit is exceeded"""
    pass


class FetchStatus(Enum):
    """Status of a fetch operation"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNCHANGED = "unchanged"
    UPDATED = "updated"
    NEW_EXCHANGE = "new_exchange"
    VALIDATION_ERROR = "validation_error"
    RATE_LIMITED = "rate_limited"


@dataclass
class HolidayEntry:
    """A parsed holiday entry"""
    date: str
    name: str
    status: str = "closed"
    early_close_time: Optional[str] = None
    source_url: str = ""
    note: Optional[str] = None
    predicted: Optional[bool] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "date": self.date,
            "name": self.name,
            "status": self.status,
            "source_url": self.source_url
        }
        if self.early_close_time:
            result["early_close_time"] = self.early_close_time
        if self.note:
            result["note"] = self.note
        if self.predicted is not None:
            result["predicted"] = self.predicted
        return result


@dataclass
class ExchangeData:
    """Complete exchange data structure"""
    code: str
    mic: str
    name: str
    timezone: str
    regular_open: str
    regular_close: str
    holidays: List[HolidayEntry] = field(default_factory=list)
    early_closes: List[HolidayEntry] = field(default_factory=list)
    source_urls: List[str] = field(default_factory=list)
    currency: str = "USD"
    country: str = ""
    city: str = ""
    
    def validate(self) -> List[str]:
        """Validate exchange data"""
        errors = []
        
        # Required fields
        if not self.code or len(self.code) != 4:
            errors.append(f"Invalid code: {self.code}")
        
        if not self.mic or len(self.mic) != 4:
            errors.append(f"Invalid MIC: {self.mic}")
        
        if not self.name:
            errors.append("Missing name")
        
        if not self.timezone:
            errors.append("Missing timezone")
        
        # Validate time format
        time_pattern = re.compile(r'^([01]\d|2[0-3]):([0-5]\d)$')
        if not time_pattern.match(self.regular_open):
            errors.append(f"Invalid open time: {self.regular_open}")
        if not time_pattern.match(self.regular_close):
            errors.append(f"Invalid close time: {self.regular_close}")
        
        # Validate holiday dates
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        seen_dates = set()
        for holiday in self.holidays:
            if not date_pattern.match(holiday.date):
                errors.append(f"Invalid date format: {holiday.date}")
            if holiday.date in seen_dates:
                errors.append(f"Duplicate holiday date: {holiday.date}")
            seen_dates.add(holiday.date)
        
        return errors


def retry(max_attempts: int = 3, delay: float = 2.0, backoff: float = 2.0,
          exceptions: Tuple = (Exception,)):
    """Retry decorator with exponential backoff"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    if attempts == max_attempts:
                        logger.error(f"All {max_attempts} attempts failed for {func.__name__}")
                        raise
                    logger.warning(
                        f"Attempt {attempts}/{max_attempts} failed for {func.__name__}: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator


class CacheManager:
    """Manages caching of fetched data"""
    
    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_hours = ttl_hours
    
    def _get_cache_key(self, mic: str, url: str) -> str:
        """Generate cache key from MIC and URL"""
        return hashlib.sha256(f"{mic}:{url}".encode()).hexdigest()
    
    def _get_cache_file(self, mic: str, url: str) -> Path:
        """Get cache file path"""
        return self.cache_dir / f"{self._get_cache_key(mic, url)}.pkl"
    
    def get(self, mic: str, url: str) -> Optional[ExchangeData]:
        """Get cached data if not expired"""
        cache_file = self._get_cache_file(mic, url)
        if not cache_file.exists():
            return None
        
        # Check TTL
        file_age = time.time() - cache_file.stat().st_mtime
        if file_age > self.ttl_hours * 3600:
            cache_file.unlink()
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None
    
    def set(self, mic: str, url: str, data: ExchangeData):
        """Cache data"""
        cache_file = self._get_cache_file(mic, url)
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)


class RateLimiter:
    """Rate limiter for HTTP requests"""
    
    def __init__(self, min_interval: float = 1.0):
        self.min_interval = min_interval
        self._last_request: Dict[str, float] = {}
    
    def wait_if_needed(self, key: str):
        """Wait if needed before making request"""
        if key in self._last_request:
            elapsed = time.time() - self._last_request[key]
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
    
    def mark_request(self, key: str):
        """Mark that a request was made"""
        self._last_request[key] = time.time()


class TransactionManager:
    """Manages backup and rollback of exchange data"""
    
    def __init__(self, registry_dir: Path):
        self.registry_dir = Path(registry_dir)
        self.backup_dir = self.registry_dir / ".backups"
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, mic: str) -> Optional[Path]:
        """Create backup of current exchange data"""
        source = self.registry_dir / "exchanges" / f"{mic.upper()}.json"
        if not source.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = self.backup_dir / f"{mic.upper()}_{timestamp}.json"
        shutil.copy2(source, backup)
        return backup
    
    def rollback(self, mic: str, backup_file: str):
        """Rollback to a backup"""
        source = self.backup_dir / backup_file
        target = self.registry_dir / "exchanges" / f"{mic.upper()}.json"
        if source.exists():
            shutil.copy2(source, target)
            logger.info(f"Rolled back {mic} to {backup_file}")
        else:
            logger.error(f"Backup file not found: {backup_file}")
    
    def list_backups(self, mic: str) -> List[str]:
        """List available backups for an exchange"""
        pattern = f"{mic.upper()}_*.json"
        backups = list(self.backup_dir.glob(pattern))
        return sorted([b.name for b in backups])


class ExchangeFetcher(ABC):
    """Abstract base class for exchange data fetchers"""

    # Class-level cache of parsed robots.txt files, keyed by origin
    # (scheme://netloc). Shared across all fetcher instances so we don't
    # refetch robots.txt on every single request. NOTE: this was previously
    # absent entirely -- the "Handle rate limits (respect robots.txt)"
    # requirement wasn't implemented by NYSEFetcher, so this fixes that gap
    # for every fetcher (including NYSE) rather than repeating the omission.
    _robots_cache: Dict[str, "robotparser.RobotFileParser"] = {}

    def __init__(
        self,
        mic: str,
        name: str,
        source_url: str,
        rate_limit: float = 1.0,
        parser_type: str = "html"
    ):
        self.mic = mic
        self.name = name
        self.source_url = source_url
        self.rate_limit = rate_limit
        self.parser_type = parser_type
        self.rate_limiter = RateLimiter(rate_limit)
        self.referer = None
    
    @abstractmethod
    def parse_html(self, html: str) -> List[HolidayEntry]:
        """Parse HTML content into holiday entries"""
        pass
    
    @abstractmethod
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch and parse exchange data"""
        pass
    
    def _check_robots_allowed(self) -> bool:
        """
        Check whether self.source_url is allowed by the site's robots.txt.

        Fails OPEN (returns True) if robots.txt is missing, unreachable, or
        returns a non-200 status -- a missing robots.txt is not a disallow
        signal, and treating fetch errors as "disallowed" would make the
        fetcher brittle against transient network issues. Fails CLOSED only
        when robots.txt explicitly disallows the path.
        """
        import requests

        parsed = urlparse(self.source_url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        rp = ExchangeFetcher._robots_cache.get(origin)
        if rp is None:
            rp = robotparser.RobotFileParser()
            try:
                resp = requests.get(f"{origin}/robots.txt", timeout=10)
                if resp.status_code == 200:
                    rp.parse(resp.text.splitlines())
                else:
                    rp.parse([])  # no robots.txt -> treat as allow-all
            except requests.exceptions.RequestException:
                rp.parse([])  # unreachable -> fail open
            ExchangeFetcher._robots_cache[origin] = rp

        return rp.can_fetch("ExchangeCalendarRegistry/1.0", self.source_url)

    def _make_request(self) -> Optional[str]:
        """Make HTTP request with rate limiting, honoring robots.txt"""
        import requests

        if not self._check_robots_allowed():
            logger.error(
                f"robots.txt disallows fetching {self.source_url} for {self.mic}"
            )
            return None

        self.rate_limiter.wait_if_needed(self.mic)
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            if self.referer:
                headers['Referer'] = self.referer

            response = requests.get(
                self.source_url,
                timeout=30,
                headers=headers
            )
            response.raise_for_status()
            self.rate_limiter.mark_request(self.mic)
            return response.text
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {self.mic}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error fetching {self.mic}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching {self.mic}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {self.mic}: {e}")
            return None

    def _make_binary_request(self) -> Optional[bytes]:
        """
        Like _make_request, but returns raw response bytes instead of
        response.text -- needed for binary sources like PDFs, where
        `.text`'s implicit charset decoding would corrupt the content.
        Shares the same robots.txt check and rate limiter as
        _make_request so binary fetchers get identical politeness behavior.
        """
        import requests

        if not self._check_robots_allowed():
            logger.error(
                f"robots.txt disallows fetching {self.source_url} for {self.mic}"
            )
            return None

        self.rate_limiter.wait_if_needed(self.mic)

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            if self.referer:
                headers['Referer'] = self.referer

            response = requests.get(
                self.source_url,
                timeout=30,
                headers=headers
            )
            response.raise_for_status()
            self.rate_limiter.mark_request(self.mic)
            return response.content
        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching {self.mic}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error fetching {self.mic}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching {self.mic}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error fetching {self.mic}: {e}")
            return None
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False
    
    def __str__(self):
        return f"{self.mic} ({self.name})"
    
    def __repr__(self):
        return f"ExchangeFetcher(mic='{self.mic}', name='{self.name}')"


class PDFFetcher(ExchangeFetcher):
    """
    Base class for exchange calendars published only as PDF.

    Added 2026-08-27 after Tier 3 verification found PDF-only sources are
    the single most common blocker across all three tiers checked so far
    (XSWX, XJKT, XJSE, XIST, and XDFM's primary source). Rather than treat
    each one as a one-off, this base class provides shared PDF-to-text
    extraction so individual fetchers only need to implement text parsing,
    the same division of labor as the HTML fetchers' `parse_html`.

    IMPORTANT: this does NOT unblock every PDF source automatically.
    - A PDF must still be genuinely fetchable (not bot-walled) -- confirmed
      this round for XDFM and XIST, but XJSE's PDF is bot-blocked exactly
      like the rest of jse.co.za, so PDF support alone doesn't help there.
    - A PDF must be text-based, not a scanned image or a rendered visual
      grid with no embedded per-cell text -- XSWX's PDF is a visual
      calendar with no per-day text labels and remains unbuildable even
      with this class available.

    Subclasses implement `parse_html(text)` (name kept for interface
    consistency with the HTML-based fetchers, despite operating on
    PDF-extracted text here) and override `fetch()` to call
    `_make_binary_request()` + `_extract_pdf_text()` instead of
    `_make_request()`.
    """

    def _extract_pdf_text(self, pdf_bytes: bytes) -> str:
        """
        Extract all text from a PDF's bytes, page by page, joined with
        newlines. Returns '' (not None) on empty/unreadable content so
        callers can treat it the same way as an empty HTML/CSV string.
        """
        if not HAS_PDFPLUMBER:
            raise ParseError(
                "pdfplumber not available -- required for PDF-based fetchers"
            )
        if not pdf_bytes:
            return ""

        import io
        text_parts = []
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:  # noqa: BLE001 -- malformed/corrupt PDF is a
            # real possibility (wrong content-type, HTML error page served
            # instead of a PDF, etc); treat as empty rather than crash
            logger.warning(f"{self.mic}: failed to parse PDF content: {e}")
            return ""

        return "\n".join(text_parts)


class NYSEFetcher(ExchangeFetcher):
    """
    Fetcher for NYSE holidays.

    SOURCE CHANGED 2026-08-27 (was nyse.com/markets/hours-calendars).
    The live CI health check (tools/live_fetcher_check.py) flagged this
    fetcher as failing. Investigation via web_fetch (not the sandboxed
    bash_tool, which has its own unrelated network allowlist that produced a
    misleading same-looking 403 initially -- see CHANGELOG for the
    correction) confirmed nyse.com itself returns "Site blocked the request
    (bot detection)" on both /markets/hours-calendars and
    /trade/hours-calendars, regardless of User-Agent. This is a WAF-level
    block (likely Akamai/Cloudflare bot management), not a header-string
    problem -- no User-Agent string fixes it with a plain `requests` call;
    that would require a real browser (Playwright/Selenium), which is a
    framework change out of scope here.

    FIX: NYSE Group's own Investor Relations press releases (ir.theice.com,
    a Q4 IR platform -- different infrastructure than the nyse.com WAF) post
    the same authoritative holiday calendar as a real static HTML table, and
    were NOT blocked when checked live. This fetcher now points there.

    SOURCE UPDATED AGAIN 2026-08-29: was pointed at the 2025-2027 press
    release (posted 2024-11-08); switched to the newer 2026-2028 release
    (posted 2025-12-23, at ir.theice.com/press/news-details/2025/...) found
    while verifying Tier 3 sources -- confirmed live via web_fetch, same
    table structure, no parser changes needed (its one "—*" cell, for a
    2028 New Year's Day that isn't observed because it falls on a Saturday,
    is already handled by the existing `date_str.startswith('—')` skip
    below). This was a real staleness gap that sat unfixed for two rounds
    after first being flagged; fixing it now rather than continuing to
    defer it.

    KNOWN LIMITATION: ir.theice.com posts a new press release covering a
    ~3-year window every year or so (this one covers 2026-2028) at a URL
    that isn't predictable in advance -- there's no stable "latest
    calendar" URL the way nyse.com's marketing page was intended to be.
    This source_url WILL go stale once 2028 passes and will need another
    manual update to whatever ICE's next press release URL is. That's a
    real, recurring tradeoff versus the old (permanently-current-looking,
    but actually unreachable) URL, and should be tracked as a standing
    maintenance item rather than assumed fixed after this update.
    """

    def __init__(self):
        super().__init__(
            mic="XNYS",
            name="New York Stock Exchange",
            source_url="https://ir.theice.com/press/news-details/2025/NYSE-Group-Announces-2026-2027-and-2028-Holiday-and-Early-Closings-Calendar/default.aspx",
            rate_limit=2.0
        )
    
    def parse_html(self, html: str) -> List[HolidayEntry]:
        """Parse NYSE holiday calendar HTML (transposed table format)"""
        if not HAS_BS4:
            raise ParseError("BeautifulSoup not available")
        
        soup = BeautifulSoup(html, 'html.parser')
        holidays = []
        
        # Find holiday table. Case-insensitive substring match on the first
        # header cell -- the original case-sensitive 'Holiday' in headers[0]
        # check would silently fail to find this exact table if the live
        # page renders the header as "HOLIDAY" (all-caps), which is what the
        # ir.theice.com press release appears to do. Also check td, not just
        # th, since not every CMS-rendered table necessarily uses <th> for
        # its header row.
        tables = soup.find_all('table')
        holiday_table = None
        
        for table in tables:
            rows = table.find_all('tr')
            if not rows:
                continue
            first_row_cells = rows[0].find_all(['th', 'td'])
            headers = [c.text.strip() for c in first_row_cells]
            if headers and 'holiday' in headers[0].lower():
                holiday_table = table
                logger.debug(f"Found NYSE holiday table with headers: {headers}")
                break
        
        if not holiday_table:
            logger.warning("Could not find NYSE holiday table")
            return holidays
        
        # Parse the transposed table
        rows = holiday_table.find_all('tr')
        if not rows:
            return holidays
        
        header_row = rows[0]
        year_headers = [c.text.strip() for c in header_row.find_all(['th', 'td'])]
        
        # Find year columns (skip Holiday column)
        year_columns = []
        for idx, header in enumerate(year_headers):
            if re.match(r'^\d{4}$', header):
                year_columns.append((idx, int(header)))
        
        logger.debug(f"Found year columns: {year_columns}")
        
        # Parse each holiday row
        for row in rows[1:]:
            cols = row.find_all(['td', 'th'])
            if len(cols) < 2:
                continue
            
            holiday_name = cols[0].text.strip()
            if not holiday_name:
                continue
            
            # Parse dates for each year
            for col_idx, year in year_columns:
                if col_idx >= len(cols):
                    continue
                
                date_str = cols[col_idx].text.strip()
                if not date_str or date_str.startswith('—'):
                    continue
                
                # Clean the date string (remove asterisks and notes)
                date_str = re.sub(r'[*†‡]', '', date_str).strip()
                
                # Parse the date (e.g., "Thursday, January 1")
                date_iso = self._parse_holiday_date(date_str, year)
                
                if date_iso:
                    holidays.append(HolidayEntry(
                        date=date_iso,
                        name=holiday_name,
                        status="closed",
                        source_url=self.source_url
                    ))
        
        # Sort holidays by date
        holidays.sort(key=lambda h: h.date)
        
        logger.info(f"Parsed {len(holidays)} holidays from NYSE")
        return holidays
    
    def _parse_holiday_date(self, date_str: str, year: int) -> Optional[str]:
        """Parse holiday date like 'Thursday, January 1' with known year"""
        if not date_str:
            return None
        
        # Remove weekday prefix (e.g., "Thursday, ")
        date_str = re.sub(r'^\w+,\s*', '', date_str.strip())
        
        # Remove parenthetical notes like "(observed)" or "(Juneteenth National Independence Day observed)"
        date_str = re.sub(r'\s*\([^)]*\)', '', date_str).strip()
        
        # Try different formats with the known year
        date_formats = [
            f'%B %d %Y',     # January 1 2025
            f'%b %d %Y',      # Jan 1 2025
        ]
        
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(f'{date_str} {year}', fmt)
                return date_obj.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Try without weekday removal
        try:
            date_obj = datetime.strptime(f'{date_str}, {year}', f'%B %d, %Y')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            pass
        
        logger.warning(f"Could not parse date: {date_str} (year: {year})")
        return None
    
    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch NYSE holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch NYSE page")
        
        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for NYSE")
        
        data = ExchangeData(
            code="XNYS",
            mic="XNYS",
            name=self.name,
            timezone="America/New_York",
            regular_open="09:30",
            regular_close="16:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="USD",
            country="United States",
            city="New York"
        )
        
        # Validate
        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")
        
        return data


class NASDAQFetcher(NYSEFetcher):
    """
    Fetcher for NASDAQ (XNAS) holidays.

    NASDAQ does NOT have its own scrapable holiday source: nasdaq.com/trading-calendar
    renders its calendar client-side (verified 2026-08-26 via direct fetch — the raw
    HTML contains a blank day-number grid with no holiday markup, so a requests+BS4
    parser would silently return zero holidays rather than raising an error).

    NASDAQ and NYSE observe an IDENTICAL holiday calendar: both are US equity markets
    that follow the SIFMA-aligned exchange holiday schedule. This is a documented fact
    of the US equities market structure, not an assumption — there has been no
    NYSE/NASDAQ holiday divergence in modern history. So instead of scraping a page
    that doesn't expose its data, this fetcher reuses NYSEFetcher's parser against
    whatever source NYSEFetcher itself currently uses (kept in sync via
    NYSEFetcher.__init__ below, rather than a second hardcoded URL, precisely so this
    class can't silently drift out of sync the way it did when NYSEFetcher's URL
    changed from nyse.com to ir.theice.com on 2026-08-27) and republishes the result
    under the XNAS MIC. If NYSE and NASDAQ calendars ever diverge, this fetcher will
    need a real NASDAQ-specific source at that point — this is a deliberate,
    documented shortcut, not a hidden one.
    """

    def __init__(self):
        # Deliberately call ExchangeFetcher.__init__ (grandparent), not
        # NYSEFetcher.__init__, so mic/name are XNAS/NASDAQ from construction —
        # avoids a set-then-overwrite of self.mic that would confuse the
        # rate limiter's per-mic cache key. source_url is read from a fresh
        # NYSEFetcher instance rather than hardcoded, so this class can never
        # point at a different (possibly stale) URL than NYSEFetcher itself uses.
        ExchangeFetcher.__init__(
            self,
            mic="XNAS",
            name="NASDAQ",
            source_url=NYSEFetcher().source_url,
            rate_limit=2.0
        )

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch NASDAQ holiday calendar (mirrored from NYSE's published source)"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch NYSE page (NASDAQ mirror source)")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for NASDAQ (via NYSE mirror)")

        # Re-tag each holiday's source_url so downstream consumers can see the
        # data actually came from NYSE's page, not a NASDAQ-published source.
        mirrored_holidays = [
            HolidayEntry(
                date=h.date,
                name=h.name,
                status=h.status,
                early_close_time=h.early_close_time,
                source_url=self.source_url,
                note="Mirrored from NYSE holiday calendar (NASDAQ publishes no independent source)"
            )
            for h in holidays
        ]

        data = ExchangeData(
            code="XNAS",
            mic="XNAS",
            name=self.name,
            timezone="America/New_York",
            regular_open="09:30",
            regular_close="16:00",
            holidays=mirrored_holidays,
            source_urls=[self.source_url],
            currency="USD",
            country="United States",
            city="New York"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class LSEFetcher(ExchangeFetcher):
    """
    Fetcher for London Stock Exchange (XLON) holidays.

    IMPORTANT DEVIATION FROM THE BRIEF: londonstockexchange.com does not
    publish its own scrapable holiday table (verified via search 2026-08-26 --
    no stable HTML holiday table found on that domain). LSE closures instead
    follow UK bank holidays (England & Wales), which the UK government
    publishes as a real, stable, structured JSON API rather than requiring
    HTML scraping at all: https://www.gov.uk/bank-holidays.json (verified live
    2026-08-26 -- returns clean JSON with "england-and-wales" -> "events").

    This is a documented approximation, not a verified 1:1 match: LSE's
    precise closure list has not been cross-checked against this feed
    holiday-by-holiday. Bank holidays are the standard, widely-used proxy for
    UK market closures, but if LSE ever closes for a day that is not a bank
    holiday (or trades on one), this fetcher will not catch that divergence.
    """

    def __init__(self):
        ExchangeFetcher.__init__(
            self,
            mic="XLON",
            name="London Stock Exchange",
            source_url="https://www.gov.uk/bank-holidays.json",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        """
        Despite the name (kept for interface consistency with the abstract
        base class), this parses the gov.uk bank-holidays JSON response, not
        HTML. LSE has no HTML source to parse.
        """
        if not html:
            return []

        try:
            data = json.loads(html)
        except (json.JSONDecodeError, TypeError):
            logger.warning("LSE: could not parse gov.uk response as JSON")
            return []

        events = data.get("england-and-wales", {}).get("events", [])
        if not events:
            return []

        holidays = []
        date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
        for event in events:
            date_str = event.get("date", "")
            title = event.get("title", "")
            if not date_pattern.match(date_str) or not title:
                continue
            holidays.append(HolidayEntry(
                date=date_str,
                name=title,
                status="closed",
                source_url=self.source_url,
                note="UK bank holiday (England & Wales) -- used as proxy for LSE closure, not independently confirmed against an LSE-published source"
            ))
        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch LSE holiday calendar (via UK gov bank holidays proxy)"""
        raw = self._make_request()
        if not raw:
            raise FetchError("Failed to fetch gov.uk bank holidays JSON")

        holidays = self.parse_html(raw)
        if not holidays:
            raise ParseError("No holidays found for LSE (gov.uk bank holidays)")

        data = ExchangeData(
            code="XLON",
            mic="XLON",
            name=self.name,
            timezone="Europe/London",
            regular_open="08:00",
            regular_close="16:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="GBP",
            country="United Kingdom",
            city="London"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class XETRFetcher(ExchangeFetcher):
    """
    Fetcher for Deutsche Boerse Xetra (XETR) holidays.

    Verified live 2026-08-26: cashmarket.deutsche-boerse.com publishes a real
    server-rendered HTML table (not JS-rendered) with one row per holiday name
    and one column per year (2026-2032), each cell containing a weekday name
    and date such as "Thursday Jan 01, 2026".

    Parsing approach: rather than trying to infer meaning from cell styling
    (e.g. bold vs not, which may indicate "actual closure" vs "already a
    weekend" but can't be reliably distinguished from extracted text alone),
    this fetcher extracts every "Mon DD, YYYY"-shaped date it finds per row
    and independently computes the weekday from the parsed date, discarding
    Saturdays/Sundays. This is robust to markup details and directly
    satisfies the weekend-exclusion requirement without depending on
    assumptions about the page's CSS classes.
    """

    DATE_RE = re.compile(r'([A-Z][a-z]{2})\s+(\d{1,2}),\s+(\d{4})')

    def __init__(self):
        ExchangeFetcher.__init__(
            self,
            mic="XETR",
            name="Deutsche Boerse Xetra",
            source_url="https://www.cashmarket.deutsche-boerse.com/cash-en/trading/trading-calendar-and-trading-hours",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        if not tables:
            return []

        holidays = []
        for table in tables:
            rows = table.find_all('tr')
            if len(rows) < 2:
                continue

            for row in rows[1:]:  # skip header row
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                holiday_name = cells[0].get_text(strip=True)
                if not holiday_name:
                    continue

                for cell in cells[1:]:
                    cell_text = cell.get_text(separator=' ', strip=True)
                    match = self.DATE_RE.search(cell_text)
                    if not match:
                        continue

                    month_abbr, day, year = match.groups()
                    try:
                        date_obj = datetime.strptime(
                            f"{month_abbr} {day} {year}", "%b %d %Y"
                        )
                    except ValueError:
                        continue

                    if date_obj.weekday() >= 5:  # Sat=5, Sun=6 -- already a non-trading day
                        continue

                    holidays.append(HolidayEntry(
                        date=date_obj.strftime('%Y-%m-%d'),
                        name=holiday_name,
                        status="closed",
                        source_url=self.source_url
                    ))

        # De-duplicate (same holiday can legitimately appear in more than one
        # table on the page, e.g. an archive table and a current table)
        seen = set()
        deduped = []
        for h in holidays:
            key = (h.date, h.name)
            if key not in seen:
                seen.add(key)
                deduped.append(h)
        return deduped

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Xetra holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch Deutsche Boerse Xetra page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XETR")

        data = ExchangeData(
            code="XETR",
            mic="XETR",
            name=self.name,
            timezone="Europe/Berlin",
            regular_open="09:00",
            regular_close="17:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="EUR",
            country="Germany",
            city="Frankfurt"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class ASXFetcher(ExchangeFetcher):
    """
    Fetcher for Australian Securities Exchange (XASX) holidays.

    Verified live 2026-08-26: asx.com.au publishes a real server-rendered
    HTML table with columns: Public Holiday | Dates for <year> | Trading Day
    | Settlement (CHESS) | Settlement (Derivatives) | Business Day. The
    "Trading Day" column value is either "CLOSED" (full closure -> holiday)
    or "CLOSE EARLY" (early close -> early_close).

    FIXED 2026 (live health check regression): the page now publishes TWO
    tables on one page ("2026 trading calendar" and "2027 trading
    calendar"), each with its own "DATES FOR <year>" / "Dates for <year>"
    header. Fixed by extracting the year from EACH table's own header text
    independently, so multi-year pages are handled correctly.

    Also added defensive de-duplication (merge same-date entries) as a
    safety net, rather than weakening ExchangeData.validate().
    """

    YEAR_HEADER_RE = re.compile(r'DATES FOR (\d{4})', re.IGNORECASE)
    ROW_DATE_RE = re.compile(
        r'\b(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\b',
        re.IGNORECASE
    )

    def __init__(self):
        ExchangeFetcher.__init__(
            self,
            mic="XASX",
            name="Australian Securities Exchange",
            source_url="https://www.asx.com.au/markets/market-resources/trading-hours-calendar/cash-market-trading-hours/trading-calendar",
            rate_limit=2.0
        )

    @staticmethod
    def _merge_duplicates(entries: List[HolidayEntry]) -> List[HolidayEntry]:
        """Merge entries sharing the same date, combining names if they differ."""
        by_date: Dict[str, HolidayEntry] = {}
        for e in entries:
            if e.date in by_date:
                existing = by_date[e.date]
                combined_name = (
                    f"{existing.name} / {e.name}"
                    if e.name != existing.name else existing.name
                )
                by_date[e.date] = HolidayEntry(
                    date=e.date,
                    name=combined_name,
                    status=existing.status,
                    source_url=existing.source_url
                )
            else:
                by_date[e.date] = e
        return list(by_date.values())

    def parse_html(self, html: str) -> Tuple[List[HolidayEntry], List[HolidayEntry]]:
        """Returns (holidays, early_closes) since ASX's table distinguishes them."""
        if not html:
            return [], []

        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        holidays, early_closes = [], []

        for table in tables:
            header_text = table.get_text(" ", strip=True)
            if 'TRADING DAY' not in header_text.upper():
                continue

            year_match = self.YEAR_HEADER_RE.search(header_text)
            if not year_match:
                continue
            year = year_match.group(1)

            rows = table.find_all('tr')
            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue

                name = cells[0].get_text(strip=True)
                date_text = cells[1].get_text(" ", strip=True)
                trading_status = cells[2].get_text(strip=True).upper()

                date_match = self.ROW_DATE_RE.search(date_text)
                if not name or not date_match:
                    continue

                try:
                    date_obj = datetime.strptime(
                        f"{date_match.group(2)} {date_match.group(1)} {year}",
                        "%B %d %Y"
                    )
                except ValueError:
                    continue

                iso_date = date_obj.strftime('%Y-%m-%d')

                if 'CLOSE EARLY' in trading_status:
                    early_closes.append(HolidayEntry(
                        date=iso_date, name=name, status="early_close",
                        source_url=self.source_url
                    ))
                elif 'CLOSED' in trading_status:
                    if date_obj.weekday() < 5:
                        holidays.append(HolidayEntry(
                            date=iso_date, name=name, status="closed",
                            source_url=self.source_url
                        ))

        return self._merge_duplicates(holidays), self._merge_duplicates(early_closes)
    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch ASX holiday calendar."""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch ASX page")

        holidays, early_closes = self.parse_html(html)
        if not holidays and not early_closes:
            raise ParseError("No holidays found for XASX")

        data = ExchangeData(
            code="XASX",
            mic="XASX",
            name=self.name,
            timezone="Australia/Sydney",
            regular_open="10:00",
            regular_close="16:00",
            holidays=holidays,
            early_closes=early_closes,
            source_urls=[self.source_url],
            currency="AUD",
            country="Australia",
            city="Sydney"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data

class EuronextFetcher(ExchangeFetcher):
    """
    Shared fetcher for Euronext markets (XPAR Paris, XAMS Amsterdam, etc).

    Verified live 2026-08-26 (Tier 1) and re-verified 2026-08-31 (Tier 4):
    euronext.com/en/trading/trading-hours-holidays publishes a real
    server-rendered HTML table with one row per calendar event and one
    column per Euronext venue (Amsterdam, Brussels, Dublin, Lisbon, Milan,
    Oslo, Paris). This single fetcher is parameterized by which column to
    read, matching the brief's request for "one shared fetcher class with
    different MIC".

    EXTENDED 2026-08-31 to cover XDUB (Dublin), XBRU (Brussels), XLIS
    (Lisbon), and XOSL (Oslo) -- all four are columns in this SAME table
    that was already verified for XPAR/XAMS in Tier 1, discovered while
    checking Tier 4's Euronext-family exchanges. Notably, XOSL (Oslo Bors)
    was originally assumed in the Tier 4 brief to need a separate "Nasdaq
    Nordic" fetcher -- that assumption was wrong. Euronext acquired Oslo
    Bors in 2019, and its holiday data has been sitting in this same table
    the whole time. Oslo's currency is NOK, not EUR, despite being part of
    the Euronext group -- confirmed via a separate check, not assumed from
    the other five markets' EUR pattern.

    BUG FIXED 2026-08-31: this fetcher previously only checked for the
    literal substring 'closed' in a cell, silently treating "Half Trading
    Day" cells (Dec 24 / Dec 31 for most markets, plus a Wednesday-before-
    Easter half day for Oslo specifically) as ordinary non-holidays. This
    meant XPAR and XAMS (built in Tier 1) had been missing their early-close
    entries since they were first shipped. Now populates `early_closes`
    (via `status="early_close"`) for cells containing "half trading day",
    in addition to `holidays` for cells containing "closed".

    KNOWN LIMITATION (documented, not silently handled): some rows describe
    multi-day ranges (e.g. "Monday 5 and Tuesday 6 January 2026") rather than
    a single date. This fetcher only extracts rows with an unambiguous single
    date; multi-day-range rows are skipped and logged, not guessed at. Given
    that Euronext's multi-day rows in the observed table were all "Full
    Trading Day" (not closures) for every market, skipping them does not
    currently drop any actual holiday -- but this should be re-verified if
    the page's layout changes.
    """

    ROW_DATE_RE = re.compile(
        r'^\s*\w+\s+(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
        re.IGNORECASE
    )
    NAME_RE = re.compile(r'\(([^)]+)\)')

    # Which market column maps to which MIC
    MARKET_COLUMN = {
        "XPAR": "Paris",
        "XAMS": "Amsterdam",
        "XDUB": "Dublin",
        "XBRU": "Brussels",
        "XLIS": "Lisbon",
        "XOSL": "Oslo",
    }
    TIMEZONE = {
        "XPAR": "Europe/Paris",
        "XAMS": "Europe/Amsterdam",
        "XDUB": "Europe/Dublin",
        "XBRU": "Europe/Brussels",
        "XLIS": "Europe/Lisbon",
        "XOSL": "Europe/Oslo",
    }
    CURRENCY = {
        "XPAR": "EUR", "XAMS": "EUR", "XDUB": "EUR", "XBRU": "EUR",
        "XLIS": "EUR", "XOSL": "NOK",  # Oslo: NOK, not EUR -- verified separately
    }
    COUNTRY = {
        "XPAR": "France", "XAMS": "Netherlands", "XDUB": "Ireland",
        "XBRU": "Belgium", "XLIS": "Portugal", "XOSL": "Norway",
    }
    CITY = {
        "XPAR": "Paris", "XAMS": "Amsterdam", "XDUB": "Dublin",
        "XBRU": "Brussels", "XLIS": "Lisbon", "XOSL": "Oslo",
    }
    # Oslo's regular hours differ from the other Euronext markets (confirmed
    # via a separate check, not assumed): continuous trading ends 16:20 CET,
    # closing auction concludes ~16:30. Others use the 09:00-17:30 default.
    REGULAR_OPEN = {mic: "09:00" for mic in MARKET_COLUMN}
    REGULAR_CLOSE = {mic: "17:30" for mic in MARKET_COLUMN}
    REGULAR_CLOSE["XOSL"] = "16:30"

    def __init__(self, mic: str, name: str):
        if mic not in self.MARKET_COLUMN:
            raise ValueError(f"EuronextFetcher does not support MIC {mic}")
        ExchangeFetcher.__init__(
            self,
            mic=mic,
            name=name,
            source_url="https://www.euronext.com/en/trading/trading-hours-holidays",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> Tuple[List[HolidayEntry], List[HolidayEntry]]:
        """Returns (holidays, early_closes) -- see bug-fix note in class docstring"""
        if not html:
            return [], []

        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        if not tables:
            return [], []

        column_name = self.MARKET_COLUMN[self.mic]
        holidays, early_closes = [], []
        skipped_multi_day = 0

        for table in tables:
            header_cells = table.find('tr')
            if not header_cells:
                continue
            headers = [c.get_text(strip=True) for c in header_cells.find_all(['th', 'td'])]
            if column_name not in headers:
                continue  # not a Euronext holiday-by-market table
            col_idx = headers.index(column_name)

            rows = table.find_all('tr')[1:]
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) <= col_idx:
                    continue

                row_label = cells[0].get_text(" ", strip=True)
                date_match = self.ROW_DATE_RE.match(row_label)
                if not date_match:
                    skipped_multi_day += 1
                    continue  # multi-day range row -- documented limitation

                day, month_name, year = date_match.groups()
                try:
                    date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
                except ValueError:
                    continue

                status_text = cells[col_idx].get_text(" ", strip=True).lower()
                name_match = self.NAME_RE.search(row_label)
                holiday_name = name_match.group(1) if name_match else row_label

                if 'half trading day' in status_text:
                    early_closes.append(HolidayEntry(
                        date=date_obj.strftime('%Y-%m-%d'),
                        name=holiday_name,
                        status="early_close",
                        source_url=self.source_url
                    ))
                elif 'closed' in status_text:
                    holidays.append(HolidayEntry(
                        date=date_obj.strftime('%Y-%m-%d'),
                        name=holiday_name,
                        status="closed",
                        source_url=self.source_url
                    ))
                # else: "Full Trading Day" / "*No TAH" -- this venue trades
                # normally that day, nothing to record

        if skipped_multi_day:
            logger.warning(
                f"{self.mic}: skipped {skipped_multi_day} multi-day-range row(s) "
                f"that could not be parsed as a single date"
            )

        return holidays, early_closes

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Euronext holiday calendar for this fetcher's market"""
        html = self._make_request()
        if not html:
            raise FetchError(f"Failed to fetch Euronext page for {self.mic}")

        holidays, early_closes = self.parse_html(html)
        if not holidays:
            raise ParseError(f"No holidays found for {self.mic}")

        data = ExchangeData(
            code=self.mic,
            mic=self.mic,
            name=self.name,
            timezone=self.TIMEZONE[self.mic],
            regular_open=self.REGULAR_OPEN[self.mic],
            regular_close=self.REGULAR_CLOSE[self.mic],
            holidays=holidays,
            early_closes=early_closes,
            source_urls=[self.source_url],
            currency=self.CURRENCY[self.mic],
            country=self.COUNTRY[self.mic],
            city=self.CITY[self.mic]
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class EuronextParisFetcher(EuronextFetcher):
    def __init__(self):
        super().__init__(mic="XPAR", name="Euronext Paris")


class EuronextAmsterdamFetcher(EuronextFetcher):
    def __init__(self):
        super().__init__(mic="XAMS", name="Euronext Amsterdam")


class EuronextDublinFetcher(EuronextFetcher):
    def __init__(self):
        super().__init__(mic="XDUB", name="Euronext Dublin")


class EuronextBrusselsFetcher(EuronextFetcher):
    def __init__(self):
        super().__init__(mic="XBRU", name="Euronext Brussels")


class EuronextLisbonFetcher(EuronextFetcher):
    def __init__(self):
        super().__init__(mic="XLIS", name="Euronext Lisbon")


class EuronextOsloFetcher(EuronextFetcher):
    def __init__(self):
        super().__init__(mic="XOSL", name="Euronext Oslo (Oslo Bors)")


class TokyoFetcher(ExchangeFetcher):
    """
    Fetcher for Tokyo Stock Exchange / JPX (XTKS) holidays.

    Verified live 2026-08-26: jpx.co.jp/english/corporate/about-jpx/calendar
    publishes a real server-rendered HTML table in ENGLISH (not requiring
    Japanese-character date parsing, contrary to the brief's assumption --
    the English-language page uses "Jan. 1 (Thu.)" style dates), organized
    under "## 2026" / "## 2027" year headings with one row per holiday.

    Date format handled: "Mon. D (Weekday.)" e.g. "Jan. 1 (Thu.)",
    "Feb. 11 (Wed.)", "Sep. 22 (Tue.)". The year is taken from the nearest
    preceding heading, not from the row itself.
    """

    YEAR_HEADING_RE = re.compile(r'^(20\d{2})$')
    ROW_DATE_RE = re.compile(
        r'([A-Z][a-z]{2})\.?\s+(\d{1,2})\s*\(\w+\.?\)'
    )

    def __init__(self):
        ExchangeFetcher.__init__(
            self,
            mic="XTKS",
            name="Tokyo Stock Exchange",
            source_url="https://www.jpx.co.jp/english/corporate/about-jpx/calendar/index.html",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []

        # Walk headings and tables in document order, tracking the most
        # recently seen year heading so each table's rows can be dated.
        current_year = None
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'table']):
            if element.name in ('h1', 'h2', 'h3', 'h4'):
                text = element.get_text(strip=True)
                year_match = self.YEAR_HEADING_RE.match(text)
                if year_match:
                    current_year = int(year_match.group(1))
                continue

            # element is a table
            if current_year is None:
                continue

            for row in element.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                date_cell = cells[0].get_text(" ", strip=True)
                name_cell = cells[1].get_text(" ", strip=True)

                date_match = self.ROW_DATE_RE.search(date_cell)
                if not date_match or not name_cell:
                    continue

                month_abbr, day = date_match.groups()
                try:
                    date_obj = datetime.strptime(
                        f"{month_abbr} {day} {current_year}", "%b %d %Y"
                    )
                except ValueError:
                    continue

                # Strip trailing footnote markers like "observed1" -> "observed"
                clean_name = re.sub(r'(\D)\d+$', r'\1', name_cell).strip()

                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=clean_name,
                    status="closed",
                    source_url=self.source_url
                ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Tokyo Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch JPX page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XTKS")

        data = ExchangeData(
            code="XTKS",
            mic="XTKS",
            name=self.name,
            timezone="Asia/Tokyo",
            regular_open="09:00",
            regular_close="15:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="JPY",
            country="Japan",
            city="Tokyo"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class SSEFetcher(ExchangeFetcher):
    """
    Fetcher for Shanghai Stock Exchange (XSHG) holidays.

    Verified live 2026-08-26: english.sse.com.cn/start/trading/schedule/ is
    real, static, server-rendered, English-language HTML, UTF-8, not
    geo-blocked, not JS-rendered. This is genuinely harder to parse than the
    Tier 1 fetchers built earlier, though: instead of one row per holiday
    date, each row describes a closure as a natural-language date RANGE
    (e.g. "January 28 (Tuesday) - February 4 (Tuesday), plus January 26
    (Sunday) and February 8 (Saturday)"). The "plus <weekend dates>" clause
    describes weekend days already inside/adjacent to the closure window and
    is deliberately ignored -- weekends are already non-trading days, so
    they don't need to appear in the `holidays` list.

    KNOWN LIMITATION: as of the verification date, this page only publishes
    2024 and 2025 schedules -- 2026 Golden Week dates were not yet posted.
    This fetcher parses whatever year sections actually exist on the page
    (it does not hardcode a year), so it will pick up 2026+ data
    automatically once SSE publishes it, but a `fetch()` run today will only
    return 2024/2025 holidays. Downstream consumers should not assume this
    fetcher has current-year coverage without checking the returned dates.
    """

    YEAR_HEADING_RE = re.compile(r'^(20\d{2})$')
    # e.g. "January 28 (Tuesday)" or "January 1, 2025 (Wednesday)"
    DATE_RE = re.compile(
        r'([A-Z][a-z]+)\s+(\d{1,2})(?:,\s*\d{4})?\s*\((\w+)\)'
    )

    def __init__(self):
        ExchangeFetcher.__init__(
            self,
            mic="XSHG",
            name="Shanghai Stock Exchange",
            source_url="https://english.sse.com.cn/start/trading/schedule/",
            rate_limit=3.0  # slower rate limit: be extra conservative on this domain
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []
        current_year = None

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'table']):
            if element.name in ('h1', 'h2', 'h3', 'h4'):
                text = element.get_text(strip=True)
                year_match = self.YEAR_HEADING_RE.match(text)
                if year_match:
                    current_year = int(year_match.group(1))
                continue

            if current_year is None:
                continue

            for row in element.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                holiday_name = cells[0].get_text(" ", strip=True)
                date_text = cells[1].get_text(" ", strip=True)
                if not holiday_name or not date_text:
                    continue

                # Ignore the "plus <weekend dates>" clause entirely -- those
                # are supplementary weekend closures, not new weekday holidays
                main_part = date_text.split(', plus')[0].split(' plus ')[0]

                matches = self.DATE_RE.findall(main_part)
                if not matches:
                    continue

                try:
                    start = datetime.strptime(
                        f"{matches[0][0]} {matches[0][1]} {current_year}", "%B %d %Y"
                    )
                except ValueError:
                    continue

                if len(matches) >= 2:
                    try:
                        end = datetime.strptime(
                            f"{matches[1][0]} {matches[1][1]} {current_year}", "%B %d %Y"
                        )
                    except ValueError:
                        end = start
                else:
                    end = start

                if end < start:
                    # range likely crosses a year boundary (e.g. Dec -> Jan);
                    # not handled -- skip rather than guess
                    logger.warning(
                        f"XSHG: skipping '{holiday_name}' -- date range appears "
                        f"to cross a year boundary, which this parser doesn't handle"
                    )
                    continue

                day = start
                while day <= end:
                    if day.weekday() < 5:  # only weekdays -- weekends are already closed
                        holidays.append(HolidayEntry(
                            date=day.strftime('%Y-%m-%d'),
                            name=holiday_name,
                            status="closed",
                            source_url=self.source_url,
                            note="Parsed from a natural-language date range, not a per-day table -- verify against source for edge cases"
                        ))
                    day += timedelta(days=1)

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Shanghai Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch SSE page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XSHG")

        data = ExchangeData(
            code="XSHG",
            mic="XSHG",
            name=self.name,
            timezone="Asia/Shanghai",
            regular_open="09:30",
            regular_close="15:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="CNY",
            country="China",
            city="Shanghai"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class SZSEFetcher(ExchangeFetcher):
    """
    Fetcher for Shenzhen Stock Exchange (XSHE) holidays.

    Verified live 2026-08-26: szse.cn/English/services/trading/calendar/ is
    real, static, server-rendered, English-language HTML, not geo-blocked.

    Format is numbered prose paragraphs, not a table: "1. New Year: The
    market will close on January 1st (Wednesday) and resume trading on
    January 2nd (Thursday)." The closure end date is computed as one day
    before the stated "resume trading" date, which is more reliable than
    trying to parse the optional "to <date>" clause since the two are
    logically redundant and "resume - 1 day" needs no ordinal-suffix
    normalization on a second date.

    KNOWN LIMITATION: like XSHG, this page's year coverage may lag the
    current year -- verify the returned dates' years before relying on them
    for the current trading year.
    """

    YEAR_HEADING_RE = re.compile(r'\((20\d{2})\)')
    ENTRY_RE = re.compile(
        r'(\d+)\.\s*([^:]+):\s*The market will close (?:on|from)\s+'
        r'([A-Z][a-z]+\s+\d{1,2})(?:st|nd|rd|th)?\s*\(\w+\)'
        r'(?:\s*to\s*[A-Z][a-z]+\s+\d{1,2}(?:st|nd|rd|th)?\s*\(\w+\))?'
        r'.*?resume trading on\s+([A-Z][a-z]+\s+\d{1,2})(?:st|nd|rd|th)?',
        re.DOTALL
    )

    def __init__(self):
        ExchangeFetcher.__init__(
            self,
            mic="XSHE",
            name="Shenzhen Stock Exchange",
            source_url="https://www.szse.cn/English/services/trading/calendar/index.html",
            rate_limit=3.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text("\n", strip=True)

        year_match = self.YEAR_HEADING_RE.search(page_text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        holidays = []
        for match in self.ENTRY_RE.finditer(page_text):
            _, name, start_text, resume_text = match.groups()
            name = name.strip()

            try:
                start = datetime.strptime(f"{start_text} {year}", "%B %d %Y")
                resume = datetime.strptime(f"{resume_text} {year}", "%B %d %Y")
            except ValueError:
                continue

            end = resume - timedelta(days=1)
            if end < start:
                logger.warning(
                    f"XSHE: skipping '{name}' -- computed end date precedes "
                    f"start date, likely a year-boundary case this parser doesn't handle"
                )
                continue

            day = start
            while day <= end:
                if day.weekday() < 5:
                    holidays.append(HolidayEntry(
                        date=day.strftime('%Y-%m-%d'),
                        name=name,
                        status="closed",
                        source_url=self.source_url,
                        note="Parsed from prose ('close on X, resume on Y'), not a per-day table -- verify against source for edge cases"
                    ))
                day += timedelta(days=1)

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Shenzhen Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch SZSE page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XSHE")

        data = ExchangeData(
            code="XSHE",
            mic="XSHE",
            name=self.name,
            timezone="Asia/Shanghai",
            regular_open="09:30",
            regular_close="15:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="CNY",
            country="China",
            city="Shenzhen"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class ViennaFetcher(PDFFetcher):
    """
    Fetcher for Vienna Stock Exchange (XWBO) holidays.

    Verified live 2026-08-31: wienerborse.at publishes a real, clean,
    single-page PDF with a predictable 2-column-per-row layout -- NOT
    scrambled like XIST's multi-table, multi-column document. Fetched and
    manually verified the extraction order matches the visual layout.

    CRITICAL SEMANTIC TRAP, confirmed by reading the actual PDF content:
    the left column is "Stock exchange holidays" (real closures); the RIGHT
    column is "Additional holiday trading days" -- days the exchange stays
    OPEN despite being Austrian public holidays (Epiphany, Ascension Day,
    Whit Monday, Corpus Christi, Immaculate Conception). This is the
    opposite of what "holiday" might suggest. This parser only keeps the
    FIRST date/name pair per line (left column); any additional pairs on
    the same line (right column) are discarded, not treated as closures.

    KNOWN LIMITATION: single year only (2026), PDF URL is year-specific,
    same annual-update pattern as XDFM/XBUD.
    """

    LINE_ENTRY_RE = re.compile(
        r'([A-Z][a-z]),\s*(\d{1,2})\s+([A-Za-z]+)\s+(.+?)(?=\s+[A-Z][a-z],\s*\d{1,2}\s+[A-Za-z]+|$)'
    )
    # Only these month names are valid -- guards against accidentally
    # matching part of a holiday name as a "month"
    MONTHS = {"January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"}

    def __init__(self):
        super().__init__(
            mic="XWBO",
            name="Vienna Stock Exchange",
            source_url="https://www.wienerborse.at/uploads/u/cms/files/trading/stock-exchange-holidays-2026-en.pdf",
            rate_limit=2.0
        )

    def parse_html(self, text: str) -> List[HolidayEntry]:
        """Parses PDF-extracted text (see PDFFetcher). Keeps only the
        left-column ("Stock exchange holidays") entry per line."""
        if not text:
            return []

        # Find the year this schedule covers, from the page's own heading
        year_match = re.search(r'Vienna Stock Exchange\s+(\d{4})', text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        holidays = []
        for line in text.splitlines():
            line = line.strip()
            if not line or 'holiday' in line.lower()[:30]:
                # skip section header lines like "Stock exchange holidays..."
                if line.lower().startswith(('stock exchange holidays', 'additional holiday')):
                    continue

            matches = list(self.LINE_ENTRY_RE.finditer(line))
            if not matches:
                continue

            # Only the FIRST match per line (left column = real closures)
            first = matches[0]
            _, day, month_name, name = first.groups()
            if month_name not in self.MONTHS:
                continue

            try:
                date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
            except ValueError:
                continue

            holidays.append(HolidayEntry(
                date=date_obj.strftime('%Y-%m-%d'),
                name=name.strip(),
                status="closed",
                source_url=self.source_url,
                note="Parsed from a 2-column PDF -- only the 'Stock exchange holidays' (real closure) column is used; the 'Additional holiday trading days' column (exchange stays OPEN) is deliberately discarded"
            ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Vienna Stock Exchange holiday calendar"""
        pdf_bytes = self._make_binary_request()
        if not pdf_bytes:
            raise FetchError("Failed to fetch Vienna Stock Exchange PDF")

        text = self._extract_pdf_text(pdf_bytes)
        holidays = self.parse_html(text)
        if not holidays:
            raise ParseError("No holidays found for XWBO")

        data = ExchangeData(
            code="XWBO",
            mic="XWBO",
            name=self.name,
            timezone="Europe/Vienna",
            regular_open="09:00",
            regular_close="17:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="EUR",
            country="Austria",
            city="Vienna"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class WarsawFetcher(ExchangeFetcher):
    """
    Fetcher for Warsaw Stock Exchange (XWAR) holidays.

    Verified live 2026-08-31: gpw.pl/session-details is real, static HTML
    with per-year tables (2025, 2026, 2027 all present at verification
    time). Format is "Weekday | Day Month" per row, grouped under a "##
    YYYY" heading -- no holiday names given, same generic-label situation
    as XMAD and HKEX.
    """

    YEAR_HEADING_RE = re.compile(r'^(20\d{2})$')
    MONTHS = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    def __init__(self):
        super().__init__(
            mic="XWAR",
            name="Warsaw Stock Exchange",
            source_url="https://www.gpw.pl/session-details",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []
        current_year = None

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'table']):
            if element.name in ('h1', 'h2', 'h3', 'h4'):
                text = element.get_text(strip=True)
                year_match = self.YEAR_HEADING_RE.match(text)
                if year_match:
                    current_year = int(year_match.group(1))
                continue

            if current_year is None:
                continue

            for row in element.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                weekday_text = cells[0].get_text(strip=True)
                date_text = cells[1].get_text(strip=True)
                if not date_text:
                    continue

                parts = date_text.split()
                if len(parts) != 2 or parts[1] not in self.MONTHS:
                    continue
                day, month_name = parts

                try:
                    date_obj = datetime.strptime(f"{month_name} {day} {current_year}", "%B %d %Y")
                except ValueError:
                    continue

                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name="Warsaw Stock Exchange Holiday",
                    status="closed",
                    source_url=self.source_url,
                    note="Source page gives no holiday name -- generic label used"
                ))

        return self._merge_duplicates(holidays)

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Warsaw Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch GPW page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XWAR")

        data = ExchangeData(
            code="XWAR",
            mic="XWAR",
            name=self.name,
            timezone="Europe/Warsaw",
            regular_open="09:00",
            regular_close="17:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="PLN",
            country="Poland",
            city="Warsaw"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data
    def _merge_duplicates(self, entries):
        by_date = {}
        for e in entries:
            if e.date in by_date:
                existing = by_date[e.date]
                by_date[e.date] = HolidayEntry(
                    date=e.date,
                    name=existing.name,
                    status=existing.status,
                    source_url=existing.source_url,
                    note=existing.note
                )
            else:
                by_date[e.date] = e
        return list(by_date.values())

class PragueFetcher(ExchangeFetcher):
    """
    Fetcher for Prague Stock Exchange (XPRA) holidays.

    Verified live 2026-08-31: pse.cz/en/trading/trading-information/
    trading-calendar is real, static HTML -- the cleanest source found in
    this round. Real holiday names, multi-year (2025 and 2026 both present
    at verification time), format "D. Mon YYYY HolidayName" per entry
    grouped under a "#### YYYY Non-business days:" heading.
    """

    YEAR_HEADING_RE = re.compile(r'(20\d{2})\s+Non-business days')
    ENTRY_RE = re.compile(
        r'(\d{1,2})\.\s*([A-Z][a-z]{2})\s*\n?\s*(\d{4})\s*\n?\s*(.+)'
    )

    def __init__(self):
        super().__init__(
            mic="XPRA",
            name="Prague Stock Exchange",
            source_url="https://www.pse.cz/en/trading/trading-information/trading-calendar",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text("\n", strip=True)

        holidays = []
        # Split into per-year sections using the "#### YYYY Non-business
        # days:" markers, then find "D. Mon\nYYYY\nName" entries within
        # each section.
        year_sections = re.split(r'(\d{4})\s+Non-business days:', page_text)
        # re.split with a capturing group interleaves: [pre, year1, section1, year2, section2, ...]
        for i in range(1, len(year_sections), 2):
            year = int(year_sections[i])
            section = year_sections[i + 1] if i + 1 < len(year_sections) else ""
            # Stop at the "Download" section which follows the last year
            section = section.split('#### Download')[0]

            for match in self.ENTRY_RE.finditer(section):
                day, month_abbr, entry_year, name = match.groups()
                if int(entry_year) != year:
                    continue  # sanity check -- entry's own year should match section
                try:
                    date_obj = datetime.strptime(f"{month_abbr} {day} {year}", "%b %d %Y")
                except ValueError:
                    continue

                clean_name = name.strip().split('\n')[0].strip()
                if not clean_name:
                    continue

                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=clean_name,
                    status="closed",
                    source_url=self.source_url
                ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Prague Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch PSE page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XPRA")

        data = ExchangeData(
            code="XPRA",
            mic="XPRA",
            name=self.name,
            timezone="Europe/Prague",
            regular_open="09:00",
            regular_close="16:20",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="CZK",
            country="Czech Republic",
            city="Prague"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class BudapestFetcher(PDFFetcher):
    """
    Fetcher for Budapest Stock Exchange (XBUD) holidays.

    Verified live 2026-08-31: bse.hu publishes an annual holiday resolution
    as a real, clean, single-column PDF (Resolution No. 380/2025). Format:
    "D Month Weekday HolidayName" per line, under a "YYYY" heading.

    NOTE: the resolution also lists specific Saturdays "declared business
    days in Hungary" that are nonetheless non-trading days for the
    exchange. These are deliberately NOT parsed as separate entries --
    they fall on Saturdays, already covered by weekend_days, so adding them
    explicitly would be redundant (and parsing free-form "10 January, 8
    August, 12 December" text reliably is not worth the risk for entries
    that don't add new information).

    KNOWN LIMITATION: single year only (2026), PDF URL is year-specific,
    same annual-update pattern as XDFM/XWBO.
    """

    ENTRY_RE = re.compile(
        r'(\d{1,2})\s+([A-Z][a-z]+)\s+([A-Z][a-z]+)\s+(.+)'
    )
    MONTHS = {"January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"}

    def __init__(self):
        super().__init__(
            mic="XBUD",
            name="Budapest Stock Exchange",
            source_url="https://www.bse.hu/pfile/file?path=/site/Angol/Documents/Products_And_Services/trading-information/trading-holidays-2026",
            rate_limit=2.0
        )

    def parse_html(self, text: str) -> List[HolidayEntry]:
        """Parses PDF-extracted text (see PDFFetcher)."""
        if not text:
            return []

        year_match = re.search(r'shall be trading holidays in (\d{4})', text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        holidays = []
        for line in text.splitlines():
            line = line.strip()
            match = self.ENTRY_RE.match(line)
            if not match:
                continue

            day, month_name, weekday_word, name = match.groups()
            if month_name not in self.MONTHS:
                continue

            try:
                date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
            except ValueError:
                continue

            holidays.append(HolidayEntry(
                date=date_obj.strftime('%Y-%m-%d'),
                name=name.strip(),
                status="closed",
                source_url=self.source_url
            ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Budapest Stock Exchange holiday calendar"""
        pdf_bytes = self._make_binary_request()
        if not pdf_bytes:
            raise FetchError("Failed to fetch Budapest Stock Exchange PDF")

        text = self._extract_pdf_text(pdf_bytes)
        holidays = self.parse_html(text)
        if not holidays:
            raise ParseError("No holidays found for XBUD")

        data = ExchangeData(
            code="XBUD",
            mic="XBUD",
            name=self.name,
            timezone="Europe/Budapest",
            regular_open="09:00",
            regular_close="17:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="HUF",
            country="Hungary",
            city="Budapest"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class NasdaqNordicFetcher(ExchangeFetcher):
    """
    Shared fetcher for Nasdaq Nordic markets (XSTO Stockholm, XHEL Helsinki,
    XCSE Copenhagen, XICE Iceland).

    Verified live 2026-08-31: nasdaq.com/european-market-activity/
    trading-hours is real, static, server-rendered HTML (Drupal-based) with
    an "Exchange Holiday Schedule" table per year (2024, 2025, 2026 all
    present at verification time), one row per market, listing "Closed"
    dates and "Half trading days" dates as semicolon-separated "Mon D, YYYY"
    lists directly in the cell text -- no per-row-per-date table structure
    needed, unlike most other fetchers in this codebase.

    NOTE: this same page also lists a "Norway" row with its own holiday
    data. Deliberately NOT used for XOSL here -- Oslo is already covered by
    EuronextOsloFetcher (built in Tier 4, sourced from euronext.com). Using
    two different sources for the same MIC risks silent disagreement between
    them; keeping one source of truth per MIC. If this Nordic page's Norway
    data and Euronext's Oslo data ever need cross-checking, that's a
    deliberate follow-up, not something this fetcher does automatically.

    Uses the "Equity/Equity derivatives" column, not "Fixed Income" --
    consistent with every other equities-focused fetcher in this registry.
    """

    MARKET_ROW = {
        "XSTO": "Stockholm",
        "XHEL": "Helsinki",
        "XCSE": "Copenhagen",
        "XICE": "Iceland",
    }
    TIMEZONE = {
        "XSTO": "Europe/Stockholm",
        "XHEL": "Europe/Helsinki",
        "XCSE": "Europe/Copenhagen",
        "XICE": "Atlantic/Reykjavik",
    }
    CURRENCY = {"XSTO": "SEK", "XHEL": "EUR", "XCSE": "DKK", "XICE": "ISK"}
    COUNTRY = {"XSTO": "Sweden", "XHEL": "Finland", "XCSE": "Denmark", "XICE": "Iceland"}
    CITY = {"XSTO": "Stockholm", "XHEL": "Helsinki", "XCSE": "Copenhagen", "XICE": "Reykjavik"}
    REGULAR_OPEN = {"XSTO": "09:00", "XHEL": "10:00", "XCSE": "09:00", "XICE": "09:30"}
    REGULAR_CLOSE = {"XSTO": "17:30", "XHEL": "18:30", "XCSE": "17:00", "XICE": "15:30"}

    YEAR_HEADING_RE = re.compile(r'Exchange Holiday Schedule\s+(\d{4})')
    DATE_RE = re.compile(r'([A-Z][a-z]{2})\s+(\d{1,2}),\s+(\d{4})')

    def __init__(self, mic: str, name: str):
        if mic not in self.MARKET_ROW:
            raise ValueError(f"NasdaqNordicFetcher does not support MIC {mic}")
        ExchangeFetcher.__init__(
            self,
            mic=mic,
            name=name,
            source_url="https://www.nasdaq.com/european-market-activity/trading-hours",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> Tuple[List[HolidayEntry], List[HolidayEntry]]:
        """Returns (holidays, early_closes)"""
        if not html:
            return [], []

        soup = BeautifulSoup(html, 'html.parser')
        market_name = self.MARKET_ROW[self.mic]
        holidays, early_closes = [], []

        # Walk headings and tables in document order, tracking the current
        # year section, same pattern used elsewhere in this codebase.
        current_year = None
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'table']):
            if element.name in ('h1', 'h2', 'h3', 'h4'):
                text = element.get_text(strip=True)
                year_match = self.YEAR_HEADING_RE.search(text)
                if year_match:
                    current_year = int(year_match.group(1))
                continue

            if current_year is None:
                continue

            rows = element.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue
                row_label = cells[0].get_text(strip=True)
                if row_label != market_name:
                    continue

                # Second cell = "Equity/Equity derivatives" column
                cell_text = cells[1].get_text(" ", strip=True)

                # Split into "Closed" section and "Half trading days" section
                half_day_split = re.split(r'Half trading days?:', cell_text)
                closed_text = half_day_split[0]
                half_day_text = half_day_split[1] if len(half_day_split) > 1 else ""

                for month_abbr, day, year in self.DATE_RE.findall(closed_text):
                    try:
                        date_obj = datetime.strptime(f"{month_abbr} {day} {year}", "%b %d %Y")
                    except ValueError:
                        continue
                    holidays.append(HolidayEntry(
                        date=date_obj.strftime('%Y-%m-%d'),
                        name=f"{market_name} Exchange Holiday",
                        status="closed",
                        source_url=self.source_url,
                        note="Source gives a combined closure-date list per market, not individually named holidays"
                    ))

                for month_abbr, day, year in self.DATE_RE.findall(half_day_text):
                    try:
                        date_obj = datetime.strptime(f"{month_abbr} {day} {year}", "%b %d %Y")
                    except ValueError:
                        continue
                    early_closes.append(HolidayEntry(
                        date=date_obj.strftime('%Y-%m-%d'),
                        name=f"{market_name} Half Trading Day",
                        status="early_close",
                        source_url=self.source_url
                    ))

        # De-duplicate (the market row can legitimately appear in more than
        # one table on the page)
        def dedupe(entries):
            seen = set()
            out = []
            for e in entries:
                key = (e.date, e.status)
                if key not in seen:
                    seen.add(key)
                    out.append(e)
            return out

        return dedupe(holidays), dedupe(early_closes)

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Nasdaq Nordic holiday calendar for this fetcher's market"""
        html = self._make_request()
        if not html:
            raise FetchError(f"Failed to fetch Nasdaq Nordic page for {self.mic}")

        holidays, early_closes = self.parse_html(html)
        if not holidays:
            raise ParseError(f"No holidays found for {self.mic}")

        data = ExchangeData(
            code=self.mic,
            mic=self.mic,
            name=self.name,
            timezone=self.TIMEZONE[self.mic],
            regular_open=self.REGULAR_OPEN[self.mic],
            regular_close=self.REGULAR_CLOSE[self.mic],
            holidays=holidays,
            early_closes=early_closes,
            source_urls=[self.source_url],
            currency=self.CURRENCY[self.mic],
            country=self.COUNTRY[self.mic],
            city=self.CITY[self.mic]
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class StockholmFetcher(NasdaqNordicFetcher):
    def __init__(self):
        super().__init__(mic="XSTO", name="Nasdaq Stockholm")


class HelsinkiFetcher(NasdaqNordicFetcher):
    def __init__(self):
        super().__init__(mic="XHEL", name="Nasdaq Helsinki")


class CopenhagenFetcher(NasdaqNordicFetcher):
    def __init__(self):
        super().__init__(mic="XCSE", name="Nasdaq Copenhagen")


class IcelandFetcher(NasdaqNordicFetcher):
    def __init__(self):
        super().__init__(mic="XICE", name="Nasdaq Iceland")


class NasdaqBalticFetcher(ExchangeFetcher):
    """
    Shared fetcher for Nasdaq Baltic markets (XTAL Tallinn, XRIS Riga,
    XLIT Vilnius).

    Verified live 2026-08-31: nasdaqbaltic.com/statistics/en/calendar?holidays=1
    is real, static, server-rendered HTML with a single "Trading holidays"
    table covering all three Baltic markets, one row per event: "Period |
    Event | Market". The Market column contains space-separated short codes
    (TLN/RIG/VLN) indicating which market(s) close that day -- a market can
    appear alone (market-specific holiday) or with others (shared holiday).

    Format quirk confirmed in the real data: at least one row has TWO dates
    in the Period cell on one line ("24.12.2026   25.12.2026") for a single
    event -- both dates apply to that row's markets. Handled by extracting
    ALL DD.MM.YYYY dates found in the period cell, not just the first.

    No holiday names given -- only "Trading holiday" as a generic event
    type -- so entries are labeled generically, same situation as XMAD/XWAR.
    """

    MARKET_CODE = {"XTAL": "TLN", "XRIS": "RIG", "XLIT": "VLN"}
    TIMEZONE = {"XTAL": "Europe/Tallinn", "XRIS": "Europe/Riga", "XLIT": "Europe/Vilnius"}
    CURRENCY = {"XTAL": "EUR", "XRIS": "EUR", "XLIT": "EUR"}
    COUNTRY = {"XTAL": "Estonia", "XRIS": "Latvia", "XLIT": "Lithuania"}
    CITY = {"XTAL": "Tallinn", "XRIS": "Riga", "XLIT": "Vilnius"}

    DATE_RE = re.compile(r'(\d{2})\.(\d{2})\.(\d{4})')

    def __init__(self, mic: str, name: str):
        if mic not in self.MARKET_CODE:
            raise ValueError(f"NasdaqBalticFetcher does not support MIC {mic}")
        ExchangeFetcher.__init__(
            self,
            mic=mic,
            name=name,
            source_url="https://nasdaqbaltic.com/statistics/en/calendar?holidays=1",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        market_code = self.MARKET_CODE[self.mic]
        holidays = []

        tables = soup.find_all('table')
        for table in tables:
            header_row = table.find('tr')
            if not header_row:
                continue
            headers = [c.get_text(strip=True) for c in header_row.find_all(['th', 'td'])]
            if 'Market' not in headers or 'Period' not in headers:
                continue  # not the holidays table

            for row in table.find_all('tr')[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue

                period_text = cells[0].get_text(" ", strip=True)
                market_text = cells[-2].get_text(strip=True) if len(cells) >= 4 else cells[2].get_text(strip=True)

                markets = market_text.split()
                if market_code not in markets:
                    continue  # this holiday doesn't apply to our market

                for day, month, year in self.DATE_RE.findall(period_text):
                    try:
                        date_obj = datetime.strptime(f"{day}.{month}.{year}", "%d.%m.%Y")
                    except ValueError:
                        continue
                    holidays.append(HolidayEntry(
                        date=date_obj.strftime('%Y-%m-%d'),
                        name=f"{self.name} Trading Holiday",
                        status="closed",
                        source_url=self.source_url,
                        note="Source gives no specific holiday name, only 'Trading holiday' as a generic event type"
                    ))

        # De-duplicate
        seen = set()
        deduped = []
        for h in holidays:
            if h.date not in seen:
                seen.add(h.date)
                deduped.append(h)
        return deduped

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Nasdaq Baltic holiday calendar for this fetcher's market"""
        html = self._make_request()
        if not html:
            raise FetchError(f"Failed to fetch Nasdaq Baltic page for {self.mic}")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError(f"No holidays found for {self.mic}")

        data = ExchangeData(
            code=self.mic,
            mic=self.mic,
            name=self.name,
            timezone=self.TIMEZONE[self.mic],
            regular_open="10:00",
            regular_close="16:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency=self.CURRENCY[self.mic],
            country=self.COUNTRY[self.mic],
            city=self.CITY[self.mic]
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class TallinnFetcher(NasdaqBalticFetcher):
    def __init__(self):
        super().__init__(mic="XTAL", name="Nasdaq Tallinn")


class RigaFetcher(NasdaqBalticFetcher):
    def __init__(self):
        super().__init__(mic="XRIS", name="Nasdaq Riga")


class VilniusFetcher(NasdaqBalticFetcher):
    def __init__(self):
        super().__init__(mic="XLIT", name="Nasdaq Vilnius")


class HKEXFetcher(ExchangeFetcher):
    """
    Fetcher for Hong Kong Exchanges and Clearing (XHKG) holidays.

    UNBLOCKED 2026-08-27. Previously blocked (see BLOCKED.md) because
    hkex.com.hk/News/HKEX-Calendar is a JS-rendered widget with no data in
    the raw HTML. Further investigation found a DIFFERENT, real, static,
    CSV-published source on the same domain: HKEX's own "Trading Hour,
    Trading and Settlement Calendar" page for Stock Connect links directly
    to CSV files, e.g.
    hkex.com.hk/-/media/.../Trading-Hour,-Trading-and-Settlement-Calendar/2026-Calendar_csv_e.csv
    -- verified live 2026-08-27, fetchable, real CSV content, not
    JS-rendered, not bot-walled the way the marketing calendar page is.

    IMPORTANT: this CSV is the *Stock Connect* trading calendar, which
    covers Hong Kong, Shanghai & Shenzhen, and Northbound/Southbound trading
    status all in one file -- Stock Connect can be "Closed" on a day when
    Hong Kong itself is actually open (e.g. when only the mainland side is
    on holiday). This fetcher deliberately reads ONLY the "Hong Kong" column
    (marked "Holiday" or "Half Day"), not the Stock Connect / mainland
    columns, so it reflects HKEX's own local market status rather than
    Stock Connect's combined trading-window status. Getting this column
    selection wrong would silently produce a mainland-flavored calendar
    mislabeled as XHKG's own.

    KNOWN LIMITATION: like the NYSE/SSE/SZSE sources, this CSV's URL is
    year-specific and not permanently stable (compare the 2025 and 2026
    files, which follow a "{year}-Calendar_csv_e.csv" naming convention that
    isn't guaranteed to hold in future years). fetch() tries the current
    year first, then the next year, since HKEX has historically published
    the following year's calendar in December -- but this fetcher will need
    a source_url update once naming drifts or a year fails to resolve via
    that pattern.
    """

    BASE_PAGE_TEMPLATE = (
        "https://www.hkex.com.hk/-/media/HKEX-Market/Mutual-Market/Stock-Connect/"
        "Reference-Materials/Trading-Hour,-Trading-and-Settlement-Calendar/"
        "{year}-Calendar_csv_e.csv"
    )

    def __init__(self):
        current_year = datetime.now().year
        # Default source_url used for _make_request/robots.txt purposes;
        # fetch() overrides this per-attempt when trying multiple years.
        super().__init__(
            mic="XHKG",
            name="Hong Kong Exchanges and Clearing",
            source_url=self.BASE_PAGE_TEMPLATE.format(year=current_year),
            rate_limit=2.0
        )

    def parse_html(self, csv_text: str) -> List[HolidayEntry]:
        """
        Despite the name (kept for interface consistency with the abstract
        base class), this parses CSV text, not HTML -- HKEX publishes this
        source as a CSV, not a table on a page.
        """
        if not csv_text:
            return []

        # Strip a UTF-8 BOM if present (the live file has one)
        csv_text = csv_text.lstrip("\ufeff")

        reader = csv.DictReader(csv_text.splitlines())
        if reader.fieldnames is None or "Hong Kong" not in reader.fieldnames:
            logger.warning("HKEX CSV: 'Hong Kong' column not found -- format may have changed")
            return []

        holidays = []
        for row in reader:
            date_str = (row.get("Date") or "").strip()
            hk_status = (row.get("Hong Kong") or "").strip()
            if not date_str or not hk_status:
                continue

            if not re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
                continue

            if hk_status.lower() == "holiday":
                holidays.append(HolidayEntry(
                    date=date_str,
                    name="Hong Kong Public Holiday",
                    status="closed",
                    source_url=self.source_url,
                    note="From the 'Hong Kong' column of HKEX's Stock Connect trading calendar CSV, not the Stock Connect/mainland columns -- reflects HKEX's own local closure, not combined Stock Connect trading status. Specific holiday name not provided by this source."
                ))
            elif hk_status.lower() == "half day":
                holidays.append(HolidayEntry(
                    date=date_str,
                    name="Hong Kong Half Trading Day",
                    status="early_close",
                    source_url=self.source_url,
                    note="From the 'Hong Kong' column of HKEX's Stock Connect trading calendar CSV -- reflects HKEX's own local status."
                ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """
        Fetch HKEX holiday calendar. Tries the current year's CSV first,
        then next year's, since HKEX has historically published next year's
        file in December of the prior year (the 2026 file was already live
        when checked in August 2026).
        """
        current_year = datetime.now().year
        all_holidays = []
        tried_urls = []

        for year in (current_year, current_year + 1):
            url = self.BASE_PAGE_TEMPLATE.format(year=year)
            self.source_url = url
            tried_urls.append(url)
            csv_text = self._make_request()
            if not csv_text:
                continue
            year_holidays = self.parse_html(csv_text)
            all_holidays.extend(year_holidays)

        if not all_holidays:
            raise FetchError(f"Failed to fetch HKEX calendar from any of: {tried_urls}")

        # Restore the base source_url (current year) for the ExchangeData
        # record and de-duplicate in case both fetches overlapped
        self.source_url = self.BASE_PAGE_TEMPLATE.format(year=current_year)
        seen = set()
        deduped = []
        for h in all_holidays:
            if h.date not in seen:
                seen.add(h.date)
                deduped.append(h)

        data = ExchangeData(
            code="XHKG",
            mic="XHKG",
            name=self.name,
            timezone="Asia/Hong_Kong",
            regular_open="09:30",
            regular_close="16:00",
            holidays=deduped,
            source_urls=list(dict.fromkeys(tried_urls)),
            currency="HKD",
            country="Hong Kong",
            city="Hong Kong"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class TSXFetcher(ExchangeFetcher):
    """
    Fetcher for Toronto Stock Exchange (XTSE) holidays.

    Verified live 2026-08-27: tsx.com/en/trading/calendars-and-trading-hours/calendar
    is real, static, server-rendered HTML -- an accordion of year sections,
    each containing a "Canadian Holidays" list (real TSX closures) and a
    separate "U.S. Holidays" list (settlement-schedule notices for
    USD-denominated issues, NOT actual TSX trading closures). Only the
    "Canadian Holidays" list is parsed; the "U.S. Holidays" heading and its
    items are deliberately skipped.

    Format per item: "Holiday Name - Weekday, Month Day, Year", e.g.
    "New Year's Day - Thursday, January 1, 2026". Early closes are marked
    with a trailing "*" (e.g. "Christmas Eve - Thursday, December 24, 2026*"),
    footnoted elsewhere on the page as "Closing at 1:00 PM (TSX/TSXV)".
    The date string already includes the year, so no separate year-heading
    lookup is needed -- and the page covers multiple years (2025 and 2026
    both present at verification time), unlike XMAD's single-year page.
    """

    ITEM_RE = re.compile(
        r'^(.+?)\s*-\s*\w+,\s*([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})(\*?)\s*$'
    )

    def __init__(self):
        super().__init__(
            mic="XTSE",
            name="Toronto Stock Exchange",
            source_url="https://www.tsx.com/en/trading/calendars-and-trading-hours/calendar",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []

        # Walk headings and list items in document order, tracking whether
        # we're currently inside a "Canadian Holidays" section (parse) or a
        # "U.S. Holidays" section (skip) or neither.
        in_canadian_section = False
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'li']):
            if element.name in ('h1', 'h2', 'h3', 'h4'):
                heading_text = element.get_text(strip=True)
                if 'canadian holiday' in heading_text.lower():
                    in_canadian_section = True
                elif 'u.s. holiday' in heading_text.lower() or 'us holiday' in heading_text.lower():
                    in_canadian_section = False
                # Any other heading (e.g. a new year's "20XX Stock Market
                # Holidays" outer heading) doesn't change section state on
                # its own; the next explicit Canadian/U.S. subheading will.
                continue

            if not in_canadian_section:
                continue

            item_text = element.get_text(" ", strip=True)
            match = self.ITEM_RE.match(item_text)
            if not match:
                continue

            name, month_name, day, year, star = match.groups()
            try:
                date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
            except ValueError:
                continue

            if star:
                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=name.strip(),
                    status="early_close",
                    source_url=self.source_url,
                    note="Early close (see TSX page for exact closing time by venue)"
                ))
            else:
                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=name.strip(),
                    status="closed",
                    source_url=self.source_url
                ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch TSX holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch TSX page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XTSE")

        data = ExchangeData(
            code="XTSE",
            mic="XTSE",
            name=self.name,
            timezone="America/Toronto",
            regular_open="09:30",
            regular_close="16:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="CAD",
            country="Canada",
            city="Toronto"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class BMEMadridFetcher(ExchangeFetcher):
    """
    Fetcher for BME/Bolsa de Madrid (XMAD) holidays.

    Verified live 2026-08-27: bolsasymercados.es/en/bme-exchange/trading/
    trading-calendar.html is real, static, server-rendered HTML.

    TWO DOCUMENTED LIMITATIONS, by design of the source page itself (not
    fixable by better parsing):

    1. NO HOLIDAY NAMES GIVEN. The page lists only ordinal-day/weekday pairs
       ("1st of January", "Thursday") with zero holiday names attached --
       unlike every other Tier 1/2 fetcher in this codebase. Rather than
       guess ("1st of January" is almost certainly New Year's Day, but this
       fetcher does not assume that), entries are labeled generically
       ("BME Non-Trading Day" / "BME Early Trading Close"), matching the
       precedent set by HKEXFetcher for its unnamed CSV source.

    2. CURRENT YEAR ONLY. The page states "BME... has set the trading
       calendar for 2026" and lists only that year -- no multi-year table
       like NYSE, XETR, or the Saudi Exchange page. `fetch()` will only ever
       return the current calendar year's dates; there is no forward
       coverage. This fetcher is marked `current_year_only = True` as a
       class attribute so callers/schedulers can treat it differently from
       multi-year fetchers (e.g. re-run it more frequently, or don't expect
       next year's data to appear until BME actually publishes it).

    Full closures and early closes are distinguished by page position: dates
    listed before the "will trade until 14:00" sentence are full closures;
    dates listed after it (24 and 31 December, at verification time) are
    early closes. This is inferred from prose structure, not a marked field,
    so it depends on that sentence continuing to appear before the
    early-close dates in future page revisions.
    """

    current_year_only = True

    YEAR_RE = re.compile(r'trading calendar for\s+(\d{4})')
    DATE_RE = re.compile(r'(\d{1,2})(?:st|nd|rd|th)\s+of\s+([A-Z][a-z]+)')
    EARLY_CLOSE_MARKER_RE = re.compile(r'trade until\s+\d{1,2}:\d{2}', re.IGNORECASE)

    def __init__(self):
        super().__init__(
            mic="XMAD",
            name="BME (Bolsa de Madrid)",
            source_url="https://www.bolsasymercados.es/en/bme-exchange/trading/trading-calendar.html",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text("\n", strip=True)

        year_match = self.YEAR_RE.search(page_text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        marker_match = self.EARLY_CLOSE_MARKER_RE.search(page_text)
        split_pos = marker_match.start() if marker_match else len(page_text)

        holidays = []
        for match in self.DATE_RE.finditer(page_text):
            day, month_name = match.groups()
            try:
                date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
            except ValueError:
                continue

            is_early_close = match.start() > split_pos
            holidays.append(HolidayEntry(
                date=date_obj.strftime('%Y-%m-%d'),
                name="BME Early Trading Close" if is_early_close else "BME Non-Trading Day",
                status="early_close" if is_early_close else "closed",
                source_url=self.source_url,
                note="Source page gives no holiday name for this date -- generic label used"
            ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch BME/Bolsa de Madrid holiday calendar (current year only)"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch BME Madrid page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XMAD")

        data = ExchangeData(
            code="XMAD",
            mic="XMAD",
            name=self.name,
            timezone="Europe/Madrid",
            regular_open="09:00",
            regular_close="17:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="EUR",
            country="Spain",
            city="Madrid"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class SaudiExchangeFetcher(ExchangeFetcher):
    """
    Fetcher for Saudi Exchange / Tadawul (XSAU) holidays.

    Verified live 2026-08-27: saudiexchange.sa/.../saudi-exchange-holiday-calendar
    is real, static, server-rendered HTML -- a single table spanning
    2020-2029, far richer than any other Tier 2 source checked. Columns are
    "Date" ("DD/MM/YYYY - DD/MM/YYYY" range, or "DD/MM/YYYY -" for a
    single day) and "Title" (prose description).

    THREE THINGS THIS PARSER DOES DELIBERATELY, EACH VERIFIED AGAINST THE
    REAL TABLE CONTENT (not assumed):

    1. FILTERS OUT NON-HOLIDAY ROWS. The same table mixes in unrelated
       "Listing of <Company>" IPO announcement rows (verified present in the
       live data, e.g. "Listing of ALBILAD Saudi Sovereign Sukuk ETF"). Only
       rows whose title contains "founding day", "national day", or "eid al"
       are treated as holidays -- an allowlist, not a blacklist, so an
       unanticipated future row type is excluded by default rather than
       silently included.

    2. WEEKEND EXCLUSION USES FRIDAY/SATURDAY, not the Sat/Sun default used
       elsewhere in this codebase -- Saudi Arabia's exchange weekend is
       Friday-Saturday. Only weekdays (Sun-Thu) within a holiday's date
       range are recorded as explicit holiday entries.

    3. PREDICTED FLAG is set based on the holiday TYPE and whether the date
       is in the future relative to when fetch() runs (datetime.now()), not
       hardcoded:
       - Founding Day / National Day are fixed Gregorian dates -- never
         moon-sighting-dependent -- so predicted=False always.
       - Eid Al Fiter / Eid Al Adha are Hijri (lunar) dates. Umm al-Qura
         pre-calculates them years in advance, but Saudi Arabia's actual
         moon-sighting committee can still shift the observed date by a day
         close to the event. So: predicted=True if the date is still in the
         future when fetch() runs, predicted=False once it's in the past
         (by then, if the exchange's own calendar still lists it, it
         reflects what actually happened, not an estimate).

    KNOWN DATA-QUALITY ISSUE IN THE SOURCE ITSELF (not a parsing bug): at
    least one row's Date-column range is internally inverted relative to its
    own Title prose (the 2021 Eid Al Adha row's Date column reads
    "22/07/2021 - 15/07/2021" -- end before start -- while its Title says
    the holiday ran 15/7 to 25/7). Rows where the Date column's end predates
    its start are skipped and logged, not silently "fixed" by guessing which
    of the two conflicting values is correct.
    """

    DATE_RANGE_RE = re.compile(
        r'(\d{2})/(\d{2})/(\d{4})\s*-\s*(?:(\d{2})/(\d{2})/(\d{4}))?'
    )
    HOLIDAY_TITLE_RE = re.compile(
        r'founding day|national day|eid al', re.IGNORECASE
    )
    LUNAR_TITLE_RE = re.compile(r'eid al', re.IGNORECASE)

    def __init__(self):
        super().__init__(
            mic="XSAU",
            name="Saudi Exchange (Tadawul)",
            source_url="https://www.saudiexchange.sa/wps/portal/saudiexchange/about-saudi-exchange/exchange-media-centre/saudi-exchange-holiday-calendar",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        tables = soup.find_all('table')
        if not tables:
            return []

        now = datetime.now()
        holidays = []

        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                date_text = cells[0].get_text(" ", strip=True)
                title_text = cells[1].get_text(" ", strip=True)

                if not title_text or not self.HOLIDAY_TITLE_RE.search(title_text):
                    continue  # not a holiday row (e.g. a "Listing of ..." row)

                date_match = self.DATE_RANGE_RE.search(date_text)
                if not date_match:
                    continue

                sd, sm, sy, ed, em, ey = date_match.groups()
                try:
                    start = datetime.strptime(f"{sd}/{sm}/{sy}", "%d/%m/%Y")
                except ValueError:
                    continue

                if ed and em and ey:
                    try:
                        end = datetime.strptime(f"{ed}/{em}/{ey}", "%d/%m/%Y")
                    except ValueError:
                        end = start
                else:
                    end = start

                if end < start:
                    logger.warning(
                        f"XSAU: skipping '{title_text[:60]}' -- Date column's "
                        f"end ({end.strftime('%Y-%m-%d')}) precedes its start "
                        f"({start.strftime('%Y-%m-%d')}); source data inconsistency, not guessing"
                    )
                    continue

                is_lunar = bool(self.LUNAR_TITLE_RE.search(title_text))
                predicted = is_lunar and (start > now) if is_lunar else False

                # Clean up the title (source titles are often duplicated
                # prose, e.g. "National Day of Saudi Arabia National Day of
                # Saudi Arabia is on..." -- collapse to first sentence)
                clean_name = title_text.split(' is on ')[0].split(' Trading will')[0].strip()
                clean_name = re.sub(r'\s+', ' ', clean_name)
                # If the title repeats itself verbatim, keep only the first half
                half = len(clean_name) // 2
                if half > 5 and clean_name[:half].strip() == clean_name[half:].strip():
                    clean_name = clean_name[:half].strip()

                day = start
                while day <= end:
                    if day.weekday() not in (4, 5):  # Fri=4, Sat=5 -- Saudi weekend
                        holidays.append(HolidayEntry(
                            date=day.strftime('%Y-%m-%d'),
                            name=clean_name,
                            status="closed",
                            source_url=self.source_url,
                            predicted=predicted
                        ))
                    day += timedelta(days=1)

        # De-duplicate (date, name) pairs -- the source table has some
        # repeated rows across its history
        seen = set()
        deduped = []
        for h in holidays:
            key = (h.date, h.name)
            if key not in seen:
                seen.add(key)
                deduped.append(h)

        return deduped

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Saudi Exchange (Tadawul) holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch Saudi Exchange page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XSAU")

        data = ExchangeData(
            code="XSAU",
            mic="XSAU",
            name=self.name,
            timezone="Asia/Riyadh",
            regular_open="10:00",
            regular_close="15:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="SAR",
            country="Saudi Arabia",
            city="Riyadh"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class XDFMFetcher(PDFFetcher):
    """
    Fetcher for Dubai Financial Market (XDFM) holidays.

    Verified live 2026-08-27: dfm.ae publishes an annual holiday circular as
    a real, text-based PDF (not a scanned image or visual grid) at
    assets.dfm.ae -- fetched and confirmed clean, extractable text with a
    simple numbered-row structure: "N DD-Mon-YYYY Weekday DESCRIPTION",
    trailing "*" marking Islamic holidays as tentative/subject to
    moon-sighting confirmation.

    First fetcher in this codebase to use PDFFetcher, added specifically
    because XDFM's data is real but PDF-only.

    Sets `predicted=True` for entries carrying the trailing "*" (Islamic
    holidays not yet confirmed by moon sighting), `predicted=False` for
    fixed-date entries (New Year's Day, National Day) -- same logic as
    SaudiExchangeFetcher, but here the source itself flags which entries
    are tentative rather than requiring inference from holiday type + date.

    KNOWN LIMITATION: like NYSE/HKEX/SSE/SZSE, this PDF's URL is
    circular-specific and year-specific (DFM issues a new circular, at an
    unpredictable URL, each December for the following year) -- this will
    need a manual update once 2026 passes and DFM issues the 2027 circular.

    Weekend: Sat/Sun (UAE moved to this from Fri/Sat in January 2022 --
    confirmed by DFM's own circular text: "the official weekend holiday on
    Saturday and Sunday").
    """

    ROW_RE = re.compile(
        r'^\d+\s+(\d{2})-(\w{3})-(\d{4})\s+\w+\s+(.+?)(\*)?\s*$'
    )

    def __init__(self):
        super().__init__(
            mic="XDFM",
            name="Dubai Financial Market",
            source_url="https://assets.dfm.ae/docs/default-source/circulars/circular-12-2025-trading-and-settlementholidays-for-the-calendar-year-2026-for-securities-market-excluding-derivatives-contracts-english.pdf?sfvrsn=cffc8981_0",
            rate_limit=2.0
        )

    def parse_html(self, text: str) -> List[HolidayEntry]:
        """
        Despite the name (kept for interface consistency), this parses
        PDF-extracted text, not HTML -- see PDFFetcher.
        """
        if not text:
            return []

        holidays = []
        for line in text.splitlines():
            line = line.strip()
            match = self.ROW_RE.match(line)
            if not match:
                continue

            day, month_abbr, year, description, star = match.groups()
            try:
                date_obj = datetime.strptime(f"{day} {month_abbr} {year}", "%d %b %Y")
            except ValueError:
                continue

            name = description.strip().rstrip('*').strip()
            # Title-case cleanup: source is in ALL CAPS ("NEW YEAR'S DAY").
            # str.title() mishandles both apostrophes ("Year'S") and
            # acronyms ("Uae" instead of "UAE"), so: title-case first, fix
            # the apostrophe pattern, then restore known acronyms explicitly
            # rather than trying to detect them heuristically.
            name = name.title()
            name = re.sub(r"'S\b", "'s", name)
            for acronym in ("Uae", "Haj"):
                name = re.sub(rf'\b{acronym}\b', acronym.upper(), name)

            holidays.append(HolidayEntry(
                date=date_obj.strftime('%Y-%m-%d'),
                name=name,
                status="closed",
                source_url=self.source_url,
                predicted=bool(star)
            ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch DFM holiday calendar from its annual PDF circular"""
        pdf_bytes = self._make_binary_request()
        if not pdf_bytes:
            raise FetchError("Failed to fetch DFM circular PDF")

        text = self._extract_pdf_text(pdf_bytes)
        holidays = self.parse_html(text)
        if not holidays:
            raise ParseError("No holidays found for XDFM")

        data = ExchangeData(
            code="XDFM",
            mic="XDFM",
            name=self.name,
            timezone="Asia/Dubai",
            regular_open="10:00",
            regular_close="14:45",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="AED",
            country="United Arab Emirates",
            city="Dubai"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class BoursaKuwaitFetcher(ExchangeFetcher):
    """
    Fetcher for Boursa Kuwait (XKUW) holidays.

    Verified live 2026-08-27: boursakuwait.com.kw/en/securities/trading/
    market-holidays/ is real, static HTML -- the site is Gatsby-generated
    (statically built), so the holiday table is present in the raw HTML
    response, not populated client-side.

    Format: a Month/Date/Vacation table. Date cells are day-of-month only
    or a "D-D" range within that month, no year -- year comes from the
    section heading ("## Kuwait Public Holidays 2026"). Combined events
    like "National Day - Liberation Day" share a single date range.

    KNOWN LIMITATION: only the current year was visible at verification
    time (no confirmed multi-year table like NYSE/XETR/XSAU) -- treated as
    single-year-only pending confirmation otherwise, similar to XMAD.
    """

    current_year_only = True

    YEAR_RE = re.compile(r'Kuwait Public Holidays\s+(\d{4})')
    MONTHS = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    def __init__(self):
        super().__init__(
            mic="XKUW",
            name="Boursa Kuwait",
            source_url="https://www.boursakuwait.com.kw/en/securities/trading/market-holidays/",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text("\n", strip=True)

        year_match = self.YEAR_RE.search(page_text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        holidays = []
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows[1:]:  # skip header
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue

                month_name = cells[0].get_text(strip=True)
                date_text = cells[1].get_text(strip=True)
                vacation = cells[2].get_text(strip=True)

                if month_name not in self.MONTHS or not date_text or date_text == '-':
                    continue
                if not vacation or vacation == '-':
                    continue

                day_match = re.match(r'(\d{1,2})\s*-?\s*(\d{1,2})?', date_text)
                if not day_match:
                    continue
                start_day = int(day_match.group(1))
                end_day = int(day_match.group(2)) if day_match.group(2) else start_day

                try:
                    start = datetime.strptime(f"{month_name} {start_day} {year}", "%B %d %Y")
                    end = datetime.strptime(f"{month_name} {end_day} {year}", "%B %d %Y")
                except ValueError:
                    continue

                day = start
                while day <= end:
                    if day.weekday() not in (4, 5):  # Fri/Sat weekend
                        holidays.append(HolidayEntry(
                            date=day.strftime('%Y-%m-%d'),
                            name=vacation,
                            status="closed",
                            source_url=self.source_url
                        ))
                    day += timedelta(days=1)

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Boursa Kuwait holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch Boursa Kuwait page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XKUW")

        data = ExchangeData(
            code="XKUW",
            mic="XKUW",
            name=self.name,
            timezone="Asia/Kuwait",
            regular_open="09:00",
            regular_close="13:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="KWD",
            country="Kuwait",
            city="Kuwait City"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class MOEXFetcher(ExchangeFetcher):
    """
    Fetcher for Moscow Exchange (XMOS) holidays.

    Verified live 2026-08-27: moex.com/n94207 is a real, static, accessible
    English-language news page -- explicitly NOT sanctions-blocked, contrary
    to the brief's initial concern. The real challenge is source fragility,
    not accessibility.

    Format: prose, not a table. "On 1-4 January, 7 January, 23 February,
    8 March, 1 May, 9 May, 12 June, 4 November and 31 December 2026, public
    holidays in Russia, all Moscow Exchange markets will be closed." A
    separate sentence lists dates where the market is unusually OPEN
    (make-up weekend sessions) -- those are deliberately NOT parsed as
    holidays, since the market trades on them.

    KNOWN LIMITATION, more severe than most other fetchers in this codebase:
    the source URL is a year-specific news-post ID (n94207) with NO
    predictable naming pattern for future years (unlike HKEX's
    "{year}-Calendar_csv_e.csv" or even NYSE's roughly-annual IR press
    releases) -- next year's schedule will be a different, undiscoverable
    node number requiring a fresh web search each year. This fetcher is
    documented as the most fragile source in the registry; consider it a
    higher-maintenance-burden inclusion, not a "set and forget" one.
    """

    DATE_LIST_RE = re.compile(
        r'all Moscow Exchange markets will be closed'
    )
    FRAGMENT_RE = re.compile(
        r'(\d{1,2})(?:-(\d{1,2}))?\s+(January|February|March|April|May|June|'
        r'July|August|September|October|November|December)(?:\s+(\d{4}))?'
    )

    def __init__(self):
        super().__init__(
            mic="XMOS",
            name="Moscow Exchange",
            source_url="https://www.moex.com/n94207",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text(" ", strip=True)

        # Find the sentence containing the closure list, ending at its
        # period, so we don't accidentally sweep in dates from the
        # following "will be open" sentence.
        closed_match = re.search(
            r'On ([^.]+?), public holidays in Russia, all Moscow Exchange markets will be closed\.',
            page_text
        )
        if not closed_match:
            return []

        fragment_text = closed_match.group(1)
        fragments = self.FRAGMENT_RE.findall(fragment_text)
        if not fragments:
            return []

        # The year only appears on the last fragment; apply it to all.
        year = None
        for _, _, _, y in fragments:
            if y:
                year = int(y)
        if year is None:
            return []

        holidays = []
        for start_day, end_day, month_name, _ in fragments:
            start = int(start_day)
            end = int(end_day) if end_day else start
            try:
                start_date = datetime.strptime(f"{month_name} {start} {year}", "%B %d %Y")
                end_date = datetime.strptime(f"{month_name} {end} {year}", "%B %d %Y")
            except ValueError:
                continue

            day = start_date
            while day <= end_date:
                holidays.append(HolidayEntry(
                    date=day.strftime('%Y-%m-%d'),
                    name="Russian Public Holiday",
                    status="closed",
                    source_url=self.source_url,
                    note="Source gives no per-day holiday name, only a combined closure-date list"
                ))
                day += timedelta(days=1)

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Moscow Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch MOEX page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XMOS")

        data = ExchangeData(
            code="XMOS",
            mic="XMOS",
            name=self.name,
            timezone="Europe/Moscow",
            regular_open="10:00",
            regular_close="18:40",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="RUB",
            country="Russia",
            city="Moscow"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class BMVMexicoFetcher(ExchangeFetcher):
    """
    Fetcher for Bolsa Mexicana de Valores (XMEX) holidays.

    Verified live 2026-09-04: bmv.com.mx/en/bmv-group/holiday-schedule is
    real, static, server-rendered HTML -- a clean two-column table
    ("Holidays" | "2026") with real holiday names and "Month Day" dates (no
    year in the cell; year comes from the column header). Simplest Tier 6
    source found -- comparable to XPRA's simplicity in Tier 4.

    KNOWN LIMITATION: only the current year's column was visible at
    verification time -- no confirmed multi-year table like NYSE/XETR/XSAU.
    Marked `current_year_only = True`, same pattern as XMAD/XWAR/XKUW.
    """

    current_year_only = True

    YEAR_HEADER_RE = re.compile(r'^(20\d{2})$')
    MONTHS = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    def __init__(self):
        super().__init__(
            mic="XMEX",
            name="Bolsa Mexicana de Valores",
            source_url="https://www.bmv.com.mx/en/bmv-group/holiday-schedule",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if not rows:
                continue

            header_cells = rows[0].find_all(['th', 'td'])
            headers = [c.get_text(strip=True) for c in header_cells]
            year = None
            year_col = None
            for idx, h in enumerate(headers):
                m = self.YEAR_HEADER_RE.match(h)
                if m:
                    year = int(m.group(1))
                    year_col = idx
                    break
            if year is None:
                continue

            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) <= year_col:
                    continue

                name = cells[0].get_text(strip=True)
                date_text = cells[year_col].get_text(strip=True)
                parts = date_text.split()
                if len(parts) != 2 or parts[0] not in self.MONTHS:
                    continue
                month_name, day = parts

                try:
                    date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
                except ValueError:
                    continue

                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=name,
                    status="closed",
                    source_url=self.source_url
                ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Bolsa Mexicana de Valores holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch BMV page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XMEX")

        data = ExchangeData(
            code="XMEX",
            mic="XMEX",
            name=self.name,
            timezone="America/Mexico_City",
            regular_open="08:30",
            regular_close="15:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="MXN",
            country="Mexico",
            city="Mexico City"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data

class BymaArgentinaFetcher(ExchangeFetcher):
    """
    Fetcher for Bolsas y Mercados Argentinos (XBUE) holidays.

    Verified live 2026-09-04: byma.com.ar/mercado/calendario-bursatil is
    real, static (Webflow-generated) HTML with footnote references.

    FIXED: parser now works off linearized text, not table tags.
    """

    SPANISH_MONTHS = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
        "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10,
        "noviembre": 11, "diciembre": 12,
    }
    WEEKDAYS_ES = r'Lunes|Martes|Mi[ée]rcoles|Jueves|Viernes|S[áa]bado|Domingo'
    ENTRY_RE = re.compile(
        r'(\d{1,2}\s+de\s+\w+(?:\s+de\s+(\d{4}))?)\s*\n\s*'
        r'(?:' + WEEKDAYS_ES + r')\s*\n\s*'
        r'([^\n]+)',
        re.IGNORECASE
    )
    DATE_RE = re.compile(r'(\d{1,2})\s+de\s+(\w+)', re.IGNORECASE)
    REF_RE = re.compile(r'\((\d)\)\s*$')
    CLOSURE_REFS = {"1", "2", "4"}

    def __init__(self):
        super().__init__(
            mic="XBUE",
            name="Bolsas y Mercados Argentinos",
            source_url="https://www.byma.com.ar/mercado/calendario-bursatil",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text("\n", strip=True)

        start_idx = page_text.find("Motivo")
        end_idx = page_text.find("Referencias")
        if start_idx == -1:
            return []
        section = page_text[start_idx:end_idx if end_idx != -1 else None]

        default_year_match = re.search(r'\b(20\d{2})\b', page_text)
        default_year = int(default_year_match.group(1)) if default_year_match else None

        holidays = []
        for match in self.ENTRY_RE.finditer(section):
            date_text, year_in_date, motivo_text = match.groups()

            date_match = self.DATE_RE.search(date_text)
            if not date_match:
                continue
            day, month_name_es = date_match.groups()
            month_num = self.SPANISH_MONTHS.get(month_name_es.lower())
            if not month_num:
                continue
            year = int(year_in_date) if year_in_date else default_year
            if year is None:
                continue

            ref_match = self.REF_RE.search(motivo_text)
            if not ref_match or ref_match.group(1) not in self.CLOSURE_REFS:
                continue

            name = self.REF_RE.sub('', motivo_text).strip()
            if not name:
                continue

            try:
                date_obj = datetime(year, month_num, int(day))
            except ValueError:
                continue

            holidays.append(HolidayEntry(
                date=date_obj.strftime('%Y-%m-%d'),
                name=name,
                status="closed",
                source_url=self.source_url
            ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch BYMA (Buenos Aires) holiday calendar."""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch BYMA page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XBUE")

        data = ExchangeData(
            code="XBUE",
            mic="XBUE",
            name=self.name,
            timezone="America/Argentina/Buenos_Aires",
            regular_open="11:00",
            regular_close="17:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="ARS",
            country="Argentina",
            city="Buenos Aires"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class B3BrazilFetcher(ExchangeFetcher):
    """
    Fetcher for B3 - Brasil Bolsa Balcao (XBSP) holidays.

    Verified live 2026-09-04: b3.com.br's trading-calendar/holidays page is
    real, static, server-rendered HTML -- an accordion of year sections
    (2021-2026 all present at verification time), each with per-month
    tables. The most complex source built so far in this registry.

    CRITICAL FILTERING LOGIC, verified against real row content:
    Rows mix real B3/Brazil closures with US-holiday settlement-only
    notices in the SAME table, distinguished by a flag icon per row:
      - Brazilian flag icon (pt_BR.gif) + description containing "There
        will be no trading on the equity...markets" -> REAL CLOSURE
      - US flag icon (icon-eua.png) ALONE, description saying "B3
        Clearinghouse will register, clear and settle all trades" ->
        NOT a closure (normal trading continues, only settlement timing
        shifts for NY-linked instruments) -- EXCLUDED
      - Rows with BOTH flags (e.g. Christmas Day, which is a holiday in
        both countries) -> REAL CLOSURE (Brazilian flag alone is sufficient)
      - Special-hours rows (e.g. Ash Wednesday, "Trading and registration
        will open at 1:00 p.m.") -> NOT a full closure, EXCLUDED (delayed
        open, not covered by this registry's closed/early_close semantics
        for a start-of-day event)
      - Pure settlement-lag footnote rows ("B3 Foreign Exchange
        Clearinghouse: T+2/T+1...") with no weekday name in the Evento
        column -> EXCLUDED, not holidays at all

    The filtering rule implemented: a row is a real closure if and only if
    its description contains the phrase "no trading on the equity" AND its
    icon column does not consist ONLY of the US flag with no Brazilian flag
    -- i.e., Brazilian-flag presence (or absence of any icon, which also
    occurs for a few purely-domestic rows) combined with explicit "no
    trading" language is the signal, not the icon alone.
    """

    YEAR_HEADING_RE = re.compile(r'Market Calendar\s+(20\d{2})')
    ROW_DATE_RE = re.compile(r'^(\d{1,2})$')
    NO_TRADING_RE = re.compile(r'no trading on the equity', re.IGNORECASE)
    US_ONLY_RE = re.compile(
        r'clearinghouse will register, clear and settle all trades', re.IGNORECASE
    )
    MONTH_HEADING_RE = re.compile(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)$'
    )

    def __init__(self):
        super().__init__(
            mic="XBSP",
            name="B3 - Brasil Bolsa Balcao",
            source_url="https://b3.com.br/en_us/solutions/platforms/puma-trading-system/for-members-and-traders/trading-calendar/holidays/",
            rate_limit=2.0
        )

    US_ONLY_RE = re.compile(
        r'clearinghouse will (?:register, clear and settle all trades|proceed with the registration, clearing and settlement of all trades)',
        re.IGNORECASE
    )
    MONTH_HEADING_RE = re.compile(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)$'
    )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []
        current_year = None
        current_month = None

        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'a', 'table']):
            if element.name in ('h1', 'h2', 'h3', 'h4'):
                text = element.get_text(strip=True)
                year_match = self.YEAR_HEADING_RE.search(text)
                if year_match:
                    current_year = int(year_match.group(1))
                continue

            if element.name == 'a':
                href = element.get('href', '')
                if not href.startswith('#panel'):
                    continue
                text = element.get_text(strip=True)
                if self.MONTH_HEADING_RE.match(text):
                    current_month = text
                continue

            if current_year is None or current_month is None:
                continue

            for row in element.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue

                day_text = cells[0].get_text(strip=True)
                day_match = self.ROW_DATE_RE.match(day_text)
                if not day_match:
                    continue

                description = cells[-1].get_text(" ", strip=True)
                if self.US_ONLY_RE.search(description):
                    continue
                if not self.NO_TRADING_RE.search(description):
                    continue

                event_name = cells[1].get_text(" ", strip=True)

                try:
                    date_obj = datetime.strptime(
                        f"{current_month} {day_text} {current_year}", "%B %d %Y"
                    )
                except ValueError:
                    continue

                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=event_name,
                    status="closed",
                    source_url=self.source_url
                ))

        seen = set()
        deduped = []
        for h in holidays:
            key = (h.date, h.name)
            if key not in seen:
                seen.add(key)
                deduped.append(h)
        return deduped

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch B3 (Brazil) holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch B3 page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XBSP")

        data = ExchangeData(
            code="XBSP",
            mic="XBSP",
            name=self.name,
            timezone="America/Sao_Paulo",
            regular_open="10:00",
            regular_close="17:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="BRL",
            country="Brazil",
            city="Sao Paulo"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class HOSEVietnamFetcher(PDFFetcher):
    """
    Fetcher for Ho Chi Minh Stock Exchange (XSTC) holidays.

    Verified live 2026-09-06: staticfile.hsx.vn hosts HOSE's own English-
    language annual holiday notice as a real, clean, text-extractable PDF.
    Format is prose date ranges per event ("From Weekday, Month Day, Year
    to the end of Weekday, Month Day, Year" or a single date for one-day
    events), grouped under an "Event" label.

    IMPORTANT NUANCE, confirmed from the actual document text: the notice
    mentions "rescheduled" compensating workdays falling on a Saturday
    (Vietnam's government sometimes moves a weekday's work obligation to a
    weekend to extend a holiday block), but the same document's closing
    bullets explicitly state "HOSE will not implement trading" on those
    same Saturdays. In practice this means the make-up-workday policy
    applies to banks/civil offices, not the exchange -- so this fetcher
    parses the given closure date ranges directly and does NOT attempt to
    add or remove days based on the "rescheduled to Saturday" parenthetical,
    since the closing bullets confirm HOSE simply doesn't trade on those
    Saturdays anyway (already covered by weekend exclusion).

    KNOWN LIMITATION: annual notice, unpredictable URL pattern (a numbered
    upload path), same maintenance pattern as XDFM/XBUD/XWBO.
    """

    EVENT_RE = re.compile(
        r'([A-Z][a-zA-Z\' ]+?)\s+(?:From\s+)?\w+,\s*([A-Z][a-z]+)\s+(\d{1,2})[a-z]{0,2},?\s*(\d{4})'
        r'(?:\s*(?:to the end of|and)\s+\w+,\s*([A-Z][a-z]+)\s+(\d{1,2})[a-z]{0,2},?\s*(\d{4}))?'
    )
    PAREN_RE = re.compile(r'\([^)]*\)')
    BULLET_RE = re.compile(r'-\s*HOSE will not implement trading[^\n]*\n?')

    def __init__(self):
        super().__init__(
            mic="XSTC",
            name="Ho Chi Minh Stock Exchange",
            source_url="https://staticfile.hsx.vn/Uploads/UploadDocuments/2428610/20251209%20-%20HOSE%20-%20Notice%20of%20trading%20holiday%20schedule%20for%202026%20-%20PV.pdf",
            rate_limit=2.0
        )

    def parse_html(self, text: str) -> List[HolidayEntry]:
        """Parses PDF-extracted text (see PDFFetcher)."""
        if not text:
            return []

        # Strip parenthetical asides (lunar-calendar cross-references,
        # rescheduling notes) and the closing "HOSE will not implement
        # trading on Saturday..." bullets FIRST, so they can't be
        # misread as event names or corrupt date-range matching. Applied
        # repeatedly since the source has NESTED parentheses (e.g. "(...
        # (lunar calendar))"), which a single non-greedy pass leaves a
        # stray closing ")" behind from.
        cleaned = text
        for _ in range(3):  # nesting depth observed in practice is at most 2
            cleaned = self.PAREN_RE.sub('', cleaned)
        cleaned = cleaned.replace(')', '').replace('(', '')
        cleaned = self.BULLET_RE.sub('', cleaned)
        # Collapse newlines to spaces so an event name and its date(s)
        # match regardless of how the PDF happened to wrap that line.
        cleaned = re.sub(r'\s+', ' ', cleaned)

        holidays = []
        for match in self.EVENT_RE.finditer(cleaned):
            name, sm, sd, sy, em, ed, ey = match.groups()
            name = name.strip().rstrip(':').strip()
            if not name or len(name) < 3:
                continue

            try:
                start = datetime.strptime(f"{sm} {sd} {sy}", "%B %d %Y")
            except ValueError:
                continue

            if em and ed and ey:
                try:
                    end = datetime.strptime(f"{em} {ed} {ey}", "%B %d %Y")
                except ValueError:
                    end = start
            else:
                end = start

            if end < start:
                continue

            day = start
            while day <= end:
                if day.weekday() < 5:  # Sat/Sun weekend
                    holidays.append(HolidayEntry(
                        date=day.strftime('%Y-%m-%d'),
                        name=name,
                        status="closed",
                        source_url=self.source_url
                    ))
                day += timedelta(days=1)

        # De-duplicate (date, name) -- "Liberation Day and Labor Day" style
        # combined events can otherwise appear twice from overlapping matches
        seen = set()
        deduped = []
        for h in holidays:
            key = (h.date, h.name)
            if key not in seen:
                seen.add(key)
                deduped.append(h)
        return deduped

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch HOSE (Ho Chi Minh) holiday calendar"""
        pdf_bytes = self._make_binary_request()
        if not pdf_bytes:
            raise FetchError("Failed to fetch HOSE PDF")

        text = self._extract_pdf_text(pdf_bytes)
        holidays = self.parse_html(text)
        if not holidays:
            raise ParseError("No holidays found for XSTC")

        data = ExchangeData(
            code="XSTC",
            mic="XSTC",
            name=self.name,
            timezone="Asia/Ho_Chi_Minh",
            regular_open="09:00",
            regular_close="15:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="VND",
            country="Vietnam",
            city="Ho Chi Minh City"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class NigeriaExchangeFetcher(ExchangeFetcher):
    """
    Fetcher for Nigerian Exchange Group (XNSA) holidays.

    Verified live 2026-09-06: ngxgroup.com/exchange/trade/becoming-an-
    investor/trading-holidays/ is real, static, server-rendered HTML with a
    clean two-column table and real holiday names. Includes Islamic
    holidays (Eidul-Fitr, Eid el-Kabir), footnoted by NGX itself as
    "dependent on public announcements from the Federal Government of
    Nigeria" -- mapped to `predicted=True`.

    KNOWN LIMITATION: at verification time the page displayed 2024 data,
    not 2026 -- unlike XCAI's confirmed ASP.NET postback-gating, there's no
    evidence this page is structurally stuck (it's a plain static table,
    not form-driven), so this is treated as the page simply not yet
    updated for the current year rather than a permanent blocker. Whoever
    runs this fetcher in production should verify it has picked up
    current-year data before trusting its output blindly.
    """

    ROW_DATE_RE = re.compile(
        r'([A-Z][a-z]+day),\s*([A-Z][a-z]+)\s+(\d{1,2}),\s*(\d{4})'
    )
    LUNAR_NAME_RE = re.compile(r'eid|ramadan', re.IGNORECASE)

    def __init__(self):
        super().__init__(
            mic="XNSA",
            name="Nigerian Exchange Group",
            source_url="https://ngxgroup.com/exchange/trade/becoming-an-investor/trading-holidays/",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []

        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr')[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                name = cells[0].get_text(strip=True)
                date_text = cells[1].get_text(strip=True)
                if not name or not date_text:
                    continue

                date_match = self.ROW_DATE_RE.search(date_text)
                if not date_match:
                    continue

                _, month_name, day, year = date_match.groups()
                try:
                    date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
                except ValueError:
                    continue

                is_lunar = bool(self.LUNAR_NAME_RE.search(name))
                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=name,
                    status="closed",
                    source_url=self.source_url,
                    predicted=is_lunar if is_lunar else None
                ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Nigerian Exchange Group holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch NGX page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XNSA")

        data = ExchangeData(
            code="XNSA",
            mic="XNSA",
            name=self.name,
            timezone="Africa/Lagos",
            regular_open="10:00",
            regular_close="14:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="NGN",
            country="Nigeria",
            city="Lagos"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class BRVMFetcher(ExchangeFetcher):
    """
    Fetcher for BRVM (Bourse Régionale des Valeurs Mobilières) holidays,
    registered under MIC XBRV.

    Verified live 2026-09-06: brvm.org/fr/jours-feries is real, static
    (Drupal 7), server-rendered HTML -- a single shared calendar table
    serving all 8 UEMOA/WAEMU member countries (Benin, Burkina Faso,
    Guinea-Bissau, Cote d'Ivoire, Mali, Niger, Senegal, Togo) under one
    exchange and one MIC, exactly matching the brief's hypothesis that a
    shared regional exchange would have a single source.

    Islamic holidays are footnoted "(*)" by BRVM itself as "Fete mobile a
    un jour pres" (a moveable feast, +/- one day) -- mapped to
    `predicted=True`. The page's intro sentence is a stale copy-paste
    artifact reading "l'annee 2023" while the actual table data is for
    2026 -- the year is read from each row's date, not from that
    sentence, so this doesn't affect parsing.
    """

    ROW_RE = re.compile(
        r'(\d{2})/(\d{2})/(\d{4})\s*(\(\*\))?\s*\|\s*(.+)'
    )

    def __init__(self):
        super().__init__(
            mic="XBRV",
            name="Bourse Regionale des Valeurs Mobilieres (BRVM)",
            source_url="https://www.brvm.org/fr/jours-feries",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []

        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 2:
                    continue

                date_text = cells[0].get_text(" ", strip=True)
                name_text = cells[1].get_text(" ", strip=True)

                date_match = re.match(r'(\d{2})/(\d{2})/(\d{4})\s*(\(\*\))?', date_text)
                if not date_match or not name_text:
                    continue

                day, month, year, star = date_match.groups()
                try:
                    date_obj = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")
                except ValueError:
                    continue

                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=name_text,
                    status="closed",
                    source_url=self.source_url,
                    predicted=bool(star)
                ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch BRVM (regional, 8-country) holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch BRVM page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XBRV")

        data = ExchangeData(
            code="XBRV",
            mic="XBRV",
            name=self.name,
            timezone="Africa/Abidjan",
            regular_open="09:00",
            regular_close="15:15",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="XOF",
            country="Cote d'Ivoire (regional: 8 UEMOA countries)",
            city="Abidjan"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class ColomboFetcher(PDFFetcher):
    """
    Fetcher for Colombo Stock Exchange (XCOL) holidays.

    Verified live 2026-09-06: CSE's official circular, hosted on
    cdn.cse.lk, is a real, clean, single-column, text-extractable PDF.
    Format: "Month | Date(ordinal) Weekday | Holiday Name" grouped by
    month heading, with some months listing multiple holidays where a
    second holiday's row omits its own date (shares the prior line's
    date) -- confirmed in the real document (May 1st: "May Day" AND
    "Vesak Full Moon Poya Day" both fall on the same date).

    Real content includes both Buddhist Poya (full moon) holidays --
    Sri Lanka's distinctive monthly lunar-calendar closures -- and Islamic
    holidays (Id-Ul-Allah, Milad-Un-Nabi), the latter mapped to
    `predicted=True` since Islamic dates are moon-sighting dependent; Poya
    days are NOT marked predicted since they follow a precisely computable
    (not sighting-dependent) full-moon calendar.

    KNOWN LIMITATION: annual circular, unpredictable URL (a hashed upload
    path) -- same maintenance pattern as other PDF-based fetchers here.
    """

    MONTH_HEADING_RE = re.compile(
        r'^(January|February|March|April|May|June|July|August|September|October|November|December)$'
    )
    ROW_RE = re.compile(
        r'^(\d{1,2})[a-z]{2}\s+[A-Z][a-z]+day\s+(.+)$'
    )
    ISLAMIC_NAME_RE = re.compile(r'id-ul|milad|hadji|ramadan', re.IGNORECASE)

    def __init__(self):
        super().__init__(
            mic="XCOL",
            name="Colombo Stock Exchange",
            source_url="https://cdn.cse.lk/cmt/upload_report_file/QMEnyQ5BhnLphDgA_22Oct2025113922GMT_1761133162860.pdf",
            rate_limit=2.0
        )
        self.referer = "https://www.cse.lk/"
    
    def parse_html(self, text: str) -> List[HolidayEntry]:
        """Parses PDF-extracted text (see PDFFetcher)."""
        if not text:
            return []

        year_match = re.search(r'HOLIDAYS FOR (\d{4})', text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        holidays = []
        current_month = None
        last_date = None

        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue

            if self.MONTH_HEADING_RE.match(line):
                current_month = line
                last_date = None
                continue

            row_match = self.ROW_RE.match(line)
            if row_match and current_month:
                day, name = row_match.groups()
                try:
                    date_obj = datetime.strptime(f"{current_month} {day} {year}", "%B %d %Y")
                except ValueError:
                    continue
                last_date = date_obj
            elif current_month and last_date:
                # A continuation line: another holiday on the same date as
                # the previous row (e.g. "Vesak Full Moon Poya Day" with no
                # date of its own, following "May Day" on May 1st)
                name = line
                date_obj = last_date
            else:
                continue

            name = name.strip()
            if not name:
                continue

            is_islamic = bool(self.ISLAMIC_NAME_RE.search(name))
            holidays.append(HolidayEntry(
                date=date_obj.strftime('%Y-%m-%d'),
                name=name,
                status="closed",
                source_url=self.source_url,
                predicted=is_islamic if is_islamic else None
            ))

        # Merge entries that land on the same date (confirmed in the real
        # data -- May Day and Vesak Full Moon Poya Day can coincide) into a
        # single HolidayEntry with a combined name. ExchangeData.validate()
        # rejects duplicate dates outright, and changing that core
        # constraint would ripple into every other fetcher and the schema
        # itself -- merging here is the conservative fix, and it's also
        # arguably more correct: a calendar consumer wants one entry per
        # actual non-trading day, not two entries claiming the same date.
        by_date: Dict[str, HolidayEntry] = {}
        for h in holidays:
            if h.date in by_date:
                existing = by_date[h.date]
                combined_name = f"{existing.name} / {h.name}"
                by_date[h.date] = HolidayEntry(
                    date=h.date,
                    name=combined_name,
                    status="closed",
                    source_url=self.source_url,
                    predicted=(existing.predicted or h.predicted) if (existing.predicted is not None or h.predicted is not None) else None
                )
            else:
                by_date[h.date] = h

        return list(by_date.values())

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Colombo Stock Exchange holiday calendar"""
        pdf_bytes = self._make_binary_request()
        if not pdf_bytes:
            raise FetchError("Failed to fetch CSE circular PDF")

        text = self._extract_pdf_text(pdf_bytes)
        holidays = self.parse_html(text)
        if not holidays:
            raise ParseError("No holidays found for XCOL")

        data = ExchangeData(
            code="XCOL",
            mic="XCOL",
            name=self.name,
            timezone="Asia/Colombo",
            regular_open="09:30",
            regular_close="14:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="LKR",
            country="Sri Lanka",
            city="Colombo"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class GhanaExchangeFetcher(ExchangeFetcher):
    """
    Fetcher for Ghana Stock Exchange (XGSE) holidays.

    Verified live 2026-09-06: gse.com.gh/events/ is real, static WordPress
    HTML (found via direct site navigation after two search-based misses --
    the site's own "Events & Holidays" nav link, not indexed cleanly by
    search). Real table with names, including Islamic holidays (Eid-Ul-Fitr,
    Eid-Al-Adha, marked "***" by GSE itself: "Dates are subject to the
    visibility of the New Moon" -- mapped to predicted=True).

    HANDLES ALTERNATE-DATE ROWS: some rows list two possible dates separated
    by "/" (e.g. "Friday July 1st/3rd" for Republic Day, "Monday December
    26th/28th" for Boxing Day) because the holiday shifts to a different day
    depending on what weekday the base date falls on. The given weekday name
    is used to disambiguate: each candidate day is checked against the known
    year, and the one whose computed weekday matches the stated "Day" column
    is used. Confirmed against 2026 specifically: July 1 is a Wednesday and
    July 3 is a Friday, so "Friday July 1st/3rd" resolves to July 3.
    """

    YEAR_RE = re.compile(r'Public Holidays for the year\s+(\d{4})')
    ROW_RE = re.compile(
        r'^([A-Za-z]+)\s*\|\s*([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:/(\d{1,2})(?:st|nd|rd|th)?)?\s*\|\s*(.+)$'
    )
    LUNAR_NAME_RE = re.compile(r'eid', re.IGNORECASE)
    MONTHS = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    def __init__(self):
        super().__init__(
            mic="XGSE",
            name="Ghana Stock Exchange",
            source_url="https://gse.com.gh/events/",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text(" ", strip=True)

        year_match = re.search(r'Public Holidays for the year (\d{4})', page_text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        holidays = []
        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue

                weekday_text = cells[0].get_text(strip=True)
                date_text = cells[1].get_text(strip=True)
                name = cells[2].get_text(strip=True)

                if not name or '***' in date_text or weekday_text == '***':
                    # Eid dates aren't given a specific date on this page
                    # ("*** | *** | Eid-Ul-Fitr") -- skip rather than guess
                    continue

                # Parse "Month Day" or "Month Day1st/Day2nd" (alternate dates)
                date_match = re.match(
                    r'([A-Za-z]+)\s+(\d{1,2})(?:st|nd|rd|th)?(?:/(\d{1,2})(?:st|nd|rd|th)?)?',
                    date_text
                )
                if not date_match:
                    continue
                month_name, day1, day2 = date_match.groups()
                if month_name not in self.MONTHS:
                    continue

                candidates = [day1] + ([day2] if day2 else [])
                chosen_date = None
                for day in candidates:
                    try:
                        candidate_date = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
                    except ValueError:
                        continue
                    if candidate_date.strftime('%A') == weekday_text or len(candidates) == 1:
                        chosen_date = candidate_date
                        break
                if chosen_date is None:
                    continue

                is_lunar = bool(self.LUNAR_NAME_RE.search(name))
                holidays.append(HolidayEntry(
                    date=chosen_date.strftime('%Y-%m-%d'),
                    name=name,
                    status="closed",
                    source_url=self.source_url,
                    predicted=is_lunar if is_lunar else None
                ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Ghana Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch GSE page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XGSE")

        data = ExchangeData(
            code="XGSE",
            mic="XGSE",
            name=self.name,
            timezone="Africa/Accra",
            regular_open="10:00",
            regular_close="15:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="GHS",
            country="Ghana",
            city="Accra"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class BermudaExchangeFetcher(ExchangeFetcher):
    """
    Fetcher for Bermuda Stock Exchange (XBDA) holidays.

    Verified live 2026-09-06: bsx.com/trading-hours-and-holidays is real,
    static (Drupal 11) HTML -- one of the cleanest sources in this entire
    registry, multi-year (2024-2027), transposed table format like NYSE's,
    real names, with a Christmas Eve early-close note ("2pm AST Close").
    """

    MONTHS = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]
    YEAR_RE = re.compile(r'^(20\d{2})$')
    DATE_RE = re.compile(
        r'([A-Z][a-z]+)\s+(\d{1,2})(?:\s+and\s+([A-Z][a-z]+)?\s*(\d{1,2}))?'
    )

    def __init__(self):
        super().__init__(
            mic="XBDA",
            name="Bermuda Stock Exchange",
            source_url="https://www.bsx.com/trading-hours-and-holidays",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []

        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            if not rows:
                continue
            header_cells = rows[0].find_all(['th', 'td'])
            headers = [c.get_text(strip=True) for c in header_cells]

            year_cols = []
            for idx, h in enumerate(headers):
                if self.YEAR_RE.match(h):
                    year_cols.append((idx, int(h)))
            if not year_cols:
                continue

            for row in rows[1:]:
                cells = row.find_all(['td', 'th'])
                if not cells:
                    continue
                name = cells[0].get_text(" ", strip=True)
                # Strip footnote markers and parenthetical asides for the name
                clean_name = re.sub(r'\*+', '', name)
                clean_name = re.sub(r'\([^)]*\)', '', clean_name).strip()
                if not clean_name:
                    continue

                for col_idx, year in year_cols:
                    if col_idx >= len(cells):
                        continue
                    date_text = cells[col_idx].get_text(" ", strip=True)
                    date_text_clean = re.sub(r'\*+', '', date_text)

                    for month_match in re.finditer(
                        r'([A-Z][a-z]+)\s+(\d{1,2})', date_text_clean
                    ):
                        month_name, day = month_match.groups()
                        if month_name not in self.MONTHS:
                            continue
                        try:
                            date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
                        except ValueError:
                            continue

                        status = "early_close" if "AST Close" in name else "closed"
                        holidays.append(HolidayEntry(
                            date=date_obj.strftime('%Y-%m-%d'),
                            name=clean_name,
                            status=status,
                            source_url=self.source_url
                        ))

        # De-duplicate
        seen = set()
        deduped = []
        for h in holidays:
            key = (h.date, h.name)
            if key not in seen:
                seen.add(key)
                deduped.append(h)
        return deduped

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Bermuda Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch BSX page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XBDA")

        data = ExchangeData(
            code="XBDA",
            mic="XBDA",
            name=self.name,
            timezone="Atlantic/Bermuda",
            regular_open="09:00",
            regular_close="16:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="BMD",
            country="Bermuda",
            city="Hamilton"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class CaymanExchangeFetcher(ExchangeFetcher):
    """
    Fetcher for Cayman Islands Stock Exchange (XCAY) holidays.

    Verified live 2026-09-06: csx.ky/aboutus/holidays.asp is real, static
    HTML with two full year sections (2025 and 2026) both present in the
    raw response. Format: "Weekday | Day(ordinal) Month | Holiday Name" per
    row, with anchor links (#2025, #2026) navigating within the same page
    rather than separate pages.
    """

    ROW_RE = re.compile(
        r'^([A-Za-z]+)\s*\|\s*(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)\s*\|\s*(.+)$'
    )
    MONTHS = ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"]

    def __init__(self):
        super().__init__(
            mic="XCAY",
            name="Cayman Islands Stock Exchange",
            source_url="https://www.csx.ky/aboutus/holidays.asp",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []

        # This page has two distinct year tables (2025, 2026) but no
        # explicit year heading immediately above each -- infer the year
        # from position (first table = earlier year based on anchor order)
        # is unreliable, so instead detect year via the first row's date:
        # if the date is Jan 1 and we haven't assigned a year yet, treat
        # tables in document order as consecutive years starting from
        # whatever year contains a January-1-on-the-correct-weekday match.
        # Simpler and more robust: this page's two tables are chronological
        # (current year first per site convention observed), determined by
        # checking which of two plausible years makes "New Year's Day"'s
        # given weekday correct.
        tables = soup.find_all('table')
        candidate_years = list(range(datetime.now().year - 1, datetime.now().year + 3))

        for table in tables:
            rows = table.find_all('tr')
            if not rows:
                continue

            first_row_cells = rows[0].find_all(['td', 'th'])
            if len(first_row_cells) < 3:
                continue
            first_weekday = first_row_cells[0].get_text(strip=True)
            first_date_text = first_row_cells[1].get_text(strip=True)
            day_match = re.match(r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)', first_date_text)
            if not day_match:
                continue
            day, month_name = day_match.groups()

            table_year = None
            for y in candidate_years:
                try:
                    d = datetime.strptime(f"{month_name} {day} {y}", "%B %d %Y")
                except ValueError:
                    continue
                if d.strftime('%A') == first_weekday:
                    table_year = y
                    break
            if table_year is None:
                continue

            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue
                weekday_text = cells[0].get_text(strip=True)
                date_text = cells[1].get_text(strip=True)
                name = cells[2].get_text(strip=True)

                day_match = re.match(r'(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)', date_text)
                if not day_match or not name:
                    continue
                day, month_name = day_match.groups()
                if month_name not in self.MONTHS:
                    continue

                try:
                    date_obj = datetime.strptime(f"{month_name} {day} {table_year}", "%B %d %Y")
                except ValueError:
                    continue

                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=name,
                    status="closed",
                    source_url=self.source_url
                ))

        seen = set()
        deduped = []
        for h in holidays:
            key = (h.date, h.name)
            if key not in seen:
                seen.add(key)
                deduped.append(h)
        return deduped

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Cayman Islands Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch CSX page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XCAY")

        data = ExchangeData(
            code="XCAY",
            mic="XCAY",
            name=self.name,
            timezone="America/Cayman",
            regular_open="09:00",
            regular_close="13:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="KYD",
            country="Cayman Islands",
            city="George Town"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class LuxembourgExchangeFetcher(ExchangeFetcher):
    """
    Fetcher for Luxembourg Stock Exchange (XLUX) holidays.

    Verified live 2026-09-06: luxse.com/trading/opening-hours-and-closing-days
    is real, static HTML, but genuinely sparse: only ONE closing day (25
    December, Christmas Day) and one "will not be closed despite being a
    public holiday" exception (23 June, National Day) were present in the
    raw response for 2026. This may accurately reflect LuxSE's actual
    calendar -- it's primarily an international bond/fund listing venue,
    not a high-volume retail equity market, and may genuinely observe far
    fewer closures than typical exchanges -- or the page may render
    additional entries client-side that weren't captured. NOT assumed to be
    complete; flagged explicitly rather than silently presented as
    equivalent in confidence to richer sources like XBDA or XMAL.
    """

    DAY_RE = re.compile(
        r'([A-Z][a-z]+)\s+(\d{1,2})\s+([A-Z][a-z]+)'  # "Friday 25 December"
    )
    MONTHS = {"January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"}

    def __init__(self):
        super().__init__(
            mic="XLUX",
            name="Luxembourg Stock Exchange",
            source_url="https://www.luxse.com/trading/opening-hours-and-closing-days",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text("\n", strip=True)

        year_match = re.search(r'Closing days\s+(\d{4})', page_text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        # Only the section BEFORE the "will not be closed" sentence
        # represents real closures; everything after is exceptions
        # (exchange stays open) and must be excluded.
        exception_marker = re.search(
            r'which are public holidays, the Luxembourg Stock Exchange will not be closed',
            page_text
        )
        closures_section = page_text[:exception_marker.start()] if exception_marker else page_text

        holidays = []
        for match in self.DAY_RE.finditer(closures_section):
            weekday, day, month_name = match.groups()
            if month_name not in self.MONTHS:
                continue
            try:
                date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
            except ValueError:
                continue

            # Find the holiday name on the next line in the original text
            idx = page_text.find(match.group(0))
            after = page_text[idx + len(match.group(0)):idx + len(match.group(0)) + 60]
            name = after.strip().split('\n')[0].strip() or "Closing Day"

            holidays.append(HolidayEntry(
                date=date_obj.strftime('%Y-%m-%d'),
                name=name,
                status="closed",
                source_url=self.source_url,
                note="Source page lists very few closures (verified: only 1 for 2026) -- may be genuinely accurate for this listing-focused exchange, or may omit entries rendered client-side. Not confirmed complete."
            ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Luxembourg Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch LuxSE page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XLUX")

        data = ExchangeData(
            code="XLUX",
            mic="XLUX",
            name=self.name,
            timezone="Europe/Luxembourg",
            regular_open="09:00",
            regular_close="17:40",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="EUR",
            country="Luxembourg",
            city="Luxembourg"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class MaltaExchangeFetcher(ExchangeFetcher):
    """
    Fetcher for Malta Stock Exchange (XMAL) holidays.

    Verified live 2026-09-06: borzamalta.com.mt/trading is real, static
    HTML with a rich table (DATE | HOLIDAY | TRADING | SETTLEMENT) spanning
    late 2025 into 2026. The TRADING column explicitly distinguishes real
    closures ("Non-trading day") from foreign-holiday settlement-only
    notices ("Normal trading day", labeled "US Holiday" / "UK Holiday" /
    "US and UK Holiday") -- the same foreign-holiday-exclusion pattern seen
    in XTSE (Tier 4) and XBSP (Tier 6). Only "Non-trading day" rows are
    real MSE closures.
    """

    ROW_RE = re.compile(
        r'([A-Z][a-z]+)\s+(\d{1,2})\s+([A-Z][a-z]+)\s+(\d{4})'
    )
    MONTHS = {"January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"}

    def __init__(self):
        super().__init__(
            mic="XMAL",
            name="Malta Stock Exchange",
            source_url="https://www.borzamalta.com.mt/trading",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        holidays = []

        tables = soup.find_all('table')
        for table in tables:
            header_row = table.find('tr')
            if not header_row:
                continue
            headers = [c.get_text(strip=True).upper() for c in header_row.find_all(['th', 'td'])]
            if 'DATE' not in headers or 'TRADING' not in headers:
                continue
            date_idx = headers.index('DATE')
            holiday_idx = headers.index('HOLIDAY') if 'HOLIDAY' in headers else date_idx + 1
            trading_idx = headers.index('TRADING')

            for row in table.find_all('tr')[1:]:
                cells = row.find_all(['td', 'th'])
                if len(cells) <= max(date_idx, holiday_idx, trading_idx):
                    continue

                date_text = cells[date_idx].get_text(" ", strip=True)
                name = cells[holiday_idx].get_text(" ", strip=True)
                trading_status = cells[trading_idx].get_text(" ", strip=True)

                if 'non-trading' not in trading_status.lower():
                    continue  # foreign holiday, MSE trades normally

                date_match = self.ROW_RE.search(date_text)
                if not date_match or not name:
                    continue
                _, day, month_name, year = date_match.groups()
                if month_name not in self.MONTHS:
                    continue

                try:
                    date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
                except ValueError:
                    continue

                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=name,
                    status="closed",
                    source_url=self.source_url
                ))

        seen = set()
        deduped = []
        for h in holidays:
            key = (h.date, h.name)
            if key not in seen:
                seen.add(key)
                deduped.append(h)
        return deduped

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Malta Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch Malta Stock Exchange page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XMAL")

        data = ExchangeData(
            code="XMAL",
            mic="XMAL",
            name=self.name,
            timezone="Europe/Malta",
            regular_open="09:30",
            regular_close="15:30",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="EUR",
            country="Malta",
            city="Valletta"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class ZagrebExchangeFetcher(ExchangeFetcher):
    """
    Fetcher for Zagreb Stock Exchange (XZAG) holidays.

    Verified live 2026-09-06: zse.hr's "Trading calendar in 2026" news post
    is real, static HTML with a clean table, real names, single year
    (2026-specific news-post URL -- same annual-URL-update pattern as
    XMOS/XBUD/XWBO).
    """

    ROW_RE = re.compile(
        r'([A-Z][a-z]+)\s*\*{0,2}([A-Z][a-z]+)\s+(\d{1,2})[a-z]{2}\*{0,2}\s*(.+)'
    )
    MONTHS = {"January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"}

    def __init__(self):
        super().__init__(
            mic="XZAG",
            name="Zagreb Stock Exchange",
            source_url="https://zse.hr/en/trading-calendar-in-2026/3260",
            rate_limit=2.0
        )

    def parse_html(self, html: str) -> List[HolidayEntry]:
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        page_text = soup.get_text(" ", strip=True)

        year_match = re.search(r'In\s+(\d{4}),\s+Zagreb Stock Exchange', page_text)
        if not year_match:
            return []
        year = int(year_match.group(1))

        holidays = []
        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                if len(cells) < 3:
                    continue

                date_text = cells[1].get_text(" ", strip=True)
                name = cells[2].get_text(" ", strip=True)

                date_match = re.search(r'([A-Za-z]+)\s+(\d{1,2})', date_text)
                if not date_match or not name:
                    continue
                month_name, day = date_match.groups()
                if month_name not in self.MONTHS:
                    continue

                try:
                    date_obj = datetime.strptime(f"{month_name} {day} {year}", "%B %d %Y")
                except ValueError:
                    continue

                holidays.append(HolidayEntry(
                    date=date_obj.strftime('%Y-%m-%d'),
                    name=name,
                    status="closed",
                    source_url=self.source_url
                ))

        return holidays

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(FetchError,))
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch Zagreb Stock Exchange holiday calendar"""
        html = self._make_request()
        if not html:
            raise FetchError("Failed to fetch ZSE page")

        holidays = self.parse_html(html)
        if not holidays:
            raise ParseError("No holidays found for XZAG")

        data = ExchangeData(
            code="XZAG",
            mic="XZAG",
            name=self.name,
            timezone="Europe/Zagreb",
            regular_open="09:30",
            regular_close="16:00",
            holidays=holidays,
            source_urls=[self.source_url],
            currency="EUR",
            country="Croatia",
            city="Zagreb"
        )

        errors = data.validate()
        if errors:
            raise ValidationError(f"Invalid data: {', '.join(errors)}")

        return data


class ExchangeFetcherRegistry:
    """Registry of available exchange fetchers"""
    
    def __init__(self):
        self.fetchers: Dict[str, ExchangeFetcher] = {}
        self._register_default_fetchers()
    
    def _register_default_fetchers(self):
        """Register default fetchers"""
        self.register(NYSEFetcher())
        self.register(NASDAQFetcher())
        self.register(LSEFetcher())
        self.register(XETRFetcher())
        self.register(ASXFetcher())
        self.register(EuronextParisFetcher())
        self.register(EuronextAmsterdamFetcher())
        self.register(TokyoFetcher())
        self.register(SSEFetcher())
        # self.register(SZSEFetcher())  # Blocked: connection reset
        self.register(HKEXFetcher())
        # All 10 originally-scoped Tier 1 exchanges now have automated
        # fetchers as of 2026-08-27. See docs/fetcher_verification.md.

        # Tier 2 (regional hubs) -- only 3 of 10 verified buildable; see
        # docs/fetcher_verification.md and BLOCKED.md for the other 7
        # (XSES, XSWX, XKRX, XBOM, XNSE, XJKT blocked; XTAI unresolved).
        self.register(TSXFetcher())
        self.register(BMEMadridFetcher())

        # Tier 3 (Gulf/EMEA) -- 3 of 10 verified buildable so far
        # (XDFM, XKUW, XMOS); see docs/fetcher_verification.md and
        # BLOCKED.md for the other 7 (XTAD, XBAH, XQSE, XCAI, XJSE, XIST
        # blocked; XMUS not yet verified).
        self.register(XDFMFetcher())
        self.register(BoursaKuwaitFetcher())
        self.register(MOEXFetcher())

        # Tier 4 (European smaller markets) -- 8 of 10 verified buildable
        # (XWBO, XWAR, XPRA, XBUD, XDUB, XBRU, XLIS, XOSL); XAMS already
        # registered above from Tier 1. Only XATH blocked (visual-grid PDF,
        # same problem as XSWX). See docs/fetcher_verification.md.
        self.register(ViennaFetcher())
        self.register(WarsawFetcher())
        self.register(PragueFetcher())
        self.register(BudapestFetcher())
        self.register(EuronextDublinFetcher())
        self.register(EuronextBrusselsFetcher())
        self.register(EuronextLisbonFetcher())
        self.register(EuronextOsloFetcher())

        # Tier 5 (Nordic/Baltic) -- 7 of 7 buildable via two shared
        # fetchers, confirming the "shared structure" hypothesis (like
        # Euronext in Tier 4). See docs/fetcher_verification.md.
        self.register(StockholmFetcher())
        self.register(HelsinkiFetcher())
        self.register(CopenhagenFetcher())
        self.register(IcelandFetcher())
        self.register(TallinnFetcher())
        self.register(RigaFetcher())
        self.register(VilniusFetcher())

        # Tier 6 (emerging markets) -- 3 of 10 verified buildable
        # (XBSP, XMEX, XBUE); 2 confirmed blocked (XSGO, XKLS); 5 not
        # verified within this round's budget (XBOG, XLIM, XPHS, XBKK,
        # XSTC). See docs/fetcher_verification.md and BLOCKED.md.
        self.register(B3BrazilFetcher())
        self.register(BMVMexicoFetcher())
        self.register(BymaArgentinaFetcher())

        # Tier 7 (Africa/South Asia) -- 4 of 9 verified buildable
        # (XNSA, XBRV, XCOL), plus XSTC resolving the one Tier 6 carryover
        # (XSTC/hsx.vn). 5 blocked (XTUN, XCAS, XKAR, XDHA) or unverified
        # (XNBO, XGSE). See docs/fetcher_verification.md and BLOCKED.md.
        self.register(HOSEVietnamFetcher())
        self.register(NigeriaExchangeFetcher())
        self.register(BRVMFetcher())
        self.register(ColomboFetcher())

        # Tier 8 (small/island markets), 2026-09-06 -- 6 of 8 verified
        # buildable (XBDA, XCAY, XLUX, XMAL, XZAG), plus XGSE resolving the
        # one Tier 7 carryover. 4 blocked (XBUL, XBEK, XNZE, XNBO). This is
        # the final tier -- see docs/fetcher_verification.md and BLOCKED.md.
        self.register(GhanaExchangeFetcher())
        self.register(BermudaExchangeFetcher())
        self.register(CaymanExchangeFetcher())
        self.register(LuxembourgExchangeFetcher())
        self.register(MaltaExchangeFetcher())
        self.register(ZagrebExchangeFetcher())
    
    def register(self, fetcher: ExchangeFetcher):
        """Register a fetcher"""
        self.fetchers[fetcher.mic] = fetcher
        logger.debug(f"Registered fetcher: {fetcher}")
    
    def get(self, mic: str) -> Optional[ExchangeFetcher]:
        """Get a fetcher by MIC code"""
        return self.fetchers.get(mic.upper())
    
    def list_available(self) -> List[str]:
        """List all available fetcher MICs"""
        return sorted(self.fetchers.keys())
    
    def __len__(self):
        return len(self.fetchers)
    
    def __iter__(self):
        return iter(self.fetchers.values())


class RegistryUpdater:
    """Updates the registry with fetched data"""
    
    def __init__(
        self,
        registry_dir: Path,
        cache_dir: Optional[Path] = None,
        use_cache: bool = True
    ):
        self.registry_dir = Path(registry_dir)
        self.exchanges_dir = self.registry_dir / "exchanges"
        self.exchanges_dir.mkdir(exist_ok=True)
        
        self.fetchers = ExchangeFetcherRegistry()
        self.transaction_manager = TransactionManager(self.registry_dir)
        
        if cache_dir is None:
            cache_dir = self.registry_dir / ".cache"
        self.cache_manager = CacheManager(cache_dir) if use_cache else None
    
    def load_current_exchange(self, mic: str) -> Optional[Dict[str, Any]]:
        """Load current exchange data from registry"""
        exchange_file = self.exchanges_dir / f"{mic.upper()}.json"
        if not exchange_file.exists():
            return None
        
        try:
            with open(exchange_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {exchange_file}: {e}")
            return None
    
    def compare_holidays(
        self,
        current: Optional[Dict[str, Any]],
        fetched: ExchangeData
    ) -> Tuple[bool, List[str]]:
        """Compare current and fetched holidays"""
        if current is None:
            return True, ["New exchange"]
        
        current_holidays = set()
        if 'holidays' in current and 'explicit' in current['holidays']:
            for holiday in current['holidays']['explicit']:
                current_holidays.add(holiday['date'])
        
        fetched_holidays = set(h.date for h in fetched.holidays)
        
        added = fetched_holidays - current_holidays
        
        changes = []
        if added:
            changes.append(f"Added {len(added)} holidays: {', '.join(sorted(added))}")
        
        return bool(changes), changes
    
    def generate_exchange_json(self, data: ExchangeData, current: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generate exchange JSON in registry format, merging with existing data if available"""
        # Start with existing holidays if available
        merged_holidays = {}
        if current and 'holidays' in current and 'explicit' in current['holidays']:
            for holiday in current['holidays']['explicit']:
                merged_holidays[holiday['date']] = holiday
        
        # Add new holidays from fetched data
        for h in data.holidays:
            holiday_dict = h.to_dict()
            if holiday_dict['date'] not in merged_holidays:
                merged_holidays[holiday_dict['date']] = holiday_dict
        
        # Sort holidays by date
        holidays_explicit = [merged_holidays[date] for date in sorted(merged_holidays.keys())]
        
        # Preserve existing fields if available
        exchange_json = {}
        if current:
            exchange_json = current.copy()
        
        # Update with fetched data
        exchange_json.update({
            "code": data.code,
            "name": data.name,
            "mic": data.mic,
            "timezone": data.timezone,
            "regular_hours": {
                "open": data.regular_open,
                "close": data.regular_close
            },
            "holidays": {
                "explicit": holidays_explicit,
                "recurrence_rules": current.get('holidays', {}).get('recurrence_rules', []) if current else []
            }
        })
        
        # Preserve extended hours if they exist
        if current and 'extended_hours' in current:
            exchange_json['extended_hours'] = current['extended_hours']
        else:
            exchange_json['extended_hours'] = {}
        
        # Preserve sessions if they exist
        if current and 'sessions' in current:
            exchange_json['sessions'] = current['sessions']
        else:
            exchange_json['sessions'] = []
        
        # Preserve ad_hoc_closures if they exist
        if current and 'ad_hoc_closures' in current:
            exchange_json['ad_hoc_closures'] = current['ad_hoc_closures']
        else:
            exchange_json['ad_hoc_closures'] = []
        
        # Update generation range
        if current and 'generation_range' in current:
            exchange_json['generation_range'] = current['generation_range']
        else:
            exchange_json['generation_range'] = [
                datetime.now().strftime("%Y-01-01"),
                (datetime.now() + timedelta(days=365*5)).strftime("%Y-12-31")
            ]
        
        return exchange_json
    
    def update_exchange(
        self,
        mic: str,
        dry_run: bool = False,
        force: bool = False
    ) -> Tuple[FetchStatus, Optional[str]]:
        """Update a single exchange"""
        mic = mic.upper()
        fetcher = self.fetchers.get(mic)
        
        if not fetcher:
            logger.warning(f"No fetcher available for {mic}")
            return FetchStatus.SKIPPED, None
        
        logger.info(f"Fetching data for {mic} ({fetcher.name})...")
        
        # Check cache first
        fetched_data = None
        if self.cache_manager and not force:
            fetched_data = self.cache_manager.get(mic, fetcher.source_url)
            if fetched_data:
                logger.debug(f"Using cached data for {mic}")
        
        # Fetch if not cached
        if not fetched_data:
            try:
                fetched_data = fetcher.fetch()
                if fetched_data and self.cache_manager:
                    self.cache_manager.set(mic, fetcher.source_url, fetched_data)
            except FetchError as e:
                logger.error(f"Failed to fetch {mic}: {e}")
                return FetchStatus.FAILED, str(e)
        
        if not fetched_data:
            logger.error(f"No data fetched for {mic}")
            return FetchStatus.FAILED, None
        
        # Validate fetched data
        errors = fetched_data.validate()
        if errors:
            logger.error(f"Validation errors for {mic}: {', '.join(errors)}")
            return FetchStatus.VALIDATION_ERROR, "; ".join(errors)
        
        # Compare with current
        current_data = self.load_current_exchange(mic)
        has_changes, change_details = self.compare_holidays(current_data, fetched_data)
        
        if current_data is None:
            status = FetchStatus.NEW_EXCHANGE
            message = f"New exchange: {fetcher.name}"
        elif has_changes:
            status = FetchStatus.UPDATED
            message = "; ".join(change_details)
        else:
            status = FetchStatus.UNCHANGED
            message = "No changes detected"
        
        # Write if needed
        if status in [FetchStatus.NEW_EXCHANGE, FetchStatus.UPDATED]:
            if not dry_run:
                # Create backup
                if current_data is not None:
                    backup = self.transaction_manager.create_backup(mic)
                    if backup:
                        logger.debug(f"Created backup: {backup.name}")
                
                # Write new data (merge with existing)
                exchange_json = self.generate_exchange_json(fetched_data, current_data)
                output_file = self.exchanges_dir / f"{mic.upper()}.json"
                
                try:
                    with open(output_file, 'w') as f:
                        json.dump(exchange_json, f, indent=2)
                        f.write('\n')
                    logger.info(f"Wrote {output_file}")
                except IOError as e:
                    logger.error(f"Failed to write {output_file}: {e}")
                    return FetchStatus.FAILED, str(e)
            else:
                logger.info(f"[DRY RUN] Would write {mic.upper()}.json")
        
        logger.info(f"{mic}: {status.value} - {message}")
        return status, message
    
    def update_all(
        self,
        dry_run: bool = False,
        force: bool = False,
        max_workers: int = 4
    ) -> Dict[str, Tuple[FetchStatus, Optional[str]]]:
        """Update all exchanges with concurrency"""
        results = {}
        fetchers_list = list(self.fetchers)  # List of ExchangeFetcher objects  # List of ExchangeFetcher objects
        
        if max_workers > 1 and len(fetchers_list) > 1:
            # Concurrent update
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {
                    executor.submit(self.update_exchange, fetcher.mic, dry_run, force): fetcher.mic
                    for fetcher in fetchers_list
                }
                
                if HAS_TQDM:
                    with tqdm(total=len(futures), desc="Updating exchanges") as pbar:
                        for future in as_completed(futures):
                            mic = futures[future]
                            try:
                                results[mic] = future.result()
                            except Exception as e:
                                logger.error(f"Error updating {mic}: {e}")
                                results[mic] = (FetchStatus.FAILED, str(e))
                            pbar.update(1)
                            pbar.set_postfix_str(f"{mic}: {results[mic][0].value}")
                else:
                    for future in as_completed(futures):
                        mic = futures[future]
                        try:
                            results[mic] = future.result()
                        except Exception as e:
                            logger.error(f"Error updating {mic}: {e}")
                            results[mic] = (FetchStatus.FAILED, str(e))
        else:
            # Sequential update
            if HAS_TQDM:
                with tqdm(total=len(fetchers_list), desc="Updating exchanges") as pbar:
                    for fetcher in fetchers_list:
                        mic = fetcher.mic
                        results[mic] = self.update_exchange(mic, dry_run, force)
                        pbar.update(1)
                        pbar.set_postfix_str(f"{mic}: {results[mic][0].value}")
            else:
                for fetcher in fetchers_list:
                    mic = fetcher.mic
                    results[mic] = self.update_exchange(mic, dry_run, force)
        
        return results
    
    def print_summary(self, results: Dict[str, Tuple[FetchStatus, Optional[str]]]):
        """Print update summary"""
        logger.info(f"\n{'='*60}")
        logger.info("UPDATE SUMMARY")
        logger.info(f"{'='*60}")
        
        status_counts = {}
        for mic, (status, _) in results.items():
            status_counts[status] = status_counts.get(status, 0) + 1
        
        for status in FetchStatus:
            count = status_counts.get(status, 0)
            if count > 0:
                logger.info(f"  {status.value}: {count}")
        
        logger.info(f"\n{'='*60}")
        logger.info("DETAILS")
        logger.info(f"{'='*60}")
        
        for mic, (status, message) in sorted(results.items()):
            if message:
                logger.info(f"  {mic}: {message}")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.registry_dir / "logs" / f"update_{timestamp}.json"
        results_file.parent.mkdir(exist_ok=True)
        
        serializable_results = {
            mic: {
                "status": status.value,
                "message": message
            }
            for mic, (status, message) in results.items()
        }
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        logger.info(f"\nResults saved to {results_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Update exchange calendar registry from official sources",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available fetchers
  %(prog)s --list-fetchers
  
  # Update a specific exchange (dry run)
  %(prog)s --exchange XNYS --dry-run
  
  # Update all exchanges
  %(prog)s --all
  
  # Force update (bypass cache)
  %(prog)s --exchange XNYS --force
  
  # Update with concurrency
  %(prog)s --all --workers 8
        """
    )
    
    parser.add_argument(
        '--exchange', '-e',
        help='Update a specific exchange (MIC code)'
    )
    parser.add_argument(
        '--all', '-a',
        help='Update all exchanges with available fetchers',
        action='store_true'
    )
    parser.add_argument(
        '--dry-run', '-d',
        help='Show what would be updated without writing files',
        action='store_true'
    )
    parser.add_argument(
        '--force', '-f',
        help='Force update (bypass cache)',
        action='store_true'
    )
    parser.add_argument(
        '--list-fetchers', '-l',
        help='List available exchange fetchers',
        action='store_true'
    )
    parser.add_argument(
        '--registry-dir',
        help='Path to registry directory',
        default='.'
    )
    parser.add_argument(
        '--workers', '-w',
        help='Number of concurrent workers',
        type=int,
        default=4
    )
    parser.add_argument(
        '--no-cache',
        help='Disable caching',
        action='store_true'
    )
    parser.add_argument(
        '--verbose', '-v',
        help='Verbose output',
        action='store_true'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Validate registry directory
    registry_dir = Path(args.registry_dir)
    if not registry_dir.exists():
        logger.error(f"Registry directory not found: {registry_dir}")
        sys.exit(1)
    
    # Create updater
    updater = RegistryUpdater(
        registry_dir,
        use_cache=not args.no_cache
    )
    
    # Handle commands
    if args.list_fetchers:
        logger.info("Available fetchers:")
        for mic in updater.fetchers.list_available():
            fetcher = updater.fetchers.get(mic)
            logger.info(f"  {mic}: {fetcher.name}")
        sys.exit(0)
    
    if args.exchange:
        mic = args.exchange.upper()
        status, message = updater.update_exchange(mic, args.dry_run, args.force)
        if status in [FetchStatus.FAILED, FetchStatus.VALIDATION_ERROR]:
            sys.exit(1)
    elif args.all:
        results = updater.update_all(
            args.dry_run,
            args.force,
            args.workers
        )
        updater.print_summary(results)
        
        # Check for failures
        failures = sum(
            1 for status, _ in results.values()
            if status in [FetchStatus.FAILED, FetchStatus.VALIDATION_ERROR]
        )
        if failures > 0:
            logger.warning(f"{failures} exchanges failed to update")
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()