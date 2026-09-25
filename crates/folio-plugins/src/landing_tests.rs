use super::*;
use crate::hook::Plugin;
use crate::testing::docs_config;
use serde_json::{json, Map, Value};

fn raw(yaml: &str) -> Value {
    serde_yaml_ng::from_str(yaml).unwrap()
}

/// The normalized `landing:` section as JSON plus the warnings, from YAML text.
fn normalize(yaml: &str) -> (Value, Vec<String>) {
    let mut diag = Vec::new();
    let landing = normalize_landing(&raw(yaml), &mut diag);
    (serde_json::to_value(&landing).unwrap(), diag)
}

fn section(yaml: &str) -> (Value, Vec<String>) {
    let (value, diag) = normalize(&format!("sections:\n{yaml}"));
    let sections = value["sections"].as_array().unwrap();
    assert_eq!(sections.len(), 1, "{sections:?}");
    (sections[0].clone(), diag)
}

#[test]
fn enabled_follows_the_bool_shorthand_and_the_enabled_subkey() {
    assert!(landing_enabled(&json!(true)));
    assert!(!landing_enabled(&json!(false)));
    assert!(!landing_enabled(&json!({"enabled": false})));
    assert!(landing_enabled(&json!({"enabled": 0})));
    assert!(landing_enabled(&json!({"enabled": "no"})));
    assert!(landing_enabled(&json!({})));
    assert!(landing_enabled(&json!("yes")));
    let (value, _) = normalize("enabled: false");
    assert_eq!(value["enabled"], json!(false));
    // A non-mapping is `{}` for every other field.
    let (value, diag) = normalize("\"yes\"");
    assert_eq!(value["hero"]["variant"], json!("docs-map"));
    assert!(diag.is_empty());
}

#[test]
fn defaults_and_key_order_match_the_python_shape() {
    let (value, diag) = normalize("{}");
    assert_eq!(
        value,
        json!({
            "enabled": true,
            "hero": {"variant": "docs-map", "tagline": null, "headline": "", "description": "", "notice": {"text": "", "link": ""}},
            "cta": {"primary": {"text": "Get Started", "link": "/docs"}, "secondary": {"text": "", "link": ""}},
            "install": [],
            "features": [],
            "sections": [],
            "comparison": false
        })
    );
    let keys: Vec<&str> = value
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect();
    assert_eq!(
        keys,
        [
            "enabled",
            "hero",
            "cta",
            "install",
            "features",
            "sections",
            "comparison"
        ]
    );
    assert!(diag.is_empty());
    assert_eq!(
        serde_json::to_value(Landing::disabled()).unwrap()["enabled"],
        json!(false)
    );
}

#[test]
fn hero_variants_tagline_notice_and_stage() {
    for (variant, expected) in [
        ("source-pipeline", "source-pipeline"),
        ("build-pipeline", "build-pipeline"),
        ("heartbeat", "heartbeat"),
        ("hologram", "docs-map"),
    ] {
        let (value, diag) = normalize(&format!("hero:\n  variant: \"{variant}\"\n"));
        assert_eq!(value["hero"]["variant"], json!(expected), "{variant}");
        assert_eq!(diag.is_empty(), variant == expected, "{variant}: {diag:?}");
    }
    // An unknown variant falls back and names the valid ones; absent is silent.
    let (_, diag) = normalize("hero:\n  variant: hologram\n");
    assert_eq!(
        diag,
        ["landing: unknown hero variant 'hologram' — using 'docs-map'; valid variants: docs-map, source-pipeline, build-pipeline, heartbeat"]
    );
    let mut diag = Vec::new();
    assert_eq!(landing_hero_variant(&json!(7), &mut diag), "docs-map");
    assert_eq!(diag.len(), 1, "{diag:?}");
    assert!(diag[0].starts_with("landing: unknown hero variant 7 — "));
    let mut diag = Vec::new();
    assert_eq!(landing_hero_variant(&Value::Null, &mut diag), "docs-map");
    assert!(diag.is_empty());
    // An explicit empty tagline is preserved; a non-string becomes "".
    let (value, _) = normalize("hero:\n  tagline: \"\"\n  headline: 42\n");
    assert_eq!(value["hero"]["tagline"], json!(""));
    assert_eq!(value["hero"]["headline"], json!(42));
    let (value, _) = normalize("hero:\n  tagline: [1]\n");
    assert_eq!(value["hero"]["tagline"], json!(""));
    // Notice: text + safe link; empty text degrades both to "".
    let (value, _) = normalize(
        "hero:\n  notice:\n    text: \"New — v1.2 released\"\n    link: \"/docs/changelog\"\n",
    );
    assert_eq!(
        value["hero"]["notice"],
        json!({"text": "New — v1.2 released", "link": "/docs/changelog"})
    );
    let (value, diag) =
        normalize("hero:\n  notice:\n    text: \"\"\n    link: \"javascript:alert(1)\"\n");
    assert_eq!(value["hero"]["notice"], json!({"text": "", "link": ""}));
    assert!(diag.is_empty());
    let (value, diag) =
        normalize("hero:\n  notice:\n    text: \"Go\"\n    link: \"javascript:alert(1)\"\n");
    assert_eq!(value["hero"]["notice"]["link"], json!(""));
    assert_eq!(
            diag,
            ["landing: hero notice 'Go' link must be an http(s) URL or a relative path — using '' instead"]
        );
    // Stage: stripped when present, absent otherwise.
    let (value, _) = normalize("hero:\n  stage: \"  The premise  \"\n");
    assert_eq!(value["hero"]["stage"], json!("The premise"));
    let (value, _) = normalize("hero:\n  headline: \"No stage rail\"\n");
    assert!(value["hero"].get("stage").is_none());
    let (value, _) = normalize("hero:\n  stage: 42\n");
    assert!(value["hero"].get("stage").is_none());
}

