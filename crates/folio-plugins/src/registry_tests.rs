use super::*;
use crate::PluginsError;
use indexmap::IndexMap;
use serde_json::json;

fn component(name: &str, import_path: &str) -> ComponentDefinition {
    ComponentDefinition::new(name, import_path)
}

fn registry_with_public_layout() -> ExtensionRegistry {
    let mut registry = ExtensionRegistry::default();
    registry
        .register_layout(
            "folio.public",
            "@/components/folio-view-layouts",
            "PublicLayout",
            &["main"],
        )
        .unwrap();
    registry
}

fn view_slots(component: &str) -> IndexMap<String, Vec<ViewBlock>> {
    IndexMap::from([(
        "main".to_string(),
        vec![ViewBlock {
            component: component.to_string(),
            props: serde_json::Map::new(),
        }],
    )])
}

#[test]
fn identifiers_follow_the_js_rule() {
    assert!(is_js_identifier("Hero"));
    assert!(is_js_identifier("_x$1"));
    assert!(!is_js_identifier("123"));
    assert!(!is_js_identifier("my-chart"));
    assert!(!is_js_identifier(""));
}

#[test]
fn component_definition_has_contract_metadata_defaults() {
    let mut registry = ExtensionRegistry::default();
    let mut diag = Vec::new();
    let comp = registry
        .register_component(component("Foo", "@/components/foo"), &mut diag)
        .unwrap()
        .clone();
    assert!(comp.props.is_empty());
    assert!(!comp.required);
    assert_eq!(comp.category, "general");
    assert!(!comp.contract);
    assert_eq!(comp.source_label, "");
    assert_eq!(comp.origin, ComponentOrigin::Plugin);
    assert!(comp.expose_mdx);
    assert_eq!(comp.source_path, None);
    assert_eq!(comp.export_name, None);
    assert_eq!(comp.imported_name(), "Foo");
    assert!(diag.is_empty());
}

#[test]
fn register_component_accepts_contract_metadata() {
    let mut registry = ExtensionRegistry::default();
    let def = ComponentDefinition {
        props: IndexMap::from([("x".to_string(), "string".to_string())]),
        required: true,
        category: "api-reference".to_string(),
        contract: true,
        source_label: "api-reference".to_string(),
        export_name: Some("default".to_string()),
        ..component("Bar", "@/components/bar")
    };
    let comp = registry.register_component(def, &mut Vec::new()).unwrap();
    assert_eq!(comp.props.get("x").map(String::as_str), Some("string"));
    assert!(comp.required);
    assert_eq!(comp.category, "api-reference");
    assert!(comp.contract);
    assert_eq!(comp.source_label, "api-reference");
    assert_eq!(comp.imported_name(), "default");
}

#[test]
fn invalid_component_names_and_exports_fail() {
    let mut registry = ExtensionRegistry::default();
    let err = registry
        .register_component(component("my-chart", "@/x"), &mut Vec::new())
        .unwrap_err();
    assert_eq!(err.to_string(), "Invalid component name: my-chart");
    let def = ComponentDefinition {
        export_name: Some("bad-export".to_string()),
        ..component("Ok", "@/x")
    };
    let err = registry
        .register_component(def, &mut Vec::new())
        .unwrap_err();
    assert_eq!(err.to_string(), "Invalid component export: bad-export");
}

#[test]
fn plugin_component_shadows_builtin_with_warning() {
    let mut registry = ExtensionRegistry::default();
    let mut diag = Vec::new();
    registry
        .register_component(
            ComponentDefinition {
                origin: ComponentOrigin::Builtin,
                ..component("Callout", "@/components/callout")
            },
            &mut diag,
        )
        .unwrap();
    registry
        .register_component(component("Other", "@/components/other"), &mut diag)
        .unwrap();
    let replaced = registry
        .register_component(component("Callout", "@/components/my-callout"), &mut diag)
        .unwrap()
        .clone();
    assert_eq!(
        diag,
        ["Component 'Callout' overrides the Folio builtin of the same name"]
    );
    assert_eq!(replaced.import_path, "@/components/my-callout");
    assert_eq!(replaced.origin, ComponentOrigin::Plugin);
    assert_eq!(registry.components["Callout"], replaced);
    // The entry keeps its original position in the ordered map.
    assert_eq!(
        registry.components.keys().collect::<Vec<_>>(),
        ["Callout", "Other"]
    );
}

