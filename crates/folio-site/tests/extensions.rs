//! Registry extensions emitted into the workspace through `apply_extensions`.

mod common;

use std::path::Path;

use folio_plugins::{
    ComponentDefinition, ComponentOrigin, DataModuleDefinition, ExtensionRegistry, ViewBlock,
    PUBLIC_LAYOUT,
};
use indexmap::IndexMap;
use serde_json::json;

const MDX_COMPONENTS_WITH_MARKERS: &str = "import { useMDXComponents as getThemeComponents } from \"nextra-theme-docs\"\n// __FOLIO_COMPONENT_IMPORTS__\n\nconst themeComponents = getThemeComponents()\n\nexport function useMDXComponents(components?: Record<string, React.ComponentType>) {\n  return {\n    ...themeComponents,\n    // __FOLIO_COMPONENT_ENTRIES__\n    ...components,\n  }\n}\n";

fn component(name: &str, import_path: &str, source: Option<&Path>) -> ComponentDefinition {
    let mut def = ComponentDefinition::new(name, import_path);
    def.export_name = Some(name.to_string());
    def.source_path = source.map(Path::to_path_buf);
    def
}

fn make_registry(components: Vec<ComponentDefinition>) -> ExtensionRegistry {
    let mut registry = ExtensionRegistry::default();
    for def in components {
        registry.register_component(def, &mut Vec::new()).unwrap();
    }
    registry
}

fn block(component: &str, props: serde_json::Value) -> ViewBlock {
    ViewBlock {
        component: component.into(),
        props: props.as_object().cloned().unwrap_or_default(),
    }
}

#[test]
fn components_are_copied_and_wired_idempotently() {
    let dir = tempfile::tempdir().unwrap();
    let template = common::make_template(dir.path());
    common::write(&template, "mdx-components.tsx", MDX_COMPONENTS_WITH_MARKERS);
    let hero = common::write(
        &dir.path().join("source-components"),
        "hero.tsx",
        "export function Hero() { return <section /> }\n",
    );
    let config = common::config(dir.path(), "");
    let build = dir.path().join("build");
    let mut builder = common::builder(&config, &template, &build);
    builder.prepare(false).unwrap();
    let registry = make_registry(vec![component(
        "Hero",
        "@/components/__folio_components/hero",
        Some(&hero),
    )]);
    builder.apply_extensions(&registry).unwrap();
    builder.apply_extensions(&registry).unwrap();
    let mdx = common::read(&build.join("mdx-components.tsx"));
    assert!(build
        .join("components/__folio_components/hero.tsx")
        .exists());
    assert_eq!(
        mdx.matches("import { Hero } from \"@/components/__folio_components/hero\"")
            .count(),
        1
    );
    assert_eq!(mdx.matches("    Hero,").count(), 1);
    assert!(common::read(&build.join("lib/folio-mdx-contract.ts"))
        .contains("export const folioMdxComponents = [] as const"));

    let first = common::write(
        &dir.path().join("first"),
        "widget.tsx",
        "export function FirstWidget() { return <section /> }\n",
    );
    let second = common::write(
        &dir.path().join("second"),
        "widget.tsx",
        "export function SecondWidget() { return <section /> }\n",
    );
    let registry = make_registry(vec![
        component(
            "FirstWidget",
            "@/components/__folio_components/widget-FirstWidget",
            Some(&first),
        ),
        component(
            "SecondWidget",
            "@/components/__folio_components/widget-SecondWidget",
            Some(&second),
        ),
    ]);
    builder.apply_extensions(&registry).unwrap();
    assert_eq!(
        common::read(&build.join("components/__folio_components/widget-FirstWidget.tsx")),
        common::read(&first)
    );
    assert_eq!(
        common::read(&build.join("components/__folio_components/widget-SecondWidget.tsx")),
        common::read(&second)
    );
    let mdx = common::read(&build.join("mdx-components.tsx"));
    assert!(
        mdx.contains(
            "import { FirstWidget } from \"@/components/__folio_components/widget-FirstWidget\""
        ) && mdx.contains(
            "import { SecondWidget } from \"@/components/__folio_components/widget-SecondWidget\""
        )
    );

    let escape = make_registry(vec![component("Escape", "@/../outside", Some(&first))]);
    assert_eq!(
        builder.apply_extensions(&escape).unwrap_err().to_string(),
        "Component import path would write outside build directory: @/../outside"
    );
    let missing = make_registry(vec![component(
        "Missing",
        "@/components/__folio_components/missing",
        Some(Path::new("/nowhere/missing.tsx")),
    )]);
    assert_eq!(
        builder.apply_extensions(&missing).unwrap_err().to_string(),
        "Component source not found: /nowhere/missing.tsx"
    );
}

