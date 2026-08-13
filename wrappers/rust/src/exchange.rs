use std::collections::HashMap;

use chrono::{Datelike, Duration, NaiveDate, NaiveTime, Weekday};

use serde::{Deserialize, Serialize};
use crate::session::SessionStatus;

/// Regular trading hours for an exchange.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct RegularHours {
    /// Opening time in HH:MM format (e.g., "09:30").
    pub open: String,

    /// Closing time in HH:MM format (e.g., "16:00").
    pub close: String,
}

impl RegularHours {
    /// Parse the open time as a `NaiveTime`.
    ///
    /// Returns `None` if the format is invalid.
    pub fn open_time(&self) -> Option<NaiveTime> {
        NaiveTime::parse_from_str(&self.open, "%H:%M").ok()
    }

    /// Parse the close time as a `NaiveTime`.
    ///
    /// Returns `None` if the format is invalid.
    pub fn close_time(&self) -> Option<NaiveTime> {
        NaiveTime::parse_from_str(&self.close, "%H:%M").ok()
    }
}

/// Extended trading hours (pre-market and after-hours).
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct ExtendedHours {
    /// Pre-market session.
    pub pre_market: Option<RegularHours>,

    /// After-hours session.
    pub after_hours: Option<RegularHours>,
}

/// A session within a trading day (auction or lunch break).
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct Session {
    /// Session type: "lunch_break", "auction", or "other".
    pub session_type: String,

    /// Start time for interval sessions (lunch break).
    pub open: Option<String>,

    /// End time for interval sessions (lunch break).
    pub close: Option<String>,

    /// Point-in-time moment for auction sessions.
    pub at: Option<String>,
}

/// A single holiday or special session entry.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct HolidayEntry {
    /// ISO date (YYYY-MM-DD).
    pub date: String,

    /// Human-readable name.
    pub name: String,

    /// Status: "closed", "early_close", "delayed_open", "special_session".
    pub status: String,

    /// Early close time (HH:MM) when status is "early_close".
    pub early_close_time: Option<String>,

    /// Delayed open time (HH:MM) when status is "delayed_open".
    pub delayed_open_time: Option<String>,

    /// Source citation URL.
    pub source_url: Option<String>,
}

/// Raw exchange data as deserialized from calendar.json.
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct ExchangeData {
    /// MIC code (e.g., "XNYS").
    pub code: String,

    /// Full exchange name.
    pub name: String,

    /// ISO 10383 MIC, equal to code.
    pub mic: String,

    /// IANA timezone (e.g., "America/New_York").
    pub timezone: String,

    /// Regular trading hours.
    pub regular_hours: RegularHours,

    /// Extended trading hours.
    pub extended_hours: Option<ExtendedHours>,

    /// Auction and lunch break sessions.
    pub sessions: Option<Vec<Session>>,

    /// Holiday data (explicit and generated).
    pub holidays: HolidaysData,

    /// Ad-hoc closures.
    pub ad_hoc_closures: Option<Vec<HolidayEntry>>,

    /// Generation range as [start_date, end_date].
    pub generation_range: Option<Vec<String>>,
}

/// Holiday data container.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize, Deserialize)]
pub struct HolidaysData {
    /// Hand-curated dates.
    pub explicit: Vec<HolidayEntry>,

    /// Generated from recurrence rules.
    pub generated: Vec<HolidayEntry>,
}

/// Error returned when Exchange construction fails.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ExchangeError {
    /// A required field is missing.
    MissingField(&'static str),

    /// Code does not match MIC.
    CodeMismatch { code: String, mic: String },

    /// Time format is invalid.
    InvalidTimeFormat(String),

    /// Open time is not before close time.
    OpenAfterClose { open: String, close: String },
}

