//! Cross-references: the project-wide symbol index (`fqn -> URL`) and the
//! resolution of a type string to one link.

use std::collections::BTreeMap;

use folio_ir::{ClassIR, ModuleIR, TypeKind};

use crate::routes::{
    anchor_slug, member_anchor, module_route, route_base, symbol_prefix, type_anchor,
};

/// Fully-qualified symbol -> site-absolute URL (plus `#anchor`). A `BTreeMap`
/// so its compact JSON is canonical: the manifest hashes it as `symbols`.
pub type SymbolIndex = BTreeMap<String, String>;

/// Python builtins and typing names, and JavaScript's `null` and `undefined`,
/// that never link.
pub const BUILTINS: &[&str] = &[
    "str",
    "int",
    "float",
    "bool",
    "bytes",
    "bytearray",
    "list",
    "dict",
    "set",
    "frozenset",
    "tuple",
    "None",
    "type",
    "object",
    "complex",
    "range",
    "memoryview",
    "slice",
    "property",
    "classmethod",
    "staticmethod",
    "super",
    "Exception",
    "BaseException",
    "Any",
    "Callable",
    "Iterator",
    "Generator",
    "Coroutine",
    "Awaitable",
    "AsyncIterator",
    "AsyncGenerator",
    "Iterable",
    "Sequence",
    "Mapping",
    "MutableMapping",
    "MutableSequence",
    "MutableSet",
    "Optional",
    "Union",
    "Type",
    "ClassVar",
    "Final",
    "Literal",
    "Protocol",
    "TypeVar",
    "TypeAlias",
    "Self",
    "Never",
    "NoReturn",
    "Concatenate",
    "ParamSpec",
    "TypeVarTuple",
    "Unpack",
    "null",
    "undefined",
];

/// Index every module, class (inner classes as `Outer.Inner`), function and
/// type under `docs_route_base` (`/docs` when blank), each at the id its page
/// writes. An `impl` block is not a symbol: it never takes its type's entry.
/// Later duplicates win.
pub fn build_symbol_index(modules: &[ModuleIR], docs_route_base: &str) -> SymbolIndex {
    let base = route_base(docs_route_base);
    let mut index = SymbolIndex::new();
    for module in modules {
        let mod_route = format!("{base}/{}", module_route(module));
        let prefix = symbol_prefix(module);
        index.insert(prefix.clone(), mod_route.clone());
        for class in &module.classes {
            index_class(&mut index, class, &prefix, &mod_route);
        }
        for func in &module.functions {
            index.insert(
                format!("{prefix}.{}", func.name),
                format!("{mod_route}#{}", anchor_slug(&func.name)),
            );
        }
        for item in module.types.iter().filter(|t| t.kind != TypeKind::Impl) {
            index.insert(
                format!("{prefix}.{}", item.name),
                format!("{mod_route}#{}", type_anchor(item)),
            );
        }
    }
    index
}

fn index_class(index: &mut SymbolIndex, class: &ClassIR, parent: &str, mod_route: &str) {
    index_class_at(index, class, parent, mod_route, &anchor_slug(&class.name));
}

/// An inner class sits at `outer-inner`, the id its `ClassOverview` carries.
fn index_class_at(
    index: &mut SymbolIndex,
    class: &ClassIR,
    parent: &str,
    mod_route: &str,
    anchor: &str,
) {
    let fqn = format!("{parent}.{}", class.name);
    index.insert(fqn.clone(), format!("{mod_route}#{anchor}"));
    for inner in &class.inner_classes {
        let inner_anchor = member_anchor(anchor, &inner.name);
        index_class_at(index, inner, &fqn, mod_route, &inner_anchor);
    }
}

/// `head[args]` or `head<args>` with a dotted head (`typing.Optional[Config]`,
/// `Promise<Connection>`, JSDoc's `Array.<Connection>`): the head and the
/// arguments' text.
fn generic_parts(part: &str) -> Option<(&str, &str)> {
    let open = part.find(['[', '<'])?;
    let (head, close) = match part[..open].trim_end() {
        head if part[open..].starts_with('[') => (head, ']'),
        head => (head.strip_suffix('.').unwrap_or(head), '>'),
    };
    let inner = part.strip_suffix(close)?.get(open + 1..)?;
    let is_name = |segment: &str| {
        !segment.is_empty() && segment.chars().all(|c| c.is_alphanumeric() || c == '_')
    };
    (head.split('.').all(is_name) && !inner.trim().is_empty()).then_some((head, inner))
}

