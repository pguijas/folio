import re

from folio_docs.docs.sidebar import generate_meta_files
from folio_docs.ir import DocstringIR, ModuleIR


def _parse_meta_ts(ts_content: str) -> dict[str, str]:
    """Parse a _meta.ts `export default { ... }` string into a dict."""
    result = {}
    for match in re.finditer(r'^  "([^"]+)":\s*"([^"]*)",?$', ts_content, re.MULTILINE):
        result[match.group(1)] = match.group(2)
    return result


def _assert_hidden_index(ts_content: str) -> None:
    assert re.search(
        r'"index":\s*\{\s*"display":\s*"hidden",?\s*\}',
        ts_content,
        re.DOTALL,
    )
    assert '"index": "Overview"' not in ts_content


def _assert_collapsed_folder(
    ts_content: str,
    slug: str,
    title: str,
) -> None:
    assert re.search(
        rf'"{re.escape(slug)}":\s*\{{\s*'
        rf'"title":\s*"{re.escape(title)}",\s*'
        r'"theme":\s*\{\s*'
        r'"collapsed":\s*true,?\s*'
        r"\},?\s*"
        r"\}",
        ts_content,
        re.DOTALL,
    )


def test_module_based_api_reference_meta():
    modules = [
        ModuleIR(
            name="mylib.utils",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="utils.py",
        ),
        ModuleIR(
            name="mylib.core",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="core.py",
        ),
    ]
    nav = ["Introduction", "API Reference"]
    files = generate_meta_files(nav, modules)

    assert "_meta.ts" in files
    assert "api-reference/_meta.ts" in files
    root_meta = _parse_meta_ts(files["_meta.ts"])
    assert root_meta["api-reference"] == "Source Code"

    api_meta_content = files["api-reference/_meta.ts"]
    _assert_hidden_index(api_meta_content)
    api_meta = _parse_meta_ts(api_meta_content)
    assert "mylib" in api_meta
    assert api_meta["mylib"] == "Mylib"

    assert "api-reference/mylib/_meta.ts" in files
    mylib_meta = _parse_meta_ts(files["api-reference/mylib/_meta.ts"])
    assert "utils" in mylib_meta
    assert "core" in mylib_meta


def test_nav_orders_real_entries_without_creating_dead_routes():
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        ),
        MarkdownResult(
            route="quickstart",
            content="# Quick Start",
            frontmatter={"title": "Quick Start"},
        ),
    ]
    modules = [
        ModuleIR(
            name="mylib.core",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="core.py",
        )
    ]

    files = generate_meta_files(
        ["API Reference", "Quick Start", "Unknown"], modules, docs
    )
    root_meta = _parse_meta_ts(files["_meta.ts"])

    assert list(root_meta) == ["api-reference", "quickstart", "index"]
    assert "unknown" not in root_meta


def test_nav_guide_alias_keeps_authored_docs_together_before_source():
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        )
    ]
    modules = [
        ModuleIR(
            name="mylib.core",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="core.py",
        )
    ]

    files = generate_meta_files(["Guide", "Source Code"], modules, docs)

    assert list(_parse_meta_ts(files["_meta.ts"])) == ["index", "api-reference"]


def test_api_reference_meta_can_default_folders_to_collapsed():
    modules = [
        ModuleIR(
            name="mylib.utils",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="utils.py",
        ),
        ModuleIR(
            name="mylib.core",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="core.py",
        ),
    ]

    files = generate_meta_files([], modules, default_collapsed=True)

    root_meta = files["_meta.ts"]
    api_meta = files["api-reference/_meta.ts"]
    mylib_meta = files["api-reference/mylib/_meta.ts"]

    _assert_collapsed_folder(root_meta, "api-reference", "Source Code")
    _assert_collapsed_folder(api_meta, "mylib", "Mylib")
    assert '"utils": "Utils"' in mylib_meta
    assert '"core": "Core"' in mylib_meta
    assert '"open": false' not in mylib_meta


