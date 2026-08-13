#!/usr/bin/env python3
"""
exchange.py — Exchange class for querying a single exchange calendar.

This is the core class in the Python wrapper. It represents one exchange
and answers questions like:
    - Is the market open right now?
    - Is this date a holiday?
    - Is this date an early close?
    - What time does the market close today?
    - What is the next trading day?

The class is immutable after construction. All date/time arguments use
ISO 8601 date strings (YYYY-MM-DD) and 24-hour time strings (HH:MM).

Example:
    xnys = Exchange(exchange_dict)
    xnys.is_open("2025-07-03", "10:00")          # True (open before early close)
    xnys.is_open("2025-07-03", "13:30")          # False (after early close)
    xnys.is_holiday("2025-07-04")                # True
    xnys.early_close_time("2025-07-03")          # "13:00"
    xnys.next_trading_day("2025-07-03")          # "2025-07-07" (Monday after July 4)
"""

from datetime import date, time, timedelta
from typing import Optional

from .session import SessionStatus


class Exchange:
    """
    Represents a single exchange calendar.

    Attributes:
        code (str): The MIC code (e.g., "XNYS")
        name (str): Full exchange name (e.g., "New York Stock Exchange")
        mic (str): ISO 10383 MIC, equal to code
        timezone (str): IANA timezone (e.g., "America/New_York")
        regular_hours (dict): {"open": "09:30", "close": "16:00"}
    """

    def __init__(self, data: dict):
        """
        Initialize from an exchange dict (as found in calendar.json).

        Args:
            data: A dict with code, name, mic, timezone, regular_hours,
                  holidays (explicit + generated), and generation_range.

        Raises:
            ValueError: If required fields are missing or malformed.
        """
        self._validate_data(data)

        self.code = data["code"]
        self.name = data["name"]
        self.mic = data["mic"]
        self.timezone = data["timezone"]
        self.regular_hours = data["regular_hours"]
        self.extended_hours = data.get("extended_hours", {})
        self.sessions = data.get("sessions", [])

        holidays = data.get("holidays", {})
        self._explicit = holidays.get("explicit", [])
        self._generated = holidays.get("generated", [])

        # Build lookup dicts for O(1) date queries
        self._holiday_by_date = {}
        self._status_by_date = {}
        self._early_close_time_by_date = {}

        for entry in self._explicit:
            self._index_entry(entry)

        for entry in self._generated:
            self._index_entry(entry)

    # ──────────────────────────────────────────────────────────
    # Data validation
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _validate_data(data: dict) -> None:
        """Validate required fields exist and are well-formed."""
        required = ["code", "name", "mic", "timezone", "regular_hours"]
        for field in required:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        if "open" not in data["regular_hours"] or "close" not in data["regular_hours"]:
            raise ValueError("regular_hours must have 'open' and 'close'")

        # Validate time formats
        for time_str in [data["regular_hours"]["open"], data["regular_hours"]["close"]]:
            Exchange._validate_time_format(time_str)

        if data["code"] != data["mic"]:
            raise ValueError(f"code '{data['code']}' must equal mic '{data['mic']}'")

    @staticmethod
    def _validate_time_format(time_str: str) -> None:
        """Validate HH:MM format."""
        try:
            hours, minutes = time_str.split(":")
            if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
                raise ValueError()
        except (ValueError, AttributeError):
            raise ValueError(f"Invalid time format: '{time_str}'. Expected HH:MM.")

    @staticmethod
    def _validate_date_format(date_str: str) -> None:
        """Validate YYYY-MM-DD format."""
        try:
            date.fromisoformat(date_str)
        except ValueError:
            raise ValueError(f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD.")

    # ──────────────────────────────────────────────────────────
    # Internal indexing
    # ──────────────────────────────────────────────────────────

    def _index_entry(self, entry: dict) -> None:
        """Index a holiday entry for fast lookup."""
        date_str = entry["date"]
        status = entry.get("status", "closed")

        self._holiday_by_date[date_str] = entry
        self._status_by_date[date_str] = status

        if status == "early_close" and "early_close_time" in entry:
            self._early_close_time_by_date[date_str] = entry["early_close_time"]

    # ──────────────────────────────────────────────────────────
    # Date helpers
    # ──────────────────────────────────────────────────────────

    def _is_weekend(self, date_str: str) -> bool:
        """Return True if the date is Saturday or Sunday."""
        self._validate_date_format(date_str)
        d = date.fromisoformat(date_str)
        return d.weekday() >= 5  # 5=Saturday, 6=Sunday

    def _is_holiday(self, date_str: str) -> bool:
        """Return True if the date is a full market closure."""
        self._validate_date_format(date_str)
        return self._status_by_date.get(date_str) == "closed"

    def _is_early_close_day(self, date_str: str) -> bool:
        """Return True if the date has an early close."""
        self._validate_date_format(date_str)
        return date_str in self._early_close_time_by_date

    # ──────────────────────────────────────────────────────────
    # Public API — status queries
    # ──────────────────────────────────────────────────────────

    def is_holiday(self, date_str: str) -> bool:
        """
        Return True if the market is fully closed on this date.

        Includes weekends and explicit/generated holidays.

        Args:
            date_str: ISO date (YYYY-MM-DD)

        Returns:
            bool: True if market is closed all day.
        """
        if self._is_weekend(date_str):
            return True
        return self._is_holiday(date_str)

    def is_early_close(self, date_str: str) -> bool:
        """
        Return True if this date has an early close.

        Args:
            date_str: ISO date (YYYY-MM-DD)

        Returns:
            bool: True if market closes early on this date.
        """
        return self._is_early_close_day(date_str)

    def early_close_time(self, date_str: str) -> Optional[str]:
        """
        Return the early close time for this date, or None if not an early close.

        Args:
            date_str: ISO date (YYYY-MM-DD)

        Returns:
            Optional[str]: Early close time as HH:MM, or None.
        """
        return self._early_close_time_by_date.get(date_str)

    def status_at(self, date_str: str, time_str: str) -> SessionStatus:
        """
        Return the full session status at a specific date and time.

        This is the most comprehensive status query. It checks:
            1. Weekend → CLOSED
            2. Holiday → CLOSED
            3. Early close day and time >= early_close_time → CLOSED
            4. Lunch break (if configured) → LUNCH_BREAK
            5. Before regular open → PRE_MARKET
            6. After regular close → AFTER_HOURS
            7. Otherwise → OPEN (or EARLY_CLOSE if before early close on early close day)

        Args:
            date_str: ISO date (YYYY-MM-DD)
            time_str: 24-hour time (HH:MM)

        Returns:
            SessionStatus: The status at the given moment.
        """
        self._validate_date_format(date_str)
        self._validate_time_format(time_str)

        # 1. Weekend
        if self._is_weekend(date_str):
            return SessionStatus.CLOSED

        # 2. Full holiday
        if self._is_holiday(date_str):
            return SessionStatus.CLOSED

        # 3. Early close day — check if past the early close time
        if self._is_early_close_day(date_str):
            close_time = self._early_close_time_by_date[date_str]
            if time_str >= close_time:
                return SessionStatus.CLOSED
            # Before early close — still trading
            # Fall through to check lunch breaks and regular hours

        # 4. Lunch break (if configured for this exchange)
        for session in self.sessions:
            if session.get("type") == "lunch_break":
                break_open = session.get("open")
                break_close = session.get("close")
                if break_open and break_close and break_open <= time_str < break_close:
                    return SessionStatus.LUNCH_BREAK

        # 5. Before regular open
        if time_str < self.regular_hours["open"]:
            return SessionStatus.PRE_MARKET

        # 6. After regular close
        if time_str >= self.regular_hours["close"]:
            return SessionStatus.AFTER_HOURS

        # 7. Within regular hours
        if self._is_early_close_day(date_str):
            return SessionStatus.EARLY_CLOSE
        return SessionStatus.OPEN

    def is_open(self, date_str: str, time_str: str = "10:00") -> bool:
        """
        Return True if the market is open for trading at the given moment.

        Convenience wrapper around status_at(). Returns True only for
        SessionStatus.OPEN and SessionStatus.EARLY_CLOSE (before close time).

        Args:
            date_str: ISO date (YYYY-MM-DD)
            time_str: 24-hour time (HH:MM), defaults to "10:00"

        Returns:
            bool: True if market is open for trading.
        """
        status = self.status_at(date_str, time_str)
        return SessionStatus.is_trading_status(status)

    # ──────────────────────────────────────────────────────────
    # Public API — date navigation
    # ──────────────────────────────────────────────────────────

    def next_trading_day(self, date_str: str) -> str:
        """
        Return the next trading day after the given date.

        Skips weekends, holidays, and any day where the market is fully closed.
        Early close days are considered trading days.

        Args:
            date_str: ISO date (YYYY-MM-DD)

        Returns:
            str: ISO date of the next trading day.
        """
        self._validate_date_format(date_str)
        d = date.fromisoformat(date_str) + timedelta(days=1)

        # Search up to 30 days ahead (sufficient for any holiday stretch)
        for _ in range(30):
            date_str = d.isoformat()
            if not self.is_holiday(date_str):
                return date_str
            d += timedelta(days=1)

        raise ValueError(f"No trading day found within 30 days after {date_str}")

    def previous_trading_day(self, date_str: str) -> str:
        """
        Return the previous trading day before the given date.

        Skips weekends, holidays, and any day where the market is fully closed.
        Early close days are considered trading days.

        Args:
            date_str: ISO date (YYYY-MM-DD)

        Returns:
            str: ISO date of the previous trading day.
        """
        self._validate_date_format(date_str)
        d = date.fromisoformat(date_str) - timedelta(days=1)

        # Search up to 30 days back (sufficient for any holiday stretch)
        for _ in range(30):
            date_str = d.isoformat()
            if not self.is_holiday(date_str):
                return date_str
            d -= timedelta(days=1)

        raise ValueError(f"No trading day found within 30 days before {date_str}")

    # ──────────────────────────────────────────────────────────
    # Public API — metadata
    # ──────────────────────────────────────────────────────────

    def holiday_count(self, year: int = None) -> int:
        """
        Return the number of explicit holidays in the registry.

        Args:
            year: Optional year filter (int). If provided, only counts
                  holidays in that year.

        Returns:
            int: Number of holidays.
        """
        if year is None:
            return len(self._holiday_by_date)

        prefix = f"{year}-"
        return sum(1 for d in self._holiday_by_date if d.startswith(prefix))

    def list_holidays(self, year: int = None) -> list:
        """
        Return a list of holiday entries, sorted by date.

        Args:
            year: Optional year filter (int).

        Returns:
            list: List of holiday dicts with date, name, status.
        """
        entries = list(self._holiday_by_date.values())
        if year is not None:
            prefix = f"{year}-"
            entries = [e for e in entries if e["date"].startswith(prefix)]
        entries.sort(key=lambda e: e["date"])
        return entries

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return f"Exchange(code='{self.code}', name='{self.name}')"

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return f"{self.name} ({self.code})"