#[test]
fn ctas_install_and_features_pass_through() {
    let (value, _) = normalize("cta:\n  primary: {text: Go, link: /start}\n  secondary: nope\ninstall: [\"folio init\", 3]\nfeatures: notalist\n");
    assert_eq!(
        value["cta"],
        json!({"primary": {"text": "Go", "link": "/start"}, "secondary": {"text": "", "link": ""}})
    );
    assert_eq!(value["install"], json!(["folio init", 3]));
    assert_eq!(value["features"], json!("notalist"));
}

#[test]
fn sections_catalog_passes_unknown_types_through_warns_and_drops_non_mappings() {
    let (value, diag) = normalize("sections:\n  - type: stats\n    eyebrow: Project scale\n    items: [{value: \"3\", label: commands}]\n  - type: cta\n    title: Start\n    actions: [{title: Read the docs, href: /docs/}]\n  - \"junk\"\n  - type: unknown\n    keep: me\n");
    let types: Vec<&str> = value["sections"]
        .as_array()
        .unwrap()
        .iter()
        .map(|s| s["type"].as_str().unwrap())
        .collect();
    assert_eq!(types, ["stats", "cta", "unknown"]);
    assert_eq!(value["sections"][2]["keep"], json!("me"));
    assert_eq!(
        value["sections"][1]["actions"],
        json!([{"title": "Read the docs", "href": "/docs/"}])
    );
    assert_eq!(
        diag,
        ["landing: a section has the unknown type 'unknown' — the bundled template does not render it; valid types: cells, comparison, cta, features, funnel, install, link-grid, mechanism, output, pipeline, routes, statement, stats, use-cases"]
    );
    // The removed `boards` and `harness` types are unknown now; so is a typeless section.
    let (value, diag) =
        normalize("sections:\n  - type: boards\n  - type: harness\n  - title: No type\n");
    assert_eq!(value["sections"].as_array().unwrap().len(), 3);
    assert_eq!(diag.len(), 3, "{diag:?}");
    assert!(diag[0].starts_with("landing: a section has the unknown type 'boards' — "));
    assert!(diag[1].starts_with("landing: a section has the unknown type 'harness' — "));
    assert!(diag[2].starts_with("landing: a section has no `type` — "));
    assert_eq!(
        landing_sections(&json!("nope"), &mut Vec::new()),
        Vec::<Map<String, Value>>::new()
    );
}

