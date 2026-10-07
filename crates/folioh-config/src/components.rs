//! `components:` splitting into directories and `{name, from}` specs.

use std::path::Path;

use serde::Serialize;
use serde_yaml_ng::Value;

use crate::error::ConfigError;
use crate::paths::join_string;
use crate::value::{quoted_value, warn_unknown_keys};

/// `components:` split into directory entries and spec mappings.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize)]
pub struct ComponentsConfig {
    pub dirs: Vec<String>,
    pub specs: Vec<ComponentSpec>,
}

/// One `{name, from, export, expose.mdx}` spec. `name`/`from`/`export` are
/// lifted only when they are strings; any other key (and a non-string value
/// under those names, or a non-mapping `expose`) stays verbatim in `rest` for
/// the site workspace to validate. Serialises as the flat mapping it came from.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize)]
pub struct ComponentSpec {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub name: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub from: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub export: Option<String>,
    #[serde(
        rename = "expose",
        skip_serializing_if = "Option::is_none",
        serialize_with = "expose_mapping"
    )]
    pub expose_mdx: Option<serde_json::Value>,
    #[serde(flatten)]
    pub rest: serde_json::Map<String, serde_json::Value>,
}

/// `expose_mdx` back to the `{mdx: value}` mapping it was read from.
fn expose_mapping<S: serde::Serializer>(
    mdx: &Option<serde_json::Value>,
    serializer: S,
) -> Result<S::Ok, S::Error> {
    let mut expose = serde_json::Map::new();
    if let Some(mdx) = mdx {
        expose.insert("mdx".to_string(), mdx.clone());
    }
    expose.serialize(serializer)
}

fn entry_error(entry: &Value) -> ConfigError {
    ConfigError::field(
        "components",
        format!(
            "components entries must be directory path strings or {{name, from}} mappings; \
             got: {}",
            quoted_value(entry)
        ),
    )
}

fn take_string(map: &mut serde_json::Map<String, serde_json::Value>, key: &str) -> Option<String> {
    match map.get(key) {
        Some(serde_json::Value::String(_)) => {
            map.remove(key).and_then(|v| v.as_str().map(str::to_string))
        }
        _ => None,
    }
}

/// Every key a component spec reads; `path` is the legacy spelling of `from`.
const SPEC_KEYS: [&str; 5] = ["name", "from", "path", "export", "expose"];

fn warn_unknown_spec_keys(entry: &Value, index: usize, warnings: &mut Vec<String>) {
    let Some(spec) = entry.as_mapping() else {
        return;
    };
    let label = match spec.get("name").and_then(Value::as_str) {
        Some(name) => format!("components.{name}"),
        None => format!("components[{index}]"),
    };
    warn_unknown_keys(spec, &SPEC_KEYS, &label, warnings);
    if let Some(expose) = spec.get("expose").and_then(Value::as_mapping) {
        warn_unknown_keys(expose, &["mdx"], &format!("{label}.expose"), warnings);
    }
}

fn normalize_spec(entry: &Value) -> Result<ComponentSpec, ConfigError> {
    let mut rest = match serde_json::to_value(entry) {
        Ok(serde_json::Value::Object(map)) => map,
        _ => return Err(entry_error(entry)),
    };
    let expose_mdx = match rest.remove("expose") {
        Some(serde_json::Value::Object(mut expose)) => expose.remove("mdx"),
        Some(other) => {
            rest.insert("expose".to_string(), other);
            None
        }
        None => None,
    };
    Ok(ComponentSpec {
        name: take_string(&mut rest, "name"),
        from: take_string(&mut rest, "from"),
        export: take_string(&mut rest, "export"),
        expose_mdx,
        rest,
    })
}

/// `_split_components`: strings are directories, mappings are specs.
pub(crate) fn parse_components(
    raw: Option<&Value>,
    warnings: &mut Vec<String>,
) -> Result<ComponentsConfig, ConfigError> {
    let entries = match raw {
        None | Some(Value::Null) => return Ok(ComponentsConfig::default()),
        Some(Value::Sequence(entries)) => entries,
        Some(_) => {
            return Err(ConfigError::field(
                "components",
                "components must be a list of directory paths or component specs",
            ))
        }
    };
    let mut components = ComponentsConfig::default();
    for (index, entry) in entries.iter().enumerate() {
        match entry {
            Value::String(dir) => components.dirs.push(dir.clone()),
            Value::Mapping(_) => {
                warn_unknown_spec_keys(entry, index, warnings);
                components.specs.push(normalize_spec(entry)?);
            }
            other => return Err(entry_error(other)),
        }
    }
    Ok(components)
}

impl ComponentsConfig {
    /// Anchor every directory and spec source (`from`, else legacy `path`) on `base`.
    pub(crate) fn resolved(&self, base: &Path) -> ComponentsConfig {
        let mut out = self.clone();
        for dir in &mut out.dirs {
            *dir = join_string(base, dir);
        }
        for spec in &mut out.specs {
            if let Some(from) = &spec.from {
                spec.from = Some(join_string(base, from));
            } else if !spec.rest.contains_key("from") {
                if let Some(serde_json::Value::String(path)) = spec.rest.get("path") {
                    let joined = join_string(base, path);
                    spec.rest
                        .insert("path".to_string(), serde_json::Value::String(joined));
                }
            }
        }
        out
    }

    /// Every resolved directory and spec source stays inside the project. A
    /// `components:` entry is trusted frontend code like a theme package, so
    /// it is held to the containment rule every other path already obeys.
    pub(crate) fn validate_contained(&self, root: &Path) -> Result<(), ConfigError> {
        let root = crate::paths::canonicalize_lenient(root);
        let check = |raw: &str, label: &str| -> Result<(), ConfigError> {
            if raw.is_empty() {
                return Ok(());
            }
            if crate::paths::canonicalize_lenient(Path::new(raw)).starts_with(&root) {
                return Ok(());
            }
            Err(ConfigError::field(
                label,
                format!("{label} must stay within the project directory: {raw}"),
            ))
        };
        for dir in &self.dirs {
            check(dir, "components")?;
        }
        for spec in &self.specs {
            let label = match &spec.name {
                Some(name) => format!("components.{name}"),
                None => "components".to_string(),
            };
            if let Some(from) = &spec.from {
                check(from, &label)?;
            } else if let Some(serde_json::Value::String(path)) = spec.rest.get("path") {
                check(path, &label)?;
            }
        }
        Ok(())
    }
}

#[cfg(test)]
#[path = "components_tests.rs"]
mod tests;