impl std::fmt::Display for ExchangeError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ExchangeError::MissingField(field) => write!(f, "missing field: {}", field),
            ExchangeError::CodeMismatch { code, mic } => {
                write!(f, "code '{}' must equal mic '{}'", code, mic)
            }
            ExchangeError::InvalidTimeFormat(t) => {
                write!(f, "invalid time format: '{}' (expected HH:MM)", t)
            }
            ExchangeError::OpenAfterClose { open, close } => {
                write!(f, "open ({}) must be before close ({})", open, close)
            }
        }
    }
}

impl std::error::Error for ExchangeError {}

/// Error returned when querying with invalid date/time input.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum QueryError {
    /// Date format is invalid.
    InvalidDate(String),

    /// Time format is invalid.
    InvalidTime(String),

    /// No trading day found within 30 days.
    NoTradingDayFound(String),
}

impl std::fmt::Display for QueryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            QueryError::InvalidDate(d) => write!(f, "invalid date format: '{}' (expected YYYY-MM-DD)", d),
            QueryError::InvalidTime(t) => write!(f, "invalid time format: '{}' (expected HH:MM)", t),
            QueryError::NoTradingDayFound(d) => {
                write!(f, "no trading day found within 30 days of {}", d)
            }
        }
    }
}

impl std::error::Error for QueryError {}

/// Represents a single exchange calendar.
///
/// Immutable after construction. Safe to share across threads.
#[derive(Debug, Clone)]
pub struct Exchange {
    /// MIC code.
    pub code: String,

    /// Full exchange name.
    pub name: String,

    /// ISO 10383 MIC.
    pub mic: String,

    /// IANA timezone.
    pub timezone: String,

    /// Regular trading hours.
    pub regular_hours: RegularHours,

    /// Extended trading hours.
    pub extended_hours: ExtendedHours,

    /// Sessions (auctions, lunch breaks).
    pub sessions: Vec<Session>,

    // Private lookup maps
    holiday_by_date: HashMap<String, HolidayEntry>,
    status_by_date: HashMap<String, String>,
    early_close_time_by_date: HashMap<String, String>,
}

impl Exchange {
    /// Create an Exchange from raw registry data.
    ///
    /// Returns an error if required fields are missing or malformed.
    pub fn new(data: ExchangeData) -> Result<Self, ExchangeError> {
        Self::validate(&data)?;

        let mut exchange = Exchange {
            code: data.code.clone(),
            name: data.name.clone(),
            mic: data.mic.clone(),
            timezone: data.timezone.clone(),
            regular_hours: data.regular_hours.clone(),
            extended_hours: data.extended_hours.clone().unwrap_or_default(),
            sessions: data.sessions.clone().unwrap_or_default(),
            holiday_by_date: HashMap::new(),
            status_by_date: HashMap::new(),
            early_close_time_by_date: HashMap::new(),
        };

        // Index all holidays
        for entry in data.holidays.explicit.iter().chain(data.holidays.generated.iter()) {
            exchange.index_entry(entry);
        }

        // Index ad-hoc closures
        if let Some(ad_hoc) = &data.ad_hoc_closures {
            for entry in ad_hoc {
                exchange.index_entry(entry);
            }
        }

        Ok(exchange)
    }

    /// Validate exchange data before construction.
    fn validate(data: &ExchangeData) -> Result<(), ExchangeError> {
        if data.code.is_empty() {
            return Err(ExchangeError::MissingField("code"));
        }
        if data.name.is_empty() {
            return Err(ExchangeError::MissingField("name"));
        }
        if data.mic.is_empty() {
            return Err(ExchangeError::MissingField("mic"));
        }
        if data.code != data.mic {
            return Err(ExchangeError::CodeMismatch {
                code: data.code.clone(),
                mic: data.mic.clone(),
            });
        }
        if data.timezone.is_empty() {
            return Err(ExchangeError::MissingField("timezone"));
        }
        if data.regular_hours.open.is_empty() {
            return Err(ExchangeError::MissingField("regular_hours.open"));
        }
        if data.regular_hours.close.is_empty() {
            return Err(ExchangeError::MissingField("regular_hours.close"));
        }

        Self::validate_time_format(&data.regular_hours.open)?;
        Self::validate_time_format(&data.regular_hours.close)?;

        if data.regular_hours.open >= data.regular_hours.close {
            return Err(ExchangeError::OpenAfterClose {
                open: data.regular_hours.open.clone(),
                close: data.regular_hours.close.clone(),
            });
        }

        Ok(())
    }

