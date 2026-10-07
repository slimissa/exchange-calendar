//! Cross-language conformance runner.
//!
//! Reads `tests/cross_language_queries.json`, answers each query through the
//! Rust wrapper, and prints key-sorted JSON (2-space indent) that must be
//! byte-identical to the Python, JavaScript and Go runners. Diffed by
//! `tools/check_cross_language.sh`.
//!
//! Key order relies on serde_json's default `BTreeMap`-backed `Map`; do not
//! enable the `preserve_order` feature.

use std::path::PathBuf;

use exchange_calendar::Registry;
use serde_json::{json, Map, Value};

fn main() {
    let root = PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..");
    let fixture: Value = serde_json::from_str(
        &std::fs::read_to_string(root.join("tests/cross_language_queries.json"))
            .expect("read fixture"),
    )
    .expect("parse fixture");
    let registry = Registry::load(root.join("calendar.json")).expect("load calendar.json");

    let mut out = Map::new();
    for q in fixture["queries"].as_array().expect("queries array") {
        let op = q["op"].as_str().expect("op");
        let label = q["label"].as_str().expect("label").to_string();
        let args = q["args"].as_array().expect("args");
        let s = |i: usize| args[i].as_str().expect("string arg");

        let value = match op {
            "sessions" => json!(registry
                .sessions(s(0))
                .iter()
                .map(|x| json!({
                    "type": x.session_type,
                    "open": x.open,
                    "close": x.close,
                    "at": x.at,
                }))
                .collect::<Vec<_>>()),
            "confidence" => {
                let year = args[1].as_i64().expect("year") as i32;
                match registry.confidence(s(0), year) {
                    Some(c) => serde_json::to_value(c).expect("serialize confidence"),
                    None => Value::Null,
                }
            }
            "is_open" => json!(registry.is_open(s(0), s(1), s(2))),
            "as_of" => {
                let rec = registry.as_of(s(0), s(1)).unwrap_or(Value::Null);
                json!({
                    "confidence": rec.get("confidence").cloned().unwrap_or_else(|| json!({})),
                    "_as_of": rec.get("_as_of").cloned().unwrap_or(Value::Null),
                })
            }
            "is_holiday" => json!(registry.get(s(0)).expect("exchange").is_holiday(s(1))),
            "holiday_entry" => {
                let ex = registry.get(s(0)).expect("exchange");
                match ex.list_holidays(None).into_iter().find(|h| h.date == s(1)) {
                    None => Value::Null,
                    Some(h) => {
                        let mut m = Map::new();
                        m.insert("date".into(), json!(h.date));
                        m.insert("name".into(), json!(h.name));
                        m.insert("status".into(), json!(h.status));
                        if let Some(x) = &h.early_close_time { m.insert("early_close_time".into(), json!(x)); }
                        if let Some(x) = &h.delayed_open_time { m.insert("delayed_open_time".into(), json!(x)); }
                        if let Some(x) = &h.source_url { m.insert("source_url".into(), json!(x)); }
                        if let Some(x) = h.predicted { m.insert("predicted".into(), json!(x)); }
                        if let Some(x) = h.weekend_exception { m.insert("weekend_exception".into(), json!(x)); }
                        Value::Object(m)
                    }
                }
            }
            other => {
                eprintln!("unknown op {other}");
                std::process::exit(2);
            }
        };
        out.insert(label, value);
    }
    println!("{}", serde_json::to_string_pretty(&Value::Object(out)).unwrap());
}
