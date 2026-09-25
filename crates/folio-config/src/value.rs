//! Helpers over `serde_yaml_ng::Value`: presence vs. null, the quoting the
//! messages use, the string-list rule and the YAML-to-JSON bridge.
//!
//! The same rendering for `serde_json::Value` lives in `folio_plugins::msgfmt`,
//! for the plugins that read an already-converted config.

use serde_yaml_ng::{Mapping, Value};

use crate::error::ConfigError;
use crate::suggest::did_you_mean;

/// A value quoted for a message: single quotes, with the escapes that keep a
/// newline or a tab from breaking the message across lines.
pub(crate) fn quoted(text: &str) -> String {
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

/// A scalar or collection for a message: `null`, `true` and `false` as the
/// config file spells them, collections flowing onto one line.
pub(crate) fn quoted_value(value: &Value) -> String {
    match value {
        Value::Null => "null".to_string(),
        Value::Bool(b) => b.to_string(),
        Value::Number(n) => {
            if let Some(f) = n.as_f64().filter(|_| !n.is_i64() && !n.is_u64()) {
                format!("{f:?}")
            } else {
                n.to_string()
            }
        }
        Value::String(s) => quoted(s),
        Value::Sequence(items) => {
            format!(
                "[{}]",
                items
                    .iter()
                    .map(quoted_value)
                    .collect::<Vec<_>>()
                    .join(", ")
            )
        }
        Value::Mapping(map) => format!(
            "{{{}}}",
            map.iter()
                .map(|(k, v)| format!("{}: {}", quoted_value(k), quoted_value(v)))
                .collect::<Vec<_>>()
                .join(", ")
        ),
        Value::Tagged(tagged) => quoted_value(&tagged.value),
    }
}

pub(crate) const NULL: Value = Value::Null;

/// `mapping.get(key, None)`: the value, or `Null` when the key is missing.
pub(crate) fn get<'a>(mapping: &'a Mapping, key: &str) -> &'a Value {
    mapping.get(key).unwrap_or(&NULL)
}

/// The value when the key is present and not `null`. For the fields whose
/// rule treats an explicit `null` like a missing key (`plugins`,
/// `source.python`, `source.<language>`, `docstring_style`); typed scalars
/// go through `string_field`/`bool_field`, where `null` is a type error.
pub(crate) fn field<'a>(mapping: &'a Mapping, key: &str) -> Option<&'a Value> {
    mapping.get(key).filter(|v| !v.is_null())
}

/// Python `value in (None, "")`.
pub(crate) fn is_blank(value: Option<&Value>) -> bool {
    match value {
        None | Some(Value::Null) => true,
        Some(Value::String(s)) => s.is_empty(),
        _ => false,
    }
}

/// `_config_string_list`: `null`/missing is `[]`; anything but a list of
/// strings fails with `{key} must be a list of strings`.
pub(crate) fn string_list(value: Option<&Value>, key: &str) -> Result<Vec<String>, ConfigError> {
    let err = || ConfigError::field(key, format!("{key} must be a list of strings"));
    match value {
        None | Some(Value::Null) => Ok(Vec::new()),
        Some(Value::Sequence(items)) => items
            .iter()
            .map(|item| item.as_str().map(str::to_string).ok_or_else(err))
            .collect(),
        Some(_) => Err(err()),
    }
}

/// A string field with a default when missing; anything else, an explicit
/// `null` included, is `{path} must be a string`.
pub(crate) fn string_field(
    mapping: &Mapping,
    key: &str,
    path: &str,
    default: &str,
) -> Result<String, ConfigError> {
    match mapping.get(key) {
        None => Ok(default.to_string()),
        Some(Value::String(s)) => Ok(s.clone()),
        Some(_) => Err(ConfigError::field(path, format!("{path} must be a string"))),
    }
}

/// A boolean field with a default when missing; anything else, an explicit
/// `null` included, is `{path} must be a boolean` (Python stored `None`,
/// which read as the feature being off).
pub(crate) fn bool_field(
    mapping: &Mapping,
    key: &str,
    path: &str,
    default: bool,
) -> Result<bool, ConfigError> {
    match mapping.get(key) {
        None => Ok(default),
        Some(Value::Bool(b)) => Ok(*b),
        Some(_) => Err(ConfigError::field(
            path,
            format!("{path} must be a boolean"),
        )),
    }
}

/// One warning naming the keys of `mapping` outside `allowed`, sorted, each
/// with the allowed key it most likely misspells:
/// `Unknown project keys in docs.yaml: vesion (did you mean 'version'?)`.
pub(crate) fn warn_unknown_keys(
    mapping: &Mapping,
    allowed: &[&str],
    section: &str,
    warnings: &mut Vec<String>,
) {
    let mut unknown: Vec<String> = mapping
        .keys()
        .filter(|key| !matches!(key.as_str(), Some(k) if allowed.contains(&k)))
        .map(|key| match key.as_str() {
            Some(k) => format!("{k}{}", did_you_mean(k, allowed.iter().copied())),
            None => quoted_value(key),
        })
        .collect();
    if unknown.is_empty() {
        return;
    }
    unknown.sort();
    warnings.push(format!(
        "Unknown {section} keys in docs.yaml: {}",
        unknown.join(", ")
    ));
}

#[cfg(test)]
#[path = "value_tests.rs"]
mod tests;
