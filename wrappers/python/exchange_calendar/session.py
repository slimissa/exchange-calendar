#!/usr/bin/env python3
"""
session.py — SessionStatus enum for exchange calendar states.

Defines the possible states of an exchange at any given moment.
The enum is used by the Exchange class to report whether the market
is open, closed, in pre-market, after-hours, or in an early close.

This is the canonical status vocabulary for the entire QuantOS ecosystem.
All language wrappers must map to the same semantic states.
"""

from enum import Enum


class SessionStatus(Enum):
    """
    The operational status of an exchange at a point in time.

    Values:
        CLOSED:       Market is closed (weekend, holiday, or outside all hours)
        PRE_MARKET:   Before regular trading hours (extended session)
        OPEN:         Regular trading hours
        EARLY_CLOSE:  Early close day, before the early close time
        AFTER_HOURS:  After regular trading hours (extended session)
        LUNCH_BREAK:  Intraday break (exchanges with lunch pauses, e.g. TSE)
    """

    CLOSED = "closed"
    PRE_MARKET = "pre_market"
    OPEN = "open"
    EARLY_CLOSE = "early_close"
    AFTER_HOURS = "after_hours"
    LUNCH_BREAK = "lunch_break"

    @classmethod
    def from_string(cls, value: str) -> "SessionStatus":
        """
        Convert a string to a SessionStatus enum value.

        Accepts case-insensitive input. Raises ValueError on unknown input.

        Examples:
            SessionStatus.from_string("open") -> SessionStatus.OPEN
            SessionStatus.from_string("CLOSED") -> SessionStatus.CLOSED
            SessionStatus.from_string("early_close") -> SessionStatus.EARLY_CLOSE

        Raises:
            ValueError: If the input string does not match any known status.
        """
        if not isinstance(value, str):
            raise TypeError(f"Expected str, got {type(value).__name__}")

        normalized = value.strip().lower()

        for status in cls:
            if normalized == status.value:
                return status

        valid = ", ".join(s.value for s in cls)
        raise ValueError(f"Unknown session status: '{value}'. Valid values: {valid}")

    @classmethod
    def is_trading_status(cls, status: "SessionStatus") -> bool:
        """
        Return True if the given status represents a state where trading
        is currently possible (regular hours or early close before the close time).

        Examples:
            SessionStatus.is_trading_status(SessionStatus.OPEN) -> True
            SessionStatus.is_trading_status(SessionStatus.EARLY_CLOSE) -> True
            SessionStatus.is_trading_status(SessionStatus.CLOSED) -> False
            SessionStatus.is_trading_status(SessionStatus.PRE_MARKET) -> False
        """
        return status in (SessionStatus.OPEN, SessionStatus.EARLY_CLOSE)

    def __str__(self) -> str:
        """Return the string value of the status."""
        return self.value

    def __repr__(self) -> str:
        """Return an unambiguous representation."""
        return f"SessionStatus.{self.name}"