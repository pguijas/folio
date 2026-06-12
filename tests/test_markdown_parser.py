import pytest

from folio.parser.markdown_parser import parse_markdown_directory, parse_markdown_file


def test_parse_markdown_basic(tmp_path):
    md_file = tmp_path / "intro.md"
    md_file.write_text("# Introduction\n\nWelcome to the project.\n")
    result = parse_markdown_file(md_file)
    assert "# Introduction" in result.content
    assert result.frontmatter["title"] == "Introduction"
    assert result.route == "intro"


def test_parse_markdown_with_existing_frontmatter(tmp_path):
    md_file = tmp_path / "guide.md"
    md_file.write_text(
        "---\ntitle: My Guide\ndescription: A guide.\n---\n\n# Guide\n\nContent here.\n"
    )
    result = parse_markdown_file(md_file)
    assert result.frontmatter["title"] == "My Guide"
    assert result.frontmatter["description"] == "A guide."
    assert "# Guide" in result.content


def test_parse_markdown_directory(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n\nWelcome.\n")
    (docs / "install.md").write_text("# Installation\n\nSteps here.\n")
    sub = docs / "guides"
    sub.mkdir()
    (sub / "quickstart.md").write_text("# Quickstart\n\nFast start.\n")
    results = parse_markdown_directory(str(docs))
    routes = {r.route for r in results}
    assert "index" in routes
    assert "install" in routes
    assert "guides/quickstart" in routes


def test_parse_markdown_directory_routes_readme_as_index(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "README.md").write_text("# Home\n\nWelcome.\n")
    sub = docs / "guides"
    sub.mkdir()
    (sub / "README.md").write_text("# Guides\n\nGuide index.\n")
    (sub / "quickstart.md").write_text("# Quickstart\n\nFast start.\n")

    results = parse_markdown_directory(str(docs))
    routes = {r.route for r in results}

    assert "index" in routes
    assert "guides/index" in routes
    assert "guides/quickstart" in routes
    assert "README" not in routes
    assert "guides/README" not in routes


def test_parse_markdown_directory_warns_that_rst_is_migration_only(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "index.md").write_text("# Home\n\nWelcome.\n")
    (docs / "legacy.rst").write_text("Legacy\n======\n")

    with pytest.warns(UserWarning, match="convert .rst files to Markdown"):
        results = parse_markdown_directory(str(docs))

    assert [result.route for result in results] == ["index"]


def test_parse_markdown_extracts_description(tmp_path):
    md_file = tmp_path / "page.md"
    md_file.write_text(
        "# Title\n\nFirst paragraph is the description.\n\nMore content.\n"
    )
    result = parse_markdown_file(md_file)
    assert result.frontmatter["description"] == "First paragraph is the description."
