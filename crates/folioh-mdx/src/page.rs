//! `MarkdownPage` and reading `.md` files and directories: frontmatter,
//! title and description inference, README to `index` routes.

use std::fs;
use std::path::{Path, PathBuf};

use serde_yaml_ng::Value;

use crate::frontmatter::{parse_frontmatter, split_frontmatter, Frontmatter};
use crate::{re, MdxError};

/// The warning `parse_markdown_directory` emits once when `.rst` files exist.
pub const RST_WARNING: &str = "source.docs supports Markdown build inputs only; convert .rst files to Markdown before adding them.";

/// One authored or generated Markdown page.
#[derive(Debug, Clone, Default, PartialEq)]
pub struct MarkdownPage {
    /// Body without frontmatter, trimmed at both ends.
    pub content: String,
    /// Author keys plus the inferred `title` and `description`.
    pub frontmatter: Frontmatter,
    /// Content route: no leading slash, no `.md` (`guide/quickstart`, `index`).
    pub route: String,
    /// Source path as given to the reader; `""` for generated docs.
    pub source_file: String,
    /// Hidden from the sidebar only (plugin docs).
    pub unlisted: bool,
}

/// The pages of a directory plus the warnings the scan raised.
#[derive(Debug, Default)]
pub struct DirectoryScan {
    pub pages: Vec<MarkdownPage>,
    pub warnings: Vec<String>,
}

/// The first paragraph of a body: lines after the first heading (or before
/// any heading when the body does not start with one), stopping at a blank
/// line or a lone element such as `<OpenApiReference />`, joined with spaces.
pub fn extract_first_paragraph(content: &str) -> String {
    let body = content.trim();
    let starts_with_heading = body.starts_with('#');
    let lone_element = re(r"^</?[A-Za-z][^>]*/?>$");
    let mut paragraph = Vec::new();
    let mut past_heading = false;
    for line in body.split('\n') {
        let stripped = line.trim();
        if stripped.starts_with('#') {
            past_heading = true;
            continue;
        }
        if stripped.is_empty() || lone_element.is_match(stripped) {
            if !paragraph.is_empty() {
                break;
            }
            continue;
        }
        if past_heading || !starts_with_heading {
            paragraph.push(stripped);
        }
    }
    paragraph.join(" ")
}

/// Parses page text: frontmatter split, `title` from the first H1 and
/// `description` from the first paragraph, images dropped and links read as
/// their text, when the author gave none.
/// `route` and `source_file` are left empty for the caller to fill.
pub(crate) fn parse_markdown(raw: &str) -> Result<MarkdownPage, serde_yaml_ng::Error> {
    let (mut frontmatter, content) = match split_frontmatter(raw) {
        Some((yaml, rest)) => (parse_frontmatter(yaml)?, rest),
        None => (Frontmatter::new(), raw),
    };
    if !frontmatter.contains_key("title") {
        if let Some(h1) = re(r"(?m)^#\s+(.+)$").captures(content) {
            frontmatter.insert("title".into(), Value::String(h1[1].trim().to_string()));
        }
    }
    if !frontmatter.contains_key("description") {
        let prose = re(r"(?s)\{/\*.*?\*/\}").replace_all(content, "");
        let paragraph = extract_first_paragraph(&prose);
        let description = re(r"!\[[^\]]*\]\([^)]+\)").replace_all(&paragraph, "");
        // A link reads as its text: the description is plain prose in the
        // page's meta and in `llms.txt`, and the link check reads it too.
        let description = re(r"\[([^\]]*)\]\([^)]+\)").replace_all(&description, "$1");
        let description = description.trim();
        if !description.is_empty() {
            frontmatter.insert("description".into(), Value::String(description.to_string()));
        }
    }
    Ok(MarkdownPage {
        content: content.trim().to_string(),
        frontmatter,
        ..MarkdownPage::default()
    })
}

/// Reads one `.md` file; `route` is the file stem (callers overwrite it) and
/// `source_file` the path as given.
pub fn parse_markdown_file(path: &Path) -> Result<MarkdownPage, MdxError> {
    let raw = fs::read_to_string(path).map_err(|source| MdxError::Io {
        path: path.to_path_buf(),
        source,
    })?;
    // The frontmatter split keys on `\n`; Python's text reader normalised
    // line endings before the regex saw them.
    let raw = raw.replace("\r\n", "\n");
    let mut page = parse_markdown(&raw).map_err(|source| MdxError::Frontmatter {
        path: path.to_path_buf(),
        source,
    })?;
    page.route = path
        .file_stem()
        .map(|stem| stem.to_string_lossy().into_owned())
        .unwrap_or_default();
    page.source_file = path.to_string_lossy().into_owned();
    Ok(page)
}

/// The route a Markdown file at `relative` publishes: `.md` comes off and a
/// README is its folder's `index`.
pub fn source_route(relative: &Path) -> String {
    let mut parts: Vec<String> = relative
        .components()
        .map(|part| part.as_os_str().to_string_lossy().into_owned())
        .collect();
    if let Some(last) = parts.last_mut() {
        if let Some(stem) = last.strip_suffix(".md") {
            *last = stem.to_string();
        }
        if last.to_lowercase() == "readme" {
            *last = "index".to_string();
        }
    }
    parts.join("/")
}

/// Every `*.md` under `dir` in sorted path order, routed with `source_route`
/// and prefixed with `route_prefix/` when one is given; `.rst` files are
/// ignored with one warning.
pub fn parse_markdown_directory(dir: &Path, route_prefix: &str) -> Result<DirectoryScan, MdxError> {
    let mut md_files = Vec::new();
    let mut has_rst = false;
    walk(
        dir,
        &mut |path| match path.extension().and_then(|ext| ext.to_str()) {
            Some("md") => md_files.push(path),
            Some("rst") => has_rst = true,
            _ => {}
        },
    )?;
    md_files.sort();
    let mut pages = Vec::with_capacity(md_files.len());
    for file in md_files {
        let mut page = parse_markdown_file(&file)?;
        let route = source_route(file.strip_prefix(dir).expect("walked under dir"));
        page.route = if route_prefix.is_empty() {
            route
        } else {
            format!("{route_prefix}/{route}")
        };
        pages.push(page);
    }
    let warnings = if has_rst {
        vec![RST_WARNING.to_string()]
    } else {
        Vec::new()
    };
    Ok(DirectoryScan { pages, warnings })
}

fn walk(dir: &Path, visit: &mut dyn FnMut(PathBuf)) -> Result<(), MdxError> {
    let io = |source| MdxError::Io {
        path: dir.to_path_buf(),
        source,
    };
    for entry in fs::read_dir(dir).map_err(io)? {
        let entry = entry.map_err(io)?;
        if entry.file_type().map_err(io)?.is_dir() {
            walk(&entry.path(), visit)?;
        } else {
            visit(entry.path());
        }
    }
    Ok(())
}

#[cfg(test)]
#[path = "page_tests.rs"]
mod tests;
