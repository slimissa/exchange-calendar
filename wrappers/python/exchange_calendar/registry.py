#!/usr/bin/env python3
"""
registry.py — CalendarRegistry class for loading the exchange calendar registry.

This class is the entry point for consuming the registry. It loads the
single-file distribution artifact (calendar.json) produced by tools/build.py
and provides access to individual exchanges by MIC code.

Usage:
    from exchange_calendar import CalendarRegistry

    registry = CalendarRegistry("calendar.json")
    xnys = registry.exchange("XNYS")

    if xnys.is_open("2025-07-03", "10:00"):
        print("NYSE is open")

    for exchange in registry.list_exchanges():
        print(exchange)

    print(f"Total exchanges: {registry.exchange_count}")
"""

import json
from pathlib import Path
from typing import List, Optional

from .exchange import Exchange


class CalendarRegistry:
    """
    A loaded exchange calendar registry.

    The registry is immutable after construction. It provides:
        - Lookup of exchanges by MIC code
        - Listing of all available exchanges
        - Registry metadata (version, exchange count)

    Attributes:
        version (str): Registry version (from meta.version)
        exchange_count (int): Number of exchanges in the registry
        exchanges (dict): Mapping of MIC code -> Exchange
    """

    def __init__(self, registry_path: str = "calendar.json"):
        """
        Load and parse the registry from a JSON file.

        Args:
            registry_path: Path to the calendar.json file.
                           Can be a string or pathlib.Path.

        Raises:
            FileNotFoundError: If the file does not exist.
            json.JSONDecodeError: If the file is not valid JSON.
            ValueError: If the JSON structure is invalid.
        """
        path = Path(registry_path)

        if not path.exists():
            raise FileNotFoundError(f"Registry file not found: {path}")

        with open(path) as f:
            data = json.load(f)

        self._validate_registry(data)

        meta = data.get("meta", {})
        self.version = meta.get("version", "unknown")
        self.exchange_count = meta.get("exchange_count", 0)

        self.exchanges = {}
        for exchange_data in data.get("exchanges", []):
            exchange = Exchange(exchange_data)
            self.exchanges[exchange.code] = exchange

    # ──────────────────────────────────────────────────────────
    # Data validation
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _validate_registry(data: dict) -> None:
        """
        Validate the top-level registry structure.

        Raises:
            ValueError: If required fields are missing or malformed.
        """
        if not isinstance(data, dict):
            raise ValueError(f"Registry must be a JSON object, got {type(data).__name__}")

        if "meta" not in data:
            raise ValueError("Registry missing 'meta' field")

        if "exchanges" not in data:
            raise ValueError("Registry missing 'exchanges' field")

        if not isinstance(data["exchanges"], list):
            raise ValueError(f"'exchanges' must be a list, got {type(data['exchanges']).__name__}")

        # Check for duplicate codes in the registry
        codes = [e.get("code") for e in data["exchanges"] if "code" in e]
        if len(codes) != len(set(codes)):
            duplicates = [c for c in codes if codes.count(c) > 1]
            raise ValueError(f"Duplicate exchange codes in registry: {set(duplicates)}")

    # ──────────────────────────────────────────────────────────
    # Public API — lookup
    # ──────────────────────────────────────────────────────────

    def exchange(self, code: str) -> Optional[Exchange]:
        """
        Return the Exchange with the given MIC code.

        Args:
            code: The MIC code (e.g., "XNYS", "XLON").
                  Case-insensitive — "xnys" works too.

        Returns:
            Optional[Exchange]: The Exchange, or None if not found.

        Example:
            registry.exchange("XNYS")  # -> Exchange
            registry.exchange("xnys")  # -> Exchange (case-insensitive)
            registry.exchange("XXXX")  # -> None
        """
        if not isinstance(code, str):
            raise TypeError(f"Expected str, got {type(code).__name__}")

        normalized = code.upper()
        return self.exchanges.get(normalized)

    def get(self, code: str) -> Exchange:
        """
        Return the Exchange with the given MIC code, raising if not found.

        Unlike exchange(), this method raises KeyError instead of
        returning None when the exchange is not found. Use this when
        you expect the exchange to exist and want a clear error.

        Args:
            code: The MIC code (case-insensitive).

        Returns:
            Exchange: The requested exchange.

        Raises:
            KeyError: If the exchange is not found.
        """
        exchange = self.exchange(code)
        if exchange is None:
            raise KeyError(f"Exchange not found: '{code}'. Available: {self.codes()}")
        return exchange

    # ──────────────────────────────────────────────────────────
    # Public API — listing
    # ──────────────────────────────────────────────────────────

    def list_exchanges(self) -> List[Exchange]:
        """
        Return all exchanges, sorted by MIC code.

        Returns:
            List[Exchange]: Sorted list of Exchange objects.
        """
        return [self.exchanges[code] for code in sorted(self.exchanges)]

    def codes(self) -> List[str]:
        """
        Return all MIC codes, sorted alphabetically.

        Returns:
            List[str]: Sorted list of MIC codes.
        """
        return sorted(self.exchanges.keys())

    def names(self) -> List[str]:
        """
        Return all exchange names, sorted by MIC code.

        Returns:
            List[str]: List of exchange names.
        """
        return [self.exchanges[code].name for code in sorted(self.exchanges)]

    # ──────────────────────────────────────────────────────────
    # Public API — convenience
    # ──────────────────────────────────────────────────────────

    def is_exchange(self, code: str) -> bool:
        """
        Return True if the given MIC code exists in the registry.

        Args:
            code: The MIC code (case-insensitive).

        Returns:
            bool: True if the exchange exists.
        """
        return self.exchange(code) is not None

    def to_dict(self) -> dict:
        """
        Return the registry as a dict with summary information.

        Returns:
            dict: {"version": str, "exchange_count": int, "codes": [str, ...]}
        """
        return {
            "version": self.version,
            "exchange_count": self.exchange_count,
            "codes": self.codes(),
        }

    # ──────────────────────────────────────────────────────────
    # Dunder methods
    # ──────────────────────────────────────────────────────────

    def __len__(self) -> int:
        """Return the number of exchanges in the registry."""
        return len(self.exchanges)

    def __contains__(self, code: str) -> bool:
        """Support 'XNYS' in registry syntax."""
        return self.is_exchange(code)

    def __iter__(self):
        """Iterate over exchanges sorted by code."""
        return iter(self.list_exchanges())

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return f"CalendarRegistry(version='{self.version}', exchanges={len(self.exchanges)})"

    def __str__(self) -> str:
        """Return a human-readable representation."""
        return f"Exchange Calendar Registry v{self.version} ({len(self.exchanges)} exchanges)"