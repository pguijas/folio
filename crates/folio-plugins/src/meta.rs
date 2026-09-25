//! Non-destructive `_meta.ts` edits: insert or replace one top-level entry,
//! keeping every other line byte for byte (the entry serialization matches the
//! sidebar generator's format).

use std::sync::LazyLock;

use folio_config::slug_label;
use regex::Regex;

use crate::builder::AssetBuilder;
use crate::error::PluginError;

/// The opening of a top-level entry: exactly two spaces, a quoted key, a colon.
static TOP_LEVEL_KEY_RE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r#"^  "((?:[^"\\]|\\.)*)"\s*:"#).expect("static pattern"));

/// The two entry shapes the built-ins write.
pub enum MetaValue {
    Title(String),
    HiddenIndex,
}

fn escape(text: &str) -> String {
    text.replace('\\', "\\\\").replace('"', "\\\"")
}

/// The lines of one entry in folio's `_meta.ts` format.
pub(crate) fn entry_lines(slug: &str, value: &MetaValue) -> Vec<String> {
    let key = escape(slug);
    match value {
        MetaValue::Title(title) => vec![format!("  \"{key}\": \"{}\",", escape(title))],
        MetaValue::HiddenIndex => vec![
            format!("  \"{key}\": {{"),
            "    \"display\": \"hidden\",".to_string(),
            "  },".to_string(),
        ],
    }
}

/// Net brace/bracket depth change of a line, ignoring string literals.
fn brace_delta(line: &str) -> i32 {
    let mut depth = 0;
    let mut in_string = false;
    let mut escaped = false;
    for c in line.chars() {
        if in_string {
            if escaped {
                escaped = false;
            } else if c == '\\' {
                escaped = true;
            } else if c == '"' {
                in_string = false;
            }
        } else if c == '"' {
            in_string = true;
        } else if c == '{' || c == '[' {
            depth += 1;
        } else if c == '}' || c == ']' {
            depth -= 1;
        }
    }
    depth
}

fn top_level_key(line: &str) -> Option<&str> {
    TOP_LEVEL_KEY_RE
        .captures(line)
        .map(|c| c.get(1).unwrap().as_str())
}

/// Insert or replace `slug` in `directory`'s `_meta.ts`; a blank file gets a
/// fresh module, an unrecognized one gets the entry appended.
pub fn merge_meta_entry(
    builder: &mut dyn AssetBuilder,
    directory: &str,
    slug: &str,
    title: &str,
    hidden_index: bool,
) -> Result<(), PluginError> {
    let existing = builder.read_meta(directory)?;
    let entry = entry_lines(slug, &MetaValue::Title(title.to_string()));
    let index = entry_lines("index", &MetaValue::HiddenIndex);
    if existing.trim().is_empty() {
        let mut lines = vec!["export default {".to_string()];
        if hidden_index {
            lines.extend(index);
        }
        lines.extend(entry);
        lines.push("}".to_string());
        return builder.write_meta(directory, &lines.join("\n"));
    }

    let lines: Vec<&str> = existing.lines().collect();
    let open = lines.iter().position(|l| l.trim() == "export default {");
    let close = lines.iter().rposition(|l| l.trim() == "}");
    let (Some(open), Some(close)) = (open, close) else {
        return append(builder, directory, &existing, &entry);
    };
    if close <= open {
        return append(builder, directory, &existing, &entry);
    }

    let body = &lines[open + 1..close];
    let escaped_slug = escape(slug);
    let mut merged: Vec<String> = Vec::new();
    let mut replaced = false;
    let mut position = 0;
    while position < body.len() {
        let line = body[position];
        if !replaced && top_level_key(line) == Some(escaped_slug.as_str()) {
            let mut depth = brace_delta(line);
            position += 1;
            while depth > 0 && position < body.len() {
                depth += brace_delta(body[position]);
                position += 1;
            }
            merged.extend(entry.iter().cloned());
            replaced = true;
            continue;
        }
        merged.push(line.to_string());
        position += 1;
    }
    if !replaced {
        merged.extend(entry.iter().cloned());
    }
    if hidden_index && !body.iter().any(|l| top_level_key(l) == Some("index")) {
        merged.splice(0..0, index);
    }
    let mut serialized: Vec<String> = lines[..=open].iter().map(|l| l.to_string()).collect();
    serialized.extend(merged);
    serialized.extend(lines[close..].iter().map(|l| l.to_string()));
    let mut text = serialized.join("\n");
    if existing.ends_with('\n') {
        text.push('\n');
    }
    builder.write_meta(directory, &text)
}

fn append(
    builder: &mut dyn AssetBuilder,
    directory: &str,
    existing: &str,
    entry: &[String],
) -> Result<(), PluginError> {
    builder.write_meta(
        directory,
        &format!(
            "{}\n{}\n",
            existing.trim_end_matches('\n'),
            entry.join("\n")
        ),
    )
}

/// The sidebar entries for a generated page: the root entry for its first
/// segment (multi-segment routes) and the page entry in its directory.
pub fn write_route_meta(
    builder: &mut dyn AssetBuilder,
    route: &str,
    title: &str,
) -> Result<(), PluginError> {
    let parts: Vec<&str> = route.split('/').filter(|p| !p.is_empty()).collect();
    let Some((slug, directory)) = parts.split_last() else {
        return Ok(());
    };
    if parts.len() > 1 {
        let root_title = if parts[0] == "api-reference" {
            "API Reference".to_string()
        } else {
            slug_label(parts[0])
        };
        merge_meta_entry(builder, "", parts[0], &root_title, false)?;
    }
    let directory = directory.join("/");
    merge_meta_entry(
        builder,
        &directory,
        slug,
        title,
        directory == "api-reference",
    )
}

#[cfg(test)]
#[path = "meta_tests.rs"]
mod tests;