def test_hierarchical_sidebar_deep_nesting():
    modules = [
        ModuleIR(
            name="demolib.learning.aggregators.fedavg",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="fedavg.py",
        ),
        ModuleIR(
            name="demolib.learning.aggregators.fedprox",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="fedprox.py",
        ),
        ModuleIR(
            name="demolib.communication.grpc",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="grpc.py",
        ),
        ModuleIR(
            name="demolib.node",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="node.py",
        ),
    ]
    nav = ["API Reference"]
    files = generate_meta_files(nav, modules)

    api_meta = _parse_meta_ts(files["api-reference/_meta.ts"])
    assert "demolib" in api_meta

    demolib_meta = _parse_meta_ts(files["api-reference/demolib/_meta.ts"])
    assert "learning" in demolib_meta
    assert "communication" in demolib_meta
    assert "node" in demolib_meta

    learning_meta = _parse_meta_ts(files["api-reference/demolib/learning/_meta.ts"])
    assert "aggregators" in learning_meta

    agg_meta = _parse_meta_ts(
        files["api-reference/demolib/learning/aggregators/_meta.ts"]
    )
    assert "fedavg" in agg_meta
    assert "fedprox" in agg_meta

    comm_meta = _parse_meta_ts(files["api-reference/demolib/communication/_meta.ts"])
    assert "grpc" in comm_meta


def test_nested_doc_pages():
    """Test that docs in subdirectories generate separate _meta.ts files."""
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        ),
        MarkdownResult(
            route="installation",
            content="# Installation",
            frontmatter={"title": "Installation"},
        ),
        MarkdownResult(
            route="components/index",
            content="# Components",
            frontmatter={"title": "Components"},
        ),
        MarkdownResult(
            route="components/mermaid",
            content="# Mermaid",
            frontmatter={"title": "Mermaid"},
        ),
        MarkdownResult(
            route="components/callout",
            content="# Callout",
            frontmatter={"title": "Callout"},
        ),
    ]
    modules = [
        ModuleIR(
            name="mylib.core",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="core.py",
        ),
    ]
    files = generate_meta_files([], modules, docs)

    root_meta = _parse_meta_ts(files["_meta.ts"])
    assert "components" in root_meta
    assert "installation" in root_meta

    assert "components/_meta.ts" in files
    comp_meta_content = files["components/_meta.ts"]
    _assert_hidden_index(comp_meta_content)
    comp_meta = _parse_meta_ts(comp_meta_content)
    assert "index" not in comp_meta
    assert "mermaid" in comp_meta
    assert "callout" in comp_meta


def test_root_doc_pages_put_introduction_before_setup_pages():
    """Introduction should not be appended after product sections."""
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        ),
        MarkdownResult(
            route="installation",
            content="# Installation",
            frontmatter={"title": "Installation"},
        ),
        MarkdownResult(
            route="quickstart",
            content="# Quick Start",
            frontmatter={"title": "Quick Start"},
        ),
        MarkdownResult(
            route="components/index",
            content="# Components",
            frontmatter={"title": "Components"},
        ),
        MarkdownResult(
            route="introduction",
            content="# Introduction",
            frontmatter={"title": "Introduction"},
        ),
    ]

    files = generate_meta_files([], [], docs)

    assert files["_meta.ts"].splitlines() == [
        "export default {",
        '  "index": "Overview",',
        '  "introduction": "Introduction",',
        '  "installation": "Installation",',
        '  "quickstart": "Quick Start",',
        '  "components": "Components",',
        "}",
    ]