#[test]
fn builtin_injection_depends_on_the_template_kind_and_sources_anchor_to_the_project() {
    let dir = tempfile::tempdir().unwrap();
    let template = common::make_template(dir.path());
    common::write(&template, "mdx-components.tsx", MDX_COMPONENTS_WITH_MARKERS);
    let hero = common::write(
        &dir.path().join("source-components"),
        "hero.tsx",
        "export function Hero() { return <section /> }\n",
    );
    let mut callout = ComponentDefinition::new("Callout", "@/components/callout");
    callout.origin = ComponentOrigin::Builtin;
    let with_builtin = || {
        make_registry(vec![
            callout.clone(),
            component("Hero", "@/components/__folio_components/hero", Some(&hero)),
        ])
    };

    let custom = common::config(dir.path(), "template:\n  path: template\n");
    let mut builder = common::builder(&custom, &template, &dir.path().join("build-custom"));
    builder.prepare(false).unwrap();
    builder.apply_extensions(&with_builtin()).unwrap();
    let mdx = common::read(&dir.path().join("build-custom/mdx-components.tsx"));
    assert!(
        !mdx.contains("import { Callout } from \"@/components/callout\"")
            && !mdx.contains("    Callout,")
    );
    assert!(
        mdx.contains("import { Hero } from \"@/components/__folio_components/hero\"")
            && mdx.contains("    Hero,")
    );

    common::write(dir.path(), "overlay/.keep", "");
    for (label, yaml) in [
        ("bundled", ""),
        ("overlay", "template:\n  overlay_path: overlay\n"),
    ] {
        let config = common::config(dir.path(), yaml);
        let build = dir.path().join(format!("build-{label}"));
        let mut builder = common::builder(&config, &template, &build);
        builder.prepare(false).unwrap();
        builder.apply_extensions(&with_builtin()).unwrap();
        let mdx = common::read(&build.join("mdx-components.tsx"));
        assert!(
            mdx.contains("import { Callout } from \"@/components/callout\"")
                && mdx.contains("    Callout,"),
            "{label}"
        );
    }

    let project = dir.path().join("proj");
    common::write(
        &project,
        "components/hero.tsx",
        "export function Hero() { return <section /> }\n",
    );
    let config = common::config(&project, "");
    let build = dir.path().join("build-relative");
    let mut builder = common::builder(&config, &template, &build);
    builder.prepare(false).unwrap();
    builder
        .apply_extensions(&make_registry(vec![component(
            "Hero",
            "@/components/__folio_components/hero",
            Some(Path::new("components/hero.tsx")),
        )]))
        .unwrap();
    assert!(build
        .join("components/__folio_components/hero.tsx")
        .exists());
}

