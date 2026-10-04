#!/usr/bin/env python3
"""
exchange_calendar — Python wrapper for the QuantOS exchange-calendar registry.

Usage:
    from exchange_calendar import CalendarRegistry

    registry = CalendarRegistry("calendar.json")
    for s in registry.sessions("XNYS"):
        print(s.type, s.open, s.close)

Version: 2.11.0
License: Apache 2.0
"""

from .session import SessionStatus
from .exchange import Exchange
from .registry import CalendarRegistry

# v2.11.0: Session dataclass, if defined in registry.py.
try:
    from .registry import Session  # type: ignore
except ImportError:
    Session = None  # type: ignore

__version__ = "2.11.0"
__all__ = [
    "SessionStatus",
    "Exchange",
    "CalendarRegistry",
] + (["Session"] if Session is not None else [])
