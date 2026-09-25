use super::*;

const EXPECTED_ORDER: [&str; 40] = [
    "ParamTable",
    "ClassOverview",
    "TypeBadge",
    "MethodAccordion",
    "ExampleTabs",
    "DeprecationNotice",
    "Callout",
    "CodeGroup",
    "SourceLink",
    "Steps",
    "Step",
    "Mermaid",
    "FileTree",
    "FeatureCard",
    "CardGrid",
    "Tabs",
    "TabItem",
    "Accordion",
    "AccordionItem",
    "Timeline",
    "TimelineItem",
    "TerminalSession",
    "ConfigPanel",
    "BuildArtifact",
    "DocPreview",
    "PreviewCode",
    "CommandGrid",
    "CommandCard",
    "BeforeAfter",
    "Swot",
    "CompareMatrix",
    "PullQuote",
    "StatStrip",
    "Checklist",
    "HookMap",
    "ComponentIndex",
    "ApiReferenceIndex",
    "ComparisonMatrix",
    "UnavailableFeature",
    "BrowserFrame",
];

const EXPECTED_REQUIRED: [&str; 8] = [
    "ParamTable",
    "ClassOverview",
    "ApiReferenceIndex",
    "SourceLink",
    "Callout",
    "Tabs",
    "TabItem",
    "Mermaid",
];

const EXPECTED_CONTRACT: [&str; 22] = [
    "ParamTable",
    "ClassOverview",
    "TypeBadge",
    "MethodAccordion",
    "Callout",
    "SourceLink",
    "Mermaid",
    "FileTree",
    "FeatureCard",
    "CardGrid",
    "Tabs",
    "TabItem",
    "Accordion",
    "AccordionItem",
    "Timeline",
    "TimelineItem",
    "Swot",
    "CompareMatrix",
    "PullQuote",
    "StatStrip",
    "ApiReferenceIndex",
    "BrowserFrame",
];

#[test]
fn builtin_manifest_order_matches_template() {
    let names: Vec<&str> = BUILTIN_COMPONENTS.iter().map(|c| c.name.as_str()).collect();
    assert_eq!(names, EXPECTED_ORDER);
}

#[test]
fn required_builtins_match_contract() {
    let mut required: Vec<&str> = BUILTIN_COMPONENTS
        .iter()
        .filter(|c| c.required)
        .map(|c| c.name.as_str())
        .collect();
    required.sort_unstable();
    let mut expected = EXPECTED_REQUIRED;
    expected.sort_unstable();
    assert_eq!(required, expected);
}

#[test]
fn contract_members_are_exactly_the_prop_bearing_components() {
    let contract: Vec<&str> = BUILTIN_COMPONENTS
        .iter()
        .filter(|c| c.contract)
        .map(|c| c.name.as_str())
        .collect();
    let with_props: Vec<&str> = BUILTIN_COMPONENTS
        .iter()
        .filter(|c| !c.props.is_empty())
        .map(|c| c.name.as_str())
        .collect();
    assert_eq!(contract, EXPECTED_CONTRACT);
    assert_eq!(with_props, EXPECTED_CONTRACT);
}

#[test]
fn contract_builtins_carry_source_label_and_category() {
    for comp in BUILTIN_COMPONENTS.iter() {
        if comp.contract {
            assert!(!comp.source_label.is_empty(), "{}", comp.name);
            assert_eq!(comp.category, comp.source_label, "{}", comp.name);
        } else {
            assert_eq!(comp.source_label, "", "{}", comp.name);
            assert_eq!(comp.category, "component-catalog", "{}", comp.name);
        }
    }
    let by_name = |name: &str| BUILTIN_COMPONENTS.iter().find(|c| c.name == name).unwrap();
    assert_eq!(by_name("ParamTable").source_label, "api-reference");
    assert_eq!(by_name("Callout").source_label, "markdown-rst");
    assert_eq!(by_name("Mermaid").source_label, "markdown-mdx");
    assert_eq!(by_name("Timeline").source_label, "component-catalog");
}

#[test]
fn all_builtins_expose_mdx_and_have_no_source_path() {
    for comp in BUILTIN_COMPONENTS.iter() {
        assert!(comp.expose_mdx);
        assert_eq!(comp.source_path, None);
        assert_eq!(comp.export_name, None);
        assert_eq!(comp.origin, ComponentOrigin::Builtin);
        assert!(comp.import_path.starts_with("@/components/"));
    }
}

#[test]
fn register_builtin_components_populates_registry_in_order() {
    let mut registry = ExtensionRegistry::default();
    register_builtin_components(&mut registry).unwrap();
    let names: Vec<&str> = registry.components.keys().map(String::as_str).collect();
    assert_eq!(names, EXPECTED_ORDER);
    assert_eq!(registry.components["Callout"].category, "markdown-rst");
    assert_eq!(registry.components["ParamTable"].category, "api-reference");
    assert_eq!(registry.components["Tabs"].import_path, "@/components/tabs");
    assert!(registry
        .components
        .values()
        .all(|c| c.origin == ComponentOrigin::Builtin));
    assert!(registry.components["Callout"].contract);
    assert!(!registry.components["CodeGroup"].contract);
    assert_eq!(registry.components["CodeGroup"].source_label, "");
    // Registering twice is the builtin-over-builtin failure.
    let err = register_builtin_components(&mut registry).unwrap_err();
    assert_eq!(
        err.to_string(),
        "Component already registered: ParamTable (existing origin: builtin; new origin: builtin)"
    );
}

#[test]
fn register_builtin_extensions_adds_the_public_layout_once() {
    let mut registry = ExtensionRegistry::default();
    register_builtin_extensions(&mut registry).unwrap();
    register_builtin_extensions(&mut registry).unwrap();
    assert_eq!(PUBLIC_LAYOUT, "folio.public");
    let layout = &registry.layouts[PUBLIC_LAYOUT];
    assert_eq!(layout.import_path, "@/components/folio-view-layouts");
    assert_eq!(layout.export_name, "PublicLayout");
    assert_eq!(layout.slots, ["main"]);
    assert_eq!(registry.layouts.len(), 1);
}
