from folio.config import Config
from folio.generator.llm_output import generate_llms_full_txt, generate_llms_txt
from folio.ir import (
    ArgIR,
    DocstringIR,
    FunctionIR,
    ModuleIR,
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


def test_generate_llms_txt_skips_disabled_docs():
    config = _make_config()
    docs = [
        MarkdownResult(
            content="# Roadmap\n\nHidden feature guide.",
            frontmatter={"title": "Roadmap"},
            route="roadmap",
        )
    ]

    result = generate_llms_txt(config, [], docs)

    assert "Roadmap" not in result
    assert "Hidden feature guide" not in result


def test_generate_llms_txt_skips_disabled_api_modules():
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
            content="# Roadmap\n\nThis guide explains the experimental feature.",
            frontmatter={"title": "Roadmap"},
            route="roadmap",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert "Roadmap" not in result
    assert "This guide explains the experimental feature." not in result
    assert result == ""


def test_generate_llms_full_txt_does_not_env_enable_disabled_docs():
    docs = [
        MarkdownResult(
            content="# Roadmap\n\nExperimental guide content.",
            frontmatter={"title": "Roadmap"},
            route="roadmap",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert "Experimental guide content." not in result
    assert result == ""


def test_generate_llms_full_txt_skips_landing_docs():
    docs = [
        MarkdownResult(
            content="# Landing Page\n\nConfigure the optional homepage.",
            frontmatter={"title": "Landing Page"},
            route="landing",
        )
    ]

    result = generate_llms_full_txt([], docs)

    assert "Landing Page" not in result
    assert "Configure the optional homepage." not in result
    assert result == ""


def test_generate_llms_full_txt_skips_disabled_api_modules():
    result = generate_llms_full_txt([_make_disabled_module()], [])

    assert "folio.plugins.roadmap" not in result
    assert "Roadmap plugin internals." not in result
    assert result == ""


def test_generate_llms_full_txt_empty():
    result = generate_llms_full_txt([], [])
    assert result == ""
