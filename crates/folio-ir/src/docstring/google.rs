//! Google-style sections (`Args:`, `Returns:`, ...). Port of `docstring_parser/google.py`,
//! plus `Note:`/`Notes:` as sections (the docs promise them; the library dropped them)
//! and the prose sections napoleon reads: `Warning(s):`, `See Also:`, `References:`,
//! `Todo:` and `Deprecated:`.

use std::sync::LazyLock;

use regex::Regex;

use super::{clean_continuation, cleandoc, Docstring, Meta, ParseError, ParsedStyle};

#[derive(Clone, Copy, PartialEq, Eq)]
enum SectionType {
    Singular,
    Multiple,
    SingularOrMultiple,
}

use SectionType::*;

const SECTIONS: &[(&str, &str, SectionType)] = &[
    ("Arguments", "param", Multiple),
    ("Args", "param", Multiple),
    ("Parameters", "param", Multiple),
    ("Params", "param", Multiple),
    ("Raises", "raises", Multiple),
    ("Exceptions", "raises", Multiple),
    ("Except", "raises", Multiple),
    ("Attributes", "attribute", Multiple),
    ("Example", "examples", Singular),
    ("Examples", "examples", Singular),
    ("Returns", "returns", SingularOrMultiple),
    ("Yields", "yields", SingularOrMultiple),
    ("Note", "note", Singular),
    ("Notes", "note", Singular),
    ("Warning", "warnings", Singular),
    ("Warnings", "warnings", Singular),
    ("See Also", "see_also", Singular),
    ("References", "references", Singular),
    ("Todo", "todo", Singular),
    ("Deprecated", "deprecation", Singular),
];

static TITLES: LazyLock<Regex> = LazyLock::new(|| {
    let titles: Vec<&str> = SECTIONS.iter().map(|(t, _, _)| *t).collect();
    Regex::new(&format!(
        "(?m)^({}):[ \\t\\r\\x0c\\x0b]*$",
        titles.join("|")
    ))
    .expect("google titles")
});
static TYPED_ARG: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^\s*(.+?)\s*\(\s*(.*[^\s]+)\s*\)").expect("typed arg"));
static ARG_DEFAULT: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^.*\. Defaults to (.+)\.").expect("arg default"));
static MULTIPLE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"^(?:\s*[^:\s]+:|[^:]*\]:.*)").expect("multiple"));

fn section(title: &str) -> (&'static str, SectionType) {
    SECTIONS
        .iter()
        .find(|(t, _, _)| *t == title)
        .map(|(_, key, ty)| (*key, *ty))
        .expect("title comes from the titles regex")
}

pub(crate) fn parse(text: &str) -> Result<Docstring, ParseError> {
    if text.is_empty() {
        return Ok(Docstring::from_description("", ParsedStyle::Google));
    }
    let text = cleandoc(text);
    let (desc_chunk, meta_chunk) = match TITLES.find(&text) {
        Some(m) => text.split_at(m.start()),
        None => (text.as_str(), ""),
    };
    let mut doc = Docstring::from_description(desc_chunk, ParsedStyle::Google);

    let matches: Vec<(usize, usize, &str)> = TITLES
        .captures_iter(meta_chunk)
        .map(|c| {
            let whole = c.get(0).expect("match");
            (
                whole.start(),
                whole.end(),
                c.get(1).expect("title").as_str(),
            )
        })
        .collect();
    if matches.is_empty() {
        return Ok(doc);
    }

    // Chunks keyed by title: a repeated title replaces the earlier chunk in place.
    let mut chunks: Vec<(&str, &str)> = Vec::new();
    for (j, &(_, end, title)) in matches.iter().enumerate() {
        let next_start = matches.get(j + 1).map_or(meta_chunk.len(), |m| m.0);
        let mut details = &meta_chunk[end..next_start];
        // Unknown meta: anything from the first column-zero line on is dropped.
        let column_zero = details.match_indices('\n').find(|(i, _)| {
            details[i + 1..]
                .chars()
                .next()
                .is_some_and(|c| !c.is_whitespace())
        });
        if let Some((pos, _)) = column_zero {
            details = &details[..pos];
        }
        let chunk = details.trim_matches('\n');
        match chunks.iter_mut().find(|(t, _)| *t == title) {
            Some(slot) => slot.1 = chunk,
            None => chunks.push((title, chunk)),
        }
    }

    for (title, chunk) in chunks {
        let (_, section_type) = section(title);
        // The item indent is that of the first non-blank line; a whitespace-only
        // line before it would otherwise swallow every item.
        let first_item_line = chunk
            .lines()
            .find(|l| !l.trim().is_empty())
            .unwrap_or(chunk);
        let indent: &str =
            &first_item_line[..first_item_line.len() - first_item_line.trim_start().len()];
        if section_type != Multiple {
            doc.meta.push(build_meta(&cleandoc(chunk), title)?);
            continue;
        }
        // Items start at every line with exactly this indent followed by non-space
        // (`^<indent>(?=\S)`, multiline). ponytail: a line scan instead of a regex
        // compiled per chunk; an indent spanning lines would need the regex form.
        let mut starts: Vec<usize> = Vec::new();
        let mut pos = 0;
        for line in chunk.split_inclusive('\n') {
            let is_item = line
                .strip_prefix(indent)
                .and_then(|rest| rest.chars().next())
                .is_some_and(|c| !c.is_whitespace());
            if is_item {
                starts.push(pos + indent.len());
            }
            pos += line.len();
        }
        if starts.is_empty() {
            return Err(ParseError(format!(
                "No specification for \"{title}\": \"{chunk}\""
            )));
        }
        for (j, &start) in starts.iter().enumerate() {
            let end = starts
                .get(j + 1)
                .map_or(chunk.len(), |&next| next - indent.len());
            let part = chunk[start..end].trim_matches('\n');
            doc.meta.push(build_meta(part, title)?);
        }
    }
    Ok(doc)
}

