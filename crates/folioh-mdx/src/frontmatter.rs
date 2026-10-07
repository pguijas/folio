//! YAML frontmatter: split the `---` block off a page, parse it, and emit one
//! back.

use std::collections::BTreeMap;

use indexmap::IndexMap;
use serde::de::Error as _;
use serde::Serialize;
use serde_yaml_ng::Value;

/// Author frontmatter: insertion-ordered, values are whatever YAML the author
/// wrote (`sidebar_position: 3` stays a number and is re-emitted as-is).
pub type Frontmatter = IndexMap<String, Value>;

/// Splits `---\n<yaml>\n---\n` off byte 0. Returns `(yaml, rest)`.
pub fn split_frontmatter(raw: &str) -> Option<(&str, &str)> {
    let rest = raw.strip_prefix("---\n")?;
    let end = rest.find("\n---\n")?;
    Some((&rest[..end], &rest[end + 5..]))
}

/// Parses the YAML of a frontmatter block: an empty document is an empty map,
/// anything but a mapping with string keys is an error (duplicate keys too).
pub(crate) fn parse_frontmatter(yaml: &str) -> Result<Frontmatter, serde_yaml_ng::Error> {
    match serde_yaml_ng::from_str::<Value>(yaml)? {
        Value::Null => Ok(Frontmatter::new()),
        Value::Mapping(mapping) => mapping
            .into_iter()
            .map(|(key, value)| match key {
                Value::String(key) => Ok((key, value)),
                other => Err(serde_yaml_ng::Error::custom(format!(
                    "frontmatter keys must be strings, found {other:?}"
                ))),
            })
            .collect(),
        _ => Err(serde_yaml_ng::Error::custom(
            "frontmatter must be a mapping",
        )),
    }
}

/// `---\n<yaml>\n---\n` with keys sorted, ambiguous scalars quoted
/// (`'True'`, `'123'`, `'# hash'`, `'ends in colon:'`), Unicode kept and no
/// line folding.
pub fn render_frontmatter<V: Serialize>(data: &IndexMap<String, V>) -> String {
    let sorted: BTreeMap<&str, &V> = data.iter().map(|(k, v)| (k.as_str(), v)).collect();
    let yaml = serde_yaml_ng::to_string(&sorted).expect("string keys and YAML values serialise");
    format!("---\n{}\n---\n", yaml.trim())
}

#[cfg(test)]
#[path = "frontmatter_tests.rs"]
mod tests;
