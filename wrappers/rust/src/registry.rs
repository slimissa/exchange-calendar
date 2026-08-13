use std::collections::HashMap;
use std::fs;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::exchange::{Exchange, ExchangeData, ExchangeError};

/// Raw JSON structure of calendar.json.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RegistryData {
    /// Metadata block.
    pub meta: MetaData,

    /// Array of exchange data.
    pub exchanges: Vec<ExchangeData>,
}

/// Metadata block in calendar.json.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MetaData {
    /// Registry version.
    pub version: String,

    /// Number of exchanges.
    pub exchange_count: usize,
}

/// Error returned when registry loading or querying fails.
#[derive(Debug)]
pub enum RegistryError {
    /// File not found.
    FileNotFound(String),

    /// Invalid JSON.
    InvalidJson(String),

    /// Registry structure is invalid.
    InvalidStructure(String),

    /// Duplicate exchange codes.
    DuplicateCode(String),

    /// Exchange construction failed.
    ExchangeError(String, ExchangeError),

    /// Exchange not found by code.
    ExchangeNotFound(String),
}

impl std::fmt::Display for RegistryError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            RegistryError::FileNotFound(path) => write!(f, "file not found: {}", path),
            RegistryError::InvalidJson(msg) => write!(f, "invalid JSON: {}", msg),
            RegistryError::InvalidStructure(msg) => write!(f, "invalid structure: {}", msg),
            RegistryError::DuplicateCode(code) => write!(f, "duplicate exchange code: {}", code),
            RegistryError::ExchangeError(code, err) => {
                write!(f, "exchange '{}' error: {}", code, err)
            }
            RegistryError::ExchangeNotFound(code) => write!(f, "exchange '{}' not found", code),
        }
    }
}

impl std::error::Error for RegistryError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            RegistryError::ExchangeError(_, err) => Some(err),
            _ => None,
        }
    }
}

impl From<serde_json::Error> for RegistryError {
    fn from(err: serde_json::Error) -> Self {
        RegistryError::InvalidJson(err.to_string())
    }
}

/// A loaded exchange calendar registry.
///
/// Immutable after construction. Safe to share across threads.
#[derive(Debug, Clone)]
pub struct Registry {
    /// Registry version.
    pub version: String,

    /// Number of exchanges declared in metadata.
    pub exchange_count: usize,

    // Private map for O(1) lookup
    exchanges: HashMap<String, Exchange>,
}

impl Registry {
    /// Load the registry from a JSON file.
    ///
    /// # Arguments
    ///
    /// * `path` — Path to calendar.json.
    ///
    /// # Errors
    ///
    /// Returns `RegistryError` if the file cannot be read or parsed,
    /// or if the registry structure is invalid.
    ///
    /// # Examples
    ///
    /// ```no_run
    /// use exchange_calendar::Registry;
    ///
    /// let registry = Registry::load("calendar.json").unwrap();
    /// ```
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self, RegistryError> {
        let path_str = path.as_ref().to_string_lossy().to_string();

        let content = fs::read_to_string(path.as_ref())
            .map_err(|_| RegistryError::FileNotFound(path_str.clone()))?;

        Self::from_str(&content)
    }

    /// Load the registry from a JSON string.
    ///
    /// # Examples
    ///
    /// ```no_run
    /// use exchange_calendar::Registry;
    ///
    /// # fn main() -> Result<(), Box<dyn std::error::Error>> {
    /// let json = r#"{
    ///     "meta": {"version": "1.0.0", "exchange_count": 1},
    ///     "exchanges": [{
    ///         "code": "TEST",
    ///         "name": "Test Exchange",
    ///         "mic": "TEST",
    ///         "timezone": "Europe/London",
    ///         "regular_hours": {"open": "09:00", "close": "17:00"},
    ///         "holidays": {"explicit": [], "generated": []}
    ///     }]
    /// }"#;
    ///
    /// let registry = Registry::from_str(json)?;
    /// # Ok(())
    /// # }
    /// ```
    pub fn from_str(json: &str) -> Result<Self, RegistryError> {
        let data: RegistryData = serde_json::from_str(json)?;
        Self::from_data(data)
    }

    /// Create a Registry from parsed data.
    pub fn from_data(data: RegistryData) -> Result<Self, RegistryError> {
        if data.meta.version.is_empty() {
            return Err(RegistryError::InvalidStructure(
                "missing meta.version".to_string(),
            ));
        }

        if data.exchanges.is_empty() {
            return Err(RegistryError::InvalidStructure(
                "no exchanges found".to_string(),
            ));
        }

        let mut exchanges = HashMap::with_capacity(data.exchanges.len());

        for exchange_data in &data.exchanges {
            if exchanges.contains_key(&exchange_data.code) {
                return Err(RegistryError::DuplicateCode(exchange_data.code.clone()));
            }

            let exchange = Exchange::new(exchange_data.clone())
                .map_err(|e| RegistryError::ExchangeError(exchange_data.code.clone(), e))?;

            exchanges.insert(exchange_data.code.clone(), exchange);
        }

        Ok(Registry {
            version: data.meta.version.clone(),
            exchange_count: data.meta.exchange_count,
            exchanges,
        })
    }

