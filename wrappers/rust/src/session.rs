use std::fmt;
use std::str::FromStr;

/// Represents the operational state of an exchange at a point in time.
///
/// This is the canonical status vocabulary for the entire QuantOS ecosystem.
/// All language wrappers must map to the same semantic states.
///
/// # Examples
///
/// ```
/// use exchange_calendar::SessionStatus;
///
/// let status = SessionStatus::Open;
/// assert_eq!(status.as_str(), "open");
/// assert!(status.is_trading());
///
/// let parsed = "EARLY_CLOSE".parse::<SessionStatus>().unwrap();
/// assert_eq!(parsed, SessionStatus::EarlyClose);
/// ```
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum SessionStatus {
    /// Market is closed (weekend, holiday, or outside all hours).
    Closed,

    /// Pre-market trading (before regular hours).
    PreMarket,

    /// Regular trading hours.
    Open,

    /// Early close day, before the early close time.
    EarlyClose,

    /// After-hours trading (after regular hours).
    AfterHours,

    /// Intraday break (exchanges with lunch pauses).
    LunchBreak,
}

impl SessionStatus {
    /// Return the string representation used in the registry JSON.
    ///
    /// # Examples
    ///
    /// ```
    /// use exchange_calendar::SessionStatus;
    ///
    /// assert_eq!(SessionStatus::Open.as_str(), "open");
    /// assert_eq!(SessionStatus::Closed.as_str(), "closed");
    /// assert_eq!(SessionStatus::EarlyClose.as_str(), "early_close");
    /// ```
    #[inline]
    pub const fn as_str(&self) -> &'static str {
        match self {
            SessionStatus::Closed => "closed",
            SessionStatus::PreMarket => "pre_market",
            SessionStatus::Open => "open",
            SessionStatus::EarlyClose => "early_close",
            SessionStatus::AfterHours => "after_hours",
            SessionStatus::LunchBreak => "lunch_break",
        }
    }

    /// Return true if this status represents a state where trading
    /// is currently possible (regular hours or early close before close).
    ///
    /// # Examples
    ///
    /// ```
    /// use exchange_calendar::SessionStatus;
    ///
    /// assert!(SessionStatus::Open.is_trading());
    /// assert!(SessionStatus::EarlyClose.is_trading());
    /// assert!(!SessionStatus::Closed.is_trading());
    /// assert!(!SessionStatus::PreMarket.is_trading());
    /// assert!(!SessionStatus::AfterHours.is_trading());
    /// assert!(!SessionStatus::LunchBreak.is_trading());
    /// ```
    #[inline]
    pub const fn is_trading(&self) -> bool {
        matches!(self, SessionStatus::Open | SessionStatus::EarlyClose)
    }

    /// Return true if this status represents a non-trading state.
    ///
    /// # Examples
    ///
    /// ```
    /// use exchange_calendar::SessionStatus;
    ///
    /// assert!(SessionStatus::Closed.is_non_trading());
    /// assert!(!SessionStatus::Open.is_non_trading());
    /// ```
    #[inline]
    pub const fn is_non_trading(&self) -> bool {
        !self.is_trading()
    }

    /// Return all six statuses in a stable order.
    ///
    /// # Examples
    ///
    /// ```
    /// use exchange_calendar::SessionStatus;
    ///
    /// let all = SessionStatus::all();
    /// assert_eq!(all.len(), 6);
    /// assert_eq!(all[0], SessionStatus::Closed);
    /// assert_eq!(all[1], SessionStatus::PreMarket);
    /// ```
    pub const fn all() -> [SessionStatus; 6] {
        [
            SessionStatus::Closed,
            SessionStatus::PreMarket,
            SessionStatus::Open,
            SessionStatus::EarlyClose,
            SessionStatus::AfterHours,
            SessionStatus::LunchBreak,
        ]
    }

    /// Return only statuses where trading is possible.
    ///
    /// # Examples
    ///
    /// ```
    /// use exchange_calendar::SessionStatus;
    ///
    /// let trading = SessionStatus::trading_statuses();
    /// assert_eq!(trading.len(), 2);
    /// assert_eq!(trading[0], SessionStatus::Open);
    /// assert_eq!(trading[1], SessionStatus::EarlyClose);
    /// ```
    pub const fn trading_statuses() -> [SessionStatus; 2] {
        [SessionStatus::Open, SessionStatus::EarlyClose]
    }

    /// Return only statuses where trading is not possible.
    ///
    /// # Examples
    ///
    /// ```
    /// use exchange_calendar::SessionStatus;
    ///
    /// let non_trading = SessionStatus::non_trading_statuses();
    /// assert_eq!(non_trading.len(), 4);
    /// ```
    pub const fn non_trading_statuses() -> [SessionStatus; 4] {
        [
            SessionStatus::Closed,
            SessionStatus::PreMarket,
            SessionStatus::AfterHours,
            SessionStatus::LunchBreak,
        ]
    }

    /// Parse from a string, case-insensitive and trimming surrounding whitespace.
    ///
    /// Returns `Ok(SessionStatus)` on success, `Err(ParseSessionStatusError)` on failure.
    ///
    /// # Examples
    ///
    /// ```
    /// use exchange_calendar::SessionStatus;
    ///
    /// assert_eq!(
    ///     SessionStatus::parse("open").unwrap(),
    ///     SessionStatus::Open
    /// );
    /// assert_eq!(
    ///     SessionStatus::parse(" OPEN ").unwrap(),
    ///     SessionStatus::Open
    /// );
    /// assert_eq!(
    ///     SessionStatus::parse("Early_Close").unwrap(),
    ///     SessionStatus::EarlyClose
    /// );
    /// assert!(SessionStatus::parse("bogus").is_err());
    /// ```
    pub fn parse(s: &str) -> Result<Self, ParseSessionStatusError> {
        s.parse()
    }

    /// Parse from a string, panicking on failure.
    ///
    /// Use only with known-valid input.
    ///
    /// # Panics
    ///
    /// Panics if the string is not a valid status.
    ///
    /// # Examples
    ///
    /// ```
    /// use exchange_calendar::SessionStatus;
    ///
    /// let status = SessionStatus::must_parse("open");
    /// assert_eq!(status, SessionStatus::Open);
    /// ```
    #[track_caller]
    pub fn must_parse(s: &str) -> Self {
        s.parse()
            .unwrap_or_else(|e| panic!("invalid session status: {}", e))
    }
}