    /// Validate HH:MM time format.
    fn validate_time_format(time_str: &str) -> Result<(), ExchangeError> {
        if NaiveTime::parse_from_str(time_str, "%H:%M").is_err() {
            return Err(ExchangeError::InvalidTimeFormat(time_str.to_string()));
        }
        Ok(())
    }

    /// Validate YYYY-MM-DD date format.
    fn validate_date_format(date_str: &str) -> Result<NaiveDate, QueryError> {
        NaiveDate::parse_from_str(date_str, "%Y-%m-%d")
            .map_err(|_| QueryError::InvalidDate(date_str.to_string()))
    }

    /// Index a holiday entry into the lookup maps.
    fn index_entry(&mut self, entry: &HolidayEntry) {
        self.holiday_by_date.insert(entry.date.clone(), entry.clone());
        self.status_by_date.insert(entry.date.clone(), entry.status.clone());

        if entry.status == "early_close" {
            if let Some(time) = &entry.early_close_time {
                self.early_close_time_by_date.insert(entry.date.clone(), time.clone());
            }
        }
    }

    /// Return true if the date is Saturday or Sunday.
    fn is_weekend(date: &NaiveDate) -> bool {
        matches!(date.weekday(), Weekday::Sat | Weekday::Sun)
    }

    // ──────────────────────────────────────────────────────────
    // Public API — holiday queries
    // ──────────────────────────────────────────────────────────

    /// Return true if the market is fully closed on this date.
    /// Includes weekends and explicit/generated holidays.
    pub fn is_holiday(&self, date_str: &str) -> bool {
        if let Ok(date) = Self::validate_date_format(date_str) {
            if Self::is_weekend(&date) {
                return true;
            }
        }
        self.status_by_date.get(date_str).map(|s| s == "closed").unwrap_or(false)
    }

    /// Return true if this date has an early close.
    pub fn is_early_close(&self, date_str: &str) -> bool {
        self.early_close_time_by_date.contains_key(date_str)
    }

    /// Return the early close time for this date, or None.
    pub fn early_close_time(&self, date_str: &str) -> Option<&str> {
        self.early_close_time_by_date.get(date_str).map(|s| s.as_str())
    }

    // ──────────────────────────────────────────────────────────
    // Public API — status
    // ──────────────────────────────────────────────────────────

    /// Return the full session status at a specific date and time.
    ///
    /// Returns an error if date or time format is invalid.
    pub fn status_at(&self, date_str: &str, time_str: &str) -> Result<SessionStatus, QueryError> {
        let date = Self::validate_date_format(date_str)?;
        let time = NaiveTime::parse_from_str(time_str, "%H:%M")
            .map_err(|_| QueryError::InvalidTime(time_str.to_string()))?;

        // Weekend
        if Self::is_weekend(&date) {
            return Ok(SessionStatus::Closed);
        }

        // Full holiday
        if self.status_by_date.get(date_str).map(|s| s == "closed").unwrap_or(false) {
            return Ok(SessionStatus::Closed);
        }

        // Early close day — check if past the early close time
        let is_early_close_day = self.is_early_close(date_str);
        if is_early_close_day {
            if let Some(close_time_str) = self.early_close_time(date_str) {
                if let Ok(close_time) = NaiveTime::parse_from_str(close_time_str, "%H:%M") {
                    if time >= close_time {
                        return Ok(SessionStatus::Closed);
                    }
                }
            }
        }

        // Lunch break
        for session in &self.sessions {
            if session.session_type == "lunch_break" {
                if let (Some(open), Some(close)) = (&session.open, &session.close) {
                    if let (Ok(open_time), Ok(close_time)) = (
                        NaiveTime::parse_from_str(open, "%H:%M"),
                        NaiveTime::parse_from_str(close, "%H:%M"),
                    ) {
                        if open_time <= time && time < close_time {
                            return Ok(SessionStatus::LunchBreak);
                        }
                    }
                }
            }
        }

        // Before regular open
        if let Some(open_time) = self.regular_hours.open_time() {
            if time < open_time {
                return Ok(SessionStatus::PreMarket);
            }
        }

        // After regular close
        if let Some(close_time) = self.regular_hours.close_time() {
            if time >= close_time {
                return Ok(SessionStatus::AfterHours);
            }
        }

        // Within regular hours
        if is_early_close_day {
            Ok(SessionStatus::EarlyClose)
        } else {
            Ok(SessionStatus::Open)
        }
    }