    /// Return the Exchange with the given MIC code.
    ///
    /// Case-insensitive. Returns `None` if not found.
    pub fn exchange(&self, code: &str) -> Option<&Exchange> {
        let normalized = code.to_uppercase();
        self.exchanges.get(&normalized)
    }

    /// Return the Exchange with the given MIC code, or an error.
    ///
    /// Case-insensitive.
    pub fn get(&self, code: &str) -> Result<&Exchange, RegistryError> {
        self.exchange(code)
            .ok_or_else(|| RegistryError::ExchangeNotFound(code.to_string()))
    }

    /// Return true if the given MIC code exists.
    ///
    /// Case-insensitive.
    pub fn has(&self, code: &str) -> bool {
        self.exchange(code).is_some()
    }

    /// Return all MIC codes, sorted alphabetically.
    pub fn codes(&self) -> Vec<String> {
        let mut codes: Vec<String> = self.exchanges.keys().cloned().collect();
        codes.sort();
        codes
    }

    /// Return all exchange names, sorted by MIC code.
    pub fn names(&self) -> Vec<String> {
        self.codes()
            .iter()
            .map(|code| self.exchanges[code].name.clone())
            .collect()
    }

    /// Return all exchanges, sorted by MIC code.
    pub fn list_exchanges(&self) -> Vec<&Exchange> {
        self.codes()
            .iter()
            .map(|code| &self.exchanges[code])
            .collect()
    }

    /// Return the number of exchanges.
    pub fn len(&self) -> usize {
        self.exchanges.len()
    }

    /// Return true if the registry is empty.
    pub fn is_empty(&self) -> bool {
        self.exchanges.is_empty()
    }
}

impl std::fmt::Display for Registry {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            f,
            "Exchange Calendar Registry v{} ({} exchanges)",
            self.version,
            self.exchanges.len()
        )
    }
}

impl std::iter::IntoIterator for Registry {
    type Item = Exchange;
    type IntoIter = std::vec::IntoIter<Self::Item>;

    fn into_iter(self) -> Self::IntoIter {
        let mut exchanges: Vec<Exchange> = self.exchanges.into_values().collect();
        exchanges.sort_by(|a, b| a.code.cmp(&b.code));
        exchanges.into_iter()
    }
}

impl<'a> std::iter::IntoIterator for &'a Registry {
    type Item = &'a Exchange;
    type IntoIter = std::vec::IntoIter<Self::Item>;

