use serde_json::json;

use crate::docs::testing::{parse_err, parse_ok, parse_yaml};

#[test]
fn dirs_and_specs_are_split_and_expose_is_pruned() {
    let (config, warnings) = parse_yaml(
            "project: {name: C}\ncomponents:\n  - \"docs/components\"\n  - name: Hero\n    from: docs/components/hero.tsx\n    export: Hero\n    expose:\n      mdx: true\n      landing: true\n  - name: Plain\n    from: x.tsx\n    expose:\n      landing: true\n  - name: Odd\n    from: y.tsx\n    expose: true\n    weight: 3\n",
        ).unwrap();
    assert_eq!(
        warnings,
        [
            "Unknown components.Hero.expose keys in docs.yaml: landing",
            "Unknown components.Plain.expose keys in docs.yaml: landing",
            "Unknown components.Odd keys in docs.yaml: weight",
        ]
    );
    assert_eq!(config.components.dirs, ["docs/components"]);
    let specs = &config.components.specs;
    assert_eq!(specs.len(), 3);
    assert_eq!(specs[0].name.as_deref(), Some("Hero"));
    assert_eq!(specs[0].from.as_deref(), Some("docs/components/hero.tsx"));
    assert_eq!(specs[0].export.as_deref(), Some("Hero"));
    assert_eq!(specs[0].expose_mdx, Some(json!(true)));
    assert!(specs[0].rest.is_empty());
    // Serialises as a passthrough mapping, `expose` kept as `{mdx}`.
    assert_eq!(
        serde_json::to_value(&specs[0]).unwrap(),
        json!({"name": "Hero", "from": "docs/components/hero.tsx", "export": "Hero", "expose": {"mdx": true}})
    );
    assert_eq!(
        serde_json::to_value(&specs[2]).unwrap(),
        json!({"name": "Odd", "from": "y.tsx", "expose": true, "weight": 3})
    );
    assert_eq!(specs[1].expose_mdx, None);
    assert!(specs[1].rest.is_empty());
    assert_eq!(specs[2].expose_mdx, None);
    assert_eq!(
        specs[2].rest,
        json!({"expose": true, "weight": 3})
            .as_object()
            .unwrap()
            .clone()
    );
}

#[test]
fn empty_and_malformed_components() {
    assert!(parse_ok("project: {name: C}\ncomponents:\n")
        .components
        .dirs
        .is_empty());
    assert!(parse_ok("project: {name: C}\ncomponents: []\n")
        .components
        .specs
        .is_empty());
    assert_eq!(
        parse_err("project: {name: C}\ncomponents:\n  - 42\n"),
        "components entries must be directory path strings or {name, from} mappings; got: 42"
    );
    assert_eq!(
        parse_err("project: {name: C}\ncomponents:\n  - [a]\n"),
        "components entries must be directory path strings or {name, from} mappings; got: ['a']"
    );
    assert_eq!(
        parse_err("project: {name: C}\ncomponents: \"docs/components\"\n"),
        "components must be a list of directory paths or component specs"
    );
}
