//! The builtin component manifest, the public layout and their registration.
//! The manifest order is the entry order of `template/mdx-components.tsx`;
//! `drift.rs` guards it.

use std::sync::LazyLock;

use indexmap::IndexMap;

use crate::error::PluginsError;
use crate::registry::{ComponentDefinition, ComponentOrigin, ExtensionRegistry};

/// The one layout every public view renders inside (internal name, never emitted).
pub const PUBLIC_LAYOUT: &str = "folio.public";

/// A manifest entry: `contract` names the source label of a contract member
/// (its category too); `None` is a catalog-only component with no props.
fn component(
    name: &str,
    module: &str,
    required: bool,
    contract: Option<&str>,
    props: &[(&str, &str)],
) -> ComponentDefinition {
    ComponentDefinition {
        required,
        category: contract.unwrap_or("component-catalog").to_string(),
        contract: contract.is_some(),
        source_label: contract.unwrap_or("").to_string(),
        props: props
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_string()))
            .collect::<IndexMap<_, _>>(),
        origin: ComponentOrigin::Builtin,
        ..ComponentDefinition::new(name, &format!("@/components/{module}"))
    }
}

const API: Option<&str> = Some("api-reference");
const RST: Option<&str> = Some("markdown-rst");
const MDX: Option<&str> = Some("markdown-mdx");
const CATALOG: Option<&str> = Some("component-catalog");

/// The forty builtin components in `mdx-components.tsx` entry order.
pub static BUILTIN_COMPONENTS: LazyLock<Vec<ComponentDefinition>> = LazyLock::new(|| {
    vec![
        component("ParamTable", "param-table", true, API, &[(
            "args",
            "Array<{ name: string; type: string; default?: string; description?: string | null; href?: string }>",
        )]),
        component("ClassOverview", "class-overview", true, API, &[
            ("name", "string"),
            ("bases", "string[] | Array<{ name: string; href?: string }> | undefined"),
            ("decorators", "string[] | undefined"),
            ("description", "string | undefined"),
        ]),
        component("TypeBadge", "type-badge", false, CATALOG, &[
            ("type", "string"),
            ("href", "string | undefined"),
        ]),
        component("MethodAccordion", "method-accordion", false, CATALOG, &[(
            "methods",
            "Array<{ name: string; signature: string; description: string; isAsync?: boolean; children?: React.ReactNode }>",
        )]),
        component("ExampleTabs", "example-tabs", false, None, &[]),
        component("DeprecationNotice", "deprecation-notice", false, None, &[]),
        component("Callout", "callout", true, RST, &[
            ("type", "\"note\" | \"warning\" | \"info\" | \"tip\" | \"check\" | \"danger\" | undefined"),
            ("title", "string | undefined"),
            ("children", "React.ReactNode"),
        ]),
        component("CodeGroup", "code-group", false, None, &[]),
        component("SourceLink", "source-link", true, API, &[("href", "string")]),
        component("Steps", "steps", false, None, &[]),
        component("Step", "steps", false, None, &[]),
        component("Mermaid", "mermaid", true, MDX, &[("chart", "string")]),
        component("FileTree", "file-tree", false, CATALOG, &[("tree", "string")]),
        component("FeatureCard", "feature-card", false, CATALOG, &[
            ("title", "string"),
            ("description", "string"),
            ("icon", "string | undefined"),
            ("href", "string | undefined"),
        ]),
        component("CardGrid", "card-grid", false, CATALOG, &[
            ("columns", "2 | 3 | 4 | undefined"),
            ("children", "React.ReactNode"),
        ]),
        component("Tabs", "tabs", true, MDX, &[
            ("children", "React.ReactNode"),
            ("aria-label", "string | undefined"),
        ]),
        component("TabItem", "tabs", true, MDX, &[
            ("label", "string"),
            ("children", "React.ReactNode"),
        ]),
        component("Accordion", "accordion", false, CATALOG, &[("children", "React.ReactNode")]),
        component("AccordionItem", "accordion", false, CATALOG, &[
            ("title", "string"),
            ("children", "React.ReactNode"),
            ("defaultOpen", "boolean | undefined"),
        ]),
        component("Timeline", "timeline", false, CATALOG, &[("children", "React.ReactNode")]),
        component("TimelineItem", "timeline", false, CATALOG, &[
            ("date", "string"),
            ("title", "string"),
            ("badge", "string | undefined"),
            ("children", "React.ReactNode"),
        ]),
        component("TerminalSession", "terminal-session", false, None, &[]),
        component("ConfigPanel", "config-panel", false, None, &[]),
        component("BuildArtifact", "build-artifact", false, None, &[]),
        component("DocPreview", "doc-preview", false, None, &[]),
        component("PreviewCode", "preview-code", false, None, &[]),
        component("CommandGrid", "command-grid", false, None, &[]),
        component("CommandCard", "command-grid", false, None, &[]),
        component("BeforeAfter", "before-after", false, None, &[]),
        component("Swot", "swot", false, CATALOG, &[
            ("strengths", "string[]"),
            ("weaknesses", "string[]"),
            ("opportunities", "string[]"),
            ("threats", "string[]"),
            ("title", "string | undefined"),
        ]),
        component("CompareMatrix", "compare-matrix", false, CATALOG, &[
            ("tools", "string[]"),
            ("rows", "{ feature: string; values: (boolean | string)[]; note?: string }[]"),
            ("caption", "string | undefined"),
            ("highlight", "number | undefined"),
        ]),
        component("PullQuote", "pull-quote", false, CATALOG, &[
            ("children", "ReactNode"),
            ("kicker", "string | undefined"),
            ("attribution", "string | undefined"),
        ]),
        component("StatStrip", "stat-strip", false, CATALOG, &[(
            "stats",
            "{ value: string; label: string; detail?: string }[]",
        )]),
        component("Checklist", "checklist", false, None, &[]),
        component("HookMap", "hook-map", false, None, &[]),
        component("ComponentIndex", "component-index", false, None, &[]),
        component("ApiReferenceIndex", "api-reference-index", true, API, &[(
            "modules",
            "Array<{ name: string; description: string; href: string; classCount: number; functionCount: number }>",
        )]),
        component("ComparisonMatrix", "comparison-matrix", false, None, &[]),
        component("UnavailableFeature", "unavailable-feature", false, None, &[]),
        component("BrowserFrame", "browser-frame", false, CATALOG, &[
            ("url", "string"),
            ("label", "string | undefined"),
            ("footer", "React.ReactNode | undefined"),
            ("children", "React.ReactNode | undefined"),
        ]),
    ]
});

/// Register every builtin component in manifest order.
pub fn register_builtin_components(registry: &mut ExtensionRegistry) -> Result<(), PluginsError> {
    for component in BUILTIN_COMPONENTS.iter() {
        registry.register_component(component.clone(), &mut Vec::new())?;
    }
    Ok(())
}

/// Register the `PUBLIC_LAYOUT` layout unless it is already present.
pub fn register_builtin_extensions(registry: &mut ExtensionRegistry) -> Result<(), PluginsError> {
    if !registry.layouts.contains_key(PUBLIC_LAYOUT) {
        registry.register_layout(
            PUBLIC_LAYOUT,
            "@/components/folio-view-layouts",
            "PublicLayout",
            &["main"],
        )?;
    }
    Ok(())
}

#[cfg(test)]
#[path = "builtins_tests.rs"]
mod tests;
