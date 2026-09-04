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


def test_description_skips_an_mdx_comment_and_a_lone_component(tmp_path):
    """A comment and a bare component are not sentences about the page.

    `folio kanban init` writes exactly this page, and its description used to
    be the comment explaining the page to whoever opened the file.
    """
    md_file = tmp_path / "index.md"
    md_file.write_text(
        "---\ntitle: Board\n---\n\n"
        "{/* The board renders from board/cards/*.md at build time.\n"
        "    Write above or below it. */}\n\n"
        "<KanbanBoard />\n"
    )
    result = parse_markdown_file(md_file)
    assert "description" not in result.frontmatter


def test_description_still_reads_prose_around_a_component(tmp_path):
    md_file = tmp_path / "index.md"
    md_file.write_text(
        "---\ntitle: Board\n---\n\n<KanbanBoard />\n\nWhat the team is doing.\n"
    )
    result = parse_markdown_file(md_file)
    assert result.frontmatter["description"] == "What the team is doing."
