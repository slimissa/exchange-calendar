//! # exchange-calendar
//!
//! Rust wrapper for the QuantOS exchange calendar registry.
//!
//! A canonical, versioned, machine-readable registry of global exchange trading
//! calendars. This crate provides an idiomatic Rust API for loading and querying
//! exchange calendars — market holidays, early closes, trading hours, and
//! session status.
//!
//! ## Features
//!
//! - **Type-safe** — `SessionStatus` is a proper enum, not a string
//! - **Immutable** — all structs read-only after construction
//! - **Thread-safe** — `Registry` and `Exchange` can be shared across threads
//! - **Case-insensitive lookups** — `registry.exchange("xnys")` works
//! - **Complete status model** — 6 session states
//! - **Date navigation** — next/previous trading day with `chrono`
//! - **Zero runtime deps** — only `serde`, `serde_json`, and `chrono`
//!
//! ## Quick Start
//!
//! ```rust,no_run
//! use exchange_calendar::Registry;
//!
//! fn main() -> Result<(), Box<dyn std::error::Error>> {
//!     // Load the registry
//!     let registry = Registry::load("calendar.json")?;
//!
//!     // Get an exchange by MIC code
//!     let xnys = registry.get("XNYS")?;
//!
//!     // Check if the market is open
//!     assert!(xnys.is_open("2025-07-07", Some("10:00")));
//!     assert!(!xnys.is_open("2025-07-04", Some("10:00"))); // Independence Day
//!
//!     // Get session status
//!     let status = xnys.status_at("2025-07-07", "10:00")?;
//!     println!("Status: {}", status); // "open"
//!
//!     Ok(())
//! }
//! ```
//!
//! ## Supported Exchanges
//!
//! | Code | Exchange | Timezone |
//! |------|----------|----------|
//! | `XNYS` | New York Stock Exchange | `America/New_York` |
//! | `XLON` | London Stock Exchange | `Europe/London` |

mod exchange;
mod registry;
mod session;

pub use exchange::{
    Exchange, ExchangeData, ExchangeError, ExtendedHours, HolidayEntry, HolidaysData,
    QueryError, RegularHours, Session,
};
pub use registry::{MetaData, Registry, RegistryData, RegistryError};
pub use session::{ParseSessionStatusError, SessionStatus};

/// Crate version.
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

#[cfg(test)]
mod integration_tests {
    use super::*;

    #[test]
    fn test_version_constant() {
        assert_eq!(VERSION, "1.0.0");
    }

    #[test]
    fn test_session_status_reexported() {
        // Verify SessionStatus is accessible from crate root
        let status = SessionStatus::Open;
        assert_eq!(status.as_str(), "open");
    }

    #[test]
    fn test_exchange_reexported() {
        // Verify Exchange types are accessible from crate root
        let hours = RegularHours {
            open: "09:00".to_string(),
            close: "17:00".to_string(),
        };
        assert_eq!(hours.open, "09:00");
    }

    #[test]
    fn test_registry_reexported() {
        // Verify Registry types are accessible from crate root
        let meta = MetaData {
            version: "1.0.0".to_string(),
            exchange_count: 0,
        };
        assert_eq!(meta.version, "1.0.0");
    }

    #[test]
    fn test_full_integration() {
        // Build a minimal registry from JSON
        let json = r#"{
            "meta": {"version": "1.0.0", "exchange_count": 1},
            "exchanges": [{
                "code": "TEST",
                "name": "Test Exchange",
                "mic": "TEST",
                "timezone": "Europe/London",
                "regular_hours": {"open": "09:00", "close": "17:00"},
                "holidays": {
                    "explicit": [
                        {
                            "date": "2025-01-01",
                            "name": "New Year's Day",
                            "status": "closed"
                        }
                    ],
                    "generated": []
                }
            }]
        }"#;

        let registry = Registry::from_json_str(json).unwrap();
        assert_eq!(registry.version, "1.0.0");

        let exchange = registry.get("TEST").unwrap();
        assert!(exchange.is_holiday("2025-01-01"));
        assert!(!exchange.is_holiday("2025-01-02"));
        assert!(exchange.is_open("2025-01-02", Some("10:00")));
        assert_eq!(
            exchange.status_at("2025-01-02", "10:00").unwrap(),
            SessionStatus::Open
        );
    }

    #[test]
    fn test_error_types_implement_error_trait() {
        fn assert_error<T: std::error::Error>() {}

        assert_error::<ExchangeError>();
        assert_error::<QueryError>();
        assert_error::<RegistryError>();
        assert_error::<ParseSessionStatusError>();
    }
}