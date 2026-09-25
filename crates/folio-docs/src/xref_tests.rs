use super::*;
use crate::fixtures::{class, function, module, type_item};
use folio_ir::{Language, TypeKind};

fn sample_modules() -> Vec<ModuleIR> {
    let mut class_ir = class("ClassIR", &[], vec![]);
    class_ir.inner_classes = vec![class("Meta", &[], vec![])];
    vec![
        module(
            "folio_docs.config",
            vec![class("Config", &[], vec![])],
            vec![function("load_config", vec![], None)],
        ),
        module(
            "folio_docs.ir",
            vec![
                class("ModuleIR", &[], vec![]),
                class("FunctionIR", &[], vec![]),
                class_ir,
            ],
            vec![],
        ),
        module(
            "folio_docs.build",
            vec![],
            vec![function("run_build", vec![], None)],
        ),
    ]
}

fn javascript_module() -> ModuleIR {
    let mut greet = function("greet", vec![], None);
    greet.signature = "export function greet(widget)".to_string();
    ModuleIR {
        language: Language::Javascript,
        types: vec![type_item("Options", TypeKind::Interface)],
        ..module("lib.util", vec![class("Widget", &[], vec![])], vec![greet])
    }
}

#[test]
fn index_maps_modules_classes_functions_and_inner_classes() {
    let index = build_symbol_index(&sample_modules(), "/docs");
    let expected = [
        ("folio_docs.config", "/docs/api-reference/folio_docs/config"),
        (
            "folio_docs.config.Config",
            "/docs/api-reference/folio_docs/config#config",
        ),
        (
            "folio_docs.config.load_config",
            "/docs/api-reference/folio_docs/config#load_config",
        ),
        (
            "folio_docs.ir.ClassIR.Meta",
            "/docs/api-reference/folio_docs/ir#classir-meta",
        ),
    ];
    for (fqn, url) in expected {
        assert_eq!(index.get(fqn).map(String::as_str), Some(url), "{fqn}");
    }
    assert!(build_symbol_index(&[], "/docs").is_empty());
}

#[test]
fn index_follows_the_docs_route_base_and_defaults_it() {
    let index = build_symbol_index(&sample_modules(), "/reference/docs/");
    assert_eq!(
        index["folio_docs.config.Config"],
        "/reference/docs/api-reference/folio_docs/config#config"
    );
    assert_eq!(
        build_symbol_index(&sample_modules(), "")["folio_docs.config"],
        "/docs/api-reference/folio_docs/config"
    );
}

#[test]
fn index_prefixes_non_python_keys_with_the_language() {
    let index = build_symbol_index(
        &[module("mylib.core", vec![], vec![]), javascript_module()],
        "/docs",
    );
    assert_eq!(index["mylib.core"], "/docs/api-reference/mylib/core");
    assert!(!index.contains_key("lib.util"));
    assert_eq!(
        index["javascript:lib.util"],
        "/docs/api-reference/javascript/lib/util"
    );
    assert_eq!(
        index["javascript:lib.util.greet"],
        "/docs/api-reference/javascript/lib/util#greet"
    );
    assert_eq!(
        index["javascript:lib.util.Widget"],
        "/docs/api-reference/javascript/lib/util#widget"
    );
    assert_eq!(
        index["javascript:lib.util.Options"],
        "/docs/api-reference/javascript/lib/util#interface-options"
    );
}

#[test]
fn resolve_type_link_table() {
    let index = build_symbol_index(&sample_modules(), "/docs");
    let config = Some("/docs/api-reference/folio_docs/config#config");
    let cases = [
        ("folio_docs.config.Config", "folio_docs.build", config),
        ("Config", "folio_docs.config", config),
        ("Config", "folio_docs.build", config),
        ("list[Config]", "folio_docs.build", config),
        ("Optional[Config]", "folio_docs.build", config),
        ("Config | None", "folio_docs.build", config),
        ("dict[ModuleIR, Config]", "folio_docs.build", None),
        ("dict[str, Config]", "folio_docs.build", config),
        ("str", "folio_docs.config", None),
        ("None", "folio_docs.config", None),
        ("SomethingUnknown", "folio_docs.config", None),
        ("", "folio_docs.config", None),
        ("  ", "folio_docs.config", None),
        ("list[str]", "folio_docs.config", None),
        ("list[Optional[Config]]", "folio_docs.build", config),
        ("'Config'", "folio_docs.build", config),
        ("\"Config\"", "folio_docs.build", config),
        ("\"Optional[Config]\"", "folio_docs.build", config),
        ("'Config' | None", "folio_docs.build", config),
        ("typing.Optional[Config]", "folio_docs.build", config),
        ("t.Dict[str, Config]", "folio_docs.build", config),
        ("list[Config | None]", "folio_docs.build", config),
        ("Literal['Config']", "folio_docs.build", None),
        ("Literal['a'] | Config", "folio_docs.build", config),
        ("Callable[[], Config]", "folio_docs.build", config),
        ("_Private", "folio_docs.config", None),
        (
            "FunctionIR",
            "folio_docs.config",
            Some("/docs/api-reference/folio_docs/ir#functionir"),
        ),
        (
            "folio_docs.config",
            "folio_docs.build",
            Some("/docs/api-reference/folio_docs/config"),
        ),
    ];
    for (type_str, current, expected) in cases {
        assert_eq!(
            resolve_type_link(type_str, &index, current).as_deref(),
            expected,
            "{type_str} from {current}"
        );
    }
}