#[test]
fn shared_actions_are_normalized_for_every_section_type() {
    let (sec, diag) = section("  - type: cta\n    title: Next\n    actions:\n      - title: Explore the docs\n        href: /docs\n        primary: true\n        detail: \"  more  \"\n        external: \"yes\"\n      - title: Missing href, dropped\n      - href: /no-title-dropped\n      - title: Unsafe scheme\n        href: \"javascript:alert(1)\"\n      - \"not-a-mapping\"\n");
    assert_eq!(
        sec["actions"],
        json!([{"title": "Explore the docs", "href": "/docs", "detail": "more", "primary": true}])
    );
    assert_eq!(
            diag,
            [
                "landing: section action 'Missing href, dropped' needs an href — dropped",
                "landing: section action {'href': '/no-title-dropped'} needs a title — dropped",
                "landing: section action 'Unsafe scheme' href must be an http(s) URL or a relative path — using '' instead",
                "landing: section action 'Unsafe scheme' needs an href — dropped",
                "landing: section action 'not-a-mapping' must be a mapping — dropped",
            ]
        );
    let (sec, diag) = section("  - type: cta\n    actions: nope\n");
    assert_eq!(sec["actions"], json!([]));
    assert_eq!(
        diag,
        ["landing: section 'actions' must be a list — ignoring it"]
    );
    // Absent stays absent; `external: true` is kept only when exactly true.
    let (sec, _) = section("  - type: cta\n");
    assert!(sec.get("actions").is_none());
    let (sec, _) = section(
        "  - type: cta\n    actions: [{title: X, href: \"https://x.y\", external: true}]\n",
    );
    assert_eq!(
        sec["actions"],
        json!([{"title": "X", "href": "https://x.y", "external": true}])
    );
}

#[test]
fn statement_section_text_accent_size_and_primary_action() {
    let (sec, diag) = section("  - type: statement\n    size: md\n    description: Lead paragraph.\n    text: \"If it breaks, our own docs break first.\"\n    accent: our own docs\n    actions:\n      - title: Read the docs\n        href: /docs\n      - title: See the plan\n        href: /roadmap\n      - title: Broken\n        href: \"javascript:alert(1)\"\n      - \"not-an-action\"\n");
    assert_eq!(
        sec["text"],
        json!("If it breaks, our own docs break first.")
    );
    assert_eq!(sec["accent"], json!("our own docs"));
    assert_eq!(sec["size"], json!("md"));
    assert_eq!(sec["description"], json!("Lead paragraph."));
    assert_eq!(
        sec["actions"],
        json!([{"title": "Read the docs", "href": "/docs", "primary": true}, {"title": "See the plan", "href": "/roadmap"}])
    );
    assert!(diag.iter().any(|w| w.contains("'Broken'")), "{diag:?}");
    let (sec, _) = section("  - type: statement\n    size: huge\n    text: [1, 2]\n    accent: {a: 1}\n    actions: nope\n");
    assert!(sec.get("size").is_none());
    assert_eq!(sec["text"], json!(""));
    assert_eq!(sec["accent"], json!(""));
    assert_eq!(sec["actions"], json!([]));
    // A configured `primary: true` survives on a later action; `primary: false`
    // is dropped by the shared actions pass first, so the first kept action
    // is primary either way.
    let (sec, _) = section("  - type: statement\n    actions: [{title: A, href: /a, primary: false}, {title: B, href: /b, primary: true}]\n");
    assert_eq!(
        sec["actions"],
        json!([{"title": "A", "href": "/a", "primary": true}, {"title": "B", "href": "/b", "primary": true}])
    );
}

