//! How a config value reads inside a message: quoted scalars, and `null`,
//! `true` and `false` spelled the way the config file spells them. Plus the
//! truthiness rule the config flags follow.

use serde_json::Value;

/// A value quoted for a message: single quotes, with the escapes that keep a
/// newline or a tab from breaking the message across lines.
pub fn quoted(text: &str) -> String {
    let mut out = String::with_capacity(text.len() + 2);
    out.push('\'');
    for c in text.chars() {
        match c {
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\'' => out.push_str("\\'"),
            c => out.push(c),
        }
    }
    out.push('\'');
    out
}

fn number(n: &serde_json::Number) -> String {
    match n.as_f64() {
        Some(f) if !n.is_i64() && !n.is_u64() => format!("{f:?}"),
        _ => n.to_string(),
    }
}

/// A config value for a message: collections flow onto one line.
pub fn quoted_value(value: &Value) -> String {
    match value {
        Value::Null => "null".to_string(),
        Value::Bool(b) => b.to_string(),
        Value::Number(n) => number(n),
        Value::String(s) => quoted(s),
        Value::Array(items) => format!(
            "[{}]",
            items
                .iter()
                .map(quoted_value)
                .collect::<Vec<_>>()
                .join(", ")
        ),
        Value::Object(map) => format!(
            "{{{}}}",
            map.iter()
                .map(|(k, v)| format!("{}: {}", quoted(k), quoted_value(v)))
                .collect::<Vec<_>>()
                .join(", ")
        ),
    }
}

/// The truthiness a config flag follows: `null`, `false`, zero and the empty
/// string, list and mapping are off, everything else is on.
pub fn truthy(value: &Value) -> bool {
    match value {
        Value::Null => false,
        Value::Bool(b) => *b,
        Value::Number(n) => n.as_f64() != Some(0.0),
        Value::String(s) => !s.is_empty(),
        Value::Array(a) => !a.is_empty(),
        Value::Object(o) => !o.is_empty(),
    }
}

/// A string as itself, anything else quoted: for the messages that name a
/// value without quoting it.
pub fn as_text(value: &Value) -> String {
    match value {
        Value::String(s) => s.clone(),
        other => quoted_value(other),
    }
}

/// The YAML name of a value's kind, for "must be X (got Y)" messages.
pub fn kind(value: &Value) -> &'static str {
    match value {
        Value::Null => "null",
        Value::Bool(_) => "bool",
        Value::Number(_) => "number",
        Value::String(_) => "string",
        Value::Array(_) => "sequence",
        Value::Object(_) => "mapping",
    }
}

#[cfg(test)]
#[path = "msgfmt_tests.rs"]
mod tests;
