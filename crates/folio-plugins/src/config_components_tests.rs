use super::*;
use crate::registry::{ComponentDefinition, ComponentOrigin};
use crate::testing::docs_config;
use std::fs;

fn register(yaml: &str, dir: &std::path::Path) -> (ExtensionRegistry, Vec<String>) {
    let config = docs_config(&format!("project: {{name: Demo}}\n{yaml}"), dir);
    let mut registry = ExtensionRegistry::default();
    let mut diag = Vec::new();
    register_config_components(&mut registry, &config, &mut diag).unwrap();
    (registry, diag)
}

#[test]
fn component_names_derive_from_file_stems() {
    assert_eq!(component_name_from_stem("hero"), "Hero");
    assert_eq!(component_name_from_stem("my-chart"), "MyChart");
    assert_eq!(component_name_from_stem("stat_strip.v2"), "StatStripV2");
    assert_eq!(component_name_from_stem("123"), "123");
}

#[test]
fn named_specs_register_with_import_path_source_and_expose() {
    let dir = tempfile::tempdir().unwrap();
    let component = dir.path().join("hero.tsx");
    fs::write(
        &component,
        "export function Hero() { return <section /> }\n",
    )
    .unwrap();
    let (registry, diag) = register(
            &format!(
                "components:\n  - name: Hero\n    from: {}\n    export: Hero\n    expose: {{mdx: true, landing: true}}\n",
                component.display()
            ),
            dir.path(),
        );
    let hero = &registry.components["Hero"];
    assert_eq!(hero.source_path.as_deref(), Some(component.as_path()));
    assert_eq!(hero.import_path, "@/components/__folio_components/hero");
    assert!(hero.expose_mdx);
    assert_eq!(hero.export_name.as_deref(), Some("Hero"));
    assert_eq!(hero.origin, ComponentOrigin::Config);
    assert!(diag.is_empty());
}

#[test]
fn expose_mdx_follows_python_truthiness_and_export_defaults_to_name() {
    let dir = tempfile::tempdir().unwrap();
    let (registry, _) = register(
            &format!(
                "components:\n  - name: A\n    from: {d}/a.tsx\n    expose: {{mdx: 0}}\n  - name: B\n    from: {d}/b.tsx\n    expose: nope\n  - name: C\n    path: {d}/c.tsx\n    expose: {{mdx: \"yes\"}}\n",
                d = dir.path().display()
            ),
            dir.path(),
        );
    assert!(!registry.components["A"].expose_mdx);
    assert!(registry.components["B"].expose_mdx);
    assert!(registry.components["C"].expose_mdx);
    assert_eq!(registry.components["C"].export_name.as_deref(), Some("C"));
    assert_eq!(
        registry.components["C"].import_path,
        "@/components/__folio_components/c"
    );
}

#[test]
fn duplicate_source_stems_are_disambiguated() {
    let dir = tempfile::tempdir().unwrap();
    let (registry, _) = register(
            &format!(
                "components:\n  - name: FirstWidget\n    from: {d}/first/widget.tsx\n  - name: SecondWidget\n    from: {d}/second/widget.tsx\n  - name: Hero\n    from: {d}/hero.tsx\n",
                d = dir.path().display()
            ),
            dir.path(),
        );
    assert_eq!(
        registry.components["FirstWidget"].import_path,
        "@/components/__folio_components/widget-FirstWidget"
    );
    assert_eq!(
        registry.components["SecondWidget"].import_path,
        "@/components/__folio_components/widget-SecondWidget"
    );
    assert_eq!(
        registry.components["Hero"].import_path,
        "@/components/__folio_components/hero"
    );
}

#[test]
fn import_stem_candidates_fall_back_to_numbered_segments() {
    let mut used = std::collections::BTreeSet::new();
    assert_eq!(
        component_import_stem("widget", "Widget", false, &mut used),
        "widget"
    );
    assert_eq!(
        component_import_stem("widget", "Widget", false, &mut used),
        "widget-Widget"
    );
    assert_eq!(
        component_import_stem("widget", "Widget", false, &mut used),
        "widget-Widget-2"
    );
    assert_eq!(
        component_import_stem("widget", "Widget", false, &mut used),
        "widget-Widget-3"
    );
    assert_eq!(
        component_import_stem("x", "$$", true, &mut used),
        "x-component"
    );
}

#[test]
fn directory_entries_expand_to_pascal_cased_tsx_and_jsx_files() {
    let dir = tempfile::tempdir().unwrap();
    let components_dir = dir.path().join("docs/components");
    fs::create_dir_all(&components_dir).unwrap();
    fs::write(
        components_dir.join("hero.tsx"),
        "export function Hero() {}\n",
    )
    .unwrap();
    fs::write(
        components_dir.join("my-chart.jsx"),
        "export function MyChart() {}\n",
    )
    .unwrap();
    fs::write(components_dir.join("notes.md"), "not a component\n").unwrap();
    fs::write(components_dir.join("Upper.TSX"), "case-sensitive suffix\n").unwrap();
    fs::create_dir_all(components_dir.join("nested")).unwrap();
    fs::write(components_dir.join("nested/deep.tsx"), "no recursion\n").unwrap();
    // Relative directories anchor to the project directory.
    let (registry, diag) = register("components:\n  - docs/components\n", dir.path());
    assert_eq!(
        registry.components.keys().collect::<Vec<_>>(),
        ["Hero", "MyChart"]
    );
    let hero = &registry.components["Hero"];
    assert_eq!(
        hero.source_path.as_deref(),
        Some(components_dir.join("hero.tsx").as_path())
    );
    assert_eq!(hero.import_path, "@/components/__folio_components/hero");
    assert_eq!(hero.origin, ComponentOrigin::Config);
    assert!(hero.expose_mdx);
    assert_eq!(
        registry.components["MyChart"].export_name.as_deref(),
        Some("MyChart")
    );
    assert!(diag.is_empty());
}

