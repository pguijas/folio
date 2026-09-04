"""Single source of truth for Folio's builtin MDX components.

These components ship inside the bundled Next/Nextra template
(``template/components/``) and are registered into the
:class:`~folio.extensions.ExtensionRegistry` so that the registry is the
authoritative description of every component Folio exposes. The MDX contract
(:mod:`folio.generator.mdx_contract`) and the build-time component injection
both derive from this manifest.

The order of :data:`BUILTIN_COMPONENTS` MUST match the entry order in
``template/mdx-components.tsx``; ``tests/test_builtin_drift.py`` guards this.

Contract membership is explicit: entries with ``contract=True`` are part of
the published MDX component contract, and ``source_label`` carries the
contract ``source`` string for those entries. ``category`` is pure taxonomy
and plays no role in the contract. The prop type strings are copied verbatim
from the hand-authored contract.
"""

from __future__ import annotations

from folio.extensions import ComponentDefinition, ExtensionRegistry


def _component(
    name: str,
    module: str,
    *,
    props: dict[str, str] | None = None,
    required: bool = False,
    category: str = "component-catalog",
    contract: bool = False,
    source_label: str = "",
) -> ComponentDefinition:
    return ComponentDefinition(
        name=name,
        import_path=f"@/components/{module}",
        expose_mdx=True,
        props=props or {},
        required=required,
        category=category,
        contract=contract,
        source_label=source_label,
        origin="builtin",
    )


