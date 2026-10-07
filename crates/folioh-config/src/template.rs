//! `template.*` normalisers: the docs route base and the deploy base path.

use serde::Serialize;
use serde_yaml_ng::Value;

use crate::error::ConfigError;
use crate::value::{get, warn_unknown_keys};

const FIELD: &str = "template.docs_route_base";

/// `template:` as validated at load; paths are relative until `resolve_paths`.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct TemplateConfig {
    pub path: String,
    pub overlay_path: String,
    pub params: serde_json::Map<String, serde_json::Value>,
    pub docs_route_base: String,
}

impl Default for TemplateConfig {
    fn default() -> Self {
        TemplateConfig {
            path: String::new(),
            overlay_path: String::new(),
            params: serde_json::Map::new(),
            docs_route_base: "/docs".to_string(),
        }
    }
}

/// Parse `template:`; a non-mapping section is the default template.
pub(crate) fn parse_template(
    raw: Option<&Value>,
    warnings: &mut Vec<String>,
) -> Result<TemplateConfig, ConfigError> {
    let Some(template) = raw.and_then(Value::as_mapping) else {
        return Ok(TemplateConfig::default());
    };
    warn_unknown_keys(
        template,
        &["path", "overlay_path", "params", "docs_route_base"],
        "template",
        warnings,
    );
    let path = get(template, "path")
        .as_str()
        .unwrap_or_default()
        .to_string();
    let mut overlay_path = get(template, "overlay_path")
        .as_str()
        .unwrap_or_default()
        .to_string();
    if !overlay_path.is_empty() && !path.is_empty() {
        warnings.push(
            "template.overlay_path is ignored when template.path is set; template.path is a \
             full replacement"
                .to_string(),
        );
        overlay_path.clear();
    }
    let params = match get(template, "params") {
        Value::Null => serde_json::Map::new(),
        params @ Value::Mapping(_) => match serde_json::to_value(params) {
            Ok(serde_json::Value::Object(map)) => map,
            _ => {
                return Err(ConfigError::field(
                    "template.params",
                    "template.params must be JSON-serializable",
                ))
            }
        },
        _ => {
            warnings.push("template.params must be a mapping; ignoring it".to_string());
            serde_json::Map::new()
        }
    };
    Ok(TemplateConfig {
        path,
        overlay_path,
        params,
        docs_route_base: normalize_docs_route_base(get(template, "docs_route_base"))?,
    })
}

/// `template.docs_route_base`: `/`-prefixed, no trailing `/`, never root, no
/// query/fragment, no `.`/`..` segments, each segment a plain URL word; anything that is not a string or is
/// blank falls back to `/docs`.
pub fn normalize_docs_route_base(value: &Value) -> Result<String, ConfigError> {
    let Some(text) = value.as_str() else {
        return Ok("/docs".to_string());
    };
    let path = text.trim();
    if path.is_empty() {
        return Ok("/docs".to_string());
    }
    let non_root = || ConfigError::field(FIELD, format!("{FIELD} must be a non-root URL path"));
    if path == "/" {
        return Err(non_root());
    }
    if path.contains('?') || path.contains('#') {
        return Err(ConfigError::field(
            FIELD,
            format!("{FIELD} cannot include query or fragment"),
        ));
    }
    let path = format!("/{}", path.trim_start_matches('/'));
    let path = path.trim_end_matches('/');
    if path.is_empty() {
        return Err(non_root());
    }
    if path
        .trim_matches('/')
        .split('/')
        .any(|seg| seg == "." || seg == "..")
    {
        return Err(ConfigError::field(
            FIELD,
            format!("{FIELD} cannot contain '.' or '..' segments"),
        ));
    }
    // A segment becomes an `app/` directory and part of every generated URL:
    // Next reads `_x`, `(x)`, `[x]` and `@x` as private, group, dynamic and
    // slot folders, and a quote or backtick would reach generated code.
    let plain = |seg: &str| {
        seg.starts_with(|c: char| c.is_ascii_alphanumeric())
            && seg
                .chars()
                .all(|c| c.is_ascii_alphanumeric() || matches!(c, '-' | '_' | '.' | '~'))
    };
    if !path.trim_start_matches('/').split('/').all(plain) {
        return Err(ConfigError::field(
            FIELD,
            format!(
                "{FIELD} segments must start with a letter or digit and use only letters, \
                 digits, '-', '_', '.' and '~'; got {}",
                crate::value::quoted(path)
            ),
        ));
    }
    Ok(path.to_string())
}

/// `deploy.base_path`: `/`-prefixed without a trailing `/`; blank, root or a
/// non-string becomes `""` (no base path).
pub fn normalize_base_path(value: &Value) -> String {
    let Some(text) = value.as_str() else {
        return String::new();
    };
    let path = text.trim();
    if path.is_empty() || path == "/" {
        return String::new();
    }
    let path = format!("/{}", path.trim_start_matches('/'));
    path.trim_end_matches('/').to_string()
}

#[cfg(test)]
#[path = "template_tests.rs"]
mod tests;

#[cfg(test)]
#[path = "template_section_tests.rs"]
mod section_tests;