#[test]
fn cells_section_items_visuals_images_and_junk() {
    let (sec, diag) = section("  - type: cells\n    items:\n      - label: Agents\n        title: llms.txt output\n        description: Every build emits llms.txt.\n        href: /llms.txt\n        link_text: See this site's llms.txt\n        visual: llms\n      - title: No link cell\n        visual: hologram\n      - description: missing title, dropped\n      - \"not-an-item\"\n      - title: Unsafe\n        href: \"javascript:alert(1)\"\n");
    assert_eq!(
        sec["items"],
        json!([
            {"title": "llms.txt output", "label": "Agents", "description": "Every build emits llms.txt.", "link_text": "See this site's llms.txt", "visual": "llms", "href": "/llms.txt"},
            {"title": "No link cell", "label": "", "description": "", "link_text": ""},
            {"title": "Unsafe", "label": "", "description": "", "link_text": ""}
        ])
    );
    assert_eq!(diag, ["landing: cells item 'Unsafe' href must be an http(s) URL or a relative path — using '' instead"]);
    let (sec, diag) = section("  - type: cells\n    items:\n      - title: Maintainers\n        image: /media/maintainers.jpg\n        image_alt: A desk with a terminal open\n      - title: Decorative\n        image: https://example.com/a.png\n      - title: Alt without an image\n        image_alt: orphaned\n      - title: Unsafe src\n        image: \"javascript:alert(1)\"\n");
    let items = sec["items"].as_array().unwrap();
    assert_eq!(items[0]["image"], json!("/media/maintainers.jpg"));
    assert_eq!(items[0]["image_alt"], json!("A desk with a terminal open"));
    assert_eq!(items[1]["image"], json!("https://example.com/a.png"));
    assert!(items[1].get("image_alt").is_none());
    assert!(items[2].get("image").is_none() && items[2].get("image_alt").is_none());
    assert!(items[3].get("image").is_none());
    assert_eq!(diag, ["landing: cells item 'Unsafe src' image must be an http(s) URL or a relative path — using '' instead"]);
    let (sec, _) = section("  - type: cells\n    title: [1, 2]\n    items: not-a-list\n");
    assert!(sec.get("title").is_none());
    assert_eq!(sec["items"], json!([]));
}

#[test]
fn mechanism_section_code_commits_and_pills() {
    let (sec, _) = section("  - type: mechanism\n    code: |-\n      source:\n      + docs: [\"docs/\"]\n    commits:\n      - hash: a3f92c1\n        message: \"docs: move guide source\"\n      - \"not-a-commit\"\n      - hash: 42\n        message: 42\n    pills: [push, 7, build]\n");
    assert_eq!(sec["code_title"], json!("docs.yaml"));
    assert_eq!(sec["code"], json!("source:\n+ docs: [\"docs/\"]"));
    assert_eq!(
        sec["commits"],
        json!([{"hash": "a3f92c1", "message": "docs: move guide source"}])
    );
    assert_eq!(sec["pills"], json!(["push", "build"]));
    assert_eq!(sec["caption"], json!(""));
    let (sec, _) = section(
        "  - type: mechanism\n    pills: not-a-list\n    commits: not-a-list\n    code: 42\n",
    );
    assert_eq!(sec["pills"], json!(["git push", "folio build", "deploy"]));
    assert_eq!(sec["commits"], json!([]));
    assert_eq!(sec["code"], json!(""));
}

#[test]
fn funnel_section_defaults_tiles_and_icons() {
    let (sec, diag) = section("  - type: funnel\n");
    assert_eq!(
        sec,
        json!({"type": "funnel", "command": "folio build", "inputs": [], "outputs": []})
    );
    assert!(diag.is_empty(), "{diag:?}");
    let (sec, _) = section("  - type: funnel\n    eyebrow: The mechanism\n    title: One build, every surface\n    command: folio build --strict\n    inputs:\n      - label: Python\n        detail: parsed, never executed\n        chip: roadmap 0.9\n      - label: TypeScript\n        ghost: true\n      - label: Go\n        ghost: \"yes\"\n      - chip: missing label, dropped\n      - not-an-input\n    outputs:\n      - label: Guides\n        detail: rendered pages\n      - icon: missing label, dropped\n      - not-an-output\n");
    assert_eq!(sec["command"], json!("folio build --strict"));
    assert_eq!(
        sec["inputs"],
        json!([
            {"label": "Python", "ghost": false, "chip": "roadmap 0.9"},
            {"label": "TypeScript", "ghost": true},
            {"label": "Go", "ghost": false}
        ])
    );
    assert_eq!(sec["outputs"], json!([{"label": "Guides"}]));
    let (sec, _) = section("  - type: funnel\n    inputs:\n      - label: Python\n        icon: python\n      - label: Rust\n        icon: rust\n      - label: mystery\n        icon: not-a-mark\n      - label: wrong-type\n        icon: 7\n    outputs:\n      - label: API reference\n        icon: api\n      - label: Markdown pages\n        icon: pages\n      - label: elsewhere\n        icon: nope\n");
    assert_eq!(
        sec["inputs"],
        json!([
            {"label": "Python", "ghost": false, "icon": "python"},
            {"label": "Rust", "ghost": false, "icon": "rust"},
            {"label": "mystery", "ghost": false},
            {"label": "wrong-type", "ghost": false}
        ])
    );
    assert_eq!(
        sec["outputs"],
        json!([
            {"label": "API reference", "icon": "api"},
            {"label": "Markdown pages", "icon": "pages"},
            {"label": "elsewhere"}
        ])
    );
}