impl fmt::Display for SessionStatus {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.write_str(self.as_str())
    }
}

impl FromStr for SessionStatus {
    type Err = ParseSessionStatusError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let normalized = s.trim().to_lowercase();

        match normalized.as_str() {
            "closed" => Ok(SessionStatus::Closed),
            "pre_market" => Ok(SessionStatus::PreMarket),
            "open" => Ok(SessionStatus::Open),
            "early_close" => Ok(SessionStatus::EarlyClose),
            "after_hours" => Ok(SessionStatus::AfterHours),
            "lunch_break" => Ok(SessionStatus::LunchBreak),
            _ => Err(ParseSessionStatusError {
                input: s.to_string(),
            }),
        }
    }
}

impl From<SessionStatus> for String {
    fn from(status: SessionStatus) -> Self {
        status.as_str().to_string()
    }
}

impl From<&SessionStatus> for String {
    fn from(status: &SessionStatus) -> Self {
        status.as_str().to_string()
    }
}

impl AsRef<str> for SessionStatus {
    fn as_ref(&self) -> &str {
        self.as_str()
    }
}

/// Error returned when parsing a string into a `SessionStatus` fails.
///
/// # Examples
///
/// ```
/// use exchange_calendar::SessionStatus;
///
/// let result = "bogus".parse::<SessionStatus>();
/// assert!(result.is_err());
///
/// let err = result.unwrap_err();
/// println!("{}", err); // "unknown session status: 'bogus'"
/// ```
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct ParseSessionStatusError {
    input: String,
}

impl fmt::Display for ParseSessionStatusError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "unknown session status: '{}' (valid: closed, pre_market, open, early_close, after_hours, lunch_break)",
            self.input
        )
    }
}

