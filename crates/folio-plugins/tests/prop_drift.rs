//! Test-only prop drift guard:
//! each contract member's manifest props must agree with the props its
//! `template/components/<module>.tsx` source accepts. Never shipped.

use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use folio_plugins::{strip_js_comments, BUILTIN_COMPONENTS};
use indexmap::IndexMap;
use regex::Regex;

fn components_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../template/components")
}

/// Index just past the bracket group opening at `text[start]`.
fn matching_brace(text: &str, start: usize) -> usize {
    let mut depth = 0i32;
    for (index, ch) in text.bytes().enumerate().skip(start) {
        match ch {
            b'{' | b'(' | b'[' | b'<' => depth += 1,
            b'}' | b')' | b']' | b'>' => {
                depth -= 1;
                if depth == 0 {
                    return index + 1;
                }
            }
            _ => {}
        }
    }
    text.len()
}

/// Object type body split into members at depth zero on `;`, `,` or newline.
fn split_members(body: &str) -> Vec<String> {
    let mut members = Vec::new();
    let mut depth = 0i32;
    let mut current = String::new();
    for ch in body.chars() {
        match ch {
            '{' | '(' | '[' | '<' => depth += 1,
            '}' | ')' | ']' | '>' => depth -= 1,
            _ => {}
        }
        if depth == 0 && matches!(ch, ';' | ',' | '\n') {
            members.push(std::mem::take(&mut current));
            continue;
        }
        current.push(ch);
    }
    members.push(current);
    members
        .into_iter()
        .filter(|m| !m.trim().is_empty())
        .collect()
}

