#!/usr/bin/env python3
"""
exchange_calendar — Python wrapper for the QuantOS exchange-calendar registry.

This package provides a clean, idiomatic Python API for loading and querying
the exchange calendar registry. It is designed to be the reference
implementation that other language wrappers follow.

Usage:
    from exchange_calendar import CalendarRegistry

    registry = CalendarRegistry("calendar.json")
    xnys = registry.exchange("XNYS")

    if xnys.is_open("2025-07-03", "10:00"):
        print("NYSE is open")

    if xnys.is_early_close("2025-07-03"):
        print(f"Early close at {xnys.early_close_time('2025-07-03')}")

Version: 1.0.0
License: Apache 2.0
"""

from .session import SessionStatus
from .exchange import Exchange
from .registry import CalendarRegistry

__version__ = "1.0.0"
__all__ = [
    "SessionStatus",
    "Exchange",
    "CalendarRegistry",
]