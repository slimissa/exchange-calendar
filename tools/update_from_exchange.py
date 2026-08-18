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

# Try imports with fallbacks
try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

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
        source = self.registry_dir / "exchanges" / f"{mic.lower()}.json"
        if not source.exists():
            return None
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = self.backup_dir / f"{mic.lower()}_{timestamp}.json"
        shutil.copy2(source, backup)
        return backup
    
    def rollback(self, mic: str, backup_file: str):
        """Rollback to a backup"""
        source = self.backup_dir / backup_file
        target = self.registry_dir / "exchanges" / f"{mic.lower()}.json"
        if source.exists():
            shutil.copy2(source, target)
            logger.info(f"Rolled back {mic} to {backup_file}")
        else:
            logger.error(f"Backup file not found: {backup_file}")
    
    def list_backups(self, mic: str) -> List[str]:
        """List available backups for an exchange"""
        pattern = f"{mic.lower()}_*.json"
        backups = list(self.backup_dir.glob(pattern))
        return sorted([b.name for b in backups])


class ExchangeFetcher(ABC):
    """Abstract base class for exchange data fetchers"""
    
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
    
    @abstractmethod
    def parse_html(self, html: str) -> List[HolidayEntry]:
        """Parse HTML content into holiday entries"""
        pass
    
    @abstractmethod
    def fetch(self) -> Optional[ExchangeData]:
        """Fetch and parse exchange data"""
        pass
    
    def _make_request(self) -> Optional[str]:
        """Make HTTP request with rate limiting"""
        import requests
        
        self.rate_limiter.wait_if_needed(self.mic)
        
        try:
            response = requests.get(
                self.source_url,
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (compatible; ExchangeCalendarRegistry/1.0)'
                }
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


class NYSEFetcher(ExchangeFetcher):
    """Fetcher for NYSE holidays"""
    
    def __init__(self):
        super().__init__(
            mic="XNYS",
            name="New York Stock Exchange",
            source_url="https://www.nyse.com/markets/hours-calendars",
            rate_limit=2.0
        )
    
    def parse_html(self, html: str) -> List[HolidayEntry]:
        """Parse NYSE holiday calendar HTML (transposed table format)"""
        if not HAS_BS4:
            raise ParseError("BeautifulSoup not available")
        
        soup = BeautifulSoup(html, 'html.parser')
        holidays = []
        
        # Find holiday table
        tables = soup.find_all('table')
        holiday_table = None
        
        for table in tables:
            headers = [th.text.strip() for th in table.find_all('th')]
            if headers and 'Holiday' in headers[0]:
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
        year_headers = [th.text.strip() for th in header_row.find_all('th')]
        
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


class ExchangeFetcherRegistry:
    """Registry of available exchange fetchers"""
    
    def __init__(self):
        self.fetchers: Dict[str, ExchangeFetcher] = {}
        self._register_default_fetchers()
    
    def _register_default_fetchers(self):
        """Register default fetchers"""
        self.register(NYSEFetcher())
        # Add more fetchers as they're implemented
    
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
        exchange_file = self.exchanges_dir / f"{mic.lower()}.json"
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
        removed = current_holidays - fetched_holidays
        
        changes = []
        if added:
            changes.append(f"Added {len(added)} holidays: {', '.join(sorted(added))}")
        if removed:
            changes.append(f"Removed {len(removed)} holidays: {', '.join(sorted(removed))}")
        
        return bool(changes), changes
    
    def generate_exchange_json(self, data: ExchangeData) -> Dict[str, Any]:
        """Generate exchange JSON in registry format"""
        holidays_explicit = [h.to_dict() for h in data.holidays]
        
        exchange_json = {
            "code": data.code,
            "name": data.name,
            "mic": data.mic,
            "timezone": data.timezone,
            "regular_hours": {
                "open": data.regular_open,
                "close": data.regular_close
            },
            "extended_hours": {},
            "sessions": [],
            "holidays": {
                "explicit": holidays_explicit,
                "recurrence_rules": []
            },
            "ad_hoc_closures": [],
            "generation_range": [
                datetime.now().strftime("%Y-01-01"),
                (datetime.now() + timedelta(days=365*5)).strftime("%Y-12-31")
            ]
        }
        
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
                
                # Write new data
                exchange_json = self.generate_exchange_json(fetched_data)
                output_file = self.exchanges_dir / f"{mic.lower()}.json"
                
                try:
                    with open(output_file, 'w') as f:
                        json.dump(exchange_json, f, indent=2)
                        f.write('\n')
                    logger.info(f"Wrote {output_file}")
                except IOError as e:
                    logger.error(f"Failed to write {output_file}: {e}")
                    return FetchStatus.FAILED, str(e)
            else:
                logger.info(f"[DRY RUN] Would write {mic.lower()}.json")
        
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