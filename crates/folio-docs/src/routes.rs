//! Routes and symbol keys per language: where a module page lives and how its
//! symbols are keyed in the cross-reference index.

use folio_config::default_route;
use folio_ir::{Language, ModuleIR, TypeIR, TypeKind};

/// Content route of a module page: Python under `api-reference/`, every other
/// language under `api-reference/<language>/`. Both `.` and `::` become `/`
/// (a Python name never carries `::`, so one rule serves every parser).
pub fn module_route(module: &ModuleIR) -> String {
    default_route(module.language.id(), &module.name.replace("::", "/"))
}

/// Index key of a module: its name for Python, `<language>:<name>` otherwise,
/// so a `utils` module in two languages stays two keys.
pub fn symbol_prefix(module: &ModuleIR) -> String {
    match module.language {
        Language::Python => module.name.clone(),
        other => format!("{}:{}", other.id(), module.name),
    }
}

/// The docs route base with its trailing `/` stripped; blank means `/docs`.
pub(crate) fn route_base(docs_route_base: &str) -> &str {
    match docs_route_base.trim_end_matches('/') {
        "" => "/docs",
        base => base,
    }
}

/// A heading id as a page writes it (`### \`name\` [#id]`): letters and
/// digits lowercased, `_` kept, every other run one `-`. Nextra's slugger
/// leaves such an id as written, so the index and the page agree.
pub fn anchor_slug(text: &str) -> String {
    let mut slug = String::with_capacity(text.len());
    for ch in text.chars() {
        if ch.is_alphanumeric() || ch == '_' {
            slug.extend(ch.to_lowercase());
        } else if !slug.is_empty() && !slug.ends_with('-') {
            slug.push('-');
        }
    }
    slug.trim_end_matches('-').to_string()
}

/// The id of a member under its owner (`calculator-add`, `struct-point-norm`):
/// a name never holds `-`, so a member id never takes a module function's.
pub fn member_anchor(owner: &str, name: &str) -> String {
    format!("{owner}-{}", anchor_slug(name))
}

/// Heading id of a type item: its label and name (`interface-options`); an
/// `impl` block adds the trait it implements (`impl-display-for-point`).
pub fn type_anchor(item: &TypeIR) -> String {
    match (item.kind, item.bases.first()) {
        (TypeKind::Impl, Some(on)) => anchor_slug(&format!("impl {on} for {}", item.name)),
        (kind, _) => anchor_slug(&format!("{} {}", kind.label(), item.name)),
    }
}

#[cfg(test)]
#[path = "routes_tests.rs"]
mod tests;