impl std::error::Error for ParseSessionStatusError {}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_as_str() {
        assert_eq!(SessionStatus::Closed.as_str(), "closed");
        assert_eq!(SessionStatus::PreMarket.as_str(), "pre_market");
        assert_eq!(SessionStatus::Open.as_str(), "open");
        assert_eq!(SessionStatus::EarlyClose.as_str(), "early_close");
        assert_eq!(SessionStatus::AfterHours.as_str(), "after_hours");
        assert_eq!(SessionStatus::LunchBreak.as_str(), "lunch_break");
    }

    #[test]
    fn test_is_trading() {
        assert!(SessionStatus::Open.is_trading());
        assert!(SessionStatus::EarlyClose.is_trading());
        assert!(!SessionStatus::Closed.is_trading());
        assert!(!SessionStatus::PreMarket.is_trading());
        assert!(!SessionStatus::AfterHours.is_trading());
        assert!(!SessionStatus::LunchBreak.is_trading());
    }

    #[test]
    fn test_is_non_trading() {
        assert!(!SessionStatus::Open.is_non_trading());
        assert!(SessionStatus::Closed.is_non_trading());
    }

    #[test]
    fn test_all() {
        let all = SessionStatus::all();
        assert_eq!(all.len(), 6);
        assert_eq!(all[0], SessionStatus::Closed);
        assert_eq!(all[5], SessionStatus::LunchBreak);
    }

    #[test]
    fn test_trading_statuses() {
        let trading = SessionStatus::trading_statuses();
        assert_eq!(trading.len(), 2);
        assert_eq!(trading[0], SessionStatus::Open);
        assert_eq!(trading[1], SessionStatus::EarlyClose);
    }

    #[test]
    fn test_non_trading_statuses() {
        let non_trading = SessionStatus::non_trading_statuses();
        assert_eq!(non_trading.len(), 4);
        assert!(non_trading.contains(&SessionStatus::Closed));
        assert!(non_trading.contains(&SessionStatus::LunchBreak));
    }

    #[test]
    fn test_parse_case_insensitive() {
        assert_eq!("open".parse::<SessionStatus>().unwrap(), SessionStatus::Open);
        assert_eq!("OPEN".parse::<SessionStatus>().unwrap(), SessionStatus::Open);
        assert_eq!("Open".parse::<SessionStatus>().unwrap(), SessionStatus::Open);
        assert_eq!(
            " early_close ".parse::<SessionStatus>().unwrap(),
            SessionStatus::EarlyClose
        );
    }

    #[test]
    fn test_parse_all_statuses() {
        for status in SessionStatus::all() {
            let parsed = status.as_str().parse::<SessionStatus>().unwrap();
            assert_eq!(parsed, status);
        }
    }

    #[test]
    fn test_parse_invalid() {
        assert!("".parse::<SessionStatus>().is_err());
        assert!("bogus".parse::<SessionStatus>().is_err());
        assert!("trading".parse::<SessionStatus>().is_err());
        assert!("open_market".parse::<SessionStatus>().is_err());
    }

    #[test]
    fn test_parse_error_display() {
        let err = "bogus".parse::<SessionStatus>().unwrap_err();
        let msg = err.to_string();
        assert!(msg.contains("bogus"));
        assert!(msg.contains("unknown session status"));
    }

    #[test]
    fn test_must_parse() {
        assert_eq!(SessionStatus::must_parse("open"), SessionStatus::Open);
        assert_eq!(SessionStatus::must_parse("CLOSED"), SessionStatus::Closed);
    }

    #[test]
    #[should_panic(expected = "invalid session status")]
    fn test_must_parse_panics() {
        SessionStatus::must_parse("bogus");
    }

    #[test]
    fn test_display() {
        assert_eq!(format!("{}", SessionStatus::Open), "open");
        assert_eq!(format!("{}", SessionStatus::EarlyClose), "early_close");
        assert_eq!(format!("{}", SessionStatus::LunchBreak), "lunch_break");
    }

    #[test]
    fn test_into_string() {
        let s: String = SessionStatus::Open.into();
        assert_eq!(s, "open");

        let s: String = (&SessionStatus::Closed).into();
        assert_eq!(s, "closed");
    }

    #[test]
    fn test_as_ref() {
        let status = SessionStatus::Open;
        let s: &str = status.as_ref();
        assert_eq!(s, "open");
    }
}