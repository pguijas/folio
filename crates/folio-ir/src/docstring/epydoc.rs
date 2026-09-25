//! Epydoc fields (`@param x:`), ported only as far as `auto` needs to weigh the
//! style against the others. Port of `docstring_parser/epydoc.py`.

use std::sync::LazyLock;

use regex::Regex;

use super::{clean_continuation, cleandoc, Docstring, Meta, ParseError, ParsedStyle};

static FIELD_START: LazyLock<Regex> = LazyLock::new(|| Regex::new("(?m)^@").expect("field"));
static PARAM: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(param|keyword|type)(\s+[_A-z][_A-z0-9]*\??):").expect("param"));
static ATTRIBUTE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(ivar|cvar|var)(\s+[_A-z][_A-z0-9]*\??):").expect("attribute"));
static RAISE: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(raise)(\s+[_A-z][_A-z0-9]*\??)?:").expect("raise"));
static RETURN: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(return|rtype|yield|ytype):").expect("return"));
static META: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"([_A-z][_A-z0-9]+)((\s+[_A-z][_A-z0-9]*\??)*):").expect("meta"));
static DEFAULTS_TO: LazyLock<Regex> =
    LazyLock::new(|| Regex::new(r"(?s)^.*defaults to (.+)").expect("defaults to"));

const RESERVED: &[&str] = &[
    "param", "ivar", "cvar", "var", "keyword", "type", "return", "rtype", "yield", "ytype",
];

#[derive(PartialEq, Eq, Clone, Copy)]
enum Base {
    Param,
    Attribute,
    Raise,
    Return,
    Meta,
}

struct Field {
    base: Base,
    key: String,
    args: Vec<String>,
    desc: String,
}

#[derive(Default)]
struct Info {
    type_name: Option<String>,
    description: Option<String>,
    is_generator: Option<bool>,
}

pub(crate) fn parse(text: &str) -> Result<Docstring, ParseError> {
    if text.is_empty() {
        return Ok(Docstring::from_description("", ParsedStyle::Epydoc));
    }
    let text = cleandoc(text);
    let (desc_chunk, meta_chunk) = match FIELD_START.find(&text) {
        Some(m) => text.split_at(m.start()),
        None => (text.as_str(), ""),
    };
    let mut doc = Docstring::from_description(desc_chunk, ParsedStyle::Epydoc);

    let starts: Vec<usize> = FIELD_START
        .find_iter(meta_chunk)
        .map(|m| m.start())
        .collect();
    let mut stream: Vec<Field> = Vec::new();
    for (j, &start) in starts.iter().enumerate() {
        let chunk = &meta_chunk[start..starts.get(j + 1).copied().unwrap_or(meta_chunk.len())];
        let error = || ParseError(format!("Error parsing meta information near \"{chunk}\"."));
        let (base, caps) = [
            (Base::Param, &*PARAM),
            (Base::Attribute, &*ATTRIBUTE),
            (Base::Raise, &*RAISE),
            (Base::Return, &*RETURN),
            (Base::Meta, &*META),
        ]
        .into_iter()
        .find_map(|(base, re)| re.captures(chunk).map(|c| (base, c)))
        .ok_or_else(&error)?;
        let key = caps[1].to_string();
        let args: Vec<String> = match base {
            Base::Param | Base::Attribute => vec![caps[2].trim().to_string()],
            Base::Raise => caps
                .get(2)
                .map(|m| vec![m.as_str().trim().to_string()])
                .unwrap_or_default(),
            Base::Return => Vec::new(),
            Base::Meta => {
                if RESERVED.contains(&key.as_str()) {
                    return Err(error());
                }
                caps.get(2)
                    .map(|m| m.as_str().split_whitespace().map(str::to_string).collect())
                    .unwrap_or_default()
            }
        };
        let whole = caps.get(0).expect("match");
        let desc = clean_continuation(chunk[whole.end()..].trim());
        stream.push(Field {
            base,
            key,
            args,
            desc,
        });
    }

    // `@type x:` merges into `@param x:`, `@rtype:` into the return.
    let mut params: Vec<(String, Info)> = Vec::new();
    for field in &stream {
        if !matches!(field.base, Base::Param | Base::Attribute | Base::Return) {
            continue;
        }
        let arg_name = field
            .args
            .first()
            .cloned()
            .unwrap_or_else(|| "return".to_string());
        let info = match params.iter().position(|(n, _)| *n == arg_name) {
            Some(i) => &mut params[i].1,
            None => {
                params.push((arg_name.clone(), Info::default()));
                &mut params.last_mut().expect("pushed").1
            }
        };
        if field.key.contains("type") {
            info.type_name = Some(field.desc.clone());
        } else {
            info.description = Some(field.desc.clone());
        }
        if field.base == Base::Return {
            let is_generator = field.key == "ytype" || field.key == "yield";
            if *info.is_generator.get_or_insert(is_generator) != is_generator {
                return Err(ParseError(format!(
                    "Error parsing meta information for \"{arg_name}\"."
                )));
            }
        }
    }

    let mut done: Vec<String> = Vec::new();
    for field in &stream {
        match field.base {
            Base::Param | Base::Attribute => {
                let arg_name = &field.args[0];
                if done.contains(arg_name) {
                    continue;
                }
                let info = &params
                    .iter()
                    .find(|(n, _)| n == arg_name)
                    .expect("collected")
                    .1;
                let (type_name, is_optional) = match info.type_name.as_deref() {
                    Some(t) => match t.strip_suffix('?') {
                        Some(t) => (Some(t.to_string()), true),
                        None => (Some(t.to_string()), false),
                    },
                    None => (None, false),
                };
                let default = DEFAULTS_TO
                    .captures(&field.desc)
                    .map(|c| c[1].trim_end_matches('.').to_string());
                doc.meta.push(Meta::Param {
                    key: field.key.clone(),
                    arg_name: arg_name.clone(),
                    type_name,
                    description: info.description.clone().unwrap_or_default(),
                    is_optional: Some(is_optional),
                    default,
                });
                done.push(arg_name.clone());
            }
            Base::Return => {
                if done.iter().any(|d| d == "return") {
                    continue;
                }
                let info = &params
                    .iter()
                    .find(|(n, _)| n == "return")
                    .expect("collected")
                    .1;
                doc.meta.push(Meta::Returns {
                    type_name: info.type_name.clone(),
                    description: info.description.clone().unwrap_or_default(),
                    is_generator: info.is_generator.unwrap_or(false),
                    return_name: None,
                });
                done.push("return".to_string());
            }
            Base::Raise => doc.meta.push(Meta::Raises {
                type_name: field.args.first().cloned(),
                description: field.desc.clone(),
            }),
            Base::Meta => doc.meta.push(Meta::Other {
                key: field.key.clone(),
                description: field.desc.clone(),
            }),
        }
    }
    Ok(doc)
}
