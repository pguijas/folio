from folio.config import Config
from folio.generator.llm_output import generate_llms_full_txt, generate_llms_txt
from folio.ir import (
    ArgIR,
    ClassIR,
    DocstringIR,
    FunctionIR,
    ModuleIR,
    RaiseIR,
    ReturnIR,
)
from folio.parser.markdown_parser import MarkdownResult


def _make_config():
    return Config(
        project_name="TestProject",
        project_version="1.0.0",
    )


def _make_module():
    func = FunctionIR(
        name="greet",
        args=[ArgIR(name="name", type="str", default=None, description="The name.")],
        returns=ReturnIR(type="str", description="A greeting."),
        raises=[],
        decorators=[],
        docstring=DocstringIR(short_description="Greet someone."),
        is_async=False,
        source_file="test.py",
        line_number=1,
    )
    return ModuleIR(
        name="mylib.utils",
        docstring=DocstringIR(short_description="Utility module."),
        classes=[],
        functions=[func],
        constants=[],
        source_file="utils.py",
    )


def _make_disabled_module():
    return ModuleIR(
        name="folio.plugins.roadmap",
        docstring=DocstringIR(short_description="Roadmap plugin internals."),
        classes=[],
        functions=[],
        constants=[],
        source_file="roadmap.py",
    )


def _make_doc():
    return MarkdownResult(
        content="# Introduction\n\nWelcome to the docs.",
        frontmatter={"title": "Introduction"},
        route="introduction",
    )


def test_generate_llms_txt():
    config = _make_config()
    modules = [_make_module()]
    docs = [_make_doc()]
    result = generate_llms_txt(config, modules, docs)
    assert "# TestProject" in result
    assert "## Docs" in result
    assert "[Introduction](/docs/introduction/)" in result
    assert "## API Reference" in result
    assert "[mylib.utils](/docs/api-reference/mylib/utils/)" in result


def test_generate_llms_txt_uses_exported_route_paths():
    config = _make_config()
    docs = [
        MarkdownResult(
            content="# Overview\n\nWelcome.",
            frontmatter={"title": "Overview"},
            route="index",
        ),
        MarkdownResult(
            content="# Components\n\nCatalog.",
            frontmatter={"title": "Components"},
            route="components/index",
        ),
    ]
    modules = [
        ModuleIR(
            name="folio.generator.llm_output",
            docstring=DocstringIR(short_description="LLM output helpers."),
            classes=[],
            functions=[],
            constants=[],
            source_file="llm_output.py",
        )
    ]

    result = generate_llms_txt(config, modules, docs)

    assert "[Overview](/docs/)" in result
    assert "[Components](/docs/components/)" in result
    assert (
        "[folio.generator.llm_output](/docs/api-reference/folio/generator/llm_output/)"
        in result
    )
    assert "/components/index" not in result
    assert "/api-reference/folio.generator.llm_output" not in result


def test_generate_llms_txt_uses_configured_site_url():
    config = Config(
        project_name="TestProject",
        project_version="1.0.0",
        site_url="https://example.com/folio/",
    )

    result = generate_llms_txt(config, [_make_module()], [_make_doc()])

    assert "[Introduction](https://example.com/folio/docs/introduction/)" in result
    assert (
        "[mylib.utils](https://example.com/folio/docs/api-reference/mylib/utils/)"
        in result
    )


def test_generate_llms_txt_uses_configured_docs_route_base():
    config = Config(
        project_name="TestProject",
        project_version="1.0.0",
        site_url="https://example.com",
        docs_route_base="/reference/docs",
    )

    result = generate_llms_txt(config, [_make_module()], [_make_doc()])

    assert "[Introduction](https://example.com/reference/docs/introduction/)" in result
    assert (
        "[mylib.utils](https://example.com/reference/docs/api-reference/mylib/utils/)"
        in result
    )


