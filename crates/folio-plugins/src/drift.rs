//! Name drift between the builtin manifest and `mdx-components.tsx`; the prop
//! drift guard is test-only and lives in `tests/prop_drift.rs`.

use std::sync::LazyLock;

use regex::Regex;

use crate::builtins::BUILTIN_COMPONENTS;
use crate::jsscan::{strip_import_statements, strip_js_comments};

/// A shorthand components-mapping entry occupying a whole line (`    Name,`).
static SHORTHAND_ENTRY_RE: LazyLock<Regex> = LazyLock::new(|| {
    Regex::new(r"(?m)^[ \t]*([A-Za-z_$][A-Za-z0-9_$]*),[ \t]*$").expect("static pattern")
});

const MANIFEST: &str = "folio-plugins/src/builtins.rs";

/// The shorthand entry names of an `mdx-components.tsx` text, in order;
/// comments and import statements are ignored.
pub fn template_component_entry_names(mdx_components_text: &str) -> Vec<String> {
    let code = strip_import_statements(&strip_js_comments(mdx_components_text));
    SHORTHAND_ENTRY_RE
        .captures_iter(&code)
        .map(|c| c[1].to_string())
        .collect()
}

/// Bidirectional: manifest names without an entry (manifest order), then
/// entries the manifest does not declare (template order). Empty = agreement.
pub fn check_template_drift(mdx_components_text: &str) -> Vec<String> {
    let template_names = template_component_entry_names(mdx_components_text);
    let mut drift: Vec<String> = BUILTIN_COMPONENTS
        .iter()
        .filter(|c| !template_names.contains(&c.name))
        .map(|c| {
            format!(
                "builtin component '{}' is declared in the manifest ({MANIFEST}) but has no entry in mdx-components.tsx",
                c.name
            )
        })
        .collect();
    drift.extend(
        template_names
            .iter()
            .filter(|name| !BUILTIN_COMPONENTS.iter().any(|c| c.name == **name))
            .map(|name| {
                format!(
                    "component entry '{name}' in mdx-components.tsx is not declared in the builtin manifest ({MANIFEST})"
                )
            }),
    );
    drift
}

#[cfg(test)]
#[path = "drift_tests.rs"]
mod tests;
