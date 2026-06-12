import re

from folio.generator.sidebar import generate_meta_files, generate_meta_json
from folio.ir import DocstringIR, ModuleIR


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


def test_nav_slugification():
    nav = ["Introduction", "API Reference", "Getting Started"]
    result = generate_meta_json(nav)
    meta = _parse_meta_ts(result)
    assert "introduction" in meta
    assert meta["introduction"] == "Introduction"
    assert "api-reference" in meta
    assert meta["api-reference"] == "API Reference"
    assert "getting-started" in meta
    assert meta["getting-started"] == "Getting Started"


def test_empty_nav():
    result = generate_meta_json([])
    meta = _parse_meta_ts(result)
    assert meta == {}


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

    api_meta_content = files["api-reference/_meta.ts"]
    _assert_hidden_index(api_meta_content)
    api_meta = _parse_meta_ts(api_meta_content)
    assert "mylib" in api_meta
    assert api_meta["mylib"] == "Mylib"

    assert "api-reference/mylib/_meta.ts" in files
    mylib_meta = _parse_meta_ts(files["api-reference/mylib/_meta.ts"])
    assert "utils" in mylib_meta
    assert "core" in mylib_meta


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
    from folio.parser.markdown_parser import MarkdownResult

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


def test_deep_nested_doc_pages_generate_recursive_meta_files():
    """Docs nested more than one level need one _meta.ts per directory."""
    from folio.parser.markdown_parser import MarkdownResult

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