#[test]
fn ambiguous_names_link_only_from_an_owning_module() {
    let modules = [
        module("pkg.a", vec![class("Helper", &[], vec![])], vec![]),
        module("pkg.b", vec![class("Helper", &[], vec![])], vec![]),
    ];
    let index = build_symbol_index(&modules, "/docs");
    assert_eq!(resolve_type_link("Helper", &index, "pkg.c"), None);
    assert_eq!(
        resolve_type_link("Helper", &index, "pkg.a").as_deref(),
        Some("/docs/api-reference/pkg/a#helper")
    );
    // The parent package owns the name: `pkg.a.sub` finds `pkg.a.Helper`.
    assert_eq!(
        resolve_type_link("Helper", &index, "pkg.a.sub").as_deref(),
        Some("/docs/api-reference/pkg/a#helper")
    );
}

#[test]
fn non_python_modules_resolve_local_symbols() {
    let index = build_symbol_index(&[javascript_module()], "/docs");
    assert_eq!(
        resolve_type_link("Widget", &index, "javascript:lib.util").as_deref(),
        Some("/docs/api-reference/javascript/lib/util#widget")
    );
    assert_eq!(resolve_type_link("Options", &index, "mylib.core"), None);
}

#[test]
fn the_suffix_match_stays_in_the_modules_language() {
    let rust = ModuleIR {
        language: Language::Rust,
        types: vec![
            type_item("Config", TypeKind::Struct),
            type_item("Store", TypeKind::Trait),
        ],
        ..module("demo_crate::models", vec![], vec![])
    };
    let javascript = ModuleIR {
        language: Language::Javascript,
        ..module("lib.client", vec![class("Config", &[], vec![])], vec![])
    };
    let python = module("pkg.models", vec![class("Config", &[], vec![])], vec![]);
    let index = build_symbol_index(&[python, javascript, rust], "/docs");
    let python_config = Some("/docs/api-reference/pkg/models#config");
    let javascript_config = Some("/docs/api-reference/javascript/lib/client#config");
    let cases = [
        // A Python module elsewhere in the package still finds the Python one.
        ("Config", "pkg.users", python_config),
        ("Store", "pkg.users", None),
        ("Config", "javascript:lib.other", javascript_config),
        ("Store", "javascript:lib.other", None),
        (
            "Store",
            "rust:other_crate",
            Some("/docs/api-reference/rust/demo_crate/models#trait-store"),
        ),
    ];
    for (type_str, current, expected) in cases {
        assert_eq!(
            resolve_type_link(type_str, &index, current).as_deref(),
            expected,
            "{type_str} from {current}"
        );
    }
}

#[test]
fn jsdoc_spellings_link_their_one_name() {
    let index = build_symbol_index(&[javascript_module()], "/docs");
    let widget = Some("/docs/api-reference/javascript/lib/util#widget");
    for type_str in [
        "Widget[]",
        "?Widget",
        "!Widget",
        "Widget|null",
        "Widget | undefined",
        "Array<Widget>",
        "Array.<Widget>",
        "Promise<Widget>",
        "Promise<Widget|null>",
        "?Widget[]",
    ] {
        assert_eq!(
            resolve_type_link(type_str, &index, "javascript:lib.app").as_deref(),
            widget,
            "{type_str}"
        );
    }
    assert_eq!(
        resolve_type_link("Map<Widget, Options>", &index, "javascript:lib.app"),
        None
    );
}

#[test]
fn bare_names_come_out_of_generics_and_unions() {
    let cases: [(&str, &[&str]); 12] = [
        ("dict[str, Config]", &["str", "Config"]),
        ("list[Optional[Config]]", &["Config"]),
        ("Config | None", &["Config", "None"]),
        ("Callable[[int, str], bool]", &["[int, str]", "bool"]),
        ("tuple[int, ...]", &["int", "..."]),
        ("Plain", &["Plain"]),
        ("'Config'", &["Config"]),
        ("typing.Optional[\"Config\"]", &["Config"]),
        ("Map<string, Array<Node>>", &["string", "Node"]),
        ("?Node[][]", &["Node"]),
        ("Promise<Node|null>", &["Node", "null"]),
        ("(a: Node) => Edge", &["(a: Node) => Edge"]),
    ];
    for (input, expected) in cases {
        assert_eq!(extract_bare_names(input), expected, "{input}");
    }
    assert_eq!(
        split_respecting_brackets("dict[str, int], list[(a, b)], c"),
        ["dict[str, int]", " list[(a, b)]", " c"]
    );
    assert_eq!(
        split_respecting_brackets("Map<K, V>, (a) => b, c"),
        ["Map<K, V>", " (a) => b", " c"]
    );
    assert_eq!(split_respecting_brackets(""), Vec::<String>::new());
}

#[test]
fn builtins_are_the_python_set_and_javascripts_null_and_undefined() {
    assert_eq!(BUILTINS.len(), 56);
    for name in [
        "str",
        "None",
        "Unpack",
        "Self",
        "Callable",
        "null",
        "undefined",
    ] {
        assert!(BUILTINS.contains(&name), "{name}");
    }
}

#[test]
fn an_impl_block_never_takes_its_types_entry() {
    let mut on_point = type_item("Point", TypeKind::Impl);
    on_point.bases = vec!["Display".to_string()];
    let rust = ModuleIR {
        language: Language::Rust,
        types: vec![
            type_item("Point", TypeKind::Struct),
            type_item("Point", TypeKind::Impl),
            on_point,
        ],
        ..module("geo", vec![], vec![])
    };
    let index = build_symbol_index(&[rust], "/docs");
    assert_eq!(
        index["rust:geo.Point"],
        "/docs/api-reference/rust/geo#struct-point"
    );
    assert_eq!(index.len(), 2);
}