/// The text inside one pair of matching quotes (`'Config'`, `"Config"`), or
/// the text as it is.
fn unquote(s: &str) -> &str {
    ['\'', '"']
        .into_iter()
        .find_map(|q| s.strip_prefix(q)?.strip_suffix(q))
        .map_or(s, str::trim)
}

/// A name without JSDoc's leading `?`/`!` or an array's trailing `[]`
/// (`?Connection`, `Connection[]` -> `Connection`).
fn strip_modifiers(mut s: &str) -> &str {
    s = s.trim_start_matches(['?', '!']).trim_start();
    while let Some(rest) = s.strip_suffix("[]") {
        s = rest.trim_end();
    }
    s
}

/// Every candidate name in a type string: union members, and the arguments of
/// generics recursively (`dict[str, Config]` -> `str`, `Config`). Quotes, a
/// leading `?`/`!` and a trailing `[]` come off each name, so `'Config'`,
/// `?Config` and `Config[]` all give `Config`. A `Literal[...]` holds values,
/// not names.
pub fn extract_bare_names(type_str: &str) -> Vec<String> {
    let mut names = Vec::new();
    for part in split_outside_brackets(unquote(type_str.trim()), '|') {
        let part = strip_modifiers(unquote(part.trim()));
        if part.is_empty() {
            continue;
        }
        match generic_parts(part) {
            Some((head, _)) if head.rsplit('.').next() == Some("Literal") => {}
            Some((_, inner)) => {
                for item in split_respecting_brackets(inner) {
                    names.extend(extract_bare_names(item.trim()));
                }
            }
            None => names.push(part.to_string()),
        }
    }
    names
}

/// Split on commas outside `()`/`[]`/`<>`.
pub fn split_respecting_brackets(s: &str) -> Vec<String> {
    split_outside_brackets(s, ',')
}

/// Split on `sep` outside `()`/`[]`/`<>`; the `>` of `->` or `=>` closes nothing.
fn split_outside_brackets(s: &str, sep: char) -> Vec<String> {
    let mut parts = Vec::new();
    let mut current = String::new();
    let mut depth = 0i32;
    let mut prev = '\0';
    for ch in s.chars() {
        match ch {
            '(' | '[' | '<' => depth += 1,
            '>' if prev == '-' || prev == '=' => {}
            ')' | ']' | '>' => depth -= 1,
            _ if ch == sep && depth == 0 => {
                parts.push(std::mem::take(&mut current));
                prev = ch;
                continue;
            }
            _ => {}
        }
        current.push(ch);
        prev = ch;
    }
    if !current.is_empty() {
        parts.push(current);
    }
    parts
}

/// The language of an index key: `""` for Python, which has no `language:`
/// prefix, and `rust` for `rust:a::b`, whose `::` comes after the prefix.
fn key_language(key: &str) -> &str {
    key.split_once(':').map_or("", |(language, _)| language)
}

/// The URL a type string links to, when exactly one non-builtin name in it
/// resolves: direct key, `current_module.name`, the parent package, then a
/// unique `.name` suffix among the keys of the current module's language.
pub fn resolve_type_link(
    type_str: &str,
    index: &SymbolIndex,
    current_module: &str,
) -> Option<String> {
    let type_str = type_str.trim();
    if type_str.is_empty() {
        return None;
    }
    if let Some(url) = index.get(type_str) {
        return Some(url.clone());
    }
    let names = extract_bare_names(type_str);
    let mut candidates = names
        .iter()
        .filter(|n| !BUILTINS.contains(&n.as_str()) && !n.starts_with('_'));
    let name = candidates.next()?;
    if candidates.next().is_some() {
        return None;
    }
    if let Some(url) = index.get(name) {
        return Some(url.clone());
    }
    if let Some(url) = index.get(&format!("{current_module}.{name}")) {
        return Some(url.clone());
    }
    if let Some((parent, _)) = current_module.rsplit_once('.') {
        if let Some(url) = index.get(&format!("{parent}.{name}")) {
            return Some(url.clone());
        }
    }
    let suffix = format!(".{name}");
    let language = key_language(current_module);
    let mut matches = index
        .iter()
        .filter(|(fqn, _)| fqn.ends_with(&suffix) && key_language(fqn) == language)
        .map(|(_, url)| url);
    let first = matches.next()?;
    matches.next().is_none().then(|| first.clone())
}

#[cfg(test)]
#[path = "xref_tests.rs"]
mod tests;
