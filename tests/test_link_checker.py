"""Tests for the build-time link checker."""

from pathlib import Path

from folio.link_checker import _normalize_target, check_links


class TestNormalizeTarget:
    """Unit tests for _normalize_target helper."""

    def test_skips_external_https(self):
        assert _normalize_target("https://example.com", "index") is None

    def test_skips_external_http(self):
        assert _normalize_target("http://example.com", "index") is None

    def test_skips_mailto(self):
        assert _normalize_target("mailto:user@example.com", "index") is None

    def test_skips_anchor_only(self):
        assert _normalize_target("#section", "index") is None

    def test_absolute_docs_path(self):
        assert _normalize_target("/docs/installation", "index") == "installation"

    def test_absolute_docs_path_nested(self):
        assert (
            _normalize_target("/docs/api-reference/folio/config", "index")
            == "api-reference/folio/config"
        )

    def test_absolute_docs_root(self):
        assert _normalize_target("/docs", "index") == "index"

    def test_absolute_docs_root_trailing_slash(self):
        assert _normalize_target("/docs/", "index") == "index"

    def test_absolute_configured_docs_path(self):
        assert (
            _normalize_target(
                "/reference/docs/api-reference/folio/config",
                "index",
                docs_route_base="/reference/docs",
            )
            == "api-reference/folio/config"
        )

    def test_relative_dot_slash(self):
        assert _normalize_target("./installation", "index") == "installation"

    def test_relative_plain(self):
        assert _normalize_target("installation", "index") == "installation"

    def test_relative_from_nested_page(self):
        # From "guide/setup", a link to "config" should resolve to "guide/config"
        assert _normalize_target("config", "guide/setup") == "guide/config"

    def test_relative_dot_slash_from_nested(self):
        assert _normalize_target("./config", "guide/setup") == "guide/config"

    def test_parent_traversal(self):
        # From "guide/setup", "../installation" should resolve to "installation"
        assert _normalize_target("../installation", "guide/setup") == "installation"

    def test_strips_md_extension(self):
        assert _normalize_target("./installation.md", "index") == "installation"

    def test_strips_mdx_extension(self):
        assert _normalize_target("./installation.mdx", "index") == "installation"

    def test_strips_anchor_from_href(self):
        assert _normalize_target("installation#quickstart", "index") == "installation"

    def test_strips_query_params(self):
        assert _normalize_target("installation?tab=linux", "index") == "installation"

    def test_anchor_after_stripping_leaves_none(self):
        # "page#section" -> strip anchor -> "page" -> valid route
        assert _normalize_target("page#section", "index") == "page"