#[test]
fn non_builtin_duplicate_component_fails_naming_origins() {
    let mut registry = ExtensionRegistry::default();
    registry
        .register_component(
            ComponentDefinition {
                origin: ComponentOrigin::Config,
                ..component("Hero", "@/components/hero")
            },
            &mut Vec::new(),
        )
        .unwrap();
    let err = registry
        .register_component(
            component("Hero", "@/components/other-hero"),
            &mut Vec::new(),
        )
        .unwrap_err();
    assert_eq!(
        err.to_string(),
        "Component already registered: Hero (existing origin: config; new origin: plugin)"
    );
}

#[test]
fn builtin_duplicate_component_still_fails() {
    let mut registry = ExtensionRegistry::default();
    let builtin = ComponentDefinition {
        origin: ComponentOrigin::Builtin,
        ..component("Callout", "@/components/callout")
    };
    registry
        .register_component(builtin.clone(), &mut Vec::new())
        .unwrap();
    let err = registry
        .register_component(builtin, &mut Vec::new())
        .unwrap_err();
    assert_eq!(
        err.to_string(),
        "Component already registered: Callout (existing origin: builtin; new origin: builtin)"
    );
}

#[test]
fn layouts_validate_export_and_slots_and_reject_duplicates() {
    let mut registry = registry_with_public_layout();
    let layout = &registry.layouts["folio.public"];
    assert_eq!(layout.export_name, "PublicLayout");
    assert_eq!(layout.slots, ["main"]);
    let err = registry
        .register_layout("folio.public", "@/x", "PublicLayout", &["main"])
        .unwrap_err();
    assert_eq!(err.to_string(), "Layout already registered: folio.public");
    let err = registry
        .register_layout("other", "@/x", "bad-export", &["main"])
        .unwrap_err();
    assert_eq!(err.to_string(), "Invalid layout export: bad-export");
    let err = registry
        .register_layout("other", "@/x", "Ok", &[])
        .unwrap_err();
    assert_eq!(err.to_string(), "Layout must define at least one slot");
    let err = registry
        .register_layout("other", "@/x", "Ok", &["main", "side-bar"])
        .unwrap_err();
    assert_eq!(err.to_string(), "Invalid layout slot: side-bar");
}

#[test]
fn data_modules_validate_export_then_reject_duplicates() {
    let mut registry = ExtensionRegistry::default();
    let module = DataModuleDefinition {
        name: "roadmap".to_string(),
        export_name: "roadmapPhases".to_string(),
        data: json!([]),
        ..DataModuleDefinition::default()
    };
    let stored = registry.write_data_module(module.clone()).unwrap();
    assert_eq!(stored.type_source, "");
    assert_eq!(stored.type_annotation, "");
    assert_eq!(stored.module_path, "");
    let err = registry.write_data_module(module.clone()).unwrap_err();
    assert_eq!(err.to_string(), "Data module already registered: roadmap");
    let err = registry
        .write_data_module(DataModuleDefinition {
            export_name: "bad export".to_string(),
            ..module
        })
        .unwrap_err();
    assert_eq!(err.to_string(), "Invalid data export: bad export");
}

#[test]
fn registry_requires_layout_for_views() {
    let mut registry = ExtensionRegistry::default();
    registry
        .register_component(component("Hero", "@/components/hero"), &mut Vec::new())
        .unwrap();
    let err = registry
        .add_view(
            "/",
            "missing",
            view_slots("Hero"),
            "",
            serde_json::Map::new(),
        )
        .unwrap_err();
    assert_eq!(err.to_string(), "Unknown layout for view /: missing");
}

#[test]
fn registry_requires_known_components_in_view_slots() {
    let mut registry = registry_with_public_layout();
    let err = registry
        .add_view(
            "/custom",
            "folio.public",
            view_slots("Missing"),
            "",
            serde_json::Map::new(),
        )
        .unwrap_err();
    assert_eq!(
        err.to_string(),
        "Unknown component for view /custom: Missing"
    );
}

