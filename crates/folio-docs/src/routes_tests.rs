use super::*;
use crate::fixtures::{module, type_item};
use folio_ir::{Language, TypeKind};

fn in_language(name: &str, language: Language) -> ModuleIR {
    ModuleIR {
        language,
        ..module(name, vec![], vec![])
    }
}

#[test]
fn module_route_namespaces_non_python_languages_and_splits_both_separators() {
    let cases = [
        ("mylib.core", Language::Python, "api-reference/mylib/core"),
        (
            "lib.util",
            Language::Javascript,
            "api-reference/javascript/lib/util",
        ),
        ("geo", Language::Rust, "api-reference/rust/geo"),
        (
            "demo_crate::utils::helpers",
            Language::Rust,
            "api-reference/rust/demo_crate/utils/helpers",
        ),
    ];
    for (name, language, route) in cases {
        assert_eq!(module_route(&in_language(name, language)), route, "{name}");
    }
}

#[test]
fn symbol_prefix_keeps_python_names_and_tags_other_languages() {
    assert_eq!(
        symbol_prefix(&in_language("mylib.core", Language::Python)),
        "mylib.core"
    );
    assert_eq!(
        symbol_prefix(&in_language("lib.util", Language::Javascript)),
        "javascript:lib.util"
    );
    assert_eq!(
        symbol_prefix(&in_language("demo_crate::models", Language::Rust)),
        "rust:demo_crate::models"
    );
}

#[test]
fn type_anchor_is_the_lowercased_label_and_name() {
    assert_eq!(
        type_anchor(&type_item("Options", TypeKind::Interface)),
        "interface-options"
    );
    assert_eq!(
        type_anchor(&type_item("Point", TypeKind::Struct)),
        "struct-point"
    );
    assert_eq!(
        type_anchor(&type_item("Id", TypeKind::TypeAlias)),
        "type-id"
    );
}

#[test]
fn an_impl_anchor_names_the_trait_it_implements() {
    let mut item = type_item("Point<T>", TypeKind::Impl);
    assert_eq!(type_anchor(&item), "impl-point-t");
    item.bases = vec!["fmt::Display".to_string()];
    assert_eq!(type_anchor(&item), "impl-fmt-display-for-point-t");
}

#[test]
fn anchor_slug_keeps_what_the_slugger_keeps() {
    assert_eq!(anchor_slug("Calculator"), "calculator");
    assert_eq!(anchor_slug("snake_case"), "snake_case");
    assert_eq!(anchor_slug("$jq.fn"), "jq-fn");
    assert_eq!(anchor_slug("Größe"), "größe");
    assert_eq!(member_anchor("calculator", "Add"), "calculator-add");
}
