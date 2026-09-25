//! `source.*`: the language seam (ids, labels, routes), `LanguageSource` and
//! the `source.<language>` shape.

use indexmap::IndexMap;
use serde::Serialize;
use serde_yaml_ng::{Mapping, Value};

use crate::error::ConfigError;
use crate::slug::title_case;
use crate::value::{field, quoted_value, string_list, warn_unknown_keys};

/// The route prefix of every API reference page.
pub const API_REFERENCE_SLUG: &str = "api-reference";
/// Language ids `source.<id>` accepts, in validation and map order.
pub const LANGUAGE_IDS: [&str; 3] = ["python", "javascript", "rust"];
/// `source.python.docstring_style` when unset.
pub const DEFAULT_DOCSTRING_STYLE: &str = "auto";
/// The documented docstring styles.
pub const DOCSTRING_STYLES: [&str; 3] = ["auto", "google", "numpy"];

/// The display label of a language id; ids outside the table are title-cased.
pub fn language_label(id: &str) -> String {
    match id {
        "python" => "Python".to_string(),
        "javascript" => "JavaScript".to_string(),
        "rust" => "Rust".to_string(),
        other => title_case(other),
    }
}

/// Module page route: Python under `api-reference/`, every other language
/// namespaced under `api-reference/<language>/`.
pub fn default_route(language: &str, module_name: &str) -> String {
    let path = module_name.replace('.', "/");
    if language == "python" {
        format!("{API_REFERENCE_SLUG}/{path}")
    } else {
        format!("{API_REFERENCE_SLUG}/{language}/{path}")
    }
}

/// Configured roots of one language: `source.<language>.paths` / `.exclude`.
#[derive(Debug, Clone, PartialEq, Eq, Default, Serialize)]
pub struct LanguageSource {
    pub paths: Vec<String>,
    pub excludes: Vec<String>,
}

/// The `source:` section: languages (`python` always present, the others when
/// configured, in `LANGUAGE_IDS` order), docs roots and the docstring style.
#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct SourceConfig {
    pub languages: IndexMap<String, LanguageSource>,
    pub docs: Vec<String>,
    pub docstring_style: String,
}

fn parse_python(
    source: &Mapping,
    warnings: &mut Vec<String>,
) -> Result<(LanguageSource, String), ConfigError> {
    let mut style = DEFAULT_DOCSTRING_STYLE.to_string();
    let roots = match field(source, "python") {
        None => LanguageSource::default(),
        Some(Value::Mapping(python)) => {
            warn_unknown_keys(
                python,
                &["paths", "exclude", "docstring_style"],
                "source.python",
                warnings,
            );
            let roots = LanguageSource {
                paths: string_list(python.get("paths"), "source.python.paths")?,
                excludes: string_list(python.get("exclude"), "source.python.exclude")?,
            };
            match field(python, "docstring_style") {
                None => {}
                Some(Value::String(value)) => {
                    if !DOCSTRING_STYLES.contains(&value.as_str()) {
                        warnings.push(format!(
                            "source.python.docstring_style must be one of 'auto', 'google', \
                             'numpy'; got {}; using 'google'",
                            quoted_value(&Value::String(value.clone()))
                        ));
                    }
                    style = value.clone();
                }
                Some(_) => {
                    return Err(ConfigError::field(
                        "source.python.docstring_style",
                        "source.python.docstring_style must be a string",
                    ))
                }
            }
            roots
        }
        Some(list @ Value::Sequence(_)) => LanguageSource {
            paths: string_list(Some(list), "source.python")?,
            excludes: Vec::new(),
        },
        Some(_) => {
            return Err(ConfigError::field(
                "source.python",
                "source.python must be a mapping or a list of strings",
            ))
        }
    };
    Ok((roots, style))
}

fn parse_language(
    source: &Mapping,
    language: &str,
    warnings: &mut Vec<String>,
) -> Result<Option<LanguageSource>, ConfigError> {
    let key = format!("source.{language}");
    let Some(raw) = field(source, language) else {
        return Ok(None);
    };
    let Value::Mapping(raw) = raw else {
        return Err(ConfigError::field(&key, format!("{key} must be a mapping")));
    };
    warn_unknown_keys(raw, &["paths", "exclude"], &key, warnings);
    let paths_key = format!("{key}.paths");
    let Some(paths) = raw.get("paths") else {
        return Err(ConfigError::field(
            &paths_key,
            format!("{paths_key} is required"),
        ));
    };
    if !paths.is_sequence() {
        return Err(ConfigError::field(
            &paths_key,
            format!("{paths_key} must be a list of strings"),
        ));
    }
    Ok(Some(LanguageSource {
        paths: string_list(Some(paths), &paths_key)?,
        excludes: string_list(raw.get("exclude"), &format!("{key}.exclude"))?,
    }))
}

/// Parse the `source:` mapping: python (mapping, list or null), docs, the
/// other languages in `LANGUAGE_IDS` order; unknown keys warn.
pub(crate) fn parse_source(
    source: &Mapping,
    warnings: &mut Vec<String>,
) -> Result<SourceConfig, ConfigError> {
    let (python, docstring_style) = parse_python(source, warnings)?;
    let docs = string_list(source.get("docs"), "source.docs")?;
    let mut languages = IndexMap::new();
    languages.insert("python".to_string(), python);
    for language in LANGUAGE_IDS.iter().skip(1) {
        if let Some(roots) = parse_language(source, language, warnings)? {
            languages.insert(language.to_string(), roots);
        }
    }
    let mut allowed = vec!["docs"];
    allowed.extend(LANGUAGE_IDS);
    warn_unknown_keys(source, &allowed, "source", warnings);
    Ok(SourceConfig {
        languages,
        docs,
        docstring_style,
    })
}

#[cfg(test)]
#[path = "source_tests.rs"]
mod tests;
