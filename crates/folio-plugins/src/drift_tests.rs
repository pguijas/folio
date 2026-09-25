use super::*;

const TEMPLATE: &str = "import { A } from \"@/a\"\nimport {\n  IgnoredWidget,\n} from \"./ignored\"\n\nexport function useMDXComponents() {\n  return {\n    ...themeComponents,\n    wrapper: WrapperWithSanitizedToc,\n    ParamTable,\n    // GhostWidget,\n    Callout,\n    ...components,\n  }\n}\n";

#[test]
fn template_entry_names_are_whole_line_shorthand_entries_only() {
    assert_eq!(
        template_component_entry_names(TEMPLATE),
        ["ParamTable", "Callout"]
    );
}

#[test]
fn name_drift_is_bidirectional_and_names_the_rust_manifest() {
    let drift = check_template_drift(TEMPLATE);
    assert_eq!(drift.len(), 38);
    assert_eq!(
            drift[0],
            "builtin component 'ClassOverview' is declared in the manifest (folio-plugins/src/builtins.rs) but has no entry in mdx-components.tsx"
        );
    assert!(drift
        .iter()
        .all(|m| m.contains("no entry in mdx-components.tsx")));
    let with_widget = TEMPLATE.replace("    ...components,", "    NewWidget,\n    ...components,");
    let drift = check_template_drift(&with_widget);
    assert_eq!(
            drift.last().unwrap(),
            "component entry 'NewWidget' in mdx-components.tsx is not declared in the builtin manifest (folio-plugins/src/builtins.rs)"
        );
    assert!(drift.iter().all(|m| !m.contains(".py")));
}