def test_root_doc_pages_put_source_code_at_the_end_after_contributing():
    """Generated source code should stay as the final root navigation entry."""
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        ),
        MarkdownResult(
            route="components/index",
            content="# Components",
            frontmatter={"title": "Components"},
        ),
        MarkdownResult(
            route="contributing",
            content="# Contributing",
            frontmatter={"title": "Contributing"},
        ),
        MarkdownResult(
            route="p2pfl_ws",
            content="# P2PFL Web Services",
            frontmatter={"title": "P2PFL Web Services"},
        ),
        MarkdownResult(
            route="tutorials/index",
            content="# Tutorials",
            frontmatter={"title": "Tutorials"},
        ),
    ]
    modules = [
        ModuleIR(
            name="mylib.core",
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file="core.py",
        ),
    ]

    files = generate_meta_files([], modules, docs)
    root_meta = _parse_meta_ts(files["_meta.ts"])

    assert list(root_meta) == [
        "index",
        "components",
        "p2pfl_ws",
        "tutorials",
        "contributing",
        "api-reference",
    ]
    assert root_meta["api-reference"] == "Source Code"


def test_ordered_doc_pages_use_document_titles():
    """Known doc pages keep their order but use the parsed page title."""
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="index",
            content="# Introduction",
            frontmatter={"title": "Introduction"},
        ),
        MarkdownResult(
            route="installation",
            content="# Installation",
            frontmatter={"title": "Installation"},
        ),
        MarkdownResult(
            route="quickstart",
            content="# First Experiment",
            frontmatter={"title": "First Experiment"},
        ),
    ]

    files = generate_meta_files([], [], docs)
    root_meta = _parse_meta_ts(files["_meta.ts"])

    assert list(root_meta) == ["index", "installation", "quickstart"]
    assert root_meta["index"] == "Introduction"
    assert root_meta["quickstart"] == "First Experiment"


def test_doc_meta_can_default_folders_to_collapsed():
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        ),
        MarkdownResult(
            route="components/index",
            content="# Components",
            frontmatter={"title": "Components"},
        ),
        MarkdownResult(
            route="components/callout",
            content="# Callout",
            frontmatter={"title": "Callout"},
        ),
    ]

    files = generate_meta_files([], [], docs, default_collapsed=True)

    root_meta = files["_meta.ts"]
    components_meta = files["components/_meta.ts"]

    _assert_collapsed_folder(root_meta, "components", "Components")
    assert '"callout": "Callout"' in components_meta
    assert '"open": false' not in components_meta


def test_deep_nested_doc_pages_generate_recursive_meta_files():
    """Docs nested more than one level need one _meta.ts per directory."""
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="source/index",
            content="# Source",
            frontmatter={"title": "Source"},
        ),
        MarkdownResult(
            route="source/common_errors/index",
            content="# Common Errors",
            frontmatter={"title": "Common Errors"},
        ),
        MarkdownResult(
            route="source/common_errors/tensorflow_hang",
            content="# TensorFlow Hang",
            frontmatter={"title": "TensorFlow Hang"},
        ),
        MarkdownResult(
            route="source/components/learner/aggregators",
            content="# Aggregators",
            frontmatter={"title": "Aggregators"},
        ),
    ]

    files = generate_meta_files([], [], docs)

    root_meta = _parse_meta_ts(files["_meta.ts"])
    source_meta_content = files["source/_meta.ts"]
    common_errors_meta_content = files["source/common_errors/_meta.ts"]
    _assert_hidden_index(source_meta_content)
    _assert_hidden_index(common_errors_meta_content)
    source_meta = _parse_meta_ts(source_meta_content)
    common_errors_meta = _parse_meta_ts(common_errors_meta_content)
    components_meta = _parse_meta_ts(files["source/components/_meta.ts"])
    learner_meta = _parse_meta_ts(files["source/components/learner/_meta.ts"])

    assert root_meta["source"] == "Source"
    assert source_meta == {
        "common_errors": "Common Errors",
        "components": "Components",
    }
    assert common_errors_meta == {
        "tensorflow_hang": "TensorFlow Hang",
    }
    assert components_meta == {"learner": "Learner"}
    assert learner_meta == {"aggregators": "Aggregators"}


def _assert_hidden_entry(ts_content: str, slug: str) -> None:
    assert re.search(
        rf'"{re.escape(slug)}":\s*\{{\s*"display":\s*"hidden",?\s*\}}',
        ts_content,
        re.DOTALL,
    )


