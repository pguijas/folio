use super::*;

fn page<'a>(route: &'a str, title: &'a str) -> SidebarPage<'a> {
    SidebarPage {
        route,
        title: Some(title),
        unlisted: false,
    }
}

fn unlisted<'a>(route: &'a str, title: &'a str) -> SidebarPage<'a> {
    SidebarPage {
        route,
        title: Some(title),
        unlisted: true,
    }
}

fn module<'a>(route: &'a str, language: &'a str) -> SidebarModule<'a> {
    SidebarModule {
        route_below_api: route,
        language,
    }
}

fn generate(
    nav: &[&str],
    modules: &[SidebarModule],
    pages: &[SidebarPage],
    collapsed: bool,
) -> BTreeMap<String, String> {
    let nav: Vec<String> = nav.iter().map(|s| s.to_string()).collect();
    generate_meta_files(&SidebarInput {
        nav: &nav,
        modules,
        pages,
        default_collapsed: collapsed,
    })
}

/// Top-level `"key": "value"` string entries of a `_meta.ts`, in order.
fn parse(ts: &str) -> Vec<(String, String)> {
    let entry = re("(?m)^  \"([^\"]+)\":\\s*\"([^\"]*)\",?$");
    entry
        .captures_iter(ts)
        .map(|c| (c[1].to_string(), c[2].to_string()))
        .collect()
}

fn keys(ts: &str) -> Vec<String> {
    re("(?m)^  \"([^\"]+)\":")
        .captures_iter(ts)
        .map(|c| c[1].to_string())
        .collect()
}

fn assert_hidden(ts: &str, slug: &str) {
    let pattern = format!(
        "\"{}\": \\{{\n    \"display\": \"hidden\",\n  \\}},",
        regex::escape(slug)
    );
    assert!(re(&pattern).is_match(ts), "{slug} not hidden in:\n{ts}");
}

fn assert_collapsed(ts: &str, slug: &str, title: &str) {
    let expected = format!("  \"{slug}\": {{\n    \"title\": \"{title}\",\n    \"theme\": {{\n      \"collapsed\": true,\n    }},\n  }},");
    assert!(
        ts.contains(&expected),
        "{slug} not a collapsed folder in:\n{ts}"
    );
}

#[test]
fn module_based_api_reference_meta() {
    let modules = [
        module("mylib/utils", "python"),
        module("mylib/core", "python"),
    ];
    let files = generate(&["Introduction", "API Reference"], &modules, &[], false);
    assert_eq!(
        parse(&files["_meta.ts"]),
        vec![("api-reference".to_string(), "Source Code".to_string())]
    );
    let api = &files["api-reference/_meta.ts"];
    assert_hidden(api, "index");
    assert_eq!(parse(api), vec![("mylib".to_string(), "Mylib".to_string())]);
    assert_eq!(
        parse(&files["api-reference/mylib/_meta.ts"]),
        vec![
            ("utils".to_string(), "Utils".to_string()),
            ("core".to_string(), "Core".to_string())
        ]
    );
}

#[test]
fn nav_orders_real_entries_and_ignores_unknown_labels() {
    let pages = [page("index", "Overview"), page("quickstart", "Quick Start")];
    let modules = [module("mylib/core", "python")];
    for (nav, expected) in [
        (
            vec!["API Reference", "Quick Start", "Unknown"],
            vec!["api-reference", "quickstart", "index"],
        ),
        (
            vec!["Guide", "Source Code"],
            vec!["index", "quickstart", "api-reference"],
        ),
        (vec![], vec!["index", "quickstart", "api-reference"]),
    ] {
        let files = generate(&nav, &modules, &pages, false);
        assert_eq!(keys(&files["_meta.ts"]), expected, "nav {nav:?}");
    }
    let files = generate(&["Guide", "Source Code"], &modules, &pages[..1], false);
    assert_eq!(keys(&files["_meta.ts"]), vec!["index", "api-reference"]);
}

#[test]
fn default_collapsed_wraps_folders_and_keeps_leaves_plain() {
    let modules = [
        module("mylib/utils", "python"),
        module("mylib/core", "python"),
    ];
    let files = generate(&[], &modules, &[], true);
    assert_collapsed(&files["_meta.ts"], "api-reference", "Source Code");
    assert_collapsed(&files["api-reference/_meta.ts"], "mylib", "Mylib");
    let mylib = &files["api-reference/mylib/_meta.ts"];
    assert!(mylib.contains("\"utils\": \"Utils\"") && mylib.contains("\"core\": \"Core\""));
    let pages = [
        page("index", "Overview"),
        page("components/index", "Components"),
        page("components/callout", "Callout"),
    ];
    let files = generate(&[], &[], &pages, true);
    assert_collapsed(&files["_meta.ts"], "components", "Components");
    assert!(files["components/_meta.ts"].contains("\"callout\": \"Callout\""));
    for content in files.values() {
        assert!(!content.contains("\"open\"") && !content.contains("\"defaultCollapsed\""));
    }
}