def test_generate_llms_txt_skips_disabled_docs():
    config = _make_config()
    docs = [
        MarkdownResult(
            content="# Versioning\n\nHidden feature guide.",
            frontmatter={"title": "Versioning"},
            route="versioning",
        )
    ]

    result = generate_llms_txt(config, [], docs)

    assert "Versioning" not in result
    assert "Hidden feature guide" not in result


def test_generate_llms_txt_includes_released_roadmap_doc():
    config = _make_config()
    docs = [
        MarkdownResult(
            content="# Roadmap\n\nShipped plugin guide.",
            frontmatter={"title": "Roadmap"},
            route="roadmap",
        )
    ]

    result = generate_llms_txt(config, [], docs)

    assert "Roadmap" in result


def test_generate_llms_txt_skips_disabled_api_modules(monkeypatch):
    from folio import features

    monkeypatch.setattr(
        features, "MVP_DISABLED_API_MODULES", {"folio.plugins.roadmap": "roadmap"}
    )
    config = _make_config()

    result = generate_llms_txt(config, [_make_disabled_module()], [])

    assert "folio.plugins.roadmap" not in result
    assert "/docs/api-reference/folio/plugins/roadmap/" not in result


def test_generate_llms_txt_empty():
    config = _make_config()
    result = generate_llms_txt(config, [], [])
    assert "# TestProject" in result
    assert "## Docs" not in result
    assert "## API Reference" not in result


def test_generate_llms_full_txt():
    modules = [_make_module()]
    docs = [_make_doc()]
    result = generate_llms_full_txt(modules, docs)
    assert "---" in result
    assert "# Introduction" in result
    assert "Welcome to the docs." in result
    assert "def greet(" in result
    assert "Greet someone." in result


