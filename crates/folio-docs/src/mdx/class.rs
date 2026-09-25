//! One class section: the `ClassOverview` card, prose, examples and notes, the
//! attributes table, methods at the same heading level and inner classes one
//! level deeper.

use folio_ir::ClassIR;
use folio_mdx::escape_jsx_attr;

use super::function::render_function;
use super::type_item::{cell, member_table};
use super::{compact_list, json_str, prose, tail, Page};
use crate::routes::member_anchor;

/// `id` is the anchor the symbol index points at: the class name, and
/// `outer-inner` for an inner class; its methods sit at `id-method` (a
/// static method that shares its name with an instance one at
/// `id-static-method`).
pub(super) fn render_class(cls: &ClassIR, level: usize, page: &Page, id: &str) -> String {
    let bases = match page.opts.symbol_index {
        Some(_) if !cls.bases.is_empty() => compact_list(cls.bases.iter().map(|base| {
            let mut entry = format!("{{\"name\": {}", json_str(base));
            if let Some(href) = page.resolve(base) {
                entry.push_str(&format!(", \"href\": {}", json_str(&href)));
            }
            entry + "}"
        })),
        _ => compact_list(cls.bases.iter().map(|base| json_str(base))),
    };
    let decorators = compact_list(cls.decorators.iter().map(|d| json_str(d)));
    let source = if cls.source_file.is_empty() {
        String::new()
    } else {
        page.source_link(&cls.source_file, cls.line_number)
    };
    // The card is no heading: an empty element before it carries the id.
    let mut parts = vec![
        format!("<span id=\"{}\" />\n", escape_jsx_attr(id)),
        format!(
            "<ClassOverview name=\"{}\" bases={{{bases}}} decorators={{{decorators}}} />{source}\n",
            escape_jsx_attr(&cls.name)
        ),
    ];
    parts.extend(prose(&cls.docstring, level + 1));
    parts.extend(tail(&cls.docstring, page));
    if !cls.class_vars.is_empty() {
        parts.push(format!(
            "{}\n",
            member_table("Attribute", &cls.class_vars, cell)
        ));
    }
    // A JavaScript class may have an instance and a static member of one
    // name; the static one's id says so, so the two never share an id.
    let is_static = |method: &folio_ir::FunctionIR| method.visibility == "static";
    parts.extend(cls.methods.iter().map(|method| {
        let shared = is_static(method)
            && cls
                .methods
                .iter()
                .any(|other| other.name == method.name && !is_static(other));
        let name = if shared {
            format!("static {}", method.name)
        } else {
            method.name.clone()
        };
        render_function(method, level, page, &member_anchor(id, &name))
    }));
    parts.extend(
        cls.inner_classes
            .iter()
            .map(|inner| render_class(inner, level + 1, page, &member_anchor(id, &inner.name))),
    );
    parts.join("\n")
}