#[test]
fn registry_rejects_unknown_slots_and_duplicate_view_paths() {
    let mut registry = registry_with_public_layout();
    registry
        .register_component(component("Hero", "@/components/hero"), &mut Vec::new())
        .unwrap();
    let mut slots = view_slots("Hero");
    slots.insert("aside".to_string(), vec![]);
    let err = registry
        .add_view("/custom", "folio.public", slots, "", serde_json::Map::new())
        .unwrap_err();
    assert_eq!(
        err.to_string(),
        "Unknown slot for layout folio.public: aside"
    );

    registry
        .add_view(
            "custom/",
            "folio.public",
            view_slots("Hero"),
            "Custom",
            serde_json::Map::new(),
        )
        .unwrap();
    assert_eq!(registry.views["/custom"].title, "Custom");
    let err = registry
        .add_view(
            "/custom",
            "folio.public",
            view_slots("Hero"),
            "",
            serde_json::Map::new(),
        )
        .unwrap_err();
    assert!(matches!(err, PluginsError::ViewRegistered(ref p) if p == "/custom"));
    assert_eq!(err.to_string(), "View path already registered: /custom");
    // "/" stays "/".
    let view = registry
        .add_view(
            "/",
            "folio.public",
            view_slots("Hero"),
            "",
            serde_json::Map::new(),
        )
        .unwrap();
    assert_eq!(view.path, "/");
}

#[test]
fn contract_components_follow_the_flag_in_registry_order() {
    let mut registry = ExtensionRegistry::default();
    for (name, contract) in [("B", true), ("A", false), ("C", true)] {
        registry
            .register_component(
                ComponentDefinition {
                    contract,
                    ..component(name, "@/x")
                },
                &mut Vec::new(),
            )
            .unwrap();
    }
    let names: Vec<&str> = registry
        .contract_components()
        .map(|c| c.name.as_str())
        .collect();
    assert_eq!(names, ["B", "C"]);
}

/// A registration made in another process has to arrive as data, so the five
/// registry types round-trip through JSON. The declaration order of props and
/// slots is part of what they mean, so it has to survive the trip.
#[test]
fn the_registry_types_round_trip_through_json_with_their_order_intact() {
    let mut component = ComponentDefinition::new("Chart", "@/components/chart");
    component.export_name = Some("default".to_string());
    component.source_path = Some(std::path::PathBuf::from("components/chart.tsx"));
    component.props = ["zeta", "alpha", "mu"]
        .iter()
        .map(|name| ((*name).to_string(), "string".to_string()))
        .collect();
    component.contract = true;
    component.origin = ComponentOrigin::Plugin;

    let text = serde_json::to_string(&component).unwrap();
    let back: ComponentDefinition = serde_json::from_str(&text).unwrap();
    assert_eq!(back, component);
    assert_eq!(
        back.props.keys().collect::<Vec<_>>(),
        ["zeta", "alpha", "mu"],
        "props keep the order they were declared in, not a sorted one"
    );

    let block = ViewBlock {
        component: "Chart".to_string(),
        props: serde_json::Map::new(),
    };
    let view = ViewDefinition {
        path: "/reports".to_string(),
        layout: "plain".to_string(),
        slots: [
            ("main".to_string(), vec![block.clone()]),
            ("aside".to_string(), vec![block]),
        ]
        .into_iter()
        .collect(),
        title: "Reports".to_string(),
        props: serde_json::Map::new(),
    };
    let back: ViewDefinition =
        serde_json::from_str(&serde_json::to_string(&view).unwrap()).unwrap();
    assert_eq!(back, view);
    assert_eq!(back.slots.keys().collect::<Vec<_>>(), ["main", "aside"]);

    let layout = LayoutDefinition {
        name: "plain".to_string(),
        import_path: "@/layouts/plain".to_string(),
        export_name: "PlainLayout".to_string(),
        slots: vec!["main".to_string(), "aside".to_string()],
    };
    let back: LayoutDefinition =
        serde_json::from_str(&serde_json::to_string(&layout).unwrap()).unwrap();
    assert_eq!(back, layout);

    let module = DataModuleDefinition::default();
    let back: DataModuleDefinition =
        serde_json::from_str(&serde_json::to_string(&module).unwrap()).unwrap();
    assert_eq!(back, module);
}