class TestCheckLinks:
    """Integration tests for check_links with real MDX files on disk."""

    def test_no_broken_links(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            "# Home\n\nSee the [installation](./installation) guide.\n"
        )
        (content_dir / "installation.mdx").write_text(
            "# Installation\n\nBack to [home](./index).\n"
        )

        pages = ["index", "installation"]
        broken = check_links(content_dir, pages)
        assert broken == []

    def test_finds_broken_link(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            "# Home\n\nSee the [missing page](./nonexistent) here.\n"
        )

        pages = ["index"]
        broken = check_links(content_dir, pages)
        assert len(broken) == 1
        assert broken[0].source_page == "index"
        assert broken[0].target == "./nonexistent"
        assert broken[0].line_number == 3

    def test_skips_external_links(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            "# Home\n\n[GitHub](https://github.com/example/repo)\n"
        )

        pages = ["index"]
        broken = check_links(content_dir, pages)
        assert broken == []

    def test_skips_anchor_links(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            "# Home\n\n[Jump to section](#details)\n"
        )

        pages = ["index"]
        broken = check_links(content_dir, pages)
        assert broken == []

    def test_absolute_docs_links(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            "# Home\n\n[Guide](/docs/guide)\n[Missing](/docs/nope)\n"
        )
        (content_dir / "guide.mdx").write_text("# Guide\n")

        pages = ["index", "guide"]
        broken = check_links(content_dir, pages)
        assert len(broken) == 1
        assert broken[0].target == "/docs/nope"

    def test_absolute_configured_docs_links(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            "# Home\n\n"
            "[Guide](/reference/docs/guide)\n"
            "[Missing](/reference/docs/nope)\n"
        )
        (content_dir / "guide.mdx").write_text("# Guide\n")

        pages = ["index", "guide"]
        broken = check_links(
            content_dir,
            pages,
            docs_route_base="/reference/docs",
        )
        assert len(broken) == 1
        assert broken[0].target == "/reference/docs/nope"

    def test_nested_pages(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        api_dir = content_dir / "api-reference" / "folio"
        api_dir.mkdir(parents=True)

        (content_dir / "index.mdx").write_text(
            "# Home\n\n[Config](/docs/api-reference/folio/config)\n"
        )
        (api_dir / "config.mdx").write_text(
            "# Config\n\n[Home](/docs/index)\n[Build](./build)\n"
        )

        pages = ["index", "api-reference/folio/config"]
        broken = check_links(content_dir, pages)
        # "./build" from api-reference/folio/config resolves to
        # api-reference/folio/build, which is NOT in pages
        assert len(broken) == 1
        assert broken[0].target == "./build"
        assert broken[0].source_page == "api-reference/folio/config"

    def test_multiple_links_on_one_line(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            "See [a](./a) and [b](./b) for details.\n"
        )

        pages = ["index", "a"]
        broken = check_links(content_dir, pages)
        assert len(broken) == 1
        assert broken[0].target == "./b"

    def test_skips_links_inside_inline_code(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            "# Home\n\nExample image syntax: `![path](path)`\n"
        )

        broken = check_links(content_dir, ["index"])

        assert broken == []

    def test_multiple_broken_across_files(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text("# Home\n[Missing1](./gone1)\n")
        (content_dir / "page.mdx").write_text("# Page\n[Missing2](./gone2)\n")

        pages = ["index", "page"]
        broken = check_links(content_dir, pages)
        assert len(broken) == 2
        targets = {bl.target for bl in broken}
        assert targets == {"./gone1", "./gone2"}

    def test_link_with_md_extension(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text("# Home\n[Guide](./guide.md)\n")
        (content_dir / "guide.mdx").write_text("# Guide\n")

        pages = ["index", "guide"]
        broken = check_links(content_dir, pages)
        assert broken == []

    def test_link_with_anchor_to_valid_page(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            "# Home\n[Guide install](./guide#installation)\n"
        )
        (content_dir / "guide.mdx").write_text("# Guide\n")

        pages = ["index", "guide"]
        broken = check_links(content_dir, pages)
        assert broken == []

    def test_finds_broken_jsx_href(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            '# Home\n\n<FeatureCard title="Plugins" href="/docs/plugins" />\n'
        )

        pages = ["index"]
        broken = check_links(content_dir, pages)
        assert len(broken) == 1
        assert broken[0].source_page == "index"
        assert broken[0].target == "/docs/plugins"
        assert broken[0].line_number == 3

    def test_skips_external_jsx_href(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        (content_dir / "index.mdx").write_text(
            '# Home\n\n<FeatureCard title="GitHub" href="https://github.com" />\n'
        )

        broken = check_links(content_dir, ["index"])
        assert broken == []

    def test_empty_content_dir(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        content_dir.mkdir()

        broken = check_links(content_dir, [])
        assert broken == []

    def test_parent_traversal_link(self, tmp_path: Path):
        content_dir = tmp_path / "content"
        guide_dir = content_dir / "guide"
        guide_dir.mkdir(parents=True)

        (content_dir / "index.mdx").write_text("# Home\n")
        (guide_dir / "setup.mdx").write_text(
            "# Setup\n[Home](../index)\n[Bad](../nonexistent)\n"
        )

        pages = ["index", "guide/setup"]
        broken = check_links(content_dir, pages)
        assert len(broken) == 1
        assert broken[0].target == "../nonexistent"
        assert broken[0].source_page == "guide/setup"


def test_site_absolute_links_validate_against_site_routes(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "index.mdx").write_text(
        "[Roadmap](/roadmap) [Board](/kanban/) [Home](/) [Nope](/missing)",
        encoding="utf-8",
    )

    broken = check_links(
        content_dir,
        ["index"],
        site_routes={"/roadmap", "/kanban"},
    )

    assert [b.target for b in broken] == ["/missing"]


def test_site_absolute_links_validate_against_emitted_static_assets(
    tmp_path: Path,
) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "index.mdx").write_text(
        "[Prototype](/_folio/kanban/demo/prototype.html) "
        "[Brief](/_folio/kanban/demo/brief.md#decision) "
        "[Missing](/_folio/kanban/demo/missing.html)",
        encoding="utf-8",
    )
    static_root = tmp_path / "public"
    asset = static_root / "_folio" / "kanban" / "demo" / "prototype.html"
    asset.parent.mkdir(parents=True)
    asset.write_text("<!doctype html>", encoding="utf-8")
    (asset.parent / "brief.md").write_text("# Decision", encoding="utf-8")

    broken = check_links(
        content_dir,
        ["index"],
        static_root=static_root,
    )

    assert [item.target for item in broken] == [
        "/_folio/kanban/demo/missing.html"
    ]


def test_static_asset_validation_cannot_escape_public_root(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "index.mdx").write_text(
        "[Secret](/../secret.txt)", encoding="utf-8"
    )
    (tmp_path / "secret.txt").write_text("private", encoding="utf-8")
    static_root = tmp_path / "public"
    static_root.mkdir()

    broken = check_links(content_dir, ["index"], static_root=static_root)

    assert [item.target for item in broken] == ["/../secret.txt"]


def test_site_root_is_always_a_valid_target(tmp_path):
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "index.mdx").write_text("[Home](/)", encoding="utf-8")

    assert check_links(content_dir, ["index"]) == []


def test_images_are_not_navigation_targets(tmp_path: Path) -> None:
    """A screenshot beside a page is a file, not a route.

    Folio copies a page's local images into the content tree; reporting them
    as broken links made every documented screenshot look like a mistake.
    """
    content = tmp_path / "content"
    content.mkdir()
    (content / "guide.mdx").write_text(
        "![The board](./board.png)\n\n![Remote](https://x.test/a.png)\n",
        encoding="utf-8",
    )
    assert check_links(content, ["guide"]) == []


def test_a_link_to_a_directory_finds_its_index(tmp_path: Path) -> None:
    """`plugins/kanban` is the `plugins/kanban/index` page.

    Nobody writes the `/index` out loud, so splitting a page into a directory
    used to break every existing link to it.
    """
    content = tmp_path / "content"
    content.mkdir()
    (content / "cli.mdx").write_text(
        "See [Kanban](./plugins/kanban) and [gone](./plugins/nope).\n",
        encoding="utf-8",
    )
    broken = check_links(content, ["cli", "plugins/kanban/index"])
    assert [b.target for b in broken] == ["./plugins/nope"]