    /// Return true if the market is open for trading at the given moment.
    ///
    /// If `time_str` is None, defaults to "10:00".
    pub fn is_open(&self, date_str: &str, time_str: Option<&str>) -> bool {
        let time = time_str.unwrap_or("10:00");
        self.status_at(date_str, time)
            .map(|s| s.is_trading())
            .unwrap_or(false)
    }

    // ──────────────────────────────────────────────────────────
    // Public API — date navigation
    // ──────────────────────────────────────────────────────────

    /// Return the next trading day after the given date.
    /// Skips weekends and full holidays. Early close days count.
    pub fn next_trading_day(&self, date_str: &str) -> Result<String, QueryError> {
        let mut date = Self::validate_date_format(date_str)?;

        for _ in 0..30 {
            date += Duration::days(1);
            let candidate = date.format("%Y-%m-%d").to_string();
            if !self.is_holiday(&candidate) {
                return Ok(candidate);
            }
        }

        Err(QueryError::NoTradingDayFound(date_str.to_string()))
    }

    /// Return the previous trading day before the given date.
    /// Skips weekends and full holidays. Early close days count.
    pub fn previous_trading_day(&self, date_str: &str) -> Result<String, QueryError> {
        let mut date = Self::validate_date_format(date_str)?;

        for _ in 0..30 {
            date -= Duration::days(1);
            let candidate = date.format("%Y-%m-%d").to_string();
            if !self.is_holiday(&candidate) {
                return Ok(candidate);
            }
        }

        Err(QueryError::NoTradingDayFound(date_str.to_string()))
    }

    // ──────────────────────────────────────────────────────────
    // Public API — metadata
    // ──────────────────────────────────────────────────────────

    /// Return the number of holidays, optionally filtered by year.
    pub fn holiday_count(&self, year: Option<i32>) -> usize {
        match year {
            Some(y) => {
                let prefix = format!("{}-", y);
                self.holiday_by_date
                    .keys()
                    .filter(|date| date.starts_with(&prefix))
                    .count()
            }
            None => self.holiday_by_date.len(),
        }
    }

    /// Return a sorted list of holiday entries, optionally filtered by year.
    pub fn list_holidays(&self, year: Option<i32>) -> Vec<&HolidayEntry> {
        let mut entries: Vec<&HolidayEntry> = self.holiday_by_date.values().collect();

        if let Some(y) = year {
            let prefix = format!("{}-", y);
            entries.retain(|e| e.date.starts_with(&prefix));
        }

        entries.sort_by(|a, b| a.date.cmp(&b.date));
        entries
    }
}

impl std::fmt::Display for Exchange {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{} ({})", self.name, self.code)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_exchange() -> Exchange {
        let data = ExchangeData {
            code: "TEST".to_string(),
            name: "Test Exchange".to_string(),
            mic: "TEST".to_string(),
            timezone: "Europe/London".to_string(),
            regular_hours: RegularHours {
                open: "09:00".to_string(),
                close: "17:00".to_string(),
            },
            extended_hours: None,
            sessions: None,
            holidays: HolidaysData {
                explicit: vec![
                    HolidayEntry {
                        date: "2025-01-01".to_string(),
                        name: "New Year's Day".to_string(),
                        status: "closed".to_string(),
                        early_close_time: None,
                        delayed_open_time: None,
                        source_url: None,
                    },
                    HolidayEntry {
                        date: "2025-07-03".to_string(),
                        name: "Early Close Day".to_string(),
                        status: "early_close".to_string(),
                        early_close_time: Some("13:00".to_string()),
                        delayed_open_time: None,
                        source_url: None,
                    },
                ],
                generated: vec![],
            },
            ad_hoc_closures: None,
            generation_range: None,
        };