#[test]
fn funnel_section_warns_on_and_drops_the_plate_keys() {
    let (sec, diag) = section("  - type: funnel\n    caption: \"FIG. 01\"\n    command_notes: [reads source only]\n    guarantees:\n      - title: Deterministic\n");
    for key in ["caption", "command_notes", "guarantees"] {
        assert!(sec.get(key).is_none(), "{key} reached the template: {sec}");
        assert!(
            diag.iter().any(|d| d.starts_with(&format!(
                "landing: funnel section '{key}' is no longer rendered"
            ))),
            "no warning for {key}: {diag:?}"
        );
    }
    assert_eq!(diag.len(), 3, "{diag:?}");
}

#[test]
fn features_section_variant_visuals_header_and_actions() {
    let (value, _) = normalize("sections:\n  - type: features\n    variant: bento\n    title: Strong beat.\n    title_muted: Muted beat.\n    actions:\n      - title: Explore\n        href: /docs\n      - title: Bad\n        href: \"javascript:alert(1)\"\n    features:\n      - title: Receipts\n        description: Build output, itemized.\n        visual: receipt\n      - title: No vignette\n        visual: sparkles\n      - plain string\n  - type: features\n    variant: grid\n    title_muted: 42\n    actions: nope\n    features: notalist\n");
    let bento = &value["sections"][0];
    let legacy = &value["sections"][1];
    assert_eq!(bento["variant"], json!("bento"));
    assert_eq!(bento["title_muted"], json!("Muted beat."));
    assert_eq!(
        bento["actions"],
        json!([{"title": "Explore", "href": "/docs"}])
    );
    assert_eq!(
        bento["features"],
        json!([{"title": "Receipts", "description": "Build output, itemized.", "visual": "receipt"}, {"title": "No vignette"}, "plain string"])
    );
    assert!(legacy.get("variant").is_none());
    assert!(legacy.get("title_muted").is_none());
    assert_eq!(legacy["actions"], json!([]));
    assert_eq!(legacy["features"], json!("notalist"));
}

#[test]
fn stage_labels_on_sections() {
    let (value, _) = normalize("sections:\n  - type: statement\n    stage: The mechanism\n    text: Thesis.\n  - type: stats\n    stage: \"\"\n  - type: cta\n    stage: 42\n");
    let sections = value["sections"].as_array().unwrap();
    assert_eq!(sections[0]["stage"], json!("The mechanism"));
    assert!(sections[1].get("stage").is_none());
    assert!(sections[2].get("stage").is_none());
}

#[test]
fn comparison_table_normalizes_cells_tools_and_rows() {
    let (value, diag) = normalize("comparison:\n  caption: \"  Capability  \"\n  tools: [Ours, \"  Theirs  \", \"\", 42]\n  rows:\n    - feature: \"  Static export  \"\n      values: [true, \"no\"]\n      note: \"  both ship files  \"\n    - feature: Partial states\n      values: [\"~\", ~]\n    - feature: Word forms\n      values: [\"YES\", \"False\"]\n");
    assert_eq!(
        value["comparison"],
        json!({"caption": "Capability", "tools": ["Ours", "Theirs"], "rows": [
            {"feature": "Static export", "values": [true, false], "note": "both ship files"},
            {"feature": "Partial states", "values": ["~", "~"]},
            {"feature": "Word forms", "values": [true, false]}
        ]})
    );
    assert!(diag.is_empty());
    let (value, diag) = normalize("comparison:\n  tools: [Ours, Theirs]\n  rows:\n    - feature: Kept\n      values: [true, false]\n    - feature: Too few values\n      values: [true]\n    - values: [true, true]\n    - feature: Values are not a list\n      values: \"true\"\n    - not-a-row\n");
    assert_eq!(
        value["comparison"],
        json!({"caption": "", "tools": ["Ours", "Theirs"], "rows": [{"feature": "Kept", "values": [true, false]}]})
    );
    assert_eq!(
        diag,
        ["landing: comparison row 'Too few values' has 1 values for 2 tools; dropping the row"]
    );
    let (value, diag) = normalize("comparison:\n  caption: Capability\n  tools: []\n");
    assert_eq!(value["comparison"], json!(false));
    assert_eq!(diag, ["landing: comparison needs a `tools:` list and at least one usable `rows:` entry; ignoring it"]);
    let (value, diag) = normalize("comparison: false\nsections:\n  - type: features\n    features: [{title: A, description: d}]\n");
    assert_eq!(value["comparison"], json!(false));
    assert!(diag.is_empty());
}

