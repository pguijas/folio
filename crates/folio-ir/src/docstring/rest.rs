//! ReST / Sphinx fields (`:param x:`, `:returns:`, `:rtype:`). Port of
//! `docstring_parser/rest.py`.

use std::sync::LazyLock;

use regex::Regex;

use super::{clean_continuation, cleandoc, Docstring, Meta, ParseError, ParsedStyle};

const PARAM_KEYWORDS: &[&str] = &[
    "param",
    "parameter",
    "arg",
    "argument",
    "attribute",
    "key",
    "keyword",
];
const RAISES_KEYWORDS: &[&str] = &["raises", "raise", "except", "exception"];
const RETURNS_KEYWORDS: &[&str] = &["return", "returns"];
const YIELDS_KEYWORDS: &[&str] = &["yield", "yields"];

static FIELD_START: LazyLock<Regex> = LazyLock::new(|| Regex::new("(?m)^:").expect("field"));
static DEFAULTS_TO: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?s)^.*defaults to (.+)").expect("defaults to"));

pub(crate) fn parse(text: &str) -> Result<Docstring, ParseError> {
    if text.is_empty() {
        return Ok(Docstring::from_description("", ParsedStyle::Rest));
    }
    let text = cleandoc(text);
    let (desc_chunk, meta_chunk) = match FIELD_START.find(&text) {
        Some(m) => text.split_at(m.start()),
        None => (text.as_str(), ""),
    };
    let mut doc = Docstring::from_description(desc_chunk, ParsedStyle::Rest);

    let mut types: Vec<(String, String)> = Vec::new();
    let mut rtypes: Vec<(Option<String>, String)> = Vec::new();
    for chunk in field_chunks(meta_chunk) {
        let Some((args_chunk, desc_chunk)) = chunk.trim_start_matches(':').split_once(':') else {
            return Err(ParseError(format!(
                "Error parsing meta information near \"{chunk}\"."
            )));
        };
        let args: Vec<&str> = args_chunk.split_whitespace().collect();
        let desc = clean_continuation(desc_chunk.trim());
        match args.as_slice() {
            // An empty key (`: : y`) has no field name to build from.
            [] => {
                return Err(ParseError(format!(
                    "Error parsing meta information near \"{chunk}\"."
                )))
            }
            ["type", name] => set(&mut types, (*name).to_string(), desc),
            ["rtype"] => set(&mut rtypes, None, desc),
            ["rtype", name] => set(&mut rtypes, Some((*name).to_string()), desc),
            _ => doc.meta.push(build_meta(&args, desc)?),
        }
    }

    for item in &mut doc.meta {
        match item {
            Meta::Param {
                arg_name,
                type_name,
                ..
            } if type_name.is_none() => {
                *type_name = types
                    .iter()
                    .find(|(n, _)| n == arg_name)
                    .map(|(_, t)| t.clone());
            }
            Meta::Returns {
                type_name,
                return_name,
                ..
            } if type_name.is_none() => {
                *type_name = rtypes
                    .iter()
                    .find(|(n, _)| n == return_name)
                    .map(|(_, t)| t.clone());
            }
            _ => {}
        }
    }
    if !doc.meta.iter().any(|m| matches!(m, Meta::Returns { .. })) {
        for (return_name, type_name) in rtypes {
            doc.meta.push(Meta::Returns {
                type_name: Some(type_name),
                description: String::new(),
                is_generator: false,
                return_name,
            });
        }
    }
    Ok(doc)
}

/// Every run from a line starting with `:` up to the next such line.
fn field_chunks(meta_chunk: &str) -> Vec<&str> {
    let starts: Vec<usize> = FIELD_START
        .find_iter(meta_chunk)
        .map(|m| m.start())
        .collect();
    starts
        .iter()
        .enumerate()
        .map(|(j, &start)| {
            &meta_chunk[start..starts.get(j + 1).copied().unwrap_or(meta_chunk.len())]
        })
        .filter(|chunk| !chunk.is_empty())
        .collect()
}

/// Dict assignment: replace in place or append.
fn set<K: PartialEq>(map: &mut Vec<(K, String)>, key: K, value: String) {
    match map.iter_mut().find(|(k, _)| *k == key) {
        Some(slot) => slot.1 = value,
        None => map.push((key, value)),
    }
}

fn build_meta(args: &[&str], desc: String) -> Result<Meta, ParseError> {
    let key = args[0];
    if PARAM_KEYWORDS.contains(&key) {
        let (arg_name, type_name, is_optional) = match args {
            [_, type_name, arg_name] => match type_name.strip_suffix('?') {
                Some(t) => (*arg_name, Some(t.to_string()), Some(true)),
                None => (*arg_name, Some((*type_name).to_string()), Some(false)),
            },
            [_, arg_name] => (*arg_name, None, None),
            _ => {
                return Err(ParseError(format!(
                    "Expected one or two arguments for a {key} keyword."
                )))
            }
        };
        let default = DEFAULTS_TO
            .captures(&desc)
            .map(|c| c[1].trim_end_matches('.').to_string());
        return Ok(Meta::Param {
            key: key.to_string(),
            arg_name: arg_name.to_string(),
            type_name,
            description: desc,
            is_optional,
            default,
        });
    }
    if RETURNS_KEYWORDS.contains(&key) || YIELDS_KEYWORDS.contains(&key) {
        return Ok(Meta::Returns {
            type_name: one_or_no_argument(args)?.map(str::to_string),
            description: desc,
            is_generator: YIELDS_KEYWORDS.contains(&key),
            return_name: None,
        });
    }
    if RAISES_KEYWORDS.contains(&key) {
        return Ok(Meta::Raises {
            type_name: one_or_no_argument(args)?.map(str::to_string),
            description: desc,
        });
    }
    Ok(Meta::Other {
        key: key.to_string(),
        description: desc,
    })
}

fn one_or_no_argument<'a>(args: &[&'a str]) -> Result<Option<&'a str>, ParseError> {
    match args {
        [_] => Ok(None),
        [_, arg] => Ok(Some(*arg)),
        [key, ..] => Err(ParseError(format!(
            "Expected one or no arguments for a {key} keyword."
        ))),
        [] => unreachable!("a field always has a key"),
    }
}

#[cfg(test)]
#[path = "rest_tests.rs"]
mod tests;