def test_unlisted_docs_leave_the_sidebar_with_their_folders():
    """An unlisted page is hidden, and so is a folder holding only such pages.

    Omission is not enough: Nextra lists content pages by default and _meta.ts
    only orders and hides, so the delist must be written out — the same
    `{"display": "hidden"}` nested index pages already get. A folder that also
    holds a listed page stays visible; only its unlisted pages hide.
    """
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        ),
        MarkdownResult(
            route="guide/intro",
            content="# Intro",
            frontmatter={"title": "Intro"},
        ),
        MarkdownResult(
            route="guide/scratch",
            content="# Scratch",
            frontmatter={"title": "Scratch"},
            unlisted=True,
        ),
        MarkdownResult(
            route="kanban/one-card/compared",
            content="# Compared",
            frontmatter={"title": "Compared"},
            unlisted=True,
        ),
        MarkdownResult(
            route="kanban/one-card/notes",
            content="# Notes",
            frontmatter={"title": "Notes"},
            unlisted=True,
        ),
    ]

    files = generate_meta_files([], [], docs)

    root_meta = files["_meta.ts"]
    assert '"index": "Overview"' in root_meta
    assert '"guide": "Guide"' in root_meta
    _assert_hidden_entry(root_meta, "kanban")

    guide_meta = files["guide/_meta.ts"]
    assert '"intro": "Intro"' in guide_meta
    _assert_hidden_entry(guide_meta, "scratch")

    _assert_hidden_entry(files["kanban/_meta.ts"], "one-card")
    card_meta = files["kanban/one-card/_meta.ts"]
    _assert_hidden_entry(card_meta, "compared")
    _assert_hidden_entry(card_meta, "notes")


def test_doc_sidebar_titles_strip_emoji_from_frontmatter():
    """Sidebar labels should stay textual even when page headings use emoji."""
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="components/index",
            content="# 🏛️ Components",
            frontmatter={"title": "🏛️ Components"},
        ),
        MarkdownResult(
            route="components/commands",
            content="# ⌨️ Commands",
            frontmatter={"title": "⌨️ Commands"},
        ),
        MarkdownResult(
            route="components/state",
            content="# 🚦 Node State",
            frontmatter={"title": "🚦 Node State"},
        ),
        MarkdownResult(
            route="tutorials/certificates",
            content="# 🛡️ Communication Encryption with Mutual TLS",
            frontmatter={"title": "🛡️ Communication Encryption with Mutual TLS"},
        ),
    ]

    files = generate_meta_files([], [], docs)

    root_meta = _parse_meta_ts(files["_meta.ts"])
    components_meta = _parse_meta_ts(files["components/_meta.ts"])
    tutorials_meta = _parse_meta_ts(files["tutorials/_meta.ts"])

    assert root_meta["components"] == "Components"
    assert components_meta == {
        "commands": "Commands",
        "state": "Node State",
    }
    assert tutorials_meta == {
        "certificates": "Communication Encryption with Mutual TLS",
    }
    assert "🏛️" not in files["_meta.ts"]
    assert "⌨️" not in files["components/_meta.ts"]
    assert "🛡️" not in files["tutorials/_meta.ts"]


def test_generated_meta_ts_shape_is_a_stable_template_contract():
    """Custom templates may rely on generated _meta.ts ordering and shape."""
    from folio_docs.parser.markdown_parser import MarkdownResult

    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        ),
        MarkdownResult(
            route="quickstart",
            content="# Quick Start",
            frontmatter={"title": "Quick Start"},
        ),
        MarkdownResult(
            route="components/index",
            content="# Components",
            frontmatter={"title": "Components"},
        ),
        MarkdownResult(
            route="components/tabs",
            content="# Tabs",
            frontmatter={"title": "Tabs"},
        ),
    ]

    files = generate_meta_files([], [], docs)

    assert files["_meta.ts"].splitlines() == [
        "export default {",
        '  "index": "Overview",',
        '  "quickstart": "Quick Start",',
        '  "components": "Components",',
        "}",
    ]
    assert files["components/_meta.ts"].splitlines() == [
        "export default {",
        '  "index": {',
        '    "display": "hidden",',
        "  },",
        '  "tabs": "Tabs",',
        "}",
    ]
    for content in files.values():
        assert '"open"' not in content
        assert '"defaultCollapsed"' not in content