        Exchange::new(data).unwrap()
    }

    #[test]
    fn test_new_exchange() {
        let e = create_test_exchange();
        assert_eq!(e.code, "TEST");
        assert_eq!(e.name, "Test Exchange");
        assert_eq!(e.mic, "TEST");
        assert_eq!(e.timezone, "Europe/London");
        assert_eq!(e.regular_hours.open, "09:00");
        assert_eq!(e.regular_hours.close, "17:00");
    }

    #[test]
    fn test_new_exchange_missing_code() {
        let data = ExchangeData {
            code: "".to_string(),
            name: "Test".to_string(),
            mic: "TEST".to_string(),
            timezone: "Europe/London".to_string(),
            regular_hours: RegularHours { open: "09:00".to_string(), close: "17:00".to_string() },
            extended_hours: None,
            sessions: None,
            holidays: HolidaysData::default(),
            ad_hoc_closures: None,
            generation_range: None,
        };
        assert!(matches!(Exchange::new(data), Err(ExchangeError::MissingField("code"))));
    }

    #[test]
    fn test_new_exchange_code_mismatch() {
        let data = ExchangeData {
            code: "TEST".to_string(),
            name: "Test".to_string(),
            mic: "OTHER".to_string(),
            timezone: "Europe/London".to_string(),
            regular_hours: RegularHours { open: "09:00".to_string(), close: "17:00".to_string() },
            extended_hours: None,
            sessions: None,
            holidays: HolidaysData::default(),
            ad_hoc_closures: None,
            generation_range: None,
        };
        assert!(matches!(Exchange::new(data), Err(ExchangeError::CodeMismatch { .. })));
    }

    #[test]
    fn test_new_exchange_invalid_time() {
        let data = ExchangeData {
            code: "TEST".to_string(),
            name: "Test".to_string(),
            mic: "TEST".to_string(),
            timezone: "Europe/London".to_string(),
            regular_hours: RegularHours { open: "9am".to_string(), close: "17:00".to_string() },
            extended_hours: None,
            sessions: None,
            holidays: HolidaysData::default(),
            ad_hoc_closures: None,
            generation_range: None,
        };
        assert!(matches!(Exchange::new(data), Err(ExchangeError::InvalidTimeFormat(_))));
    }

    #[test]
    fn test_new_exchange_open_after_close() {
        let data = ExchangeData {
            code: "TEST".to_string(),
            name: "Test".to_string(),
            mic: "TEST".to_string(),
            timezone: "Europe/London".to_string(),
            regular_hours: RegularHours { open: "17:00".to_string(), close: "09:00".to_string() },
            extended_hours: None,
            sessions: None,
            holidays: HolidaysData::default(),
            ad_hoc_closures: None,
            generation_range: None,
        };
        assert!(matches!(Exchange::new(data), Err(ExchangeError::OpenAfterClose { .. })));
    }

    #[test]
    fn test_is_holiday() {
        let e = create_test_exchange();
        assert!(e.is_holiday("2025-01-01"));
        assert!(!e.is_holiday("2025-03-14"));
        assert!(e.is_holiday("2025-03-15")); // Saturday
        assert!(e.is_holiday("2025-03-16")); // Sunday
        assert!(!e.is_holiday("2025-07-03")); // Early close, not full holiday
    }

    #[test]
    fn test_is_early_close() {
        let e = create_test_exchange();
        assert!(e.is_early_close("2025-07-03"));
        assert!(!e.is_early_close("2025-07-04"));
    }

    #[test]
    fn test_early_close_time() {
        let e = create_test_exchange();
        assert_eq!(e.early_close_time("2025-07-03"), Some("13:00"));
        assert_eq!(e.early_close_time("2025-07-04"), None);
    }

    #[test]
    fn test_status_at_open() {
        let e = create_test_exchange();
        assert_eq!(e.status_at("2025-03-14", "10:00").unwrap(), SessionStatus::Open);
    }

    #[test]
    fn test_status_at_weekend() {
        let e = create_test_exchange();
        assert_eq!(e.status_at("2025-03-15", "10:00").unwrap(), SessionStatus::Closed);
    }

    #[test]
    fn test_status_at_holiday() {
        let e = create_test_exchange();
        assert_eq!(e.status_at("2025-01-01", "10:00").unwrap(), SessionStatus::Closed);
    }

    #[test]
    fn test_status_at_pre_market() {
        let e = create_test_exchange();
        assert_eq!(e.status_at("2025-03-14", "08:00").unwrap(), SessionStatus::PreMarket);
    }

    #[test]
    fn test_status_at_after_hours() {
        let e = create_test_exchange();
        assert_eq!(e.status_at("2025-03-14", "18:00").unwrap(), SessionStatus::AfterHours);
    }

    #[test]
    fn test_status_at_early_close_before() {
        let e = create_test_exchange();
        assert_eq!(e.status_at("2025-07-03", "10:00").unwrap(), SessionStatus::EarlyClose);
    }

    #[test]
    fn test_status_at_early_close_after() {
        let e = create_test_exchange();
        assert_eq!(e.status_at("2025-07-03", "13:30").unwrap(), SessionStatus::Closed);
    }

    #[test]
    fn test_status_at_early_close_exact() {
        let e = create_test_exchange();
        assert_eq!(e.status_at("2025-07-03", "13:00").unwrap(), SessionStatus::Closed);
    }

    #[test]
    fn test_status_at_invalid_date() {
        let e = create_test_exchange();
        assert!(e.status_at("2025/01/01", "10:00").is_err());
    }

    #[test]
    fn test_status_at_invalid_time() {
        let e = create_test_exchange();
        assert!(e.status_at("2025-03-14", "10am").is_err());
    }

    #[test]
    fn test_is_open() {
        let e = create_test_exchange();
        assert!(e.is_open("2025-03-14", Some("10:00")));
        assert!(e.is_open("2025-03-14", None)); // default 10:00
        assert!(e.is_open("2025-07-03", Some("10:00")));
        assert!(!e.is_open("2025-07-03", Some("13:30")));
        assert!(!e.is_open("2025-01-01", Some("10:00")));
        assert!(!e.is_open("2025-03-15", Some("10:00")));
    }

    #[test]
    fn test_next_trading_day() {
        let e = create_test_exchange();
        assert_eq!(e.next_trading_day("2025-03-14").unwrap(), "2025-03-17");
        assert_eq!(e.next_trading_day("2025-06-30").unwrap(), "2025-07-01");
    }

    #[test]
    fn test_previous_trading_day() {
        let e = create_test_exchange();
        assert_eq!(e.previous_trading_day("2025-03-17").unwrap(), "2025-03-14");
    }

    #[test]
    fn test_next_trading_day_invalid() {
        let e = create_test_exchange();
        assert!(e.next_trading_day("invalid").is_err());
    }

    #[test]
    fn test_holiday_count() {
        let e = create_test_exchange();
        assert_eq!(e.holiday_count(None), 2);
        assert_eq!(e.holiday_count(Some(2025)), 2);
        assert_eq!(e.holiday_count(Some(2026)), 0);
    }

    #[test]
    fn test_list_holidays() {
        let e = create_test_exchange();
        let holidays = e.list_holidays(None);
        assert_eq!(holidays.len(), 2);
        assert!(holidays[0].date <= holidays[1].date);
    }

    #[test]
    fn test_display() {
        let e = create_test_exchange();
        assert_eq!(format!("{}", e), "Test Exchange (TEST)");
    }
}