#[test]
fn hierarchical_module_tree_writes_one_meta_per_package() {
    let modules = [
        module("demolib/learning/aggregators/fedavg", "python"),
        module("demolib/learning/aggregators/fedprox", "python"),
        module("demolib/communication/grpc", "python"),
        module("demolib/node", "python"),
    ];
    let files = generate(&["API Reference"], &modules, &[], false);
    assert_eq!(
        keys(&files["api-reference/demolib/_meta.ts"]),
        vec!["learning", "communication", "node"]
    );
    assert_eq!(
        keys(&files["api-reference/demolib/learning/_meta.ts"]),
        vec!["aggregators"]
    );
    assert_eq!(
        keys(&files["api-reference/demolib/learning/aggregators/_meta.ts"]),
        vec!["fedavg", "fedprox"]
    );
    assert_eq!(
        keys(&files["api-reference/demolib/communication/_meta.ts"]),
        vec!["grpc"]
    );
}

#[test]
fn nested_doc_pages_hide_their_index_and_list_siblings() {
    let pages = [
        page("index", "Overview"),
        page("installation", "Installation"),
        page("components/index", "Components"),
        page("components/mermaid", "Mermaid"),
        page("components/callout", "Callout"),
    ];
    let files = generate(&[], &[module("mylib/core", "python")], &pages, false);
    assert_eq!(
        keys(&files["_meta.ts"]),
        vec!["index", "installation", "components", "api-reference"]
    );
    let components = &files["components/_meta.ts"];
    assert_hidden(components, "index");
    assert_eq!(
        parse(components),
        vec![
            ("callout".to_string(), "Callout".to_string()),
            ("mermaid".to_string(), "Mermaid".to_string())
        ]
    );
}

#[test]
fn root_order_is_declared_then_discovery_then_trailing_entries() {
    let pages = [
        page("index", "Overview"),
        page("installation", "Installation"),
        page("quickstart", "Quick Start"),
        page("components/index", "Components"),
        page("introduction", "Introduction"),
    ];
    let files = generate(&[], &[], &pages, false);
    assert_eq!(
            files["_meta.ts"],
            "export default {\n  \"index\": \"Overview\",\n  \"introduction\": \"Introduction\",\n  \"installation\": \"Installation\",\n  \"quickstart\": \"Quick Start\",\n  \"components\": \"Components\",\n}"
        );
    let pages = [
        page("index", "Overview"),
        page("components/index", "Components"),
        page("contributing", "Contributing"),
        page("p2pfl_ws", "P2PFL Web Services"),
        page("tutorials/index", "Tutorials"),
    ];
    let files = generate(&[], &[module("mylib/core", "python")], &pages, false);
    assert_eq!(
        keys(&files["_meta.ts"]),
        vec![
            "index",
            "components",
            "p2pfl_ws",
            "tutorials",
            "contributing",
            "api-reference"
        ]
    );
}

#[test]
fn declared_slugs_keep_their_position_but_use_the_page_title() {
    let pages = [
        page("index", "Introduction"),
        page("installation", "Installation"),
        page("quickstart", "First Experiment"),
    ];
    let files = generate(&[], &[], &pages, false);
    assert_eq!(
        parse(&files["_meta.ts"]),
        vec![
            ("index".to_string(), "Introduction".to_string()),
            ("installation".to_string(), "Installation".to_string()),
            ("quickstart".to_string(), "First Experiment".to_string()),
        ]
    );
}

#[test]
fn deep_nested_docs_generate_one_meta_per_directory() {
    let pages = [
        page("source/index", "Source"),
        page("source/common_errors/index", "Common Errors"),
        page("source/common_errors/tensorflow_hang", "TensorFlow Hang"),
        page("source/components/learner/aggregators", "Aggregators"),
    ];
    let files = generate(&[], &[], &pages, false);
    assert_eq!(
        parse(&files["_meta.ts"]),
        vec![("source".to_string(), "Source".to_string())]
    );
    assert_hidden(&files["source/_meta.ts"], "index");
    assert_hidden(&files["source/common_errors/_meta.ts"], "index");
    assert_eq!(
        parse(&files["source/_meta.ts"]),
        vec![
            ("common_errors".to_string(), "Common Errors".to_string()),
            ("components".to_string(), "Components".to_string())
        ]
    );
    assert_eq!(
        parse(&files["source/common_errors/_meta.ts"]),
        vec![("tensorflow_hang".to_string(), "TensorFlow Hang".to_string())]
    );
    assert_eq!(
        parse(&files["source/components/_meta.ts"]),
        vec![("learner".to_string(), "Learner".to_string())]
    );
    assert_eq!(
        parse(&files["source/components/learner/_meta.ts"]),
        vec![("aggregators".to_string(), "Aggregators".to_string())]
    );
}

#[test]
fn unlisted_pages_and_all_unlisted_folders_are_hidden() {
    let pages = [
        page("index", "Overview"),
        page("guide/intro", "Intro"),
        unlisted("guide/scratch", "Scratch"),
        unlisted("gallery/one-item/compared", "Compared"),
        unlisted("gallery/one-item/notes", "Notes"),
    ];
    let files = generate(&[], &[], &pages, false);
    let root = &files["_meta.ts"];
    assert!(root.contains("\"index\": \"Overview\"") && root.contains("\"guide\": \"Guide\""));
    assert_hidden(root, "gallery");
    let guide = &files["guide/_meta.ts"];
    assert!(guide.contains("\"intro\": \"Intro\""));
    assert_hidden(guide, "scratch");
    assert_hidden(&files["gallery/_meta.ts"], "one-item");
    assert_hidden(&files["gallery/one-item/_meta.ts"], "compared");
    assert_hidden(&files["gallery/one-item/_meta.ts"], "notes");
}

#[test]
fn titles_strip_emoji_and_collapse_whitespace() {
    let pages = [
        page("components/index", "🏛️ Components"),
        page("components/commands", "⌨️ Commands"),
        page("components/state", "🚦 Node State"),
        page(
            "tutorials/certificates",
            "🛡️ Communication Encryption with Mutual TLS",
        ),
    ];
    let files = generate(&[], &[], &pages, false);
    assert_eq!(
        parse(&files["_meta.ts"]),
        vec![
            ("components".to_string(), "Components".to_string()),
            ("tutorials".to_string(), "Tutorials".to_string())
        ]
    );
    assert_eq!(
        parse(&files["components/_meta.ts"]),
        vec![
            ("commands".to_string(), "Commands".to_string()),
            ("state".to_string(), "Node State".to_string())
        ]
    );
    assert_eq!(
        parse(&files["tutorials/_meta.ts"]),
        vec![(
            "certificates".to_string(),
            "Communication Encryption with Mutual TLS".to_string()
        )]
    );
    for content in files.values() {
        assert!(!content.contains('🏛') && !content.contains('⌨') && !content.contains('🛡'));
    }
    for (title, fallback, expected) in [
        (Some("  Quick   Start "), "X", "Quick Start"),
        (Some("🚦"), "Node State", "Node State"),
        (None, "Common Errors", "Common Errors"),
        (Some("   "), "Fallback", "Fallback"),
        (Some("Trade™ → ©"), "X", "Trade™ → ©"),
    ] {
        assert_eq!(sidebar_title(title, fallback), expected);
    }
}

#[test]
fn meta_ts_shape_is_a_stable_template_contract() {
    let pages = [
        page("index", "Overview"),
        page("quickstart", "Quick Start"),
        page("components/index", "Components"),
        page("components/tabs", "Tabs"),
    ];
    let files = generate(&[], &[], &pages, false);
    assert_eq!(
            files["_meta.ts"],
            "export default {\n  \"index\": \"Overview\",\n  \"quickstart\": \"Quick Start\",\n  \"components\": \"Components\",\n}"
        );
    assert_eq!(
            files["components/_meta.ts"],
            "export default {\n  \"index\": {\n    \"display\": \"hidden\",\n  },\n  \"tabs\": \"Tabs\",\n}"
        );
    let mut meta = Meta::new();
    meta.insert(
        "a\"b".to_string(),
        MetaValue::Str("back\\slash".to_string()),
    );
    assert_eq!(
        meta_to_ts(&meta),
        "export default {\n  \"a\\\"b\": \"back\\\\slash\",\n}"
    );
}

#[test]
fn declared_child_groups_order_their_own_pages() {
    type Case = (
        &'static str,
        &'static [(&'static str, &'static str)],
        &'static str,
    );
    let cases: [Case; 2] = [
            (
                "plugins",
                &[("landing", "Landing Page"), ("trust", "Trust & Safety"), ("index", "Plugins"), ("catalog", "Catalog"), ("roadmap", "Roadmap"), ("authoring", "Writing Plugins")],
                "export default {\n  \"index\": {\n    \"display\": \"hidden\",\n  },\n  \"roadmap\": \"Roadmap\",\n  \"landing\": \"Landing Page\",\n  \"catalog\": \"Catalog\",\n  \"authoring\": \"Writing Plugins\",\n  \"trust\": \"Trust & Safety\",\n}",
            ),
            (
                "theming",
                &[("custom-templates", "Custom Templates"), ("theme-packages", "Theme Packages"), ("index", "Theming"), ("personalization", "Personalization")],
                "export default {\n  \"index\": {\n    \"display\": \"hidden\",\n  },\n  \"personalization\": \"Personalization\",\n  \"theme-packages\": \"Theme Packages\",\n  \"custom-templates\": \"Custom Templates\",\n}",
            ),
        ];
    for (dir, entries, expected) in cases {
        let routes: Vec<String> = entries
            .iter()
            .map(|(slug, _)| format!("{dir}/{slug}"))
            .collect();
        let mut pages = vec![page("index", "Overview")];
        pages.extend(
            routes
                .iter()
                .zip(entries)
                .map(|(route, (_, title))| page(route, title)),
        );
        let files = generate(&[], &[], &pages, false);
        assert_eq!(files[&format!("{dir}/_meta.ts")], expected);
    }
}