fn member_re() -> Regex {
    Regex::new(r#"^\s*(?:"(?P<quoted>[^"]+)"|(?P<bare>[A-Za-z_$][\w$]*))\s*(?P<optional>\?)?\s*:"#)
        .unwrap()
}

/// Member name to "required" for one object type body.
fn object_fields(body: &str) -> IndexMap<String, bool> {
    let re = member_re();
    let mut fields = IndexMap::new();
    for member in split_members(body) {
        if let Some(m) = re.captures(&member) {
            let name = m
                .name("quoted")
                .or_else(|| m.name("bare"))
                .unwrap()
                .as_str();
            fields.insert(name.to_string(), m.name("optional").is_none());
        }
    }
    fields
}

/// The object body of a same-file `interface`/`type` declaration.
fn resolve_alias(source: &str, name: &str) -> Option<String> {
    let re = Regex::new(&format!(
        r"(?:interface\s+{n}\s*|type\s+{n}\s*=\s*)\{{",
        n = regex::escape(name)
    ))
    .unwrap();
    let m = re.find(source)?;
    let open = m.end() - 1;
    Some(source[open + 1..matching_brace(source, open) - 1].to_string())
}

/// The type expression annotating `component`'s destructured props.
fn props_type_text(source: &str, component: &str) -> Option<String> {
    let re = Regex::new(&format!(
        r"(?:export\s+)?(?:default\s+)?function\s+{}\s*\(",
        regex::escape(component)
    ))
    .unwrap();
    let signature = re.find(source)?;
    let params_open = signature.end() - 1;
    let params = &source[params_open + 1..matching_brace(source, params_open) - 1];
    if !params.trim_start().starts_with('{') {
        return None;
    }
    let pattern_start = params.find('{').unwrap();
    let after_pattern = params[matching_brace(params, pattern_start)..].trim_start();
    let rest = after_pattern.strip_prefix(':')?;
    Some(rest.trim().to_string())
}

fn leading_identifier(text: &str) -> Option<&str> {
    Regex::new(r"^[A-Za-z_$][\w$]*")
        .unwrap()
        .find(text)
        .map(|m| m.as_str())
}

fn props_body(code: &str, component: &str) -> Option<String> {
    let type_text = props_type_text(code, component)?;
    if type_text.starts_with('{') {
        return Some(type_text[1..matching_brace(&type_text, 0) - 1].to_string());
    }
    resolve_alias(code, leading_identifier(&type_text)?)
}

/// `component`'s prop names to whether they are required; `None` when the
/// component is not declared in `source`.
fn component_prop_names(source: &str, component: &str) -> Option<IndexMap<String, bool>> {
    let code = strip_js_comments(source);
    props_body(&code, component).map(|body| object_fields(&body))
}

/// Field names of the first object shape a type expression resolves to.
fn type_expression_fields(source: &str, type_text: &str) -> BTreeSet<String> {
    if let Some(brace) = type_text.find('{') {
        let body = &type_text[brace + 1..matching_brace(type_text, brace) - 1];
        return object_fields(body).into_keys().collect();
    }
    let ident = Regex::new(r"[A-Za-z_$][\w$]*").unwrap();
    for identifier in ident.find_iter(type_text) {
        if matches!(
            identifier.as_str(),
            "Array" | "ReadonlyArray" | "React" | "ReactNode"
        ) {
            continue;
        }
        if let Some(body) = resolve_alias(source, identifier.as_str()) {
            return object_fields(&body).into_keys().collect();
        }
    }
    BTreeSet::new()
}

/// For each object-shaped prop, the field names it carries.
fn component_object_field_names(
    source: &str,
    component: &str,
) -> IndexMap<String, BTreeSet<String>> {
    let code = strip_js_comments(source);
    let Some(body) = props_body(&code, component) else {
        return IndexMap::new();
    };
    let re = member_re();
    let mut shapes = IndexMap::new();
    for member in split_members(&body) {
        if let Some(m) = re.captures(&member) {
            let name = m
                .name("quoted")
                .or_else(|| m.name("bare"))
                .unwrap()
                .as_str();
            let fields = type_expression_fields(&code, &member[m.get(0).unwrap().end()..]);
            if !fields.is_empty() {
                shapes.insert(name.to_string(), fields);
            }
        }
    }
    shapes
}

fn manifest_field_names(type_text: &str) -> BTreeSet<String> {
    let Some(brace) = type_text.find('{') else {
        return BTreeSet::new();
    };
    let body = &type_text[brace + 1..matching_brace(type_text, brace) - 1];
    object_fields(body).into_keys().collect()
}

/// Manifest props the component does not accept, component props the
/// manifest omits, optionality mismatches and object-shape field mismatches.
fn check_component_prop_drift(components_dir: &Path) -> Vec<String> {
    let mut drift = Vec::new();
    for component in BUILTIN_COMPONENTS.iter().filter(|c| c.contract) {
        let module = component.import_path.trim_start_matches("@/components/");
        let source_path = components_dir.join(format!("{module}.tsx"));
        let Ok(source) = std::fs::read_to_string(&source_path) else {
            continue;
        };
        let Some(actual) = component_prop_names(&source, &component.name) else {
            continue;
        };
        let declared = &component.props;
        let where_ = format!(
            "{} ({})",
            component.name,
            source_path.file_name().unwrap().to_string_lossy()
        );
        let declared_names: BTreeSet<&String> = declared.keys().collect();
        let actual_names: BTreeSet<&String> = actual.keys().collect();
        for name in declared_names.difference(&actual_names) {
            drift.push(format!(
                "{where_}: manifest declares prop '{name}', which the component does not accept"
            ));
        }
        for name in actual_names.difference(&declared_names) {
            drift.push(format!(
                "{where_}: component accepts prop '{name}', which the manifest does not declare"
            ));
        }
        for name in declared_names.intersection(&actual_names) {
            let manifest_optional = declared[*name].contains("undefined");
            if actual[*name] == manifest_optional {
                let state = if actual[*name] {
                    "required"
                } else {
                    "optional"
                };
                drift.push(format!("{where_}: prop '{name}' is {state} in the component but the manifest says otherwise"));
            }
        }
        for (name, fields) in component_object_field_names(&source, &component.name) {
            let Some(declared_type) = declared.get(&name) else {
                continue;
            };
            let manifest_fields = manifest_field_names(declared_type);
            if manifest_fields.is_empty() {
                continue;
            }
            for field in manifest_fields.difference(&fields) {
                drift.push(format!("{where_}: manifest prop '{name}' declares field '{field}', which the component never reads"));
            }
            for field in fields.difference(&manifest_fields) {
                drift.push(format!("{where_}: component prop '{name}' carries field '{field}', which the manifest does not declare"));
            }
        }
    }
    drift
}

fn fields(pairs: &[(&str, bool)]) -> IndexMap<String, bool> {
    pairs.iter().map(|(k, v)| (k.to_string(), *v)).collect()
}

#[test]
fn inline_destructured_annotation() {
    let source = "\nexport function TimelineItem({\n  date,\n  title,\n  badge,\n  children,\n}: {\n  date: string\n  title: string\n  badge?: string\n  children: React.ReactNode\n}) {\n  return null\n}\n";
    assert_eq!(
        component_prop_names(source, "TimelineItem"),
        Some(fields(&[
            ("date", true),
            ("title", true),
            ("badge", false),
            ("children", true)
        ]))
    );
}

#[test]
fn named_props_interface() {
    let source = "\ninterface CardGridProps {\n  columns?: 2 | 3 | 4\n  children: React.ReactNode\n}\n\nexport function CardGrid({ columns = 3, children }: CardGridProps) {\n  return null\n}\n";
    assert_eq!(
        component_prop_names(source, "CardGrid"),
        Some(fields(&[("columns", false), ("children", true)]))
    );
}

#[test]
fn quoted_prop_name() {
    let source = "\ninterface TabsProps {\n  children: React.ReactNode\n  \"aria-label\"?: string\n}\n\nexport function Tabs({ children }: TabsProps) {\n  return null\n}\n";
    assert_eq!(
        component_prop_names(source, "Tabs"),
        Some(fields(&[("children", true), ("aria-label", false)]))
    );
}

#[test]
fn object_fields_behind_a_named_type_alias_are_resolved() {
    let source = "\ntype ApiModule = {\n  name: string\n  description: string\n  href: string\n  classCount: number\n  functionCount: number\n}\n\nexport function ApiReferenceIndex({ modules }: { modules: ApiModule[] }) {\n  return null\n}\n";
    assert_eq!(
        component_prop_names(source, "ApiReferenceIndex"),
        Some(fields(&[("modules", true)]))
    );
    let shapes = component_object_field_names(source, "ApiReferenceIndex");
    let expected: BTreeSet<String> = ["name", "description", "href", "classCount", "functionCount"]
        .map(String::from)
        .into();
    assert_eq!(shapes["modules"], expected);
}

#[test]
fn unknown_component_returns_nothing() {
    assert_eq!(component_prop_names("export const x = 1\n", "Nope"), None);
}

#[test]
fn manifest_props_match_the_bundled_components() {
    assert_eq!(
        check_component_prop_drift(&components_dir()),
        Vec::<String>::new()
    );
}

#[test]
fn a_renamed_prop_is_reported() {
    let dir = tempfile::tempdir().unwrap();
    for entry in std::fs::read_dir(components_dir()).unwrap() {
        let path = entry.unwrap().path();
        if path.is_file() {
            std::fs::copy(&path, dir.path().join(path.file_name().unwrap())).unwrap();
        }
    }
    let card_grid = dir.path().join("card-grid.tsx");
    let text = std::fs::read_to_string(&card_grid)
        .unwrap()
        .replace("columns", "cols");
    std::fs::write(&card_grid, text).unwrap();
    let drift = check_component_prop_drift(dir.path());
    assert!(
        drift
            .iter()
            .any(|e| e.contains("CardGrid") && e.contains("columns")),
        "{drift:?}"
    );
}