#[test]
fn missing_directory_fails_and_empty_directory_warns() {
    let dir = tempfile::tempdir().unwrap();
    let config = docs_config(
        &format!(
            "project: {{name: Demo}}\ncomponents:\n  - {}/missing\n",
            dir.path().display()
        ),
        dir.path(),
    );
    let err =
        register_config_components(&mut ExtensionRegistry::default(), &config, &mut Vec::new())
            .unwrap_err();
    assert_eq!(
        err.to_string(),
        format!(
            "Component directory not found: {}/missing",
            dir.path().display()
        )
    );

    let empty = dir.path().join("docs/components");
    fs::create_dir_all(&empty).unwrap();
    let (registry, diag) = register("components:\n  - docs/components\n", dir.path());
    assert!(registry.components.is_empty());
    assert_eq!(
        diag,
        [format!(
            "Component directory contains no .tsx/.jsx files: {}",
            empty.display()
        )]
    );
}

#[test]
fn unusable_stem_fails_loudly() {
    let dir = tempfile::tempdir().unwrap();
    let components_dir = dir.path().join("c");
    fs::create_dir_all(&components_dir).unwrap();
    fs::write(components_dir.join("123.tsx"), "x\n").unwrap();
    let config = docs_config("project: {name: Demo}\ncomponents:\n  - c\n", dir.path());
    let err =
        register_config_components(&mut ExtensionRegistry::default(), &config, &mut Vec::new())
            .unwrap_err();
    assert_eq!(
        err.to_string(),
        format!(
            "Cannot derive a component name from file: {}",
            components_dir.join("123.tsx").display()
        )
    );
}

#[test]
fn directory_and_spec_stems_share_deduplication() {
    let dir = tempfile::tempdir().unwrap();
    let components_dir = dir.path().join("dir");
    fs::create_dir_all(&components_dir).unwrap();
    fs::write(
        components_dir.join("widget.tsx"),
        "export function Widget() {}\n",
    )
    .unwrap();
    let spec_file = dir.path().join("widget.tsx");
    fs::write(&spec_file, "export function SpecWidget() {}\n").unwrap();
    let (registry, _) = register(
        &format!(
            "components:\n  - dir\n  - name: SpecWidget\n    from: {}\n",
            spec_file.display()
        ),
        dir.path(),
    );
    assert_eq!(
        registry.components["Widget"].import_path,
        "@/components/__folio_components/widget-Widget"
    );
    assert_eq!(
        registry.components["SpecWidget"].import_path,
        "@/components/__folio_components/widget-SpecWidget"
    );
}

#[test]
fn spec_field_errors_name_the_rule() {
    let dir = tempfile::tempdir().unwrap();
    let config = docs_config(
        "project: {name: Demo}\ncomponents:\n  - name: Hero\n",
        dir.path(),
    );
    let err =
        register_config_components(&mut ExtensionRegistry::default(), &config, &mut Vec::new())
            .unwrap_err();
    assert_eq!(
        err.to_string(),
        "Component specs require string 'name' and 'from' fields"
    );
    let config = docs_config(
        "project: {name: Demo}\ncomponents:\n  - name: Hero\n    from: hero.tsx\n    export: 3\n",
        dir.path(),
    );
    let err =
        register_config_components(&mut ExtensionRegistry::default(), &config, &mut Vec::new())
            .unwrap_err();
    assert_eq!(err.to_string(), "Component export must be a string: Hero");
}

#[test]
fn config_component_shadows_a_builtin_with_config_origin() {
    let dir = tempfile::tempdir().unwrap();
    let component = dir.path().join("callout.tsx");
    fs::write(
        &component,
        "export function Callout() { return <aside /> }\n",
    )
    .unwrap();
    let config = docs_config(
            &format!("project: {{name: Demo}}\ncomponents:\n  - name: Callout\n    from: {}\n    export: Callout\n", component.display()),
            dir.path(),
        );
    let mut registry = ExtensionRegistry::default();
    registry
        .register_component(
            ComponentDefinition {
                origin: ComponentOrigin::Builtin,
                ..ComponentDefinition::new("Callout", "@/components/callout")
            },
            &mut Vec::new(),
        )
        .unwrap();
    let mut diag = Vec::new();
    register_config_components(&mut registry, &config, &mut diag).unwrap();
    assert_eq!(
        diag,
        ["Component 'Callout' overrides the Folio builtin of the same name"]
    );
    let callout = &registry.components["Callout"];
    assert_eq!(callout.origin, ComponentOrigin::Config);
    assert_eq!(callout.source_path.as_deref(), Some(component.as_path()));
}