#[test]
fn legacy_comparison_true_still_works_and_warns() {
    let (value, diag) = normalize("comparison: true");
    assert_eq!(value["comparison"], json!(true));
    assert_eq!(diag.len(), 1);
    assert_eq!(
            diag[0],
            "landing: `comparison: true` renders Folio's own table of documentation tools on your landing page. The built-in table is deprecated and will be removed; fill in your own instead: `comparison: {caption, tools: [...], rows: [{feature, values: [...], note}]}` (see https://pguijas.github.io/folio/docs/plugins/landing)"
        );
    assert!(matches!(
        landing_comparison(&json!(true), &mut Vec::new()),
        Comparison::Flag(true)
    ));
    assert!(matches!(
        landing_comparison(&json!("x"), &mut Vec::new()),
        Comparison::Flag(false)
    ));
}

#[test]
fn comparison_section_carries_its_own_table_or_warns() {
    let (sec, diag) = section("  - type: comparison\n    title: Where this fits\n    caption: Capability\n    tools: [Ours, Theirs]\n    rows:\n      - feature: Runs offline\n        values: [true, false]\n");
    assert_eq!(sec["title"], json!("Where this fits"));
    assert_eq!(sec["caption"], json!("Capability"));
    assert_eq!(sec["tools"], json!(["Ours", "Theirs"]));
    assert_eq!(
        sec["rows"],
        json!([{"feature": "Runs offline", "values": [true, false]}])
    );
    assert!(diag.is_empty());
    let (sec, diag) = section("  - type: comparison\n    caption: Capability\n");
    assert!(
        sec.get("caption").is_none() && sec.get("tools").is_none() && sec.get("rows").is_none()
    );
    assert_eq!(
            diag,
            ["landing: a `comparison` section without `tools:` and `rows:` renders Folio's own table of documentation tools on your landing page. The built-in table is deprecated and will be removed; fill in your own instead: `comparison: {caption, tools: [...], rows: [{feature, values: [...], note}]}` (see https://pguijas.github.io/folio/docs/plugins/landing)"]
        );
}

#[test]
fn plugin_writes_extra_only_when_the_key_is_present() {
    let dir = tempfile::tempdir().unwrap();
    let plugin = LandingPlugin;
    assert_eq!(plugin.name(), "landing");
    assert_eq!(plugin.config_keys(), ["landing"]);
    let mut config = docs_config("project: {name: Demo}\n", dir.path());
    let raw: Map<String, Value> =
        serde_json::from_value(json!({"project": {"name": "Demo"}})).unwrap();
    plugin
        .configure(&mut config, &raw, &mut Vec::new())
        .unwrap();
    assert!(!config.extra.contains_key("landing"));
    assert!(!config.landing_enabled);
    assert_eq!(Landing::from_config(&config), Landing::disabled());

    let mut config = docs_config(
        "project: {name: Demo}\nlanding:\n  hero: {variant: heartbeat}\n",
        dir.path(),
    );
    let raw: Map<String, Value> = serde_json::from_value(
        json!({"project": {"name": "Demo"}, "landing": {"hero": {"variant": "heartbeat"}}}),
    )
    .unwrap();
    plugin
        .configure(&mut config, &raw, &mut Vec::new())
        .unwrap();
    assert_eq!(
        config.extra["landing"]["hero"]["variant"],
        json!("heartbeat")
    );
    assert!(config.landing_enabled);
    let landing = Landing::from_config(&config);
    assert!(landing.enabled);
    assert_eq!(landing.hero.variant, "heartbeat");

    let mut config = docs_config("project: {name: Demo}\nlanding: false\n", dir.path());
    let raw: Map<String, Value> =
        serde_json::from_value(json!({"project": {"name": "Demo"}, "landing": false})).unwrap();
    plugin
        .configure(&mut config, &raw, &mut Vec::new())
        .unwrap();
    assert!(!config.landing_enabled);
    assert!(!Landing::from_config(&config).enabled);
}