def test_generate_llms_full_txt_skips_disabled_docs():
    docs = [
        MarkdownResult(
            content="# Versioning\n\nThis guide explains the experimental feature.",
            frontmatter={"title": "Versioning"},
            route="versioning",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert "Versioning" not in result
    assert "This guide explains the experimental feature." not in result
    assert result == ""


def test_generate_llms_full_txt_does_not_env_enable_disabled_docs():
    docs = [
        MarkdownResult(
            content="# Versioning\n\nExperimental guide content.",
            frontmatter={"title": "Versioning"},
            route="versioning",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert "Experimental guide content." not in result
    assert result == ""


def test_generate_llms_full_txt_skips_gated_feature_docs():
    docs = [
        MarkdownResult(
            content="# Internationalization\n\nExperimental locales guide.",
            frontmatter={"title": "Internationalization"},
            route="i18n",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert "Internationalization" not in result
    assert result == ""


def test_generate_llms_full_txt_includes_landing_docs():
    docs = [
        MarkdownResult(
            content="# Landing Page\n\nConfigure the optional homepage.",
            frontmatter={"title": "Landing Page"},
            route="landing",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert "Landing Page" in result
    assert "Configure the optional homepage." in result


def test_generate_llms_full_txt_skips_disabled_api_modules(monkeypatch):
    from folio import features

    monkeypatch.setattr(
        features, "MVP_DISABLED_API_MODULES", {"folio.plugins.roadmap": "roadmap"}
    )
    result = generate_llms_full_txt([_make_disabled_module()], [])

    assert "folio.plugins.roadmap" not in result
    assert "Roadmap plugin internals." not in result
    assert result == ""


def test_generate_llms_full_txt_empty():
    result = generate_llms_full_txt([], [])
    assert result == ""


def _make_rich_module():
    """A module exercising every IR field the llms-full.txt writer renders."""
    func = FunctionIR(
        name="greet",
        args=[
            ArgIR(name="name", type="str", default=None, description="The name."),
            ArgIR(name="times", type="int", default="1", description="Repeat | count."),
        ],
        returns=ReturnIR(type="str", description="A greeting."),
        raises=[RaiseIR(exception="ValueError", description="If name is empty.")],
        decorators=[],
        docstring=DocstringIR(
            short_description="Greet someone.",
            long_description="Builds the greeting string.",
            examples=["greet('ada')"],
            notes=["Not thread safe."],
        ),
        is_async=False,
        source_file="/proj/mylib/utils.py",
        line_number=12,
    )
    method = FunctionIR(
        name="run",
        args=[],
        returns=None,
        raises=[],
        decorators=[],
        docstring=DocstringIR(short_description="Run the greeter."),
        is_async=False,
        source_file="/proj/mylib/utils.py",
        line_number=40,
    )
    cls = ClassIR(
        name="Greeter",
        bases=["object"],
        decorators=[],
        docstring=DocstringIR(short_description="Greets people."),
        methods=[method],
        class_vars=[],
        source_file="/proj/mylib/utils.py",
        line_number=30,
    )
    return ModuleIR(
        name="mylib.utils",
        docstring=DocstringIR(short_description="Utility module."),
        classes=[cls],
        functions=[func],
        constants=[],
        source_file="/proj/mylib/utils.py",
    )


def test_generate_llms_txt_includes_doc_descriptions():
    config = _make_config()
    docs = [
        MarkdownResult(
            content="# Introduction\n\nWelcome to the docs.",
            frontmatter={
                "title": "Introduction",
                "description": "Welcome to the docs.",
            },
            route="introduction",
        )
    ]

    result = generate_llms_txt(config, [], docs)

    assert "- [Introduction](/docs/introduction/): Welcome to the docs." in result


def test_generate_llms_txt_collapses_multiline_descriptions():
    config = _make_config()
    docs = [
        MarkdownResult(
            content="# Introduction\n\nWelcome.",
            frontmatter={"title": "Introduction", "description": "Line one\nline two"},
            route="introduction",
        )
    ]

    result = generate_llms_txt(config, [], docs)

    assert "- [Introduction](/docs/introduction/): Line one line two" in result


def test_generate_llms_txt_omits_separator_without_description():
    config = _make_config()

    result = generate_llms_txt(config, [], [_make_doc()])

    assert "- [Introduction](/docs/introduction/)\n" in result
    assert "- [Introduction](/docs/introduction/):" not in result


def test_generate_llms_txt_includes_module_descriptions():
    config = _make_config()

    result = generate_llms_txt(config, [_make_module()], [])

    assert (
        "- [mylib.utils](/docs/api-reference/mylib/utils/): Utility module." in result
    )


def test_generate_llms_txt_includes_hero_summary_blockquote():
    config = Config(
        project_name="TestProject",
        project_version="1.0.0",
        landing_hero_description="One config file builds the site.",
    )

    result = generate_llms_txt(config, [], [])

    assert result.startswith("# TestProject\n\n> One config file builds the site.\n")


def test_generate_llms_txt_omits_blockquote_without_hero_description():
    result = generate_llms_txt(_make_config(), [], [])

    assert ">" not in result


def test_generate_llms_full_txt_does_not_repeat_the_document_h1():
    result = generate_llms_full_txt([], [_make_doc()])

    assert result.count("# Introduction") == 1
    assert "Welcome to the docs." in result


def test_generate_llms_full_txt_adds_heading_when_document_has_none():
    docs = [
        MarkdownResult(
            content="Just a paragraph.",
            frontmatter={"title": "Untitled Page"},
            route="untitled",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert result.startswith("# Untitled Page\n")
    assert "Just a paragraph." in result


def test_generate_llms_full_txt_falls_back_to_route_without_title():
    docs = [
        MarkdownResult(content="Body only.", frontmatter={}, route="orphan"),
    ]

    result = generate_llms_full_txt([], docs)

    assert result.startswith("# orphan\n")


def test_generate_llms_full_txt_strips_mdx_syntax():
    docs = [
        MarkdownResult(
            content=(
                "import { Callout } from 'nextra/components'\n"
                "export const meta = {}\n"
                "\n"
                "# Guide\n"
                "\n"
                "<Callout type='info'>Read this.</Callout>\n"
                "\n"
                "Plain body.\n"
            ),
            frontmatter={"title": "Guide"},
            route="guide",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert "import {" not in result
    assert "export const" not in result
    assert "<Callout" not in result
    assert "</Callout>" not in result
    assert "Read this." in result
    assert "Plain body." in result
    assert result.startswith("# Guide\n")


def test_generate_llms_full_txt_finds_h1_below_mdx_imports():
    docs = [
        MarkdownResult(
            content="import { Tabs } from 'x'\n\n# Real Heading\n\nBody.",
            frontmatter={"title": "Frontmatter Title"},
            route="page",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert result.startswith("# Real Heading\n")
    assert "Frontmatter Title" not in result


def test_generate_llms_full_txt_includes_section_urls():
    config = Config(
        project_name="TestProject",
        project_version="1.0.0",
        site_url="https://example.com",
    )

    result = generate_llms_full_txt([_make_module()], [_make_doc()], config)

    assert "URL: https://example.com/docs/introduction/" in result
    assert "URL: https://example.com/docs/api-reference/mylib/utils/" in result


def test_generate_llms_full_txt_urls_follow_docs_route_base():
    config = Config(
        project_name="TestProject",
        project_version="1.0.0",
        docs_route_base="/reference/docs",
    )

    result = generate_llms_full_txt([_make_module()], [_make_doc()], config)

    assert "URL: /reference/docs/introduction/" in result
    assert "URL: /reference/docs/api-reference/mylib/utils/" in result


def test_generate_llms_full_txt_omits_urls_without_config():
    result = generate_llms_full_txt([_make_module()], [_make_doc()])

    assert "URL:" not in result


def test_generate_llms_full_txt_renders_argument_table():
    result = generate_llms_full_txt([_make_rich_module()], [])

    assert "| Parameter | Type | Default | Description |" in result
    assert "| `name` | `str` |  | The name. |" in result
    assert "| `times` | `int` | `1` | Repeat \\| count. |" in result


def test_generate_llms_full_txt_renders_returns_raises_examples_and_notes():
    result = generate_llms_full_txt([_make_rich_module()], [])

    assert "**Returns:** `str` - A greeting." in result
    assert "**Raises:**\n- `ValueError` - If name is empty." in result
    assert "**Examples:**\n\n```python\ngreet('ada')\n```" in result
    assert "**Notes:**\n- Not thread safe." in result
    assert "Builds the greeting string." in result


def test_generate_llms_full_txt_cites_source_file_and_line():
    config = Config(
        project_name="TestProject",
        project_version="1.0.0",
        project_dir="/proj",
    )

    result = generate_llms_full_txt([_make_rich_module()], [], config)

    assert "Source: mylib/utils.py:12" in result
    assert "Source: mylib/utils.py:30" in result
    assert "/proj/mylib" not in result


def test_generate_llms_full_txt_shortens_unrooted_absolute_paths():
    result = generate_llms_full_txt([_make_rich_module()], [])

    assert "Source: utils.py:12" in result
    assert "/proj/" not in result


def test_generate_llms_full_txt_describes_class_methods():
    result = generate_llms_full_txt([_make_rich_module()], [])

    assert "### run" in result
    assert "Run the greeter." in result
    assert "## Greeter" in result
    assert "Greets people." in result


def test_generate_llms_full_txt_separates_sections_with_blank_lines():
    docs = [
        _make_doc(),
        MarkdownResult(
            content="# Second\n\nMore text.",
            frontmatter={"title": "Second"},
            route="second",
        ),
    ]

    result = generate_llms_full_txt([], docs)

    assert "\n\n---\n\n" in result
    assert "Welcome to the docs.\n---" not in result