fn build_meta(text: &str, title: &str) -> Result<Meta, ParseError> {
    let (key, section_type) = section(title);
    if section_type == Singular || (section_type == SingularOrMultiple && !MULTIPLE.is_match(text))
    {
        return Ok(single_meta(key, text));
    }
    let Some((before, desc)) = text.split_once(':') else {
        return Err(ParseError(format!("Expected a colon in {text:?}.")));
    };
    let before = match before.split_once('\n') {
        Some((first, rest)) if !before.is_empty() => format!("{first}{}", cleandoc(rest)),
        _ => before.to_string(),
    };
    let desc = if desc.is_empty() {
        String::new()
    } else {
        let desc = desc.strip_prefix(' ').unwrap_or(desc);
        clean_continuation(desc).trim_matches('\n').to_string()
    };
    Ok(multi_meta(key, before, desc))
}

fn single_meta(key: &str, desc: &str) -> Meta {
    match key {
        "returns" | "yields" => Meta::Returns {
            type_name: None,
            description: desc.to_string(),
            is_generator: key == "yields",
            return_name: None,
        },
        "raises" => Meta::Raises {
            type_name: None,
            description: desc.to_string(),
        },
        "examples" => Meta::Example {
            snippet: None,
            description: desc.to_string(),
        },
        _ => Meta::Other {
            key: key.to_string(),
            description: desc.to_string(),
        },
    }
}

fn multi_meta(key: &str, before: String, desc: String) -> Meta {
    match key {
        "param" | "attribute" => {
            let (arg_name, type_name, is_optional) = match TYPED_ARG.captures(&before) {
                Some(caps) => {
                    let mut type_name = caps[2].to_string();
                    let is_optional = if let Some(t) = type_name.strip_suffix(", optional") {
                        type_name = t.to_string();
                        true
                    } else if let Some(t) = type_name.strip_suffix('?') {
                        type_name = t.to_string();
                        true
                    } else {
                        false
                    };
                    (caps[1].to_string(), Some(type_name), Some(is_optional))
                }
                None => (before, None, None),
            };
            let default = ARG_DEFAULT.captures(&desc).map(|c| c[1].to_string());
            Meta::Param {
                key: key.to_string(),
                arg_name,
                type_name,
                description: desc,
                is_optional,
                default,
            }
        }
        "returns" | "yields" => Meta::Returns {
            type_name: Some(before),
            description: desc,
            is_generator: key == "yields",
            return_name: None,
        },
        "raises" => Meta::Raises {
            type_name: Some(before),
            description: desc,
        },
        _ => Meta::Other {
            key: key.to_string(),
            description: desc,
        },
    }
}