def test_plugins_group_orders_the_trust_page_after_writing_plugins():
    """The plugin trust page is a registered page in the Plugins group."""
    from folio_docs.parser.markdown_parser import MarkdownResult

    pages = [
        ("landing", "Landing Page"),
        ("trust", "Trust & Safety"),
        ("index", "Plugins"),
        ("catalog", "Catalog"),
        ("roadmap", "Roadmap"),
        ("authoring", "Writing Plugins"),
    ]
    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        ),
        *[
            MarkdownResult(
                route=f"plugins/{slug}",
                content=f"# {title}",
                frontmatter={"title": title},
            )
            for slug, title in pages
        ],
    ]

    files = generate_meta_files([], [], docs)

    assert files["plugins/_meta.ts"].splitlines() == [
        "export default {",
        '  "index": {',
        '    "display": "hidden",',
        "  },",
        '  "catalog": "Catalog",',
        '  "authoring": "Writing Plugins",',
        '  "trust": "Trust & Safety",',
        '  "roadmap": "Roadmap",',
        '  "landing": "Landing Page",',
        "}",
    ]


def test_plugin_trust_page_exists_for_its_sidebar_entry():
    """Every ordered slug needs a page; the trust page must not be a dead entry."""
    from pathlib import Path

    from folio_docs.docs.sidebar import _DOC_PAGE_ORDER

    plugins_group = next(entry for entry in _DOC_PAGE_ORDER if entry[0] == "plugins")
    slugs = [entry[0] for entry in plugins_group[2]]
    assert slugs.index("trust") == slugs.index("authoring") + 1

    docs_dir = Path(__file__).resolve().parents[1] / "docs" / "guide" / "plugins"
    assert (docs_dir / "trust.md").is_file()


def test_nested_section_orders_by_declaration_not_alphabetically():
    """A declared child group orders its own pages."""
    from folio_docs.parser.markdown_parser import MarkdownResult

    pages = [
        ("custom-templates", "Custom Templates"),
        ("theme-packages", "Theme Packages"),
        ("index", "Theming"),
        ("personalization", "Personalization"),
    ]
    docs = [
        MarkdownResult(
            route="index",
            content="# Overview",
            frontmatter={"title": "Overview"},
        ),
        *[
            MarkdownResult(
                route=f"theming/{slug}",
                content=f"# {title}",
                frontmatter={"title": title},
            )
            for slug, title in pages
        ],
    ]

    files = generate_meta_files([], [], docs)

    assert files["theming/_meta.ts"].splitlines() == [
        "export default {",
        '  "index": {',
        '    "display": "hidden",',
        "  },",
        '  "personalization": "Personalization",',
        '  "theme-packages": "Theme Packages",',
        '  "custom-templates": "Custom Templates",',
        "}",
    ]


def test_order_for_dir_returns_slug_title_pairs_at_every_depth():
    """Callers unpack 2-tuples, so nesting must not leak a child's own children."""
    from folio_docs.docs.sidebar import _order_for_dir

    for path in [(), ("plugins",), ("theming",)]:
        assert all(len(entry) == 2 for entry in _order_for_dir(path)), path

    assert ("theming", "Theming") in _order_for_dir(())
    assert [slug for slug, _ in _order_for_dir(("theming",))] == [
        "index",
        "personalization",
        "theme-packages",
        "custom-templates",
    ]


def test_order_for_dir_returns_nothing_for_an_undeclared_path():
    """Undeclared directories keep their discovery order instead of guessing."""
    from folio_docs.docs.sidebar import _order_for_dir

    assert _order_for_dir(("plugins", "landing")) == []
    assert _order_for_dir(("theming", "nope")) == []
    assert _order_for_dir(("nope",)) == []