#[test]
fn layout_backed_views_and_data_modules() {
    let dir = tempfile::tempdir().unwrap();
    let template = common::make_template(dir.path());
    common::write(&template, "mdx-components.tsx", "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n  return { ...components }\n}\n");
    let config = common::config(dir.path(), "");
    let build = dir.path().join("build");
    let mut builder = common::builder(&config, &template, &build);
    builder.prepare(false).unwrap();

    let mut registry = make_registry(vec![
        ComponentDefinition::new("Roadmap", "@/components/roadmap"),
        ComponentDefinition::new("GalleryGrid", "@/components/gallery-grid"),
    ]);
    registry
        .register_layout(
            PUBLIC_LAYOUT,
            "@/components/folio-view-layouts",
            "PublicLayout",
            &["main", "aside"],
        )
        .unwrap();
    let mut props = serde_json::Map::new();
    props.insert("eyebrow".into(), json!("Official plugin"));
    registry
        .add_view(
            "/roadmap",
            PUBLIC_LAYOUT,
            IndexMap::from([("main".to_string(), vec![block("Roadmap", json!({}))])]),
            "Roadmap",
            props,
        )
        .unwrap();
    registry
        .add_view(
            "/",
            PUBLIC_LAYOUT,
            IndexMap::from([(
                "main".to_string(),
                vec![block("GalleryGrid", json!({"compact": true}))],
            )]),
            "Gallery",
            Default::default(),
        )
        .unwrap();
    registry
        .add_view(
            "gallery",
            PUBLIC_LAYOUT,
            IndexMap::from([
                ("main".to_string(), vec![]),
                ("aside".to_string(), vec![block("GalleryGrid", json!({}))]),
            ]),
            "",
            Default::default(),
        )
        .unwrap();
    registry
        .write_data_module(DataModuleDefinition {
            name: "roadmap".into(),
            export_name: "roadmapPhases".into(),
            data: json!([{"title": "0.3"}]),
            type_source: "export interface RoadmapPhase { title: string }".into(),
            type_annotation: "RoadmapPhase[]".into(),
            module_path: "roadmap-data".into(),
        })
        .unwrap();
    registry
        .write_data_module(DataModuleDefinition {
            name: "openapi".into(),
            export_name: "openapiSpecs".into(),
            data: json!({}),
            ..Default::default()
        })
        .unwrap();
    builder.apply_extensions(&registry).unwrap();
    assert_eq!(
        builder.view_routes(),
        std::collections::BTreeSet::from([
            "/roadmap".to_string(),
            "/".to_string(),
            "/gallery".to_string()
        ])
    );

    let page = common::read(&build.join("app/roadmap/page.tsx"));
    assert_eq!(
        page,
        "import { PublicLayout } from \"@/components/folio-view-layouts\"\nimport { Roadmap } from \"@/components/roadmap\"\n\nconst layoutProps = {\n  \"eyebrow\": \"Official plugin\",\n  \"title\": \"Roadmap\",\n  \"pathToRoot\": \"..\"\n}\n\nexport const metadata = { title: \"Roadmap\" }\n\nexport default function FolioExtensionView() {\n  return (\n    <PublicLayout {...layoutProps}>\n        <Roadmap />\n    </PublicLayout>\n  )\n}\n"
    );
    let root = common::read(&build.join("app/page.tsx"));
    assert!(
        root.contains("\"pathToRoot\": \".\"")
            && root.contains("const block0Props = {\n  \"compact\": true\n}")
            && root.contains("        <GalleryGrid {...block0Props} />")
    );
    let gallery = common::read(&build.join("app/gallery/page.tsx"));
    assert!(
        gallery.contains("\"pathToRoot\": \"..\"")
            && gallery.contains("        {/* Slot: aside */}\n        <GalleryGrid />")
            && !gallery.contains("metadata")
    );
    assert_eq!(common::read(&build.join("lib/roadmap-data.ts")), "export interface RoadmapPhase { title: string }\nexport const roadmapPhases: RoadmapPhase[] = [\n  {\n    \"title\": \"0.3\"\n  }\n]\n");
    assert_eq!(
        common::read(&build.join("lib/__folio_data/openapi.ts")),
        "export const openapiSpecs = {}\n"
    );

    registry
        .write_data_module(DataModuleDefinition {
            name: "bad".into(),
            export_name: "x".into(),
            data: json!(1),
            module_path: "../escape".into(),
            ..Default::default()
        })
        .unwrap();
    assert_eq!(
        builder.apply_extensions(&registry).unwrap_err().to_string(),
        "Data module path must stay inside lib: ../escape"
    );
    registry.data_modules.clear();
    registry
        .add_view(
            "/../x",
            PUBLIC_LAYOUT,
            IndexMap::new(),
            "",
            Default::default(),
        )
        .unwrap();
    assert_eq!(
        builder.apply_extensions(&registry).unwrap_err().to_string(),
        "Route would write outside app directory: /../x"
    );
}