#[test]
fn declared_order_returns_pairs_at_every_depth_and_nothing_for_undeclared_paths() {
    assert!(declared_order(&[]).contains(&("theming", "Theming")));
    assert_eq!(
        declared_order(&["theming"])
            .iter()
            .map(|(s, _)| *s)
            .collect::<Vec<_>>(),
        vec![
            "index",
            "personalization",
            "theme-packages",
            "custom-templates"
        ]
    );
    let plugins = declared_order(&["plugins"]);
    let slugs: Vec<&str> = plugins.iter().map(|(s, _)| *s).collect();
    assert_eq!(
        slugs.iter().position(|s| *s == "trust"),
        slugs.iter().position(|s| *s == "authoring").map(|i| i + 1)
    );
    assert_eq!(
        &slugs[..4],
        ["index", "roadmap", "openapi", "landing"],
        "the plugins this release ships come first"
    );
    let root: Vec<&str> = declared_order(&[]).iter().map(|(s, _)| *s).collect();
    let at = |slug: &str| root.iter().position(|s| *s == slug).unwrap();
    assert!(at("quickstart") < at("configuration") && at("configuration") < at("components"));
    assert!(at("migration") < at("architecture") && at("troubleshooting") < at("developing"));
    for path in [&["plugins", "landing"][..], &["theming", "nope"], &["nope"]] {
        assert!(declared_order(path).is_empty(), "{path:?}");
    }
}

#[test]
fn language_grouping_only_when_more_than_one_language() {
    let modules = [
        module("rust/geo/shapes", "rust"),
        module("mylib/core", "python"),
        module("javascript/lib/util", "javascript"),
    ];
    let files = generate(&["API Reference"], &modules, &[], true);
    let api = &files["api-reference/_meta.ts"];
    assert_hidden(api, "index");
    assert!(api.contains(
        "  \"---python\": {\n    \"type\": \"separator\",\n    \"title\": \"Python\",\n  },"
    ));
    assert_collapsed(api, "mylib", "Mylib");
    assert_collapsed(api, "rust", "Rust");
    assert_collapsed(api, "javascript", "JavaScript");
    assert_eq!(
        keys(api),
        vec!["index", "---python", "mylib", "rust", "javascript"]
    );
    assert_eq!(
        parse(&files["api-reference/mylib/_meta.ts"]),
        vec![("core".to_string(), "Core".to_string())]
    );
    assert_eq!(
        parse(&files["api-reference/rust/geo/_meta.ts"]),
        vec![("shapes".to_string(), "Shapes".to_string())]
    );
    assert_eq!(
        parse(&files["api-reference/javascript/lib/_meta.ts"]),
        vec![("util".to_string(), "Util".to_string())]
    );
    assert_collapsed(&files["_meta.ts"], "api-reference", "Source Code");

    let files = generate(&[], &[module("rust/geo", "rust")], &[], false);
    let api = &files["api-reference/_meta.ts"];
    assert_hidden(api, "index");
    assert!(!api.contains("separator"));
    assert_eq!(parse(api), vec![("rust".to_string(), "Rust".to_string())]);
    assert_eq!(
        parse(&files["api-reference/rust/_meta.ts"]),
        vec![("geo".to_string(), "Geo".to_string())]
    );

    let files = generate(&[], &[module("mylib/core", "python")], &[], false);
    let api = &files["api-reference/_meta.ts"];
    assert!(!api.contains("separator") && !api.contains("Python"));
    assert_eq!(parse(api), vec![("mylib".to_string(), "Mylib".to_string())]);
}

#[test]
fn empty_inputs_still_produce_the_root_file() {
    let files = generate(&[], &[], &[], false);
    assert_eq!(files.len(), 1);
    assert_eq!(files["_meta.ts"], "export default {\n}");
}

#[test]
fn page_and_folder_sharing_a_slug_render_as_the_folder() {
    let pages = [page("guide", "Guide Page"), page("guide/intro", "Intro")];
    let files = generate(&[], &[], &pages, true);
    assert_collapsed(&files["_meta.ts"], "guide", "Guide");
    assert_eq!(keys(&files["_meta.ts"]), vec!["guide"]);
}
