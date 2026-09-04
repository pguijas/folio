from folio.builtins import BUILTIN_COMPONENTS, register_builtin_components
from folio.extensions import ExtensionRegistry

EXPECTED_ORDER = [
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
]

EXPECTED_REQUIRED = {
    "ParamTable",
    "ClassOverview",
    "ApiReferenceIndex",
    "SourceLink",
    "Callout",
    "Tabs",
    "TabItem",
    "Mermaid",
}


def test_builtin_manifest_order_matches_template() -> None:
    assert [c.name for c in BUILTIN_COMPONENTS] == EXPECTED_ORDER


def test_required_builtins_match_contract() -> None:
    required = {c.name for c in BUILTIN_COMPONENTS if c.required}
    assert required == EXPECTED_REQUIRED


def test_contract_flag_set_for_exactly_prop_bearing_components() -> None:
    # Contract membership is now the explicit ``contract`` flag; it must match
    # the previous implicit membership (non-empty props) so derived output is
    # unchanged.
    contract_names = {c.name for c in BUILTIN_COMPONENTS if c.contract}
    with_props = {c.name for c in BUILTIN_COMPONENTS if c.props}
    assert contract_names == with_props


def test_contract_builtins_carry_source_label() -> None:
    for comp in BUILTIN_COMPONENTS:
        if comp.contract:
            assert comp.source_label
        else:
            assert comp.source_label == ""
    by_name = {c.name: c for c in BUILTIN_COMPONENTS}
    assert by_name["ParamTable"].source_label == "api-reference"
    assert by_name["Callout"].source_label == "markdown-rst"
    assert by_name["Mermaid"].source_label == "markdown-mdx"
    assert by_name["Timeline"].source_label == "component-catalog"


def test_contract_components_are_exactly_those_with_props() -> None:
    # The contract subset is identified by having a non-empty props mapping.
    with_props = {c.name for c in BUILTIN_COMPONENTS if c.props}
    assert with_props == {
        "ParamTable",
        "ClassOverview",
        "ApiReferenceIndex",
        "SourceLink",
        "Callout",
        "Tabs",
        "TabItem",
        "Mermaid",
        "TypeBadge",
        "MethodAccordion",
        "FileTree",
        "FeatureCard",
        "CardGrid",
        "Accordion",
        "AccordionItem",
        "Timeline",
        "TimelineItem",
        "Swot",
        "CompareMatrix",
        "PullQuote",
        "StatStrip",
        "BrowserFrame",
    }


def test_all_builtins_expose_mdx_and_have_no_source_path() -> None:
    for comp in BUILTIN_COMPONENTS:
        assert comp.expose_mdx is True
        assert comp.source_path is None
        assert comp.import_path.startswith("@/components/")


def test_register_builtin_components_populates_registry_in_order() -> None:
    registry = ExtensionRegistry()
    register_builtin_components(registry)
    assert list(registry.components) == EXPECTED_ORDER
    assert registry.components["Callout"].category == "markdown-rst"
    assert registry.components["ParamTable"].category == "api-reference"
    assert registry.components["Tabs"].import_path == "@/components/tabs"


def test_register_builtin_components_sets_builtin_origin_and_contract() -> None:
    registry = ExtensionRegistry()
    register_builtin_components(registry)
    assert all(c.origin == "builtin" for c in registry.components.values())
    assert registry.components["Callout"].contract is True
    assert registry.components["Callout"].source_label == "markdown-rst"
    assert registry.components["CodeGroup"].contract is False
    assert registry.components["CodeGroup"].source_label == ""