    fn into_iter(self) -> Self::IntoIter {
        self.list_exchanges().into_iter()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::exchange::{HolidaysData, RegularHours};

    fn create_test_exchange_data(code: &str) -> ExchangeData {
        ExchangeData {
            code: code.to_string(),
            name: format!("{} Exchange", code),
            mic: code.to_string(),
            timezone: "Europe/London".to_string(),
            regular_hours: RegularHours {
                open: "09:00".to_string(),
                close: "17:00".to_string(),
            },
            extended_hours: None,
            sessions: None,
            holidays: HolidaysData {
                explicit: vec![],
                generated: vec![],
            },
            ad_hoc_closures: None,
            generation_range: None,
        }
    }

    fn create_test_registry_data() -> RegistryData {
        RegistryData {
            meta: MetaData {
                version: "1.0.0".to_string(),
                exchange_count: 1,
            },
            exchanges: vec![create_test_exchange_data("TEST")],
        }
    }

    #[test]
    fn test_from_data_valid() {
        let registry = Registry::from_data(create_test_registry_data()).unwrap();
        assert_eq!(registry.version, "1.0.0");
        assert_eq!(registry.exchange_count, 1);
        assert_eq!(registry.len(), 1);
        assert!(!registry.is_empty());
    }

    #[test]
    fn test_from_data_missing_version() {
        let mut data = create_test_registry_data();
        data.meta.version = "".to_string();
        assert!(matches!(
            Registry::from_data(data),
            Err(RegistryError::InvalidStructure(_))
        ));
    }

    #[test]
    fn test_from_data_no_exchanges() {
        let mut data = create_test_registry_data();
        data.exchanges = vec![];
        assert!(matches!(
            Registry::from_data(data),
            Err(RegistryError::InvalidStructure(_))
        ));
    }

    #[test]
    fn test_from_data_duplicate_codes() {
        let mut data = create_test_registry_data();
        data.exchanges.push(create_test_exchange_data("TEST"));
        assert!(matches!(
            Registry::from_data(data),
            Err(RegistryError::DuplicateCode(_))
        ));
    }

    #[test]
    fn test_from_data_bad_exchange() {
        let mut data = create_test_registry_data();
        data.exchanges[0].code = "".to_string();
        assert!(matches!(
            Registry::from_data(data),
            Err(RegistryError::ExchangeError(_, _))
        ));
    }

    #[test]
    fn test_exchange_lookup() {
        let registry = Registry::from_data(create_test_registry_data()).unwrap();
        let exchange = registry.exchange("TEST").unwrap();
        assert_eq!(exchange.code, "TEST");
    }

    #[test]
    fn test_exchange_lookup_case_insensitive() {
        let registry = Registry::from_data(create_test_registry_data()).unwrap();
        let exchange = registry.exchange("test").unwrap();
        assert_eq!(exchange.code, "TEST");
    }

    #[test]
    fn test_exchange_not_found() {
        let registry = Registry::from_data(create_test_registry_data()).unwrap();
        assert!(registry.exchange("XXXX").is_none());
    }

    #[test]
    fn test_get_returns_err() {
        let registry = Registry::from_data(create_test_registry_data()).unwrap();
        assert!(registry.get("XXXX").is_err());
    }

    #[test]
    fn test_has() {
        let registry = Registry::from_data(create_test_registry_data()).unwrap();
        assert!(registry.has("TEST"));
        assert!(!registry.has("XXXX"));
    }

    #[test]
    fn test_codes_sorted() {
        let mut data = create_test_registry_data();
        data.exchanges.push(create_test_exchange_data("ALPHA"));
        data.exchanges.push(create_test_exchange_data("ZED"));
        data.meta.exchange_count = 3;

        let registry = Registry::from_data(data).unwrap();
        let codes = registry.codes();
        assert_eq!(codes, vec!["ALPHA", "TEST", "ZED"]);
    }

    #[test]
    fn test_names_sorted() {
        let mut data = create_test_registry_data();
        data.exchanges.push(create_test_exchange_data("ALPHA"));
        data.meta.exchange_count = 2;

        let registry = Registry::from_data(data).unwrap();
        let names = registry.names();
        assert_eq!(names, vec!["ALPHA Exchange", "TEST Exchange"]);
    }

    #[test]
    fn test_list_exchanges_sorted() {
        let mut data = create_test_registry_data();
        data.exchanges.push(create_test_exchange_data("ALPHA"));
        data.meta.exchange_count = 2;

        let registry = Registry::from_data(data).unwrap();
        let exchanges = registry.list_exchanges();
        assert_eq!(exchanges.len(), 2);
        assert_eq!(exchanges[0].code, "ALPHA");
        assert_eq!(exchanges[1].code, "TEST");
    }

    #[test]
    fn test_display() {
        let registry = Registry::from_data(create_test_registry_data()).unwrap();
        let s = format!("{}", registry);
        assert!(s.contains("1.0.0"));
        assert!(s.contains("1 exchanges"));
    }

    #[test]
    fn test_into_iter_owned() {
        let registry = Registry::from_data(create_test_registry_data()).unwrap();
        let exchanges: Vec<Exchange> = registry.into_iter().collect();
        assert_eq!(exchanges.len(), 1);
    }

    #[test]
    fn test_into_iter_borrowed() {
        let registry = Registry::from_data(create_test_registry_data()).unwrap();
        let exchanges: Vec<&Exchange> = (&registry).into_iter().collect();
        assert_eq!(exchanges.len(), 1);
    }

    #[test]
    fn test_load_missing_file() {
        assert!(matches!(
            Registry::load("/nonexistent/path/calendar.json"),
            Err(RegistryError::FileNotFound(_))
        ));
    }

    #[test]
    fn test_load_invalid_json() {
        let result = Registry::from_str("{invalid json");
        assert!(matches!(result, Err(RegistryError::InvalidJson(_))));
    }

    #[test]
    fn test_from_str_valid() {
        let json = r#"{
            "meta": {"version": "1.0.0", "exchange_count": 1},
            "exchanges": [{
                "code": "TEST",
                "name": "Test Exchange",
                "mic": "TEST",
                "timezone": "Europe/London",
                "regular_hours": {"open": "09:00", "close": "17:00"},
                "holidays": {"explicit": [], "generated": []}
            }]
        }"#;

        let registry = Registry::from_str(json).unwrap();
        assert_eq!(registry.version, "1.0.0");
        assert_eq!(registry.len(), 1);
    }
}