BUILTIN_COMPONENTS: tuple[ComponentDefinition, ...] = (
    _component(
        "ParamTable",
        "param-table",
        required=True,
        category="api-reference",
        contract=True,
        source_label="api-reference",
        props={
            "args": (
                "Array<{ name: string; type: string; default?: string; "
                "description?: string | null; href?: string }>"
            )
        },
    ),
    _component(
        "ClassOverview",
        "class-overview",
        required=True,
        category="api-reference",
        contract=True,
        source_label="api-reference",
        props={
            "name": "string",
            "bases": "string[] | Array<{ name: string; href?: string }>",
            "decorators": "string[]",
            "description": "string",
        },
    ),
    _component(
        "TypeBadge",
        "type-badge",
        category="component-catalog",
        contract=True,
        source_label="component-catalog",
        props={"type": "string", "href": "string"},
    ),
    _component(
        "MethodAccordion",
        "method-accordion",
        category="component-catalog",
        contract=True,
        source_label="component-catalog",
        props={
            "methods": (
                "Array<{ name: string; signature: string; description?: string }>"
            )
        },
    ),
    _component("ExampleTabs", "example-tabs"),
    _component("DeprecationNotice", "deprecation-notice"),
    _component(
        "Callout",
        "callout",
        required=True,
        category="markdown-rst",
        contract=True,
        source_label="markdown-rst",
        props={
            "type": '"note" | "warning" | "info" | "tip" | "check" | "danger"',
            "title": "string",
            "children": "React.ReactNode",
        },
    ),
    _component("CodeGroup", "code-group"),
    _component(
        "SourceLink",
        "source-link",
        required=True,
        category="api-reference",
        contract=True,
        source_label="api-reference",
        props={"href": "string"},
    ),
    _component("Steps", "steps"),
    _component("Step", "steps"),
    _component(
        "Mermaid",
        "mermaid",
        required=True,
        category="markdown-mdx",
        contract=True,
        source_label="markdown-mdx",
        props={"chart": "string"},
    ),
    _component(
        "FileTree",
        "file-tree",
        category="component-catalog",
        contract=True,
        source_label="component-catalog",
        props={"tree": "string"},
    ),
    _component(
        "FeatureCard",
        "feature-card",
        category="component-catalog",
        contract=True,
        source_label="component-catalog",
        props={"title": "string", "description": "string", "href": "string"},
    ),
    _component(
        "CardGrid",
        "card-grid",
        category="component-catalog",
        contract=True,
        source_label="component-catalog",
        props={"columns": "number", "children": "React.ReactNode"},
    ),
    _component(
        "Tabs",
        "tabs",
        required=True,
        category="markdown-mdx",
        contract=True,
        source_label="markdown-mdx",
        props={"defaultValue": "string", "children": "React.ReactNode"},
    ),
    _component(
        "TabItem",
        "tabs",
        required=True,
        category="markdown-mdx",
        contract=True,
        source_label="markdown-mdx",
        props={
            "label": "string",
            "value": "string",
            "children": "React.ReactNode",
        },
    ),
    _component(
        "Accordion",
        "accordion",
        category="component-catalog",
        contract=True,
        source_label="component-catalog",
        props={"children": "React.ReactNode"},
    ),
    _component(
        "AccordionItem",
        "accordion",
        category="component-catalog",
        contract=True,
        source_label="component-catalog",
        props={"title": "string", "children": "React.ReactNode"},
    ),
    _component(
        "Timeline",
        "timeline",
        category="component-catalog",
        contract=True,
        source_label="component-catalog",
        props={"children": "React.ReactNode"},
    ),
    _component(
        "TimelineItem",
        "timeline",
        category="component-catalog",
        contract=True,
        source_label="component-catalog",
        props={
            "date": "string",
            "title": "string",
            "badge": "string",
            "description": "string",
        },
    ),
    _component("TerminalSession", "terminal-session"),
    _component("ConfigPanel", "config-panel"),
    _component("BuildArtifact", "build-artifact"),
    _component("DocPreview", "doc-preview"),
    _component("PreviewCode", "preview-code"),
    _component("CommandGrid", "command-grid"),
    _component("CommandCard", "command-grid"),
    _component("BeforeAfter", "before-after"),
    _component(
        "Swot",
        "swot",
        contract=True,
        source_label="component-catalog",
        props={
            "strengths": "string[]",
            "weaknesses": "string[]",
            "opportunities": "string[]",
            "threats": "string[]",
            "title": "string | undefined",
        },
    ),
    _component(
        "CompareMatrix",
        "compare-matrix",
        contract=True,
        source_label="component-catalog",
        props={
            "tools": "string[]",
            "rows": "{ feature: string; values: (boolean | string)[]; note?: string }[]",
            "caption": "string | undefined",
            "highlight": "number | undefined",
        },
    ),
    _component(
        "PullQuote",
        "pull-quote",
        contract=True,
        source_label="component-catalog",
        props={
            "children": "ReactNode",
            "kicker": "string | undefined",
            "attribution": "string | undefined",
        },
    ),
    _component(
        "StatStrip",
        "stat-strip",
        contract=True,
        source_label="component-catalog",
        props={
            "stats": "{ value: string; label: string; detail?: string }[]",
        },
    ),
    _component("Checklist", "checklist"),
    _component("HookMap", "hook-map"),
    _component("ComponentIndex", "component-index"),
    _component(
        "ApiReferenceIndex",
        "api-reference-index",
        required=True,
        category="api-reference",
        contract=True,
        source_label="api-reference",
        props={
            "modules": (
                "Array<{ name: string; classes: number; "
                "functions: number; path: string }>"
            )
        },
    ),
    _component("ComparisonMatrix", "comparison-matrix"),
    _component("UnavailableFeature", "unavailable-feature"),
    _component(
        "BrowserFrame",
        "browser-frame",
        contract=True,
        source_label="component-catalog",
        props={
            "url": "string",
            "label": "string | undefined",
            "children": "React.ReactNode",
        },
    ),
)


def register_builtin_components(registry: ExtensionRegistry) -> None:
    """Register every builtin component into ``registry`` in manifest order."""
    for component in BUILTIN_COMPONENTS:
        registry.register_component(
            component.name,
            import_path=component.import_path,
            export_name=component.export_name,
            expose_mdx=component.expose_mdx,
            props=component.props,
            required=component.required,
            category=component.category,
            contract=component.contract,
            source_label=component.source_label,
            origin="builtin",
        )
