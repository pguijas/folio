import gzip
import json
import os
import re
from pathlib import Path
import subprocess
from typing import Any
import warnings

import pytest

from folio_docs.build import (
    _build_manifest_context,
    _generate_content_pages,
)
from folio_docs.config import Config, load_config
from folio_docs.docs.site_builder import SiteBuilder
from folio_docs.docs.static_rewriter import StaticAssetRewriter
from folio_docs.ir import DocstringIR, ModuleIR
from folio_docs.parser.markdown_parser import MarkdownResult


def _extract_ts_object(source: str, marker: str) -> object:
    """Extract the JSON object/array literal that follows ``marker = `` in TS.

    The project theme module emits ``const <name>... = <json.dumps(...)>``
    blocks. This locates ``marker`` then parses the balanced ``{...}``/``[...]``
    literal that starts at the next opening brace/bracket, so assertions can be
    made against the parsed structure instead of whitespace-sensitive
    substrings.
    """

    start = source.index(marker)
    idx = start + len(marker)
    while source[idx] not in "{[":
        idx += 1
    open_char = source[idx]
    close_char = "}" if open_char == "{" else "]"

    depth = 0
    in_string = False
    escaped = False
    end = idx
    for pos in range(idx, len(source)):
        ch = source[pos]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == open_char:
            depth += 1
        elif ch == close_char:
            depth -= 1
            if depth == 0:
                end = pos + 1
                break
    return json.loads(source[idx:end])


def _make_config(tmp_path: Path) -> Config:
    return Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
    )


def _make_template(tmp_path: Path) -> Path:
    """Create a minimal template with placeholder markers."""
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text('{"name": "test"}')

    app_dir = template_dir / "app"
    app_dir.mkdir()
    (app_dir / "layout.tsx").write_text(
        "export const metadata = {\n"
        "  title: {\n"
        '    default: "__PROJECT_NAME__",\n'
        '    template: "%s - __PROJECT_NAME__",\n'
        "  },\n"
        '  description: "__PROJECT_DESCRIPTION__",\n'
        "}\n"
    )

    docs_dir = app_dir / "docs"
    docs_dir.mkdir()
    (docs_dir / "layout.tsx").write_text(
        'import { getPageMap } from "nextra/page-map"\n'
        "<span>__PROJECT_MONOGRAM__</span>\n"
        "<span>__PROJECT_NAME__</span>\n"
        "{/* __PROJECT_REPO_LINK_START__ */}\n"
        '<a href="__PROJECT_REPO__" aria-label="GitHub repository">GitHub</a>\n'
        "{/* __PROJECT_REPO_LINK_END__ */}\n"
        'pageMap={await getPageMap("/docs")}\n'
        "footer={<Footer />}\n"
    )

    (app_dir / "page.tsx").write_text("Built with __PROJECT_NAME__\n")

    previews_dir = app_dir / "previews"
    previews_dir.mkdir()
    (previews_dir / "layout.tsx").write_text(
        'import { getPageMap } from "nextra/page-map"\n'
        "<span>__PROJECT_MONOGRAM__</span>\n"
        "<span>__PROJECT_NAME__</span>\n"
        "{/* __PROJECT_REPO_LINK_START__ */}\n"
        '<a href="__PROJECT_REPO__" aria-label="GitHub repository">GitHub</a>\n'
        "{/* __PROJECT_REPO_LINK_END__ */}\n"
        'pageMap={await getPageMap("/docs")}\n'
    )

    components_dir = template_dir / "components"
    components_dir.mkdir()
    (components_dir / "landing-navbar.tsx").write_text(
        "<span>__PROJECT_MONOGRAM__</span>\n<span>__PROJECT_NAME__</span>\n"
    )

    (template_dir / "next.config.mjs").write_text(
        "const configuredBasePath = '' // __FOLIO_BASE_PATH__\n"
        "const nextConfig = {\n"
        "  images: { unoptimized: true },\n"
        "  __I18N_CONFIG__\n"
        "}\n"
    )

    return template_dir


def _write_generated_doc_page(
    *,
    tmp_path: Path,
    route: str,
    content: str,
    title: str = "Landing Page",
) -> Path:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    source_file = docs_dir / f"{route}.md"
    source_file.write_text(content, encoding="utf-8")

    build_dir = tmp_path / "build"
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text('{"name": "test"}', encoding="utf-8")
    config_path = tmp_path / "docs.yaml"
    config_path.write_text('project:\n  name: "TestProject"\n', encoding="utf-8")

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    _generate_content_pages(
        builder=builder,
        config=config,
        modules=[],
        docs=[
            MarkdownResult(
                content=content,
                frontmatter={"title": title},
                route=route,
                source_file=str(source_file),
            )
        ],
        project_dir=tmp_path,
        build_context=_build_manifest_context(config_path, template_dir, "main"),
        clean=True,
        verbose=False,
    )
    return build_dir / "content" / f"{route}.mdx"


def test_site_builder_prepare(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)

    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    builder.prepare()

    assert build_dir.exists()
    assert (build_dir / "package.json").exists()
    assert (build_dir / "app" / "layout.tsx").exists()
    assert (build_dir / "content").is_dir()


def test_prepare_does_not_copy_template_content(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    template_content = template_dir / "content"
    (template_content / "guide").mkdir(parents=True)
    (template_content / "_meta.json").write_text('{"guide": "Guide"}')
    (template_content / "guide" / "index.mdx").write_text("# Getting Started")

    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    builder.prepare()

    assert (build_dir / "content").is_dir()
    assert not (build_dir / "content" / "_meta.json").exists()
    assert not (build_dir / "content" / "guide" / "index.mdx").exists()


def test_docs_route_normalizes_root_static_param_for_export() -> None:
    page = (
        Path(__file__).parents[1]
        / "template"
        / "app"
        / "docs"
        / "[[...mdxPath]]"
        / "page.jsx"
    ).read_text(encoding="utf-8")

    assert "expandStaticParams" in page
    assert "isDisabledMdxPath" in page
    assert "normalizeMdxPath" in page
    assert "return expandStaticParams(params)" in page
    assert "if (isDisabledMdxPath(mdxPath))" in page
    assert "notFound()" in page
    assert "const mdxPath = normalizeMdxPath(params.mdxPath)" in page


def test_docs_route_expands_index_html_aliases_for_dev_export_requests() -> None:
    helper = Path(__file__).parents[1] / "template" / "lib" / "docs-route-params.js"
    script = f"""
      import {{
        expandStaticParams,
        isDisabledMdxPath,
        normalizeMdxPath,
      }} from {json.dumps(helper.as_uri())}

      const assert = (condition, message) => {{
        if (!condition) throw new Error(message)
      }}

      assert(
        JSON.stringify(normalizeMdxPath(["index.html"])) === JSON.stringify([]),
        "index.html should resolve to the docs root",
      )
      assert(
        JSON.stringify(normalizeMdxPath(["components", "index.html"])) ===
          JSON.stringify(["components"]),
        "nested index.html should resolve to its directory route",
      )
      assert(
        JSON.stringify(normalizeMdxPath(["source", "common_errors"])) ===
          JSON.stringify(["source", "common-errors"]),
        "hand-written docs paths should accept underscore aliases",
      )
      assert(
        JSON.stringify(normalizeMdxPath(["source", "common_errors", "index.html"])) ===
          JSON.stringify(["source", "common-errors"]),
        "underscore aliases should compose with index.html aliases",
      )
      assert(
        JSON.stringify(
          normalizeMdxPath(["api-reference", "example_package", "module_name"]),
        ) === JSON.stringify(["api-reference", "example_package", "module_name"]),
        "API reference package and module names should keep underscores",
      )
      assert(
        isDisabledMdxPath(["i18n"]),
        "disabled docs routes should be recognized",
      )
      assert(
        isDisabledMdxPath(["i18n", "index.html"]),
        "disabled index.html aliases should be recognized",
      )
      assert(
        isDisabledMdxPath(["versioning"]),
        "gated versioning docs route should be recognized",
      )
      assert(
        !isDisabledMdxPath(["configuration"]),
        "enabled docs routes should not be marked disabled",
      )
      assert(
        !isDisabledMdxPath(["roadmap"]),
        "the released roadmap docs route must not be gated",
      )
      assert(
        !isDisabledMdxPath(["landing"]),
        "the released landing docs route must not be gated",
      )
      assert(
        !isDisabledMdxPath(["plugins"]),
        "the released plugins docs route must not be gated",
      )
      assert(
        !isDisabledMdxPath(["api-reference", "folio", "plugins", "roadmap"]),
        "released plugin API reference routes must not be gated",
      )

      const params = expandStaticParams(
        [
          {{ mdxPath: [""] }},
          {{ mdxPath: ["components"] }},
          {{ mdxPath: ["source", "common-errors"] }},
          {{ mdxPath: ["api-reference", "example_package"] }},
          {{ lang: "en", mdxPath: ["guide"] }},
        ],
        {{ includeIndexHtmlAliases: true, includeDisabledParams: true }},
      )

      assert(
        params.some((param) => JSON.stringify(param.mdxPath) === JSON.stringify([])),
        "root param should be normalized",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) === JSON.stringify(["index.html"]),
        ),
        "root index.html alias should be included",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["components", "index.html"]),
        ),
        "nested index.html alias should be included",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["source", "common_errors"]),
        ),
        "underscore aliases should be included for hand-written docs routes",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["source", "common_errors", "index.html"]),
        ),
        "underscore index.html aliases should be included for hand-written docs routes",
      )
      assert(
        !params.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["api-reference", "example-package"]),
        ),
        "API reference static params should not get hyphenated package-name aliases",
      )
      assert(
        params.some(
          (param) =>
            param.lang === "en" &&
            JSON.stringify(param.mdxPath) === JSON.stringify(["guide", "index.html"]),
        ),
        "locale params should keep their non-route fields on aliases",
      )
      assert(
        params.some(
          (param) => JSON.stringify(param.mdxPath) === JSON.stringify(["i18n"]),
        ),
        "disabled docs route should be included for dev export requests",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["i18n", "index.html"]),
        ),
        "disabled docs route index.html alias should be included for dev",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) === JSON.stringify(["versioning"]),
        ),
        "disabled versioning route should be included for dev export requests",
      )

      const productionParams = expandStaticParams(
        [
          {{ mdxPath: [""] }},
          {{ mdxPath: ["components"] }},
          {{ mdxPath: ["source", "common-errors"] }},
        ],
        {{ includeIndexHtmlAliases: false, includeDisabledParams: false }},
      )
      assert(
        !productionParams.some((param) => param.mdxPath.includes("index.html")),
        "index.html aliases should stay out of production static exports",
      )
      assert(
        !productionParams.some((param) => param.mdxPath.includes("i18n")),
        "disabled params should stay out of production static exports",
      )
      assert(
        productionParams.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["source", "common_errors"]),
        ),
        "underscore aliases should be generated for static exports",
      )
    """

    subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=True,
        cwd=Path(__file__).parents[1],
    )


def test_docs_route_disabled_paths_match_python_feature_gates() -> None:
    """The JS static-path gate must mirror folio/features.py exactly.

    ``template/app/docs/[[...mdxPath]]/page.jsx`` 404s every path in
    ``DISABLED_DOC_STATIC_PATHS`` in production builds. Any entry left behind
    after a feature is de-gated in ``folio/features.py`` ships a released
    route as a prerendered Next.js error shell (this is exactly how the
    released roadmap docs route broke), so the two lists are compared
    entry-for-entry here.
    """
    from folio_docs.features import MVP_DISABLED_API_MODULES, MVP_DISABLED_DOC_ROUTES

    helper = Path(__file__).parents[1] / "template" / "lib" / "docs-route-params.js"
    source = helper.read_text(encoding="utf-8")
    match = re.search(
        r"const DISABLED_DOC_STATIC_PATHS = (\[.*?\])\n", source, re.DOTALL
    )
    assert match, "DISABLED_DOC_STATIC_PATHS literal not found"
    literal = re.sub(r",(\s*[\]\}])", r"\1", match.group(1))
    js_paths = {tuple(path) for path in json.loads(literal)}

    expected = {(route,) for route in MVP_DISABLED_DOC_ROUTES}
    expected |= {
        ("api-reference", *module.split(".")) for module in MVP_DISABLED_API_MODULES
    }
    assert js_paths == expected


def test_prepare_removes_stale_template_content(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    template_content = template_dir / "content"
    (template_content / "guide").mkdir(parents=True)
    (template_content / "_meta.json").write_text('{"guide": "Guide"}')
    (template_content / "guide" / "index.mdx").write_text("# Getting Started")

    build_dir = tmp_path / "build"
    content_dir = build_dir / "content"
    content_dir.mkdir(parents=True)
    (content_dir / "_meta.json").write_text('{"guide": "Guide"}')
    (content_dir / "guide").mkdir()
    (content_dir / "guide" / "index.mdx").write_text("# Getting Started")
    (content_dir / "index.mdx").write_text("# Generated Overview")

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    builder.prepare()

    assert (content_dir / "index.mdx").exists()
    assert not (content_dir / "_meta.json").exists()
    assert not (content_dir / "guide" / "index.mdx").exists()


def test_inject_root_layout(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "layout.tsx").read_text()
    assert '"TestProject"' in content
    assert '"Documentation for TestProject"' in content
    assert "__PROJECT_NAME__" not in content
    assert "__PROJECT_DESCRIPTION__" not in content


def test_inject_previews_page(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="MyLib",
        project_repo="https://github.com/org/mylib",
        output_dir=str(tmp_path / "output"),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "previews" / "layout.tsx").read_text()
    assert "MyLib" in content
    assert "my" in content  # monogram
    assert 'href="https://github.com/org/mylib"' in content
    assert "search={<SearchCommand" in content
    assert "__PROJECT_NAME__" not in content
    assert "__PROJECT_MONOGRAM__" not in content
    assert "__PROJECT_REPO__" not in content
    assert "__PROJECT_REPO_LINK_" not in content


def test_inject_previews_page_removes_repo_link_without_repo(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "previews" / "layout.tsx").read_text()
    assert 'aria-label="GitHub repository"' not in content
    assert "__PROJECT_REPO__" not in content


def test_inject_docs_layout(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="MyLib",
        project_repo="https://github.com/org/mylib",
        output_dir=str(tmp_path / "output"),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "docs" / "layout.tsx").read_text()
    assert "MyLib" in content
    assert "my" in content  # monogram
    assert "__PROJECT_NAME__" not in content
    assert "__PROJECT_MONOGRAM__" not in content
    assert 'href="https://github.com/org/mylib"' in content
    assert 'aria-label="GitHub repository"' in content
    assert "__PROJECT_REPO__" not in content
    assert "__PROJECT_REPO_LINK_" not in content
    assert 'docsRepositoryBase="https://github.com/org/mylib"' in content
    # The feedback link and the 404 page are built from docsRepositoryBase, so
    # it stays. Nextra's "Edit this page" is built from it plus the page's
    # `filePath` — the generated `content/<route>.mdx`, which exists only in
    # .build/ — so every one of those links was a 404 and the link is off.
    assert "editLink={null}" in content


def test_inject_docs_layout_removes_repo_button_without_repo(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="NoRepoDocs",
        project_repo="",
        output_dir=str(tmp_path / "output"),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "docs" / "layout.tsx").read_text()
    assert 'aria-label="GitHub repository"' not in content
    assert "__PROJECT_REPO__" not in content
    assert "__PROJECT_REPO_LINK_" not in content
    assert "https://github.com" not in content


def test_bundled_docs_layout_removes_repo_imports_without_repo(
    tmp_path: Path,
) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="NoRepoDocs",
        project_repo="",
        output_dir=str(tmp_path / "output"),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "docs" / "layout.tsx").read_text()
    assert "GithubIcon" not in content
    assert "HugeiconsIcon" not in content
    assert 'aria-label="GitHub repository"' not in content
    assert "__PROJECT_REPO__" not in content
    assert "__PROJECT_REPO_" not in content


def test_inject_landing_page(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    page = (build_dir / "app" / "page.tsx").read_text()
    assert "Built with TestProject" in page
    assert "__PROJECT_NAME__" not in page

    navbar = (build_dir / "components" / "landing-navbar.tsx").read_text()
    assert "TestProject" in navbar
    assert "te" in navbar  # monogram
    assert "__PROJECT_NAME__" not in navbar
    assert "__PROJECT_MONOGRAM__" not in navbar


def test_inject_landing_page_into_optional_theme_route(
    tmp_path: Path,
) -> None:
    template_dir = _make_template(tmp_path)
    product_dir = template_dir / "app" / "product"
    product_dir.mkdir()
    (product_dir / "page.tsx").write_text(
        "const monogram = __PROJECT_MONOGRAM_JSON__\n"
        "const headline = __LANDING_HEADLINE_JSON__\n"
        "const description = __LANDING_DESCRIPTION_JSON__\n"
        "const primaryText = __LANDING_CTA_PRIMARY_TEXT_JSON__\n"
        "const primaryLink = __LANDING_CTA_PRIMARY_LINK_JSON__\n"
        "const secondaryText = __LANDING_CTA_SECONDARY_TEXT_JSON__\n"
        "const secondaryLink = __LANDING_CTA_SECONDARY_LINK_JSON__\n"
        "const commands = __LANDING_INSTALL_COMMANDS__\n"
        "const sections = __LANDING_SECTIONS__\n",
        encoding="utf-8",
    )
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    config.landing_hero_headline = "Docs from source"
    config.landing_sections = [{"type": "features", "title": "Complete"}]

    SiteBuilder(config, str(template_dir), str(build_dir)).prepare()

    page = (build_dir / "app" / "product" / "page.tsx").read_text()
    assert 'const monogram = "te"' in page
    assert 'const headline = "Docs from source"' in page
    assert 'const sections = [{"type": "features", "title": "Complete"}]' in page
    assert "__LANDING_" not in page
    assert "__PROJECT_MONOGRAM_JSON__" not in page


def test_navbar_is_injected_even_without_a_landing(tmp_path: Path) -> None:
    """The navbar belongs to the site, not to the landing page.

    PublicLayout renders LandingNavbar on every public plugin view, so a
    project with a board and no `landing:` key used to ship a navbar still
    containing `__PROJECT_NAME_JSON__` and die at prerender with
    `ReferenceError: __PROJECT_NAME_JSON__ is not defined`. The substitution
    lived inside `_inject_landing_page`, behind its `landing_enabled` gate.
    """
    template_dir = _make_template(tmp_path)
    # The navbar the real template ships uses the JSON placeholders, which
    # are the ones that become a ReferenceError rather than a stray string.
    (template_dir / "components" / "landing-navbar.tsx").write_text(
        "const name = __PROJECT_NAME_JSON__\n"
        "const monogram = __PROJECT_MONOGRAM_JSON__\n",
        encoding="utf-8",
    )
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    config.landing_enabled = False
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    navbar = (build_dir / "components" / "landing-navbar.tsx").read_text()
    assert "__PROJECT_NAME_JSON__" not in navbar
    assert "__PROJECT_MONOGRAM_JSON__" not in navbar
    assert '"TestProject"' in navbar


def test_inject_landing_page_uses_safe_serialized_values(tmp_path: Path) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name='Quote "Docs"',
        output_dir=str(tmp_path / "output"),
        landing_hero_tagline='Ship "docs"',
        landing_hero_headline='Docs for "quoted" APIs',
        landing_hero_description='Line one\nLine "two"',
        landing_cta_primary_text='Start "now"',
        landing_cta_primary_link='/docs?query="quoted"',
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    page = (build_dir / "app" / "page.tsx").read_text()
    navbar = (build_dir / "components" / "landing-navbar.tsx").read_text()

    assert 'const landingHeadline = "Docs for \\"quoted\\" APIs"' in page
    assert 'const landingDescription = "Line one\\nLine \\"two\\""' in page
    assert 'const primaryCtaLink = "/docs?query=\\"quoted\\""' in page
    assert "const secondaryCtaLink: string | null = null" in page
    assert "https://github.com" not in page
    assert "{projectMonogram}" in page
    assert "const secondaryCtaLink: string | null = null" in navbar
    assert "https://github.com" not in navbar
    assert "Register parsers" not in page
    assert (
        "Register components, write typed data, generate views, and run post-build hooks."
        in page
    )


def test_inject_landing_page_preserves_an_explicitly_empty_tagline(
    tmp_path: Path,
) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="No Kicker",
        output_dir=str(tmp_path / "output"),
        landing_hero_tagline="",
    )

    SiteBuilder(config, str(template_dir), str(build_dir)).prepare()

    page = (build_dir / "app" / "page.tsx").read_text()
    assert 'const landingTagline = ""' in page
    assert ".py → no kicker" not in page


def test_inject_landing_navbar_typechecks_without_secondary_link(
    tmp_path: Path,
) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="NoRepoDocs",
        project_repo="",
        output_dir=str(tmp_path / "output"),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    navbar = (build_dir / "components" / "landing-navbar.tsx").read_text()

    assert 'normalizeLandingHref,\n} from "@/components/landing/actions"' in navbar
    assert "const secondaryCtaLink: string | null = null" in navbar
    assert "secondaryCtaLink?.startsWith" not in navbar
    assert "const normalizedSecondaryCtaLink = secondaryCtaLink" in navbar
    # Normalized against the bar's own depth, so a "/path" CTA is right on a
    # landing served below the root too.
    assert "? normalizeLandingHref(secondaryCtaLink, pathToRoot)" in navbar


def test_inject_landing_page_keeps_secondary_link_when_configured(
    tmp_path: Path,
) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="RepoDocs",
        project_repo="https://github.com/acme/repo",
        output_dir=str(tmp_path / "output"),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    page = (build_dir / "app" / "page.tsx").read_text()
    navbar = (build_dir / "components" / "landing-navbar.tsx").read_text()

    assert (
        'const secondaryCtaLink: string | null = "https://github.com/acme/repo"' in page
    )
    assert (
        'const secondaryCtaLink: string | null = "https://github.com/acme/repo"'
        in navbar
    )
    assert 'const secondaryCtaText = "GitHub"' in page
    assert 'const secondaryCtaText = "GitHub"' in navbar


def test_inject_landing_page_keeps_custom_secondary_cta_text(tmp_path: Path) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="ExampleDocs",
        output_dir=str(tmp_path / "output"),
        landing_cta_secondary_text="View API",
        landing_cta_secondary_link="/docs/api-reference/example_package/arithmetic/",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    page = (build_dir / "app" / "page.tsx").read_text()
    navbar = (build_dir / "components" / "landing-navbar.tsx").read_text()

    assert 'const secondaryCtaText = "View API"' in page
    assert 'const secondaryCtaText = "View API"' in navbar
    assert (
        'const secondaryCtaLink: string | null = "/docs/api-reference/example_package/arithmetic/"'
        in navbar
    )


def test_inject_landing_page_can_disable_comparison_section(tmp_path: Path) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="ExampleDocs",
        output_dir=str(tmp_path / "output"),
        landing_hero_variant="source-pipeline",
        landing_comparison=False,
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    page = (build_dir / "app" / "page.tsx").read_text()

    assert '"type": "comparison"' not in page
    assert "__LANDING_SHOW_COMPARISON__" not in page


def test_inject_landing_page_serves_docs_index_when_public_landing_is_disabled(
    tmp_path: Path,
) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="DocsOnly",
        output_dir=str(tmp_path / "output"),
        landing_enabled=False,
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    page = (build_dir / "app" / "page.tsx").read_text()

    assert "LandingNavbar" not in page
    assert 'import DocsLayout from "./docs/layout"' in page
    assert (
        'import DocsPage, { generateMetadata as generateDocsMetadata } from "./docs/[[...mdxPath]]/page"'
        in page
    )
    assert "mdxPath: []" in page
    assert "<DocsLayout>" in page
    assert "<DocsPage {...rootDocsProps()} />" in page
    assert "Opening documentation" not in page
    assert 'httpEquiv="refresh"' not in page
    assert "__LANDING_" not in page


def test_prepare_uses_configured_docs_route_base(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    docs_page_dir = template_dir / "app" / "docs" / "[[...mdxPath]]"
    docs_page_dir.mkdir(parents=True)
    (docs_page_dir / "page.jsx").write_text(
        'import { useMDXComponents as getMDXComponents } from "../../../mdx-components"\n'
        'const docsOgImageUrl = siteUrl ? `${siteUrl}/docs/opengraph-image` : "/docs/opengraph-image"\n'
        'const docsIndexCanonicalPath = "__DOCS_INDEX_CANONICAL_PATH__"\n'
        "function docsRouteForMdxPath(mdxPath) {\n"
        "  if (!mdxPath.length) {\n"
        '    return docsIndexCanonicalPath === "/" ? "/" : "/docs/"\n'
        "  }\n"
        '  return `/docs/${mdxPath.join("/")}/`\n'
        "}\n",
        encoding="utf-8",
    )
    (template_dir / "app" / "docs" / "opengraph-image.tsx").write_text(
        "export const alt = '__PROJECT_NAME__ documentation'\n",
        encoding="utf-8",
    )
    (template_dir / "next.config.mjs").write_text(
        "const configuredBasePath = '' // __FOLIO_BASE_PATH__\n"
        "const withNextra = nextra({\n"
        "  contentDirBasePath: '/docs',\n"
        "})\n"
        "const nextConfig = {\n"
        "  env: {\n"
        '    NEXT_PUBLIC_FOLIO_BASE_PATH: basePath ?? "",\n'
        "  },\n"
        "  __I18N_CONFIG__\n"
        "}\n",
        encoding="utf-8",
    )

    build_dir = tmp_path / "build"
    config = Config(
        project_name="RouteDocs",
        output_dir=str(tmp_path / "output"),
        site_url="https://example.com",
        docs_route_base="/reference/docs",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    assert not (build_dir / "app" / "docs").exists()
    assert (build_dir / "app" / "reference" / "docs" / "layout.tsx").exists()
    page_path = build_dir / "app" / "reference" / "docs" / "[[...mdxPath]]" / "page.jsx"
    assert page_path.exists()

    layout = (build_dir / "app" / "reference" / "docs" / "layout.tsx").read_text(
        encoding="utf-8"
    )
    page = page_path.read_text(encoding="utf-8")
    next_config = (build_dir / "next.config.mjs").read_text(encoding="utf-8")
    context = (build_dir / "lib" / "folio-template.ts").read_text(encoding="utf-8")

    assert 'getPageMap("/reference/docs")' in layout
    assert 'contentDirBasePath: "/reference/docs"' in next_config
    assert "/reference/docs/opengraph-image" in page
    assert 'return docsIndexCanonicalPath === "/" ? "/" : "/reference/docs/"' in page
    assert 'return `/reference/docs/${mdxPath.join("/")}/`' in page
    assert 'from "@/mdx-components"' in page
    assert '"docsRouteBase": "/reference/docs"' in context


def test_inject_landing_page_selects_source_pipeline_hero(tmp_path: Path) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="Folio",
        output_dir=str(tmp_path / "output"),
        landing_hero_variant="source-pipeline",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    page = (build_dir / "app" / "page.tsx").read_text()

    assert 'const landingHeroVariant = "source-pipeline"' in page
    assert "__LANDING_HERO_VARIANT_JSON__" not in page


def test_inject_landing_page_serializes_configured_section_catalog(
    tmp_path: Path,
) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="CatalogDocs",
        output_dir=str(tmp_path / "output"),
        landing_sections=[
            {
                "type": "stats",
                "eyebrow": "Adoption",
                "title": 'Used by "teams"',
                "items": [
                    {"value": "3", "label": "commands"},
                    {"value": "1", "label": "config file"},
                ],
            },
            {
                "type": "cta",
                "title": "Read the generated docs",
                "actions": [{"title": "Open docs", "href": "/docs/"}],
            },
        ],
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    page = (build_dir / "app" / "page.tsx").read_text()

    assert 'const landingSections = [{"type": "stats"' in page
    assert '"title": "Used by \\"teams\\""' in page
    assert '"type": "cta"' in page
    assert "__LANDING_SECTIONS__" not in page


def test_inject_landing_page_uses_default_section_catalog(tmp_path: Path) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="DefaultCatalog",
        output_dir=str(tmp_path / "output"),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    page = (build_dir / "app" / "page.tsx").read_text()

    assert 'const landingSections = [{"type": "features"' in page
    assert '"type": "routes"' in page
    assert '"type": "output"' in page
    assert '"type": "cta"' in page
    assert "__LANDING_SECTIONS__" not in page


def test_bundled_landing_keeps_roadmap_out_of_homepage() -> None:
    page = (Path(__file__).parents[1] / "template" / "app" / "page.tsx").read_text()
    navbar = (
        Path(__file__).parents[1] / "template" / "components" / "landing-navbar.tsx"
    ).read_text()

    assert 'import { Roadmap } from "@/components/roadmap"' not in page
    assert "<Roadmap />" not in page
    assert 'href="#roadmap"' not in navbar
    assert "const actionLinks" in page
    assert "landing-action-grid" in page


def test_bundled_landing_uses_only_configured_cta_links() -> None:
    page = (Path(__file__).parents[1] / "template" / "app" / "page.tsx").read_text()
    navbar = (
        Path(__file__).parents[1] / "template" / "components" / "landing-navbar.tsx"
    ).read_text()

    assert "./docs/installation/" not in page
    assert "./docs/api-reference/" not in page
    assert 'href="./docs/"' not in navbar
    assert 'title: "Docs"' not in page
    assert 'title: "Install"' not in page
    assert "const footerLinks: LandingLink[] = actionLinks.map" in page
    assert 'actionLinks.length > 1 ? "sm:grid-cols-2" : "sm:grid-cols-1"' in page
    # The navbar owns a single Documentation link built from pathToRoot; the
    # hero owns the configured primary CTA.
    assert "primaryCtaLink" not in navbar
    assert "href={`${pathToRoot}/docs/`}" in navbar
    assert "const secondaryCtaText = __LANDING_CTA_SECONDARY_TEXT_JSON__" in navbar
    assert 'aria-label="GitHub repository"' not in navbar


def _directive(source: str) -> str:
    """The module's first statement, or "" — a "use client" directive or not.

    Read as the first non-blank, non-comment line rather than by substring,
    because both roadmap files talk *about* "use client" in their prose.
    """
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("//", "/*", "*", "*/")):
            continue
        return stripped
    return ""


def test_bundled_roadmap_is_source_defined_and_read_only() -> None:
    template = Path(__file__).parents[1] / "template"
    component = (template / "components" / "roadmap.tsx").read_text()

    assert 'from "@/lib/roadmap-data"' in component
    # The landing renders the miniature, so this file must stay a server
    # component: no directive, no hooks, no browser storage.
    assert _directive(component) != '"use client"'
    assert "useState" not in component
    assert "localStorage" not in component
    assert "draggable" not in component
    assert "onDrag" not in component
    assert "onDrop" not in component
    assert "Edit" not in component
    assert "Move" not in component
    # Compact excerpt mode stays server-renderable: slicing plus a muted
    # "+ N more" line that links to the full public roadmap.
    assert "maxPhases" in component
    assert 'aria-label="Releases by project"' in component
    assert 'from "@/lib/kanban-data"' not in component
    assert "boardHref" not in component
    assert "milestone?: string" in (template / "lib/roadmap-data.ts").read_text()
    assert "project?: string" in (template / "lib/roadmap-data.ts").read_text()
    assert "compact" in component
    assert "ordered.slice(0, Math.max(maxPhases, 0))" in component
    assert 'href="/roadmap"' in component
    assert "full roadmap" in component


def test_roadmap_orders_releases_by_version_never_by_status() -> None:
    """Version is the sort key; status is drawn, never sorted on.

    Two ways this has gone wrong: ordering by status prints 0.5, 0.7, 0.6
    because this project marks 0.6 `later` and 0.7 `next`, and comparing
    version strings puts 0.10 before 0.2. The page, the miniature and the
    design studies share these helpers, so the rule is pinned once, here.
    """
    helper = Path(__file__).parents[1] / "template" / "lib" / "roadmap-utils.ts"
    script = f"""
      import {{
        compareVersions,
        sortByVersion,
        groupPhasesByProject,
        projectLabel,
        DEFAULT_PROJECT_KEY,
      }} from {json.dumps(helper.as_uri())}

      const assert = (condition, message) => {{
        if (!condition) throw new Error(message)
      }}
      const phase = (version, status, project) => ({{
        id: `${{project ?? "x"}}-${{version}}`,
        version,
        status,
        project,
        title: version,
        layer: "Layer",
        summary: "Summary.",
        features: [],
      }})
      const versions = (phases) => sortByVersion(phases).map((p) => p.version)

      assert(
        JSON.stringify(
          versions([phase("0.7", "next"), phase("0.6", "later")]),
        ) === JSON.stringify(["0.6", "0.7"]),
        "0.6 must precede 0.7 even though 0.6 is later and 0.7 is next",
      )
      assert(
        compareVersions("0.6", "0.7") < 0,
        "0.6 must compare before 0.7",
      )
      assert(
        JSON.stringify(
          versions([phase("0.10", "next"), phase("0.2", "shipped")]),
        ) === JSON.stringify(["0.2", "0.10"]),
        "0.10 must sort after 0.2, not before it as strings would",
      )
      assert(
        compareVersions("0.10", "0.2") > 0,
        "0.10 must compare after 0.2",
      )
      assert(
        JSON.stringify(
          versions([
            phase("0.10", "later"),
            phase("0.2", "next"),
            phase("0.7", "next"),
            phase("0.6", "later"),
            phase("v0.1", "shipped"),
          ]),
        ) === JSON.stringify(["v0.1", "0.2", "0.6", "0.7", "0.10"]),
        "a mixed list must count forwards, leading v tolerated",
      )
      assert(
        sortByVersion([]).length === 0,
        "an empty release list must not throw",
      )

      // Non-mutating: the caller's array keeps its own order.
      const input = [phase("0.7", "next"), phase("0.6", "later")]
      sortByVersion(input)
      assert(
        JSON.stringify(input.map((p) => p.version)) ===
          JSON.stringify(["0.7", "0.6"]),
        "sortByVersion must not mutate its argument",
      )

      // Grouping sorts each project's line the same way.
      const grouped = groupPhasesByProject([
        phase("0.7", "next", "docs"),
        phase("0.1", "shipped", "agents"),
        phase("0.6", "later", "docs"),
      ])
      assert(
        JSON.stringify(grouped.map((g) => g.key)) ===
          JSON.stringify(["docs", "agents"]),
        "groups keep first-appearance order when no projects are configured",
      )
      assert(
        JSON.stringify(grouped[0].phases.map((p) => p.version)) ===
          JSON.stringify(["0.6", "0.7"]),
        "each group is version-sorted",
      )
      // Declaration order in docs.yaml decides which column a rail draws
      // first, so it has to beat the order phases happen to appear in.
      const ordered = groupPhasesByProject(
        [phase("0.1", "shipped", "agents"), phase("0.1", "shipped", "docs")],
        {{ docs: {{ label: "Folio Docs", description: "Docs copy." }} }},
      )
      assert(
        JSON.stringify(ordered.map((g) => g.key)) ===
          JSON.stringify(["docs", "agents"]),
        "declared order wins, undeclared keys follow rather than disappear",
      )
      assert(
        ordered[0].label === "Folio Docs" && ordered[0].description === "Docs copy.",
        "a group carries the label and description the site configured",
      )
      assert(
        ordered[1].label === "agents" && ordered[1].description === undefined,
        "an unconfigured group falls back to its key and has no description",
      )
      assert(
        JSON.stringify(
          groupPhasesByProject([phase("0.1", "shipped")]).map((g) => g.key),
        ) === JSON.stringify([DEFAULT_PROJECT_KEY]),
        "a phase with no project belongs to the default one",
      )

      assert(
        projectLabel("docs", {{ docs: {{ label: "Folio Docs" }} }}) === "Folio Docs",
        "a configured label is used",
      )
      assert(
        projectLabel("docs", undefined) === "docs",
        "an unlabelled project falls back to its key",
      )
    """

    subprocess.run(
        [
            "node",
            "--disable-warning=ExperimentalWarning",
            "--input-type=module",
            "--eval",
            script,
        ],
        check=True,
        cwd=Path(__file__).parents[1],
    )


def test_roadmap_components_only_import_helpers_that_exist() -> None:
    """Every component and `lib/roadmap-utils.ts` must agree on names.

    The roadmap page, the miniature and the design studies all read their
    ordering and grouping from roadmap-utils; a named import that the module
    does not export is a build failure the Python suite otherwise never sees.
    """
    template = Path(__file__).parents[1] / "template"
    utils = (template / "lib" / "roadmap-utils.ts").read_text()
    exported = set(
        re.findall(
            r"^export (?:const|function|type|interface)\s+(\w+)", utils, re.MULTILINE
        )
    )

    for path in sorted((template / "components").glob("roadmap*.tsx")):
        name = path.name
        source = path.read_text()
        for block in re.findall(
            r"import\s*(?:type\s*)?\{([^}]*)\}\s*from\s*\"@/lib/roadmap-utils\"",
            source,
        ):
            imported = {
                part.strip().removeprefix("type ").split(" as ")[0].strip()
                for part in block.split(",")
                if part.strip()
            }
            assert imported <= exported, (
                f"{name} imports {sorted(imported - exported)} "
                f"from lib/roadmap-utils.ts, which does not export them"
            )


def test_roadmap_plugin_emits_data_and_public_page(tmp_path: Path) -> None:
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions
    from folio_docs.docs.integrations import roadmap as roadmap_plugin

    template_dir = _make_template(tmp_path)
    (template_dir / "lib").mkdir()
    (template_dir / "lib" / "roadmap-data.ts").write_text(
        "export const roadmapPhases = []"
    )
    build_dir = tmp_path / "build"
    config = Config(
        project_name="RoadmapProject",
        output_dir=str(tmp_path / "output"),
        extra={
            "roadmap": {
                "routes": {"docs": True, "public": True},
                "description": "From source analysis to a project OS.",
                "phases": [
                    {
                        "id": "foundation",
                        "version": "0.1",
                        "title": "Foundation",
                        "status": "shipped",
                        "layer": "Source analysis",
                        "summary": "Parse source files into docs.",
                        "command": "folio build",
                        "features": ["Parser", "Search"],
                    }
                ],
            }
        },
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    roadmap_plugin.register_extensions(registry=registry, config=config)
    builder.apply_extensions(registry)

    data = (build_dir / "lib" / "roadmap-data.ts").read_text()
    public_page = (build_dir / "app" / "roadmap" / "page.tsx").read_text()

    assert "export const roadmapPhases: RoadmapPhase[]" in data
    assert '"title": "Foundation"' in data
    assert '"status": "shipped"' in data
    assert '"features": [' in data
    assert (
        'import { PublicLayout } from "@/components/folio-view-layouts"' in public_page
    )
    assert 'import { RoadmapPage } from "@/components/roadmap-page"' in public_page
    assert "<RoadmapPage {...block0Props} />" in public_page
    # `dense`, not `narrow`: the page draws its own name, description and
    # board link, so the layout's title band is suppressed rather than filled.
    assert '"dense": true' in public_page
    assert '"narrow"' not in public_page
    # The copy reaches the component, which is what draws it.
    assert '"title": "RoadmapProject Roadmap"' in public_page
    assert "From source analysis to a project OS." in public_page


def test_roadmap_cross_links_follow_configured_kanban_path(tmp_path: Path) -> None:
    """The roadmap's board link follows wherever kanban.routes.public puts it."""
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions
    from folio_docs.docs.integrations import roadmap as roadmap_plugin

    # Root path "/" → links href "../"
    config = Config(
        project_name="RoadmapProject",
        output_dir=str(tmp_path / "output"),
        extra={
            "roadmap": {"routes": {"public": True}, "phases": []},
            "kanban": {"routes": {"public": "/"}},
        },
    )
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    roadmap_plugin.register_extensions(registry=registry, config=config)
    roadmap_view = registry.views["/roadmap"]
    assert roadmap_view.props["dense"] is True
    assert roadmap_view.slots["main"][0].props["links"] == [
        {"label": "Development board", "href": "../"}
    ]

    # Custom path "/board" → links href "../board/"
    config = Config(
        project_name="RoadmapProject",
        output_dir=str(tmp_path / "output"),
        extra={
            "roadmap": {"routes": {"public": True}, "phases": []},
            "kanban": {"routes": {"public": "/board"}},
        },
    )
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    roadmap_plugin.register_extensions(registry=registry, config=config)
    roadmap_view = registry.views["/roadmap"]
    assert roadmap_view.props["dense"] is True
    assert roadmap_view.slots["main"][0].props["links"] == [
        {"label": "Development board", "href": "../board/"}
    ]

    # True (unchanged) → links href "../kanban/"
    config = Config(
        project_name="RoadmapProject",
        output_dir=str(tmp_path / "output"),
        extra={
            "roadmap": {"routes": {"public": True}, "phases": []},
            "kanban": {"routes": {"public": True}},
        },
    )
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    roadmap_plugin.register_extensions(registry=registry, config=config)
    roadmap_view = registry.views["/roadmap"]
    assert roadmap_view.props["dense"] is True
    assert roadmap_view.slots["main"][0].props["links"] == [
        {"label": "Development board", "href": "../kanban/"}
    ]


def _project_roadmap_config(tmp_path: Path, **extra: Any) -> Config:
    """A roadmap whose phases name two projects, plus anything else under extra."""

    def phase(pid: str, version: str, project: str | None) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "id": pid,
            "version": version,
            "title": pid.title(),
            "status": "shipped",
            "layer": "Layer",
            "summary": "Summary.",
            "features": ["One"],
        }
        if project is not None:
            entry["project"] = project
        return entry

    return Config(
        project_name="RoadmapProject",
        output_dir=str(tmp_path / "output"),
        extra={
            "roadmap": {
                "routes": {"public": True},
                "description": "Every project.",
                "projects": {
                    "docs": {
                        "slug": "folio-docs",
                        "label": "Folio Docs",
                        "title": "Folio Docs Roadmap",
                        "description": "The site side.",
                    },
                    "agents": {"slug": "folio-agents", "label": "Folio for Agents"},
                },
                "phases": [
                    phase("foundation", "0.1", "docs"),
                    phase("project-os", "0.4", "agents"),
                    phase("platform", "0.3", None),
                ],
            },
            **extra,
        },
    )


def _register_roadmap(config: Config) -> Any:
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions
    from folio_docs.docs.integrations import roadmap as roadmap_plugin

    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    roadmap_plugin.register_extensions(registry=registry, config=config)
    return registry


def test_roadmap_is_one_page_that_draws_its_own_header(tmp_path: Path) -> None:
    """One /roadmap view, and the component draws its name and description.

    The page's copy travels as component props, not as view props: the page
    owns its header — the name, the description and the board cross-link, on
    one background — so the layout's title band is switched off with `dense`
    rather than filled. Both would stack two page names.
    """
    registry = _register_roadmap(_project_roadmap_config(tmp_path))

    assert [p for p in registry.views if p.startswith("/roadmap")] == ["/roadmap"]

    view = registry.views["/roadmap"]
    assert view.title == "RoadmapProject Roadmap"
    assert view.props["dense"] is True
    assert "narrow" not in view.props
    assert "description" not in view.props

    block = view.slots["main"][0]
    assert block.component == "RoadmapPage"
    assert block.props["title"] == "RoadmapProject Roadmap"
    assert block.props["description"] == "Every project."


def test_roadmap_page_is_prerenderable_with_its_projects(tmp_path: Path) -> None:
    """One page.tsx at depth 1, and every phase's project reaches the data."""
    from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions
    from folio_docs.docs.integrations import roadmap as roadmap_plugin

    template_dir = _make_template(tmp_path)
    (template_dir / "lib").mkdir()
    (template_dir / "lib" / "roadmap-data.ts").write_text(
        "export const roadmapPhases = []"
    )
    build_dir = tmp_path / "build"
    config = _project_roadmap_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()
    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    roadmap_plugin.register_extensions(registry=registry, config=config)
    builder.apply_extensions(registry)

    page = (build_dir / "app" / "roadmap" / "page.tsx").read_text()
    assert '"pathToRoot": ".."' in page
    assert 'export const metadata = { title: "RoadmapProject Roadmap" }' in page
    assert not (build_dir / "app" / "roadmap" / "folio-docs").exists()

    data = (build_dir / "lib" / "roadmap-data.ts").read_text()
    assert '"project": "docs"' in data
    assert '"project": "agents"' in data


def test_roadmap_keeps_a_described_project_that_has_no_label() -> None:
    """A description alone is enough to reach a page that groups by project.

    Filtering on "has a label" dropped a described-but-unlabelled project out
    of the map while it still had phases. The rule is pinned on the helper
    rather than on the shipped view because a view only ever sees whichever
    projects a given docs.yaml happens to configure.
    """
    from folio_docs.docs.integrations import roadmap as roadmap_plugin

    roadmap = roadmap_plugin.normalize_roadmap(
        {
            "projects": {
                "agents": {"description": "The agent side."},
                "docs": {"label": "Folio Docs"},
            },
            "phases": [
                {"id": "docs-0.1", "project": "docs", "version": "0.1"},
                {"id": "agents-0.1", "project": "agents", "version": "0.1"},
            ],
        }
    )
    block = roadmap_plugin.project_block(roadmap)

    assert block == {
        "agents": {"description": "The agent side."},
        "docs": {"label": "Folio Docs"},
    }
    # Declaration order wins over the order the phases appear in.
    assert list(block) == ["agents", "docs"]


def test_roadmap_board_link_climbs_out_of_its_own_route(tmp_path: Path) -> None:
    """The board href is computed from the route depth, not assumed.

    board_href took a hard-coded single "../" before, which was right only
    because /roadmap happens to sit one level down.
    """
    from folio_docs.docs.integrations import roadmap as roadmap_plugin

    registry = _register_roadmap(
        _project_roadmap_config(tmp_path, kanban={"routes": {"public": True}})
    )

    view = registry.views["/roadmap"]
    assert view.slots["main"][0].props["links"][-1] == {
        "label": "Development board",
        "href": "../kanban/",
    }

    assert roadmap_plugin.board_href("/kanban", 2) == "../../kanban/"
    assert roadmap_plugin.board_href("/", 1) == "../"


def test_landing_hrefs_carry_the_page_depth() -> None:
    """A landing served below the root has to climb back out for "/path" hrefs.

    Every dot-relative href on /folio-docs/ pointed one level too deep, which a
    post-hydration <base href="../"> papered over for clicks and for nothing
    else — not a middle-click, not a copied link, not a crawler.
    """
    template = Path(__file__).parents[1] / "template"
    actions = (template / "components" / "landing" / "actions.tsx").read_text()
    assert 'export function normalizeLandingHref(href: string, pathToRoot = ".")' in (
        actions
    )
    assert "`${pathToRoot}${href}`" in actions

    # The context carries the depth to every section that builds an href.
    types = (template / "components" / "landing" / "types.ts").read_text()
    assert "pathToRoot?: string" in types
    sections = (template / "components" / "landing" / "sections.tsx").read_text()
    assert "normalizeLandingHref(" in sections
    assert re.search(r"normalizeLandingHref\((?![^)]*pathToRoot)", sections) is None

    # The docs landing declares its own depth instead of injecting a <base>.
    theme = Path(__file__).parents[2] / "docs/theme/folio-site"
    page = (theme / "app/folio-docs/page.tsx").read_text()
    assert 'const pathToRoot = ".."' in page
    assert "RouteBase" not in page
    assert "pathToRoot={pathToRoot}" in page
    assert "context={{ actionLinks, buildSteps, installCommands, pathToRoot }}" in page

    # Product hrefs are root-relative and normalized against that depth.
    products = (theme / "components/folio-products.ts").read_text()
    assert 'href: "/folio-docs/"' in products
    assert 'href: "./' not in products


def test_apply_extensions_generates_mdx_component_imports(tmp_path: Path) -> None:
    from folio_docs.extensions import ExtensionRegistry

    template_dir = _make_template(tmp_path)
    (template_dir / "mdx-components.tsx").write_text(
        'import { useMDXComponents as getThemeComponents } from "nextra-theme-docs"\n'
        "// __FOLIO_COMPONENT_IMPORTS__\n\n"
        "const themeComponents = getThemeComponents()\n\n"
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return {\n"
        "    ...themeComponents,\n"
        "    // __FOLIO_COMPONENT_ENTRIES__\n"
        "    ...components,\n"
        "  }\n"
        "}\n"
    )
    source_dir = tmp_path / "source-components"
    source_dir.mkdir()
    hero_source = source_dir / "hero.tsx"
    hero_source.write_text("export function Hero() { return <section /> }\n")

    registry = ExtensionRegistry()
    registry.register_component(
        "Hero",
        import_path="@/components/__folio_components/hero",
        export_name="Hero",
        source_path=hero_source,
    )
    build_dir = tmp_path / "build"
    builder = SiteBuilder(_make_config(tmp_path), str(template_dir), str(build_dir))
    builder.prepare()
    builder.apply_extensions(registry)

    mdx_components = (build_dir / "mdx-components.tsx").read_text()

    assert (build_dir / "components" / "__folio_components" / "hero.tsx").exists()
    assert (
        'import { Hero } from "@/components/__folio_components/hero"' in mdx_components
    )
    assert "    Hero," in mdx_components


def test_apply_extensions_keeps_mdx_component_injection_idempotent(
    tmp_path: Path,
) -> None:
    from folio_docs.extensions import ExtensionRegistry

    template_dir = _make_template(tmp_path)
    (template_dir / "mdx-components.tsx").write_text(
        'import { useMDXComponents as getThemeComponents } from "nextra-theme-docs"\n'
        "// __FOLIO_COMPONENT_IMPORTS__\n\n"
        "const themeComponents = getThemeComponents()\n\n"
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return {\n"
        "    ...themeComponents,\n"
        "    // __FOLIO_COMPONENT_ENTRIES__\n"
        "    ...components,\n"
        "  }\n"
        "}\n"
    )
    source_dir = tmp_path / "source-components"
    source_dir.mkdir()
    hero_source = source_dir / "hero.tsx"
    hero_source.write_text("export function Hero() { return <section /> }\n")

    registry = ExtensionRegistry()
    registry.register_component(
        "Hero",
        import_path="@/components/__folio_components/hero",
        export_name="Hero",
        source_path=hero_source,
    )
    build_dir = tmp_path / "build"
    builder = SiteBuilder(_make_config(tmp_path), str(template_dir), str(build_dir))
    builder.prepare()
    builder.apply_extensions(registry)
    builder.apply_extensions(registry)

    mdx_components = (build_dir / "mdx-components.tsx").read_text()

    assert (
        mdx_components.count(
            'import { Hero } from "@/components/__folio_components/hero"'
        )
        == 1
    )
    assert mdx_components.count("    Hero,") == 1


_MDX_COMPONENTS_WITH_MARKERS = (
    'import { useMDXComponents as getThemeComponents } from "nextra-theme-docs"\n'
    "// __FOLIO_COMPONENT_IMPORTS__\n\n"
    "const themeComponents = getThemeComponents()\n\n"
    "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
    "  return {\n"
    "    ...themeComponents,\n"
    "    // __FOLIO_COMPONENT_ENTRIES__\n"
    "    ...components,\n"
    "  }\n"
    "}\n"
)


def test_apply_extensions_skips_builtin_injection_for_custom_template(
    tmp_path: Path,
) -> None:
    """A custom template.path frontend does not bundle the builtin component
    files, so builtin-origin components must not be injected into it."""
    from folio_docs.extensions import ExtensionRegistry

    template_dir = _make_template(tmp_path)
    (template_dir / "mdx-components.tsx").write_text(_MDX_COMPONENTS_WITH_MARKERS)
    source_dir = tmp_path / "source-components"
    source_dir.mkdir()
    hero_source = source_dir / "hero.tsx"
    hero_source.write_text("export function Hero() { return <section /> }\n")

    registry = ExtensionRegistry()
    registry.register_component(
        "Callout",
        import_path="@/components/callout",
        origin="builtin",
    )
    registry.register_component(
        "Hero",
        import_path="@/components/__folio_components/hero",
        export_name="Hero",
        source_path=hero_source,
    )
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        template_path=str(template_dir),
    )
    build_dir = tmp_path / "build"
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()
    builder.apply_extensions(registry)

    mdx_components = (build_dir / "mdx-components.tsx").read_text()

    assert 'import { Callout } from "@/components/callout"' not in mdx_components
    assert "    Callout," not in mdx_components
    # Non-builtin components are still injected.
    assert (
        'import { Hero } from "@/components/__folio_components/hero"' in mdx_components
    )
    assert "    Hero," in mdx_components


def test_apply_extensions_injects_builtins_for_bundled_and_overlay_templates(
    tmp_path: Path,
) -> None:
    from folio_docs.extensions import ExtensionRegistry

    template_dir = _make_template(tmp_path)
    (template_dir / "mdx-components.tsx").write_text(_MDX_COMPONENTS_WITH_MARKERS)

    for label, config in {
        "bundled": _make_config(tmp_path),
        "overlay": Config(
            project_name="TestProject",
            output_dir=str(tmp_path / "output"),
            template_overlay_path=str(tmp_path / "overlay"),
        ),
    }.items():
        registry = ExtensionRegistry()
        registry.register_component(
            "Callout",
            import_path="@/components/callout",
            origin="builtin",
        )
        build_dir = tmp_path / f"build-{label}"
        builder = SiteBuilder(config, str(template_dir), str(build_dir))
        builder.prepare()
        builder.apply_extensions(registry)

        mdx_components = (build_dir / "mdx-components.tsx").read_text()

        assert 'import { Callout } from "@/components/callout"' in mdx_components, label
        assert "    Callout," in mdx_components, label


def test_apply_extensions_resolves_relative_component_sources_against_project_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio_docs.extensions import ExtensionRegistry

    template_dir = _make_template(tmp_path)
    (template_dir / "mdx-components.tsx").write_text(_MDX_COMPONENTS_WITH_MARKERS)
    project_dir = tmp_path / "proj"
    (project_dir / "components").mkdir(parents=True)
    (project_dir / "components" / "hero.tsx").write_text(
        "export function Hero() { return <section /> }\n"
    )

    registry = ExtensionRegistry()
    registry.register_component(
        "Hero",
        import_path="@/components/__folio_components/hero",
        export_name="Hero",
        source_path="components/hero.tsx",
    )
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        project_dir=str(project_dir),
    )
    build_dir = tmp_path / "build"
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()
    # The process CWD is NOT the project dir; the emitter must anchor the
    # relative source path to config.project_dir.
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    builder.apply_extensions(registry)

    assert (build_dir / "components" / "__folio_components" / "hero.tsx").exists()


def test_apply_extensions_copies_components_to_import_paths(tmp_path: Path) -> None:
    from folio_docs.extensions import ExtensionRegistry

    template_dir = _make_template(tmp_path)
    (template_dir / "mdx-components.tsx").write_text(
        'import { useMDXComponents as getThemeComponents } from "nextra-theme-docs"\n'
        "// __FOLIO_COMPONENT_IMPORTS__\n\n"
        "const themeComponents = getThemeComponents()\n\n"
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return {\n"
        "    ...themeComponents,\n"
        "    // __FOLIO_COMPONENT_ENTRIES__\n"
        "    ...components,\n"
        "  }\n"
        "}\n"
    )
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    first_source = first_dir / "widget.tsx"
    second_source = second_dir / "widget.tsx"
    first_source.write_text("export function FirstWidget() { return <section /> }\n")
    second_source.write_text("export function SecondWidget() { return <section /> }\n")

    registry = ExtensionRegistry()
    registry.register_component(
        "FirstWidget",
        import_path="@/components/__folio_components/widget-FirstWidget",
        export_name="FirstWidget",
        source_path=first_source,
    )
    registry.register_component(
        "SecondWidget",
        import_path="@/components/__folio_components/widget-SecondWidget",
        export_name="SecondWidget",
        source_path=second_source,
    )
    build_dir = tmp_path / "build"
    builder = SiteBuilder(_make_config(tmp_path), str(template_dir), str(build_dir))
    builder.prepare()

    builder.apply_extensions(registry)

    first_target = (
        build_dir / "components" / "__folio_components" / "widget-FirstWidget.tsx"
    )
    second_target = (
        build_dir / "components" / "__folio_components" / "widget-SecondWidget.tsx"
    )
    mdx_components = (build_dir / "mdx-components.tsx").read_text()
    assert first_target.read_text() == first_source.read_text()
    assert second_target.read_text() == second_source.read_text()
    assert (
        'import { FirstWidget } from "@/components/__folio_components/widget-FirstWidget"'
        in mdx_components
    )
    assert (
        'import { SecondWidget } from "@/components/__folio_components/widget-SecondWidget"'
        in mdx_components
    )


def test_apply_extensions_writes_layout_backed_public_view(tmp_path: Path) -> None:
    from folio_docs.extensions import ExtensionRegistry

    template_dir = _make_template(tmp_path)
    (template_dir / "mdx-components.tsx").write_text(
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return { ...components }\n"
        "}\n"
    )
    build_dir = tmp_path / "build"
    registry = ExtensionRegistry()
    registry.register_layout(
        "folio_docs.public",
        import_path="@/components/folio-view-layouts",
        export_name="PublicLayout",
    )
    registry.register_component("Roadmap", import_path="@/components/roadmap")
    registry.add_view(
        path="/roadmap",
        layout="folio_docs.public",
        title="Roadmap",
        props={"eyebrow": "Official plugin"},
        slots={"main": [{"component": "Roadmap"}]},
    )

    builder = SiteBuilder(_make_config(tmp_path), str(template_dir), str(build_dir))
    builder.prepare()
    builder.apply_extensions(registry)

    page = (build_dir / "app" / "roadmap" / "page.tsx").read_text()

    assert 'import { PublicLayout } from "@/components/folio-view-layouts"' in page
    assert 'import { Roadmap } from "@/components/roadmap"' in page
    assert 'title": "Roadmap"' in page
    assert 'eyebrow": "Official plugin"' in page
    assert "<PublicLayout {...layoutProps}>" in page
    assert "<Roadmap />" in page


def test_public_view_receives_computed_pathToRoot(tmp_path: Path) -> None:
    from folio_docs.extensions import ExtensionRegistry

    template_dir = _make_template(tmp_path)
    (template_dir / "mdx-components.tsx").write_text(
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return { ...components }\n"
        "}\n"
    )
    build_dir = tmp_path / "build"
    registry = ExtensionRegistry()
    registry.register_layout(
        "folio_docs.public",
        import_path="@/components/folio-view-layouts",
        export_name="PublicLayout",
    )
    registry.register_component("KanbanBoard", import_path="@/components/kanban-board")
    # Root view: pathToRoot should be "."
    registry.add_view(
        path="/",
        layout="folio_docs.public",
        title="Board",
        slots={"main": [{"component": "KanbanBoard"}]},
    )
    # One-segment view: pathToRoot should be ".."
    registry.add_view(
        path="/kanban",
        layout="folio_docs.public",
        title="Kanban",
        slots={"main": [{"component": "KanbanBoard"}]},
    )

    builder = SiteBuilder(_make_config(tmp_path), str(template_dir), str(build_dir))
    builder.prepare()
    builder.apply_extensions(registry)

    root_page = (build_dir / "app" / "page.tsx").read_text()
    kanban_page = (build_dir / "app" / "kanban" / "page.tsx").read_text()

    # Root view gets pathToRoot "."
    assert '"pathToRoot": "."' in root_page
    # One-segment view gets pathToRoot ".."
    assert '"pathToRoot": ".."' in kanban_page


def test_bundled_landing_keeps_neutral_layout_and_preserves_organic_editorial_preset() -> (
    None
):
    template_dir = Path(__file__).parents[1] / "template"
    page = (template_dir / "app" / "page.tsx").read_text()
    hero = (template_dir / "components" / "landing" / "hero.tsx").read_text()
    css = (template_dir / "app" / "globals.css").read_text()
    presets = (template_dir / "theme" / "presets.ts").read_text()

    assert not (template_dir / "components" / "landing-artwork.tsx").exists()
    assert 'import { LandingArtwork } from "@/components/landing-artwork"' not in page
    assert "<LandingArtwork />" not in page
    assert "landing-editorial-hero" not in page
    assert "landing-hero-title" not in page
    assert "landing-editorial-image-grid" not in page
    assert "Build pipeline overview" in hero
    assert "landing-artifact" in hero
    assert "landing-sequence" in hero
    assert "landing-shell" in page
    assert (
        "landing-navbar"
        in (template_dir / "components" / "landing-navbar.tsx").read_text()
    )
    assert "--landing-white" not in css
    assert ".landing-editorial-hero" not in css
    assert ".landing-hero-title" not in css
    assert ".landing-editorial-image-grid" not in css
    assert ".landing-artwork" not in css
    assert 'bg: "oklch(0.997 0.001 260)"' in presets
    assert 'headingWeight: "220"' in presets


def test_bundled_landing_uses_modular_distinct_hero_components() -> None:
    template_dir = Path(__file__).parents[1] / "template"
    page = (template_dir / "app" / "page.tsx").read_text()
    hero = (template_dir / "components" / "landing" / "hero.tsx").read_text()
    sections = (template_dir / "components" / "landing" / "sections.tsx").read_text()
    types = (template_dir / "components" / "landing" / "types.ts").read_text()
    docs_yaml = (Path(__file__).parents[2] / "docs.yaml").read_text()

    assert "DocsMapLandingHero" in page
    assert "SourcePipelineLandingHero" in page
    assert "BuildPipelineLandingHero" in page
    assert "HeartbeatLandingHero" in page
    assert '"@/components/landing/hero"' in page
    assert '"@/components/landing/sections"' in page
    assert "const LandingHero =" in page
    assert 'landingHeroVariant === "source-pipeline"' in page
    assert 'landingHeroVariant === "build-pipeline"' in page
    assert 'landingHeroVariant === "heartbeat"' in page
    assert "export function DocsMapLandingHero" in hero
    assert "export function SourcePipelineLandingHero" in hero
    assert "export function BuildPipelineLandingHero" in hero
    assert "export function HeartbeatLandingHero" in hero
    assert "Documentation routes" in hero
    assert "Build pipeline overview" in hero
    assert "Docstrings rendered into an API reference" in hero
    assert "stamps the build receipt" in hero
    assert "LANDING_SECTION_COMPONENTS" in sections
    for section_type in [
        "features",
        "comparison",
        "output",
        "routes",
        "pipeline",
        "install",
        "stats",
        "use-cases",
        "cta",
        "link-grid",
        "boards",
        "harness",
        "mechanism",
        "statement",
    ]:
        assert f'"{section_type}"' in types
        assert f'"{section_type}"' in sections
    assert "function HarnessSection" in sections
    assert "section.docs_label" in sections
    assert "section.agents_label" in sections
    assert 'from "@/components/landing/hero"' in sections
    assert "<HeartbeatLandingHero" in sections
    assert "embedded" in sections
    # This repository's own landing: the family story lives on the cover at
    # the site root, so the docs landing keeps the heartbeat hero and no
    # two-product harness section.
    assert 'variant: "heartbeat"' in docs_yaml
    assert 'type: "harness"' not in docs_yaml


def test_roadmap_guide_embeds_the_live_source_defined_demo() -> None:
    roadmap = (
        Path(__file__).parents[1] / "docs" / "guide" / "plugins" / "roadmap.md"
    ).read_text()

    # The guide page embeds the live demo now that roadmap.routes.docs is
    # disabled in docs.yaml (no plugin-generated duplicate at /docs/roadmap).
    assert "<Roadmap />" in roadmap
    assert "the same data as the standalone `/roadmap/` route" in roadmap
    assert "change phases in `docs.yaml`" in roadmap
    assert "## Product Direction" not in roadmap


def test_bundled_theme_configurator_uses_editable_preset_library() -> None:
    template_dir = Path(__file__).parents[1] / "template"
    configurator = (template_dir / "components" / "theme-configurator.tsx").read_text()
    preset_types = (template_dir / "theme" / "preset-types.ts").read_text()
    presets = (template_dir / "theme" / "presets.ts").read_text()
    root_layout = (template_dir / "app" / "layout.tsx").read_text()
    docs_layout = (template_dir / "app" / "docs" / "layout.tsx").read_text()
    navbar = (template_dir / "components" / "landing-navbar.tsx").read_text()
    css = (template_dir / "app" / "globals.css").read_text()

    assert not (template_dir / "theme" / "flavor-types.ts").exists()
    assert not (template_dir / "theme" / "flavors.ts").exists()
    assert not (template_dir / "app" / "tmp-theme-trigger" / "page.tsx").exists()
    assert "export interface ThemePreset" in preset_types
    assert "export interface PresetControl" in preset_types
    assert "resolvePresetTheme" in preset_types
    # Theme style properties are now generated in theme-contract.generated.ts
    theme_contract = (
        template_dir / "theme" / "theme-contract.generated.ts"
    ).read_text()
    assert '"--folio-workspace-shell-padding"?' in theme_contract
    assert '"--folio-workspace-shell-topbar-blur"?' in theme_contract
    assert '"--folio-workspace-shell-topbar-border"?' in theme_contract
    assert 'from "./project-theme"' in presets
    assert "projectThemePreset" in presets
    assert "export const presets" in presets
    assert 'id: "workshop"' in presets
    assert 'name: "Workshop"' in presets
    assert 'id: "canopy"' in presets
    assert 'name: "Canopy"' in presets
    assert "resolveSourceWorkspace" in presets
    assert "const sourceWorkspaceFrames" in presets
    assert 'label: "Borders"' in presets
    assert '"--folio-workspace-shell-padding": "22px"' in presets
    assert (
        'defaultOptions: { surface: "paper", density: "balanced", code: "panel", frame: "structured" }'
        in presets
    )
    assert (
        'defaultOptions: { surface: "moss", density: "compact", code: "panel", frame: "ruled" }'
        in presets
    )
    assert "oklch(0.966 0.008 82)" in presets
    assert "oklch(0.315 0.050 145)" in presets
    assert 'id: "beacon"' in presets
    assert 'name: "Beacon"' in presets
    assert 'id: "atlas"' in presets
    assert 'name: "Atlas"' in presets
    assert 'id: "ledger"' in presets
    assert 'id: "proof"' in presets
    assert 'id: "stacks"' in presets
    assert 'id: "draftline"' in presets
    assert 'id: "aperture"' in presets
    assert 'id: "organic-editorial"' in presets
    assert 'name: "Organic Editorial"' in presets
    assert "resolveOrganicEditorial" in presets
    assert (
        'defaultOptions: { scale: "poster", image: "cobalt", code: "quiet" }' in presets
    )
    assert 'id: "carbon"' in presets
    assert "linear-gradient" not in presets
    assert "neon" not in presets.lower()
    assert "glow" not in presets.lower()
    assert 'from "@/theme/presets"' in configurator
    assert 'from "@/theme/project-theme"' in configurator
    assert "projectThemeDefaultConfig" in configurator
    assert "import { ProjectHeaderActions }" not in docs_layout
    assert "__PROJECT_HEADER_ACTIONS_START__" in docs_layout
    assert (
        Path(__file__).parents[1]
        / "template"
        / "components"
        / "project-header-actions.tsx"
    ).exists()
    assert "const selectPreset" in configurator
    assert 'id: "geist"' in configurator
    assert "var(--font-geist-sans)" in configurator
    assert "var(--font-geist-mono)" in configurator
    assert "function PresetVisualTile" in configurator
    assert "theme-visual-preview" in configurator
    assert "preset.controls.map" in configurator
    assert "data-preset-control" in configurator
    assert "data-preset-option" in configurator
    assert "data-preset-option-swatch" in configurator
    assert "option.swatch" in configurator
    assert "data-preset-panel" in configurator
    assert "data-theme-page" in configurator
    assert "data-theme-back" in configurator
    assert "apply(readConfig(), false, false)" in configurator
    assert (
        "const apply = (rawConfig, persist = false, syncControls = true)"
        in configurator
    )
    assert (
        "aria-label={`Customize appearance. Current mode: ${activeModeLabel}. Current theme: ${activePreset.name}`}"
        in configurator
    )
    assert (
        "title={`Change appearance. Current mode: ${activeModeLabel}. Current theme: ${activePreset.name}`}"
        in configurator
    )
    assert "const presetGroups" in configurator
    # Preset groups are now sourced from the preset registry instead of a
    # hardcoded array; the labels + ordering live in presets.ts via registerGroup.
    assert "getGroups()" in configurator
    presets = (template_dir / "theme" / "presets.ts").read_text()
    assert 'registerGroup("project", "Project"' in presets
    assert 'registerGroup("workspace", "Workspace"' in presets
    assert 'registerGroup("product-docs", "Product Docs"' in presets
    assert 'registerGroup("reference", "Reference"' in presets
    assert 'registerGroup("expressive", "Expressive"' in presets
    assert presets.index('"Expressive"') < presets.index('"Workspace"')
    assert "data-theme-current" in configurator
    assert "data-theme-group" in configurator
    assert "data-theme-group-label" in configurator
    assert "data-theme-carousel" in configurator
    assert "overflow-x-auto" in configurator
    assert "shrink-0" in configurator
    assert "data-theme-default-tag" in configurator
    assert "preset.id === DEFAULT_CONFIG.presetId" in configurator
    assert "data-theme-chip" not in configurator
    assert "getPresetSummaryLabels" not in configurator
    assert "summaryControlPriority" not in configurator
    assert "Back" in configurator
    assert "Appearance" not in configurator
    assert "Preset library" not in configurator
    assert "Advanced controls" not in configurator
    assert "Customize preset" not in configurator
    assert ">Customize<" in configurator
    assert "Reset appearance" in configurator
    assert "theme-panel-header" in configurator
    assert "theme-back-button" in configurator
    assert "theme-section-label" not in configurator
    assert "data-theme-preset" in configurator
    assert "data-theme-custom" in configurator
    assert "data-theme-mode" in configurator
    assert "Theme scheme" in configurator
    assert "{ resolvedTheme, theme, setTheme }" in configurator
    assert "setTheme(mode)" in configurator
    assert "createPortal" in configurator
    assert "nextra-sidebar-footer" in configurator
    assert "theme-drawer-fallback" in configurator
    assert "createPortal(control, drawerTarget)" in configurator
    assert "data-config-page" not in configurator
    assert "data-config-panel" not in configurator
    assert "visibleThemeIds" not in configurator
    assert "data-theme-open" not in configurator
    assert "data-theme-settings-panel" not in configurator
    assert "data-folio-presets-panel" not in configurator
    assert "data-flavor" not in configurator
    assert "ThemeFlavor" not in configurator
    assert "FlavorControlsPanel" not in configurator
    assert "preset.description" not in configurator
    assert "Choose a complete documentation look" not in configurator
    assert "Fine-tune" not in configurator
    assert "Adjust the material" not in configurator
    assert "Changes stay attached" not in configurator
    assert "control.description &&" not in configurator
    assert "{option.description}" not in configurator
    assert "data-font-option" in configurator
    assert "data-color-option" in configurator
    assert "surfaceColorOptions" in configurator
    assert "shellPaddingOptions" in configurator
    assert "contentWidthOptions" in configurator
    assert "rhythmOptions" in configurator
    assert "borderOptions" in configurator
    assert "codeTreatmentOptions" in configurator
    assert "data-surface-color-option" in configurator
    assert "data-shell-padding-option" in configurator
    assert "data-content-width-option" in configurator
    assert "data-rhythm-option" in configurator
    assert "data-border-option" in configurator
    assert "data-code-treatment-option" in configurator
    assert "Surface color" in configurator
    assert "Shell spacing" in configurator
    assert "Content width" in configurator
    assert "Reading rhythm" in configurator
    assert "Code blocks" in configurator
    assert "Workspace surface" not in presets
    assert "fontOptions" in configurator
    assert "colorOptions" in configurator
    assert '"custom"' in configurator
    assert '"presets"' in configurator
    # Font family properties are now in generated contract
    assert '"--folio-heading-font-family"?' in theme_contract
    assert '"--folio-body-font-family"?' in theme_contract
    assert '"--folio-code-font-family"?' in theme_contract
    assert 'surfaceColorId: "preset"' in configurator
    assert 'shellPaddingId: "preset"' in configurator
    assert 'contentWidthId: "preset"' in configurator
    assert 'rhythmId: "preset"' in configurator
    assert 'borderId: "preset"' in configurator
    assert 'codeTreatmentId: "preset"' in configurator
    assert "optionsByFlavor" in configurator
    assert 'fontId: "sans"' in configurator
    assert 'colorId: "ink"' in configurator
    assert '"promptix": "beacon"' in configurator
    assert '"openai": "aperture"' in configurator
    assert 'id="theme-configurator-boot"' in configurator
    # The bootstrap must be a synchronous inline <script> so saved themes
    # apply before first paint (next/script afterInteractive would flash).
    assert 'import Script from "next/script"' not in configurator
    assert "<Script" not in configurator
    assert "<script" in configurator
    assert "updateConfig(DEFAULT_CONFIG)" in configurator
    assert "<ThemeConfigurator />" not in root_layout
    assert (
        'import { ThemeConfigurator } from "@/components/theme-configurator"'
        not in root_layout
    )
    assert "<ThemeConfigurator />" in docs_layout
    assert (
        'import { ThemeConfigurator } from "@/components/theme-configurator"'
        in docs_layout
    )
    assert "<VersionSelector />\n          <ThemeConfigurator />" not in docs_layout
    assert "darkMode={false}" in docs_layout
    assert "<ThemeConfigurator />" in docs_layout.split("<Layout", maxsplit=1)[1]
    assert "fixed right-5 bottom-5" not in configurator
    assert "theme-floating-panel" not in configurator
    assert "theme-navbar-panel" not in configurator
    assert "theme-drawer-control" in configurator
    assert "theme-drawer-panel" in configurator
    assert "theme-drawer-trigger" in configurator
    assert "theme-drawer-trigger-icon" not in configurator
    assert "const ActiveModeIcon = isDark ? Moon02Icon : Sun03Icon" not in configurator
    assert "icon={ActiveModeIcon}" not in configurator
    assert "PaintBoardIcon" not in configurator
    assert ">Theme</span>" in configurator
    assert "{activeModeLabel}</span>" not in configurator
    assert "theme-drawer-trigger-swatches" not in configurator
    assert "theme-drawer-trigger-swatch" not in configurator
    assert "theme-drawer-trigger-chevron" in configurator
    assert ".theme-drawer-control:not([open]) > .theme-drawer-panel" in css
    assert "data-theme-trigger-preset" not in configurator
    assert "Current theme: ${activePreset.name}" in configurator
    assert ">{activePreset.name}<" not in configurator
    assert "theme-drawer-trigger-meta" not in configurator
    assert "theme-drawer-trigger-copy" not in configurator
    assert "theme-drawer-trigger-tools" not in configurator
    assert "theme-drawer-trigger-preset-icon" not in configurator
    assert "const drawerRef = useRef<HTMLDetailsElement | null>(null)" in configurator
    assert "ref={drawerRef}" in configurator
    assert "function closeDrawerOnOutsidePointerDown" in configurator
    assert 'document.addEventListener("pointerdown"' in configurator
    assert 'document.removeEventListener("pointerdown"' in configurator
    assert "control.contains(target)" in configurator
    assert "control.open = false" in configurator
    assert "SHELL_THEME_CSS" in configurator
    assert "body > .nextra-navbar" in configurator
    assert "var(--folio-workspace-shell-topbar-blur)" in configurator
    assert "var(--folio-workspace-shell-topbar-border)" in configurator
    assert (
        "const STORAGE_KEY = `folio-theme:${DEFAULT_CONFIG.presetId}`" in configurator
    )
    assert "const DEFAULT_THEME_CSS = configToCss(DEFAULT_CONFIG)" in configurator
    assert 'id="theme-configurator-style"' in configurator
    assert "dangerouslySetInnerHTML={{ __html: DEFAULT_THEME_CSS }}" in configurator
    assert ".landing-shell" in configurator
    assert ".landing-navbar" in configurator
    assert re.search(
        r"\.landing-navbar\s*\{[^}]*border: var\(--folio-workspace-shell-border\)",
        configurator,
    )
    assert ".theme-floating-panel" not in css
    assert ".theme-navbar-panel" not in css
    assert ".theme-drawer-control" in css
    assert ".theme-drawer-fallback" in css
    assert ".theme-drawer-fallback .theme-drawer-trigger" in css
    assert "background: var(--sidebar);" in css
    assert ".theme-drawer-panel" in css
    assert ".theme-drawer-trigger" in css
    assert ".theme-drawer-trigger-icon" not in css
    assert ".theme-drawer-trigger-swatches" not in css
    assert ".theme-drawer-trigger-swatch" not in css
    assert ".theme-drawer-trigger-chevron" in css
    assert ".theme-drawer-control[open] > .theme-drawer-trigger" in css
    assert "min-height: 2.75rem" in css
    assert "padding: 0.5rem 0.625rem" in css
    assert (
        "font-weight: 700"
        not in css.split(
            ".theme-drawer-trigger-label",
            maxsplit=1,
        )[1].split("}", maxsplit=1)[0]
    )
    assert (
        "font-weight: 400"
        in css.split(
            ".theme-drawer-trigger-label",
            maxsplit=1,
        )[1].split("}", maxsplit=1)[0]
    )
    assert ".theme-drawer-trigger-meta" not in css
    assert ".theme-drawer-trigger-copy" not in css
    assert ".theme-drawer-trigger-tools" not in css
    assert ".theme-drawer-trigger-preset-icon" not in css
    assert "--folio-workspace-shell-padding: 0px" in css
    assert "padding: var(--folio-workspace-shell-padding)" in css
    assert "body > div:has(> .nextra-sidebar)" in css
    assert re.search(
        r"\.nextra-sidebar\s*\{[^}]*z-index:\s*60\s*!important;",
        css,
        re.DOTALL,
    )
    assert (
        'className="theme-drawer-panel absolute left-0 bottom-full mb-2' in configurator
    )
    assert "top: var(--folio-workspace-shell-padding)" in css
    assert ".landing-shell" in css
    assert "min-height: calc(100vh - (var(--folio-workspace-shell-padding) * 2))" in css
    assert ".landing-navbar" in css
    assert "width: calc(100% - (var(--folio-workspace-shell-padding) * 2))" in css
    assert "var(--folio-workspace-shell-topbar-blur)" in css
    assert "var(--folio-workspace-shell-topbar-border)" in css
    assert "Geist, Geist_Mono" in root_layout
    assert "--font-geist-sans" in root_layout
    assert "--font-geist-mono" in root_layout
    assert re.search(
        r"\.landing-navbar\s*\{[^}]*border: var\(--folio-workspace-shell-border\)", css
    )
    assert "ThemeConfigurator" not in navbar


def test_bundled_presets_register_builtins_before_project_preset() -> None:
    """The registration ORDER is load-bearing: registerPreset is last-wins, so
    the generated project preset must be registered after every builtin or a
    project preset reusing a builtin id would be clobbered by the builtin.

    tests/test_template_theme_behavior.py proves the last-wins/merge behavior
    against the real registry module; this test pins the presets.ts call order
    that behavior depends on.
    """
    template_dir = Path(__file__).parents[1] / "template"
    presets = (template_dir / "theme" / "presets.ts").read_text()
    registry = (template_dir / "theme" / "preset-registry.ts").read_text()
    configurator = (template_dir / "components" / "theme-configurator.tsx").read_text()

    # Builtins first, project preset last (last-wins direction).
    assert "builtinPresets.forEach((preset) => registerPreset(preset))" in presets
    assert 'registerPreset(projectThemePreset, "project")' in presets
    assert presets.index("builtinPresets.forEach") < presets.index(
        'registerPreset(projectThemePreset, "project")'
    )
    # ...and the project preset is registered before any registerGroup call so
    # the "project" placeholder group is created first (first-group-wins dedup
    # in the configurator relies on this Map insertion order).
    assert presets.index(
        'registerPreset(projectThemePreset, "project")'
    ) < presets.index('registerGroup("project", "Project"')

    # Registry semantics the ordering relies on: last-wins replacement and the
    # placeholder-group merge that makes registration order irrelevant for
    # group labels.
    assert "registeredPresets.set(preset.id, preset)" in registry
    assert (
        "Create a placeholder group so registration order does not matter" in registry
    )
    assert "existing.label = label" in registry

    # The configurator renders each preset exactly once via the shared
    # grouping helper (first group wins, "Other" fallback, empty groups
    # dropped) -- behaviorally covered in test_template_theme_behavior.py.
    assert "groupPresetsForDisplay(presetGroups, presets)" in configurator
    assert "seenPresetIds" in registry
    assert 'label: "Other"' in registry


def test_bundled_theme_configurator_migrates_legacy_storage_key() -> None:
    """Both theme-application paths must migrate the legacy "folio-theme"
    localStorage key to the project-scoped key: the React loadConfig() path
    and the duplicated JS inside the inline THEME_BOOTSTRAP_SCRIPT literal.
    Deleting either migration block must fail this test.
    """
    template_dir = Path(__file__).parents[1] / "template"
    configurator = (template_dir / "components" / "theme-configurator.tsx").read_text()

    assert 'const LEGACY_STORAGE_KEY = "folio-theme"' in configurator

    # React path (loadConfig): read legacy key, persist under the namespaced
    # key, remove the legacy key.
    assert "const legacy = localStorage.getItem(LEGACY_STORAGE_KEY)" in configurator
    assert "localStorage.setItem(STORAGE_KEY, JSON.stringify(migrated))" in configurator
    assert "localStorage.removeItem(LEGACY_STORAGE_KEY)" in configurator

    # Inline bootstrap path: the template literal interpolates the same keys
    # into the emitted script, so the pre-hydration path migrates too.
    assert (
        'const legacy = localStorage.getItem("${LEGACY_STORAGE_KEY}");' in configurator
    )
    assert (
        'localStorage.setItem("${STORAGE_KEY}", JSON.stringify(migrated));'
        in configurator
    )
    assert 'localStorage.removeItem("${LEGACY_STORAGE_KEY}");' in configurator


def test_generated_layout_keeps_theme_configurator_in_docs_navbar_for_mvp(
    tmp_path: Path,
) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(project_name="MvpDocs", output_dir=str(tmp_path / "output"))
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    builder.prepare()

    root_layout = (build_dir / "app" / "layout.tsx").read_text()
    docs_layout = (build_dir / "app" / "docs" / "layout.tsx").read_text()
    assert "<ThemeConfigurator />" not in root_layout
    assert (
        'import { ThemeConfigurator } from "@/components/theme-configurator"'
        not in root_layout
    )
    assert "<ThemeConfigurator />" in docs_layout
    assert (
        'import { ThemeConfigurator } from "@/components/theme-configurator"'
        in docs_layout
    )
    assert "darkMode={false}" in docs_layout
    assert "<VersionSelector />\n          <ThemeConfigurator />" not in docs_layout
    assert (build_dir / "components" / "theme-configurator.tsx").exists()


def test_generated_layout_uses_nextra_theme_switch_when_theme_configurator_disabled(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "folio_docs.docs.template_workspace.is_feature_enabled",
        lambda feature: feature != "theme_configurator",
    )
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(project_name="BasicDocs", output_dir=str(tmp_path / "output"))
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    builder.prepare()

    docs_layout = (build_dir / "app" / "docs" / "layout.tsx").read_text()
    assert "<ThemeConfigurator />" not in docs_layout
    assert (
        'import { ThemeConfigurator } from "@/components/theme-configurator"'
        not in docs_layout
    )
    assert "darkMode={false}" not in docs_layout


def test_generated_layout_keeps_theme_configurator_in_docs_navbar(
    tmp_path: Path,
) -> None:
    template_dir = Path(__file__).parents[1] / "template"
    build_dir = tmp_path / "build"
    config = Config(
        project_name="ExperimentalDocs", output_dir=str(tmp_path / "output")
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    builder.prepare()

    root_layout = (build_dir / "app" / "layout.tsx").read_text()
    docs_layout = (build_dir / "app" / "docs" / "layout.tsx").read_text()
    assert "<ThemeConfigurator />" not in root_layout
    assert (
        'import { ThemeConfigurator } from "@/components/theme-configurator"'
        not in root_layout
    )
    assert "<ThemeConfigurator />" in docs_layout
    assert (
        'import { ThemeConfigurator } from "@/components/theme-configurator"'
        in docs_layout
    )


def test_bundled_mdx_wrapper_sanitizes_toc_navigation_labels() -> None:
    root = Path(__file__).parents[1]
    mdx_components = (root / "template" / "mdx-components.tsx").read_text()

    assert "navigationEmojiPattern" in mdx_components
    assert "sanitizeToc" in mdx_components
    assert "WrapperWithSanitizedToc" in mdx_components
    assert "wrapper: WrapperWithSanitizedToc" in mdx_components


def test_documentation_quality_components_are_registered_and_documented() -> None:
    root = Path(__file__).parents[1]
    template_dir = root / "template"
    mdx_components = (template_dir / "mdx-components.tsx").read_text()
    component_index = (template_dir / "components" / "component-index.tsx").read_text()
    sidebar = (root / "folio_docs" / "docs" / "sidebar.py").read_text()

    components = [
        ("terminal-session", "TerminalSession"),
        ("config-panel", "ConfigPanel"),
        ("build-artifact", "BuildArtifact"),
        ("command-grid", "CommandGrid"),
        ("before-after", "BeforeAfter"),
        ("doc-preview", "DocPreview"),
        ("checklist", "Checklist"),
        ("hook-map", "HookMap"),
    ]

    for slug, export in components:
        component_path = template_dir / "components" / f"{slug}.tsx"
        docs_path = root / "docs" / "guide" / "components" / f"{slug}.md"

        assert component_path.exists(), f"Missing component file for {export}"
        component = component_path.read_text()
        assert f"export function {export}" in component
        assert f"import {{ {export}" in mdx_components
        assert f"{export}," in mdx_components
        assert docs_path.exists(), f"Missing docs page for {export}"
        assert f"# {export}" in docs_path.read_text()
        assert f'title: "{export}"' in component_index
        assert f'href: "/docs/components/{slug}"' in component_index
        assert f'("{slug}",' in sidebar

    assert "CommandCard," in mdx_components
    assert (
        "export function CommandCard"
        in (template_dir / "components" / "command-grid.tsx").read_text()
    )


def test_terminal_session_docs_avoid_invented_build_output() -> None:
    root = Path(__file__).parents[1]
    docs = (root / "docs" / "guide" / "components" / "terminal-session.md").read_text()
    pyproject = (root / "pyproject.toml").read_text()
    version_match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)

    assert version_match is not None
    assert "Avoid invented success logs" in docs
    assert "copies only the `command` value" in docs
    assert "folio --version" in docs
    assert f"folio {version_match.group(1)}" in docs
    assert "✓ Sources" not in docs
    assert "✨ Site ready" not in docs


def test_component_catalog_examples_use_preview_code() -> None:
    root = Path(__file__).parents[1]
    template_dir = root / "template"
    component_path = template_dir / "components" / "preview-code.tsx"
    mdx_components = (template_dir / "mdx-components.tsx").read_text()
    component_index = (template_dir / "components" / "component-index.tsx").read_text()
    sidebar = (root / "folio_docs" / "docs" / "sidebar.py").read_text()
    agents = (root.parent / "AGENTS.md").read_text()

    assert component_path.exists()
    component = component_path.read_text()
    assert "export function PreviewCode" in component
    assert 'role="radiogroup"' in component
    assert 'type="radio"' in component
    assert "data-preview-code-panel" in component
    assert component.index('role="radiogroup"') < component.index('className="min-w-0"')
    assert "sm:justify-between" not in component
    assert "ViewIcon" in component
    assert "FileCodeIcon" in component
    assert "nextra-code" in component
    assert 'type === "pre"' in component
    assert 'import { PreviewCode } from "@/components/preview-code"' in mdx_components
    assert "PreviewCode," in mdx_components
    assert 'title: "PreviewCode"' in component_index
    assert 'href: "/docs/components/preview-code"' in component_index
    assert '("preview-code", "PreviewCode")' in sidebar
    assert "**PreviewCode**" in agents

    docs_dir = root / "docs" / "guide" / "components"
    docs_with_examples = [
        path
        for path in sorted(docs_dir.glob("*.md"))
        if path.name != "preview-code.md"
        and re.search(r"^## Example\b", path.read_text(), re.MULTILINE)
    ]

    assert docs_with_examples
    for path in docs_with_examples:
        text = path.read_text()
        assert "<PreviewCode" in text, f"{path.name} should use PreviewCode"
        assert "## Rendered Example" not in text, (
            f"{path.name} still splits rendered examples"
        )


def test_code_group_uses_instance_scoped_accessible_tab_ids() -> None:
    component = (
        Path(__file__).parents[1] / "template" / "components" / "code-group.tsx"
    ).read_text()

    assert "React.useId().replace" in component
    assert "tabRefs.current[index]?.focus()" in component
    assert "id={`${codeGroupId}-tab-${i}`}" in component
    assert "aria-controls={`${codeGroupId}-panel-${i}`}" in component
    assert "id={`${codeGroupId}-panel-${i}`}" in component
    assert "aria-labelledby={`${codeGroupId}-tab-${i}`}" in component
    assert "hidden={i !== active}" in component
    assert "code-panel-" not in component


def test_docs_layout_exposes_global_skip_target() -> None:
    root = Path(__file__).parents[1]
    root_layout = (root / "template" / "app" / "layout.tsx").read_text()
    docs_layout = (root / "template" / "app" / "docs" / "layout.tsx").read_text()

    assert 'href="#main-content"' in root_layout
    assert '<div id="main-content">{children}</div>' in docs_layout


def test_quickstart_uses_the_installed_cli_for_the_complete_first_run() -> None:
    root = Path(__file__).parents[1]
    quickstart = (root / "docs" / "guide" / "quickstart.md").read_text()

    assert "<TerminalSession" not in quickstart
    for command in ["folio init", "folio serve", "folio build --clean"]:
        assert command in quickstart
    assert "uv tool install folio-docs" in quickstart
    assert "git clone https://github.com/pguijas/folio_docs.git" not in quickstart
    assert "uv run folio" not in quickstart


def test_public_docs_do_not_include_troubleshooting_content() -> None:
    root = Path(__file__).parents[1]
    public_docs = [
        root / "docs" / "guide" / "installation.md",
        root / "docs" / "guide" / "components" / "checklist.md",
        root / "template" / "components" / "component-index.tsx",
    ]

    for path in public_docs:
        assert "troubleshooting" not in path.read_text().lower()


def test_disabled_feature_docs_are_hidden_from_public_docs() -> None:
    root = Path(__file__).parents[1]
    docs_dir = root / "docs" / "guide"
    configuration = (docs_dir / "configuration.md").read_text()
    cli = (docs_dir / "cli.md").read_text()
    migration = (docs_dir / "migration.md").read_text()
    overview = (docs_dir / "index.md").read_text()
    sidebar = (root / "folio_docs" / "docs" / "sidebar.py").read_text()
    agents = (root.parent / "AGENTS.md").read_text()

    assert "**MVP-disabled features**" in configuration
    # custom components are released: the components: key is documented.
    assert "### components" in configuration
    assert "### versions" not in configuration
    # Released features are documented publicly.
    assert "folio roadmap" in cli
    assert "build-versions" not in cli
    assert "--versions" not in cli
    assert '("landing", "Landing Page")' in sidebar
    assert '("versioning", "Versioning (Alpha)")' not in sidebar
    assert '("i18n", "Internationalization (Experimental)")' not in sidebar
    assert "[**Versioning (Alpha)**](./versioning)" not in overview
    assert "pluggy-based (early)" not in migration
    assert "**Disabled feature surfaces**" in agents
    assert "**Experimental feature docs**" not in agents


def test_custom_template_docs_define_expert_contract() -> None:
    root = Path(__file__).parents[1]
    legacy_guide = root / "docs" / "guide" / "templates.md"
    guide = root / "docs" / "guide" / "theming" / "custom-templates.md"
    docs = guide.read_text(encoding="utf-8")
    configuration = (root / "docs" / "guide" / "configuration.md").read_text(
        encoding="utf-8"
    )
    overview = (root / "docs" / "guide" / "index.md").read_text(encoding="utf-8")
    theming = (root / "docs" / "guide" / "theming" / "index.md").read_text(
        encoding="utf-8"
    )
    personalization = (
        root / "docs" / "guide" / "theming" / "personalization.md"
    ).read_text(encoding="utf-8")
    packages = (root / "docs" / "guide" / "theming" / "theme-packages.md").read_text(
        encoding="utf-8"
    )
    sidebar = (root / "folio_docs" / "docs" / "sidebar.py").read_text(encoding="utf-8")
    agents = (root.parent / "AGENTS.md").read_text(encoding="utf-8")

    assert not legacy_guide.exists()
    assert "one theming model with three ownership levels" in theming
    assert "[theme packages](./theme-packages)" in personalization
    assert "`theme.package`" in packages
    assert "full frontend workspace" in docs
    assert "Next/Nextra-compatible" in docs
    assert "`template.path`" in docs
    assert "`template.params`" in docs
    assert "`/docs`" in docs
    assert "`mdx-components.tsx`" in docs
    assert "Do not edit `.build/`" in docs
    assert "not a color-token override system" in docs
    assert "### template" in configuration
    assert "`template`" in configuration
    assert "[**Theming**](./theming/index)" in overview
    assert "[Custom Templates](./theming/custom-templates)" in configuration
    assert '"theming",\n        "Theming",' in sidebar
    assert '("custom-templates", "Custom Templates")' in sidebar
    assert "**Custom templates**" in agents


def test_migration_guide_documents_migration_field_feedback() -> None:
    migration = (
        Path(__file__).parents[1] / "docs" / "guide" / "migration.md"
    ).read_text()

    assert "Markdown docs routes use kebab-case URLs" in migration
    assert "`common_errors/index.md`" in migration
    assert "`/docs/common-errors/`" in migration
    assert "does not emit a warning if the `.rst` files were" in migration
    assert "already removed before running `folio build` or `folio serve`" in migration
    assert "Raw `<iframe>` tags are stripped" in migration
    assert "`<Tabs>` and `<TabItem>`" in migration
    assert "`> **Warning:**`" in migration
    assert '`<Callout type="warning">`' in migration


def test_configuration_guide_documents_sidebar_default_collapsed() -> None:
    configuration = (
        Path(__file__).parents[1] / "docs" / "guide" / "configuration.md"
    ).read_text()

    assert "### sidebar" in configuration
    assert "`default_collapsed`" in configuration
    assert "`open: false`" in configuration
    assert "sidebar.default_collapsed: true" in configuration


def test_disabled_feature_docs_are_not_generated(tmp_path: Path) -> None:
    page = _write_generated_doc_page(
        tmp_path=tmp_path,
        route="i18n",
        content="# Internationalization\n\nThis guide explains the experimental feature.",
        title="Internationalization",
    )

    assert not page.exists()


def test_disabled_api_modules_are_not_generated(tmp_path: Path, monkeypatch) -> None:
    from folio_docs import features

    monkeypatch.setattr(
        features,
        "MVP_DISABLED_API_MODULES",
        {"folio_docs.extensions": "roadmap", "folio_docs.docs.integrations": "roadmap"},
    )
    source_dir = tmp_path / "folio_docs" / "docs" / "integrations"
    source_dir.mkdir(parents=True)
    source_file = source_dir / "roadmap.py"
    source_file.write_text('"""Roadmap plugin internals."""\n', encoding="utf-8")
    extensions_file = tmp_path / "folio_docs" / "extensions.py"
    extensions_file.write_text(
        '"""Extension registry internals."""\n', encoding="utf-8"
    )

    build_dir = tmp_path / "build"
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text('{"name": "test"}', encoding="utf-8")
    config_path = tmp_path / "docs.yaml"
    config_path.write_text('project:\n  name: "TestProject"\n', encoding="utf-8")

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    stale_route = "api-reference/folio_docs/docs/integrations/roadmap"
    builder.write_page("api-reference/index", "# Stale API index\n")
    builder.write_page(stale_route, "# Stale roadmap API\n")
    builder.write_meta("api-reference", 'export default { "folio": "Folio" }')
    builder.write_meta("api-reference/folio", 'export default { "docs": "Docs" }')
    stale_extensions_route = "api-reference/folio_docs/extensions"
    builder.write_page(stale_extensions_route, "# Stale extensions API\n")

    _generate_content_pages(
        builder=builder,
        config=config,
        modules=[
            ModuleIR(
                name="folio_docs.docs.integrations.roadmap",
                docstring=DocstringIR(short_description="Roadmap plugin internals."),
                classes=[],
                functions=[],
                constants=[],
                source_file=str(source_file),
            ),
            ModuleIR(
                name="folio_docs.extensions",
                docstring=DocstringIR(
                    short_description="Extension registry internals."
                ),
                classes=[],
                functions=[],
                constants=[],
                source_file=str(extensions_file),
            ),
        ],
        docs=[],
        project_dir=tmp_path,
        build_context=_build_manifest_context(config_path, template_dir, "main"),
        clean=True,
        verbose=False,
    )

    assert not (build_dir / "content" / "api-reference" / "index.mdx").exists()
    assert not (build_dir / "content" / "api-reference" / "_meta.ts").exists()
    assert not (build_dir / "content" / "api-reference" / "folio" / "_meta.ts").exists()
    assert not (build_dir / ".folio" / "pages" / "api-reference" / "index.md").exists()
    assert not (
        build_dir
        / "content"
        / "api-reference"
        / "folio"
        / "docs"
        / "integrations"
        / "roadmap.mdx"
    ).exists()
    assert not (
        build_dir / "content" / "api-reference" / "folio" / "extensions.mdx"
    ).exists()
    assert not (
        build_dir
        / ".folio"
        / "pages"
        / "api-reference"
        / "folio"
        / "plugins"
        / "roadmap.md"
    ).exists()
    assert not (
        build_dir / ".folio" / "pages" / "api-reference" / "folio" / "extensions.md"
    ).exists()


def test_unavailable_feature_component_does_not_expose_preview_escape() -> None:
    root = Path(__file__).parents[1]
    component = (
        root / "template" / "components" / "unavailable-feature.tsx"
    ).read_text()

    assert "Preview when needed" not in component
    assert "Not finished" in component
    assert "This page is not finished yet." in component
    assert "not available in the MVP build" not in component
    assert "MVP build" not in component


def test_disabled_feature_docs_ignore_env_overrides(tmp_path: Path) -> None:
    page = _write_generated_doc_page(
        tmp_path=tmp_path,
        route="i18n",
        content="# Internationalization\n\nExperimental guide content.",
        title="Internationalization",
    )

    assert not page.exists()


def test_landing_guide_is_generated(tmp_path: Path) -> None:
    page = _write_generated_doc_page(
        tmp_path=tmp_path,
        route="landing",
        content="# Landing Page\n\nConfigure the optional homepage.",
    )

    assert page.exists()


def test_manifest_context_tracks_disabled_feature_state(tmp_path: Path) -> None:
    config_path = tmp_path / "docs.yaml"
    config_path.write_text('project:\n  name: "TestProject"\n', encoding="utf-8")
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text('{"name": "test"}', encoding="utf-8")

    context = _build_manifest_context(config_path, template_dir, "main")

    assert context["experimental_features"] == "disabled"


def test_doc_preview_uses_configured_base_path_for_internal_assets() -> None:
    root = Path(__file__).parents[1]
    component = (root / "template" / "components" / "doc-preview.tsx").read_text()
    next_config = (root / "template" / "next.config.mjs").read_text()

    assert 'NEXT_PUBLIC_FOLIO_BASE_PATH: basePath ?? ""' in next_config
    assert (
        "const FOLIO_BASE_PATH = process.env.NEXT_PUBLIC_FOLIO_BASE_PATH" in component
    )
    assert "function withFolioBasePath(path: string)" in component
    assert "return `${FOLIO_BASE_PATH}${path}`" in component
    assert (
        "withFolioBasePath(`/_folio/examples/${examplePath(example)}/index.html`)"
        in component
    )
    assert (
        "withFolioBasePath(`/_folio/examples/${examplePath(example)}/manifest.json`)"
        in component
    )
    assert "url: withFolioBasePath(file.url)" in component
    assert 'const sourcePath = withFolioBasePath("/_folio/markdown/")' in component


def test_api_reference_index_component_is_registered() -> None:
    root = Path(__file__).parents[1]
    mdx_components = (root / "template" / "mdx-components.tsx").read_text()
    api_index = (
        root / "template" / "components" / "api-reference-index.tsx"
    ).read_text()

    assert (
        'import { ApiReferenceIndex } from "@/components/api-reference-index"'
        in mdx_components
    )
    assert "ApiReferenceIndex," in mdx_components
    assert "export function ApiReferenceIndex" in api_index
    assert "api-reference-index-hero" in api_index
    assert "Python source catalog" in api_index


def test_docs_static_params_do_not_include_synthetic_index_route() -> None:
    page = (
        Path(__file__).parents[1]
        / "template"
        / "app"
        / "docs"
        / "[[...mdxPath]]"
        / "page.jsx"
    ).read_text()

    assert "mdxPath: ['index']" not in page


def test_page_actions_markdown_url_uses_configured_base_path() -> None:
    root = Path(__file__).parents[1]
    actions = (root / "template" / "components" / "page-actions-button.tsx").read_text()
    next_config = (root / "template" / "next.config.mjs").read_text()

    assert 'NEXT_PUBLIC_FOLIO_BASE_PATH: basePath ?? ""' in next_config
    assert "const FOLIO_BASE_PATH = process.env.NEXT_PUBLIC_FOLIO_BASE_PATH" in actions
    assert "function withFolioBasePath(path: string)" in actions
    assert "withFolioBasePath(`/_folio/markdown/${getDocsRoute()}.md`)" in actions


def test_docs_page_head_links_the_markdown_mirror() -> None:
    """Every docs page must advertise its Markdown mirror in the rendered head.

    The mirrors ship with every build, but their only other pointer is a click
    handler inside the client bundle — nothing an agent reading the HTML can
    see. Next renders ``alternates.types`` as
    ``<link rel="alternate" type="text/markdown" href="...">``.
    """
    root = Path(__file__).parents[1]
    page = (
        root / "template" / "app" / "docs" / "[[...mdxPath]]" / "page.jsx"
    ).read_text()

    assert 'import { existsSync } from "fs"' in page
    assert 'import { join } from "path"' in page
    assert (
        'const markdownMirrorDir = join(process.cwd(), "public", "_folio", "markdown")'
        in page
    )
    # Mirrors are named after the content file, so a directory index page keeps
    # its `index.md` name instead of collapsing onto the parent route.
    assert "for (const candidate of [`${route}.md`, `${route}/index.md`])" in page
    assert "if (existsSync(join(markdownMirrorDir, candidate)))" in page
    assert "return `/_folio/markdown/${candidate}`" in page
    assert '"text/markdown": markdownUrl,' in page
    assert "const alternates = pageAlternates(" in page


def test_docs_page_markdown_link_uses_configured_base_path() -> None:
    root = Path(__file__).parents[1]
    page = (
        root / "template" / "app" / "docs" / "[[...mdxPath]]" / "page.jsx"
    ).read_text()
    next_config = (root / "template" / "next.config.mjs").read_text()

    assert 'NEXT_PUBLIC_FOLIO_BASE_PATH: basePath ?? ""' in next_config
    assert (
        'const folioBasePath = process.env.NEXT_PUBLIC_FOLIO_BASE_PATH?.replace(/\\/+$/, "") ?? ""'
        in page
    )
    assert (
        "return siteUrl ? `${siteUrl}${mirrorPath}` : `${folioBasePath}${mirrorPath}`"
        in page
    )


def test_docs_page_markdown_url_resolves_the_mirror_the_build_wrote(
    tmp_path: Path,
) -> None:
    """The head href must name a mirror file that is really on disk.

    The resolver is lifted out of the docs page and run against a build
    directory ``SiteBuilder`` filled in: a flat page, a directory index page
    (whose mirror keeps the ``index.md`` name), and a route with no mirror.
    Both link shapes are covered, since a site with no configured URL is served
    from the deploy base path instead.
    """
    root = Path(__file__).parents[1]
    page = (
        root / "template" / "app" / "docs" / "[[...mdxPath]]" / "page.jsx"
    ).read_text()
    resolver = re.search(
        r"function markdownMirrorPath\(mdxPath\) \{.*?\nfunction markdownMirrorUrl"
        r"\(mdxPath\) \{.*?\n\}\n",
        page,
        re.DOTALL,
    )
    assert resolver, "markdown mirror resolver not found in the docs route page"

    build_dir = tmp_path / "build"
    (build_dir / "content").mkdir(parents=True)
    builder = SiteBuilder(
        _make_config(tmp_path), str(tmp_path / "template"), str(build_dir)
    )
    builder.write_page("index", "# Home\n")
    builder.write_page("quickstart", "# Quickstart\n")
    builder.write_page("guide/index", "# Guide\n")

    prelude = (
        f"const markdownMirrorDir = "
        f"{json.dumps(str(build_dir / 'public' / '_folio' / 'markdown'))}\n"
        f"{resolver.group(0)}"
    )
    script = f"""
      import {{ existsSync }} from "fs"
      import {{ join }} from "path"

      const assert = (condition, message) => {{
        if (!condition) throw new Error(message)
      }}

      {{
        const siteUrl = "https://example.com/base"
        const folioBasePath = "/base"
        {prelude}

        assert(
          markdownMirrorUrl([]) ===
            "https://example.com/base/_folio/markdown/index.md",
          "the docs index should link its own mirror",
        )
        assert(
          markdownMirrorUrl(["quickstart"]) ===
            "https://example.com/base/_folio/markdown/quickstart.md",
          "a flat page should link its own mirror",
        )
        assert(
          markdownMirrorUrl(["guide"]) ===
            "https://example.com/base/_folio/markdown/guide/index.md",
          "a directory index page should link its index.md mirror",
        )
        assert(
          markdownMirrorUrl(["nothing-here"]) === "",
          "a route with no mirror on disk should link nothing",
        )
      }}

      {{
        const siteUrl = ""
        const folioBasePath = "/base"
        {prelude}

        assert(
          markdownMirrorUrl(["quickstart"]) ===
            "/base/_folio/markdown/quickstart.md",
          "without a site URL the mirror link should carry the deploy base path",
        )
      }}
    """

    subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=True,
        cwd=root,
    )


def test_sitemap_lists_the_markdown_mirrors(tmp_path: Path) -> None:
    """The sitemap is the crawlable index of the mirrors.

    The mirror URL is derived from the content file, which is exactly how
    ``SiteBuilder`` names the file it writes — asserted here against a real
    write so the two cannot drift.
    """
    root = Path(__file__).parents[1]
    sitemap = (root / "template" / "app" / "sitemap.ts").read_text()

    assert "function markdownMirrorPath(filePath: string)" in sitemap
    assert (
        'return `/_folio/markdown/${relativePath.replace(/\\.mdx$/, ".md")}`' in sitemap
    )
    assert "contentMdxFiles(CONTENT_DIR).map(markdownMirrorPath).sort()" in sitemap
    assert "url: absoluteUrl(mirrorPath)," in sitemap
    assert "return [...pages, ...markdownMirrors]" in sitemap

    build_dir = tmp_path / "build"
    (build_dir / "content").mkdir(parents=True)
    builder = SiteBuilder(
        _make_config(tmp_path), str(tmp_path / "template"), str(build_dir)
    )
    builder.write_page("guide/index", "# Guide\n")

    mirror = build_dir / "public" / "_folio" / "markdown" / "guide" / "index.md"
    assert mirror.exists()
    served_path = "/" + mirror.relative_to(build_dir / "public").as_posix()
    assert served_path == "/_folio/markdown/guide/index.md"


def test_docs_sidebar_index_groups_open_their_index_pages() -> None:
    root = Path(__file__).parents[1]
    docs_layout = (root / "template" / "app" / "docs" / "layout.tsx").read_text()
    sidebar_links = (
        root / "template" / "components" / "sidebar-index-links.tsx"
    ).read_text()

    assert (
        'import { SidebarIndexLinks } from "@/components/sidebar-index-links"'
        in docs_layout
    )
    assert "<SidebarIndexLinks />" in docs_layout
    assert "button[data-href]" in sidebar_links
    assert "NEXT_PUBLIC_FOLIO_BASE_PATH" in sidebar_links
    assert "function withFolioBasePath(path: string)" in sidebar_links
    assert "function withTrailingSlash(href: string)" in sidebar_links
    assert "return withTrailingSlash(withFolioBasePath(href))" in sidebar_links
    assert 'target.closest("svg")' in sidebar_links
    assert "window.location.assign" in sidebar_links
    assert 'event.key !== "Enter"' in sidebar_links


def test_site_builder_write_page(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    content_dir = build_dir / "content"
    content_dir.mkdir(parents=True)

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.write_page("getting-started", "# Getting Started\n\nHello world.")

    page_file = content_dir / "getting-started.mdx"
    assert page_file.exists()
    assert "# Getting Started" in page_file.read_text()
    markdown_file = build_dir / "public" / "_folio" / "markdown" / "getting-started.md"
    assert markdown_file.exists()
    assert markdown_file.read_text() == "# Getting Started\n\nHello world.\n"


def test_site_builder_read_page_roundtrip(tmp_path: Path) -> None:
    """read_page returns write_page content and rejects escaping routes.

    Plugins (openapi, kanban) rely on ``builder.read_page`` for their
    warm-build write-if-changed refresh of generated pages.
    """
    build_dir = tmp_path / "build"
    (build_dir / "content").mkdir(parents=True)

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.write_page("kanban", "# Board A\n")
    assert builder.read_page("kanban") == "# Board A\n"

    with pytest.raises(ValueError, match="outside content directory"):
        builder.read_page("../secrets")


def test_site_builder_list_pages(tmp_path: Path) -> None:
    """list_pages names on-disk routes under a prefix and rejects escapes.

    The kanban plugin generates one folder index per card that publishes
    documents; on a warm build it has to find last build's indexes before it
    can drop the ones whose card stopped publishing.
    """
    build_dir = tmp_path / "build"
    (build_dir / "content").mkdir(parents=True)

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.write_page("kanban/index", "# Board\n")
    builder.write_page("kanban/one-card/index", "# One card\n")
    builder.write_page("kanban/one-card/compared", "# Compared\n")
    builder.write_page("guide/intro", "# Intro\n")

    assert builder.list_pages("kanban") == [
        "kanban/index",
        "kanban/one-card/compared",
        "kanban/one-card/index",
    ]
    assert builder.list_pages("kanban/one-card") == [
        "kanban/one-card/compared",
        "kanban/one-card/index",
    ]
    assert builder.list_pages("kanban/missing") == []

    with pytest.raises(ValueError, match="outside content directory"):
        builder.list_pages("../secrets")

    # The real build constructs the builder on a relative build dir
    # (".build"), so listing must not depend on content_dir being absolute.
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.chdir(tmp_path)
    try:
        relative = SiteBuilder(config, "template", "build")
        assert relative.list_pages("kanban/one-card") == [
            "kanban/one-card/compared",
            "kanban/one-card/index",
        ]
    finally:
        monkeypatch.undo()


def test_site_builder_write_page_nested(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    content_dir = build_dir / "content"
    content_dir.mkdir(parents=True)

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.write_page("api-reference/mylib/core", "# mylib.core")

    page_file = content_dir / "api-reference" / "mylib" / "core.mdx"
    assert page_file.exists()
    assert (
        build_dir
        / "public"
        / "_folio"
        / "markdown"
        / "api-reference"
        / "mylib"
        / "core.md"
    ).exists()


def test_site_builder_write_page_index(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    content_dir = build_dir / "content"
    content_dir.mkdir(parents=True)

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.write_page("index", "# Home")

    assert (content_dir / "index.mdx").exists()
    assert (build_dir / "public" / "_folio" / "markdown" / "index.md").exists()


def test_site_builder_ignores_handwritten_doc_preview_examples(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    examples_dir = tmp_path / "docs" / "examples"
    sample_dir = examples_dir / "sample-preview"
    files_dir = sample_dir / "files"
    files_dir.mkdir(parents=True)
    (sample_dir / "preview.html").write_text(
        "<!doctype html><title>Sample preview</title><main>Sample</main>",
        encoding="utf-8",
    )
    (files_dir / "docs").mkdir()
    (files_dir / "docs" / "index.md").write_text("# Tiny docs\n", encoding="utf-8")
    (files_dir / "docs.yaml").write_text("project:\n  name: Tiny\n", encoding="utf-8")

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))
    builder.write_preview_examples(examples_dir)

    output_dir = build_dir / "public" / "_folio" / "examples" / "sample-preview"
    assert not output_dir.exists()


def test_site_builder_builds_doc_preview_examples_from_folio_projects(
    tmp_path: Path,
    monkeypatch,
) -> None:
    build_dir = tmp_path / "build"
    examples_dir = tmp_path / "docs" / "examples"
    sample_dir = examples_dir / "sample-preview"
    docs_dir = sample_dir / "docs"
    src_dir = sample_dir / "src" / "demo"
    docs_dir.mkdir(parents=True)
    src_dir.mkdir(parents=True)
    (sample_dir / "docs.yaml").write_text(
        "project:\n"
        "  name: Demo\n"
        "source:\n"
        "  python:\n"
        "    paths:\n"
        "      - src/demo\n"
        "  docs:\n"
        "    - docs\n",
        encoding="utf-8",
    )
    (docs_dir / "index.md").write_text("# Demo docs\n", encoding="utf-8")
    (src_dir / "core.py").write_text(
        "def add(left: int, right: int) -> int:\n"
        '    """Add two numbers."""\n'
        "    return left + right\n",
        encoding="utf-8",
    )
    (sample_dir / "preview.html").write_text(
        "<!doctype html><title>Old design reference</title>",
        encoding="utf-8",
    )

    calls: list[tuple[Path, Path]] = []

    def fake_build_preview_example_project(
        self: SiteBuilder,
        example_dir: Path,
        target_dir: Path,
    ) -> None:
        calls.append((example_dir, target_dir))
        target_dir.mkdir(parents=True)
        (target_dir / "index.html").write_text(
            "<!doctype html><main>Generated by Folio</main>",
            encoding="utf-8",
        )

    monkeypatch.setattr(
        SiteBuilder,
        "_build_preview_example_project",
        fake_build_preview_example_project,
        raising=False,
    )

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))
    builder.write_preview_examples(examples_dir)

    output_dir = build_dir / "public" / "_folio" / "examples" / "sample-preview"
    assert calls == [(sample_dir, output_dir)]
    assert "Generated by Folio" in (output_dir / "index.html").read_text(
        encoding="utf-8"
    )
    assert not (output_dir / "preview.html").exists()

    manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest == {
        "files": [
            {
                "path": "docs/index.md",
                "url": "/_folio/examples/sample-preview/files/docs/index.md",
                "language": "markdown",
            },
            {
                "path": "docs.yaml",
                "url": "/_folio/examples/sample-preview/files/docs.yaml",
                "language": "yaml",
            },
            {
                "path": "src/demo/core.py",
                "url": "/_folio/examples/sample-preview/files/src/demo/core.py",
                "language": "python",
            },
        ]
    }


def test_preview_example_project_uses_main_build_workspace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    calls: list[dict] = []

    def fake_run_build(project_dir: Path, **kwargs) -> None:
        calls.append(
            {
                "project_dir": project_dir,
                "folio_base_path": os.environ.get("FOLIO_BASE_PATH"),
                **kwargs,
            }
        )

    monkeypatch.setattr("folio_docs.build.run_build", fake_run_build)
    monkeypatch.setenv("FOLIO_BASE_PATH", "/folio")

    build_dir = tmp_path / "build"
    example_dir = tmp_path / "docs" / "examples" / "sample-preview"
    target_dir = build_dir / "public" / "_folio" / "examples" / "sample-preview"
    example_dir.mkdir(parents=True)

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))
    builder._build_preview_example_project(example_dir, target_dir)

    assert calls == [
        {
            "project_dir": example_dir,
            "folio_base_path": "/folio/_folio/examples/sample-preview",
            "serve": False,
            "verbose": False,
            "config_file": "docs.yaml",
            "clean": False,
            "output_override": str(target_dir),
            "include_versions": False,
            "build_dir_override": str(
                build_dir / ".preview-examples" / "sample-preview"
            ),
            "quiet": True,
        }
    ]
    assert os.environ["FOLIO_BASE_PATH"] == "/folio"


def test_preview_example_workspace_reset_preserves_dependency_cache(
    tmp_path: Path,
) -> None:
    example_build_dir = tmp_path / "build" / ".preview-examples" / "sample-preview"
    for directory in [".next", "content", "out", "public"]:
        (example_build_dir / directory).mkdir(parents=True)
        (example_build_dir / directory / "stale.txt").write_text("stale")
    (example_build_dir / ".folio-manifest.json").write_text("{}")
    (example_build_dir / ".folio-build.log").write_text("old log")
    (example_build_dir / ".folio-deps.hash").write_text("deps")
    (example_build_dir / "node_modules").mkdir()

    SiteBuilder._reset_preview_example_workspace(example_build_dir)

    for name in [".next", "content", "out", "public"]:
        assert not (example_build_dir / name).exists()
    assert not (example_build_dir / ".folio-manifest.json").exists()
    assert not (example_build_dir / ".folio-build.log").exists()
    assert (example_build_dir / ".folio-deps.hash").read_text() == "deps"
    assert (example_build_dir / "node_modules").is_dir()


def test_doc_preview_examples_referenced_in_docs_are_folio_projects() -> None:
    repo_root = Path(__file__).parents[1]
    examples_dir = repo_root / "docs" / "examples"
    docs_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (repo_root / "docs" / "guide").rglob("*.md")
    )
    example_names = sorted(set(re.findall(r'example="([^"]+)"', docs_text)))

    # The landing-page example project stays in docs/examples/ for when the
    # landing feature ships, but published guides only embed enabled surfaces.
    assert example_names == ["generated-site"]
    for example_name in example_names:
        example_dir = examples_dir / example_name
        assert (example_dir / "docs.yaml").is_file()

        source_files = [
            path.relative_to(example_dir).as_posix()
            for path in SiteBuilder._preview_example_source_paths(example_dir)
        ]
        assert "docs.yaml" in source_files
        assert "preview.html" not in source_files


def test_bundled_generated_site_preview_combines_step_two_pages() -> None:
    example_dir = Path(__file__).parents[1] / "docs" / "examples" / "generated-site"
    source_paths = SiteBuilder._preview_example_source_paths(example_dir)
    files = sorted(path.relative_to(example_dir).as_posix() for path in source_paths)
    source_text = "\n".join(path.read_text(encoding="utf-8") for path in source_paths)

    assert "TinyMath" not in source_text
    assert "tinymath" not in source_text
    assert "Example docs" in source_text
    assert "Compiled example" not in source_text
    assert "Guide" in source_text
    assert "CLI" in source_text
    assert "API reference" in source_text
    assert "Components" in source_text
    assert load_config(example_dir / "docs.yaml").landing_enabled is False
    assert load_config(example_dir / "docs.yaml").landing_comparison is False
    assert files == [
        "docs.yaml",
        "docs/cli.md",
        "docs/components.md",
        "docs/index.md",
        "src/example_package/__init__.py",
        "src/example_package/arithmetic.py",
    ]


def test_site_builder_write_page_markdown_strips_mdx_shell(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    content_dir = build_dir / "content"
    content_dir.mkdir(parents=True)

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.write_page(
        "guide",
        "---\ntitle: Guide\n---\n"
        'import { Callout } from "@/components/callout"\n\n'
        "# Guide\n\n"
        '<Callout type="info">\n'
        "Use this content.\n"
        "</Callout>\n\n"
        "<ParamTable args={[]} />\n",
    )

    markdown = (build_dir / "public" / "_folio" / "markdown" / "guide.md").read_text()

    assert "title: Guide" not in markdown
    assert "import {" not in markdown
    assert "<Callout" not in markdown
    assert "# Guide" in markdown
    assert "Use this content." in markdown


def test_mdx_to_markdown_keeps_real_guide_index_useful() -> None:
    from folio_docs.docs.mdx_writer import _convert_mermaid_blocks

    guide = Path(__file__).parents[1] / "docs" / "guide" / "index.md"
    compiled_mdx = _convert_mermaid_blocks(guide.read_text(encoding="utf-8"))

    markdown = SiteBuilder._mdx_to_markdown(compiled_mdx)

    assert "```mermaid\nflowchart LR" in markdown
    assert 'Parse --> IRNode["◇ IR objects"]' in markdown
    assert "`} />" not in markdown
    assert "<Mermaid" not in markdown
    assert "- **[Automatic API reference](/docs/docstrings)**:" in markdown
    assert "Point Folio at your source directories" in markdown
    assert "<FeatureCard" not in markdown


@pytest.mark.parametrize(
    "content, kept",
    [
        # Indented under a list item: the fence protector anchored at column 0,
        # so the JSX-looking content inside was handed to the component
        # stripper and deleted.
        (
            "1. Render it:\n\n   ```html\n   <Page title=\"x\">body</Page>\n   ```\n",
            '<Page title="x">body</Page>',
        ),
        # Indented under a blockquote.
        (
            "> Example:\n>\n> ```html\n> <Card>text</Card>\n> ```\n",
            "<Card>text</Card>",
        ),
        # A nested fence must not close the outer block early.
        (
            "````markdown\n```html\n<Note>hi</Note>\n```\n````\n",
            "<Note>hi</Note>",
        ),
    ],
)
def test_mdx_to_markdown_protects_indented_and_nested_fences(
    content: str, kept: str
) -> None:
    markdown = SiteBuilder._mdx_to_markdown(content)

    assert kept in markdown


def test_mdx_to_markdown_keeps_real_why_folio_children_and_code() -> None:
    guide = Path(__file__).parents[1] / "docs" / "guide" / "why-folio.md"

    markdown = SiteBuilder._mdx_to_markdown(guide.read_text(encoding="utf-8"))

    assert "Documentation rots because it lives apart from the code." in markdown
    assert "### Why Folio instead of Sphinx or MkDocs Material?" in markdown
    assert "Same job — parse Python source into reference docs" in markdown
    assert "`<Callout>`" in markdown
    assert "`<Swot>`" in markdown
    assert "stats={[" not in markdown
    assert "strengths={[" not in markdown


def test_site_builder_write_meta(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    content_dir = build_dir / "content"
    content_dir.mkdir(parents=True)

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.write_meta("", '{"introduction": "Introduction"}')
    assert (content_dir / "_meta.ts").exists()

    builder.write_meta("api-reference", '{"module": "module"}')
    assert (content_dir / "api-reference" / "_meta.ts").exists()


def test_warm_generation_removes_meta_for_a_moved_docs_directory(
    tmp_path: Path,
) -> None:
    docs_dir = tmp_path / "docs" / "kanban"
    docs_dir.mkdir(parents=True)
    source_file = docs_dir / "index.md"
    source_file.write_text("# Kanban\n", encoding="utf-8")

    build_dir = tmp_path / "build"
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    config_path = tmp_path / "docs.yaml"
    config_path.write_text('project:\n  name: "TestProject"\n', encoding="utf-8")

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.write_meta(
        "plugins/kanban",
        'export default { "index": { "display": "hidden" } }',
    )
    stale_asset = build_dir / "content" / "plugins" / "kanban" / "card.png"
    stale_asset.write_bytes(b"image")

    _generate_content_pages(
        builder=builder,
        config=config,
        modules=[],
        docs=[
            MarkdownResult(
                content="# Kanban\n",
                frontmatter={"title": "Kanban"},
                route="kanban/index",
                source_file=str(source_file),
            )
        ],
        project_dir=tmp_path,
        build_context=_build_manifest_context(config_path, template_dir, "main"),
        clean=False,
        verbose=False,
    )

    assert not (build_dir / "content" / "plugins" / "kanban" / "_meta.ts").exists()
    assert stale_asset.exists()
    assert (build_dir / "content" / "kanban" / "_meta.ts").exists()


def test_site_builder_write_llm_files(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    build_dir.mkdir(parents=True)

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.write_llm_files("# Test\n", "Full content")

    output_dir = Path(config.output_dir)
    assert (output_dir / "llms.txt").exists()
    assert (output_dir / "llms-full.txt").exists()

    builder.write_llm_files("# Test\n", None)

    assert (output_dir / "llms.txt").exists()
    assert not (output_dir / "llms-full.txt").exists()


def test_write_llm_files_points_robots_at_the_llm_files_it_wrote(
    tmp_path: Path,
) -> None:
    """robots.txt is the file agents fetch first; llms.txt must be named in it.

    The Next robots route runs before the llm files exist and its serializer
    only emits User-Agent/Allow/Disallow/Sitemap lines, so the pointer is
    appended here — as comments, and only for files this build wrote.
    """
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "robots.txt").write_text(
        "User-Agent: *\nAllow: /\n\nSitemap: https://example.com/base/sitemap.xml\n",
        encoding="utf-8",
    )
    config = Config(
        project_name="MyLib",
        output_dir=str(output_dir),
        site_url="https://example.com/base",
    )
    builder = SiteBuilder(config, str(tmp_path / "template"), str(tmp_path / "build"))

    builder.write_llm_files("# MyLib\n", "# MyLib full\n")

    robots = (output_dir / "robots.txt").read_text(encoding="utf-8")
    assert robots.startswith("User-Agent: *\nAllow: /\n")
    assert "Sitemap: https://example.com/base/sitemap.xml\n" in robots
    assert "# llms.txt: https://example.com/base/llms.txt\n" in robots
    assert "# llms-full.txt: https://example.com/base/llms-full.txt\n" in robots

    builder.write_llm_files("# MyLib\n", "# MyLib full\n")

    robots = (output_dir / "robots.txt").read_text(encoding="utf-8")
    assert robots.count("# llms.txt:") == 1
    assert robots.count("# llms-full.txt:") == 1


def test_write_llm_files_robots_pointer_falls_back_to_base_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "robots.txt").write_text(
        "User-Agent: *\nAllow: /\n", encoding="utf-8"
    )
    monkeypatch.setenv("FOLIO_BASE_PATH", "/mylib")
    config = Config(project_name="MyLib", output_dir=str(output_dir))
    builder = SiteBuilder(config, str(tmp_path / "template"), str(tmp_path / "build"))

    builder.write_llm_files("# MyLib\n", None)

    robots = (output_dir / "robots.txt").read_text(encoding="utf-8")
    assert "# llms.txt: /mylib/llms.txt\n" in robots
    assert "llms-full.txt" not in robots


def test_write_llm_files_without_robots_file_writes_no_pointer(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    config = Config(project_name="MyLib", output_dir=str(output_dir))
    builder = SiteBuilder(config, str(tmp_path / "template"), str(tmp_path / "build"))

    builder.write_llm_files("# MyLib\n", None)

    assert (output_dir / "llms.txt").exists()
    assert not (output_dir / "robots.txt").exists()


def test_site_builder_serve_forwards_kill_existing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    calls = []
    fake_proc = object()

    class FakeRuntime:
        def serve(self, port: int, *, kill_existing: bool = False):
            calls.append((port, kill_existing))
            return fake_proc

    monkeypatch.setattr(builder, "_runtime", lambda: FakeRuntime())

    assert builder.serve(5678, kill_existing=True) is fake_proc
    assert calls == [(5678, True)]


def test_incremental_prepare_preserves_node_modules(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    builder.prepare()
    assert build_dir.exists()

    (build_dir / "node_modules").mkdir()
    (build_dir / "node_modules" / "some-pkg").mkdir()
    (build_dir / "node_modules" / "some-pkg" / "index.js").write_text(
        "module.exports = {}"
    )
    (build_dir / ".next").mkdir()
    (build_dir / ".next" / "cache").mkdir()
    (build_dir / ".next" / "cache" / "data.json").write_text("{}")

    content_dir = build_dir / "content"
    content_dir.mkdir(exist_ok=True)
    (content_dir / "test.mdx").write_text("old content")

    builder.prepare()

    assert (build_dir / "node_modules" / "some-pkg" / "index.js").exists()
    assert (build_dir / ".next" / "cache" / "data.json").exists()
    assert (content_dir / "test.mdx").exists()
    assert content_dir.exists()


def test_install_deps_repairs_incomplete_node_modules(
    tmp_path: Path, monkeypatch
) -> None:
    from folio_docs.docs.next_runtime import NextRuntime

    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    build_dir.mkdir()
    (template_dir / "pnpm-lock.yaml").write_text("lock")
    (build_dir / "pnpm-lock.yaml").write_text("lock")
    (build_dir / "node_modules").mkdir()

    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    monkeypatch.setattr(NextRuntime, "_check_dependencies", lambda self: None)

    calls = []

    def fake_run(*args, **kwargs):
        assert not (build_dir / "node_modules").exists()
        calls.append((args, kwargs))

    monkeypatch.setattr("folio_docs.docs.next_runtime.subprocess.run", fake_run)

    assert builder.install_deps() is True
    assert calls


def test_install_deps_repairs_broken_next_runtime(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio_docs.docs.next_runtime import NextRuntime

    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    next_bin = build_dir / "node_modules" / ".bin" / "next"
    next_bin.parent.mkdir(parents=True)
    next_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    build_dir.mkdir(exist_ok=True)
    (template_dir / "pnpm-lock.yaml").write_text("lock", encoding="utf-8")
    (build_dir / "pnpm-lock.yaml").write_text("lock", encoding="utf-8")

    monkeypatch.setattr(NextRuntime, "_check_dependencies", lambda self: None)
    calls = []

    def fake_run(args, **kwargs):
        calls.append(args)
        if args == ["pnpm", "exec", "next", "--version"]:
            return subprocess.CompletedProcess(args, 1, stderr="missing @next/env")
        assert args == ["pnpm", "install", "--frozen-lockfile"]
        assert not (build_dir / "node_modules").exists()
        return subprocess.CompletedProcess(args, 0)

    monkeypatch.setattr("folio_docs.docs.next_runtime.subprocess.run", fake_run)

    runtime = NextRuntime(template_dir, build_dir, tmp_path / "output")

    assert runtime.install_deps() is True
    assert calls == [
        ["pnpm", "exec", "next", "--version"],
        ["pnpm", "install", "--frozen-lockfile"],
    ]


def test_dev_server_removes_stale_static_export_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio_docs.docs.next_runtime import NextRuntime

    template_dir = tmp_path / "template"
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "output"
    stale_out = build_dir / "out"
    stale_dev = build_dir / ".next" / "dev"
    stale_out.mkdir(parents=True)
    stale_dev.mkdir(parents=True)
    (stale_out / "index.html").write_text(
        '<script>self.__next_f.push([1,"has-data-[icon=inline-start]"])</script>',
        encoding="utf-8",
    )
    (stale_dev / "page-data.json").write_text("", encoding="utf-8")
    calls = []
    fake_proc = object()

    monkeypatch.setattr(NextRuntime, "is_port_in_use", staticmethod(lambda port: False))
    monkeypatch.setattr(
        NextRuntime,
        "kill_port",
        staticmethod(lambda port: (_ for _ in ()).throw(AssertionError(port))),
    )

    def fake_popen(args, cwd):
        assert not stale_out.exists()
        assert not stale_dev.exists()
        calls.append((args, cwd))
        return fake_proc

    monkeypatch.setattr("folio_docs.docs.next_runtime.subprocess.Popen", fake_popen)

    runtime = NextRuntime(template_dir, build_dir, output_dir)

    assert runtime.serve(4321) is fake_proc
    assert calls == [
        (
            ["pnpm", "exec", "next", "dev", "--turbopack", "--port", "4321"],
            build_dir,
        )
    ]


def test_dev_server_refuses_occupied_port_without_opt_in(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio_docs.docs.next_runtime import NextRuntime

    template_dir = tmp_path / "template"
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "output"

    monkeypatch.setattr(NextRuntime, "is_port_in_use", staticmethod(lambda port: True))
    monkeypatch.setattr(
        NextRuntime,
        "kill_port",
        staticmethod(lambda port: (_ for _ in ()).throw(AssertionError(port))),
    )

    runtime = NextRuntime(template_dir, build_dir, output_dir)

    with pytest.raises(RuntimeError, match="Port 4321 is already in use"):
        runtime.serve(4321)


def test_dev_server_kills_occupied_port_only_when_requested(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio_docs.docs.next_runtime import NextRuntime

    template_dir = tmp_path / "template"
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "output"
    calls = []
    fake_proc = object()

    monkeypatch.setattr(NextRuntime, "is_port_in_use", staticmethod(lambda port: True))
    monkeypatch.setattr(
        NextRuntime,
        "kill_port",
        staticmethod(lambda port: calls.append(("kill", port))),
    )

    def fake_popen(args, cwd):
        calls.append(("popen", args, cwd))
        return fake_proc

    monkeypatch.setattr("folio_docs.docs.next_runtime.subprocess.Popen", fake_popen)

    runtime = NextRuntime(template_dir, build_dir, output_dir)

    assert runtime.serve(4321, kill_existing=True) is fake_proc
    assert calls == [
        ("kill", 4321),
        (
            "popen",
            ["pnpm", "exec", "next", "dev", "--turbopack", "--port", "4321"],
            build_dir,
        ),
    ]


def test_next_runtime_patches_nextra_loader_to_skip_generated_git_timestamps(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio_docs.docs.next_runtime import NextRuntime

    template_dir = tmp_path / "template"
    build_dir = tmp_path / "build"
    loader_path = (
        build_dir / "node_modules" / "nextra" / "dist" / "server" / "loader.js"
    )
    loader_path.parent.mkdir(parents=True)
    loader_path.write_text(
        "const lastCommitTime = IS_PRODUCTION ? await getLastCommitTime(resourcePath) : NOW;\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(NextRuntime, "_check_dependencies", lambda self: None)
    monkeypatch.setattr(NextRuntime, "_has_working_next", lambda self: True)

    runtime = NextRuntime(template_dir, build_dir, tmp_path / "output")
    runtime.install_deps()

    content = loader_path.read_text(encoding="utf-8")
    assert "resourcePath.includes(`${CWD}/content/`)" in content
    assert "getLastCommitTime(resourcePath)" in content


def test_next_runtime_build_writes_log_and_reports_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio_docs.docs.next_runtime import NextRuntime

    template_dir = tmp_path / "template"
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "output"
    build_dir.mkdir()
    log_path = build_dir / ".folio-build.log"
    reported_lines: list[str] = []
    popen_calls = []

    class FakeProcess:
        returncode = 0

        def __init__(self) -> None:
            self.stdout = iter(
                [
                    "> folio@0.0.1 build\n",
                    "Creating an optimized production build ...\n",
                    "Compiled successfully\n",
                ]
            )

        def wait(self) -> int:
            return self.returncode

    def fake_popen(*args, **kwargs):
        popen_calls.append((args, kwargs))
        return FakeProcess()

    monkeypatch.setattr("folio_docs.docs.next_runtime.subprocess.Popen", fake_popen)
    monkeypatch.setattr(NextRuntime, "copy_static_output", lambda self: None)

    runtime = NextRuntime(template_dir, build_dir, output_dir)
    runtime.build(log_path=log_path, output_callback=reported_lines.append)

    assert log_path.read_text(encoding="utf-8") == (
        "> folio@0.0.1 build\n"
        "Creating an optimized production build ...\n"
        "Compiled successfully\n"
    )
    assert reported_lines == [
        "> folio@0.0.1 build\n",
        "Creating an optimized production build ...\n",
        "Compiled successfully\n",
    ]
    assert popen_calls
    assert popen_calls[0][0] == (["pnpm", "run", "build"],)
    assert popen_calls[0][1]["cwd"] == build_dir
    assert popen_calls[0][1]["stderr"] is subprocess.STDOUT
    assert popen_calls[0][1]["stdout"] is subprocess.PIPE
    assert popen_calls[0][1]["stdin"] is subprocess.DEVNULL


def test_next_runtime_build_removes_stale_export_and_dev_artifacts(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio_docs.docs.next_runtime import NextRuntime

    template_dir = tmp_path / "template"
    build_dir = tmp_path / "build"
    output_dir = tmp_path / "output"
    stale_out = build_dir / "out"
    stale_dev = build_dir / ".next" / "dev"
    stale_out.mkdir(parents=True)
    stale_dev.mkdir(parents=True)
    (stale_out / "index.html").write_text(
        '<script>self.__next_f.push([1,"has-data-[icon=inline-start]"])</script>',
        encoding="utf-8",
    )
    (stale_dev / "app.css").write_text(
        ".has-data-\\[icon\\=inline-start\\]\\:pl-1\\.5 {}",
        encoding="utf-8",
    )

    class FakeProcess:
        returncode = 0
        stdout = iter(["Compiled successfully\n"])

        def wait(self) -> int:
            return self.returncode

    def fake_popen(*args, **kwargs):
        assert not stale_out.exists()
        assert not stale_dev.exists()
        return FakeProcess()

    monkeypatch.setattr("folio_docs.docs.next_runtime.subprocess.Popen", fake_popen)
    monkeypatch.setattr(NextRuntime, "copy_static_output", lambda self: None)

    runtime = NextRuntime(template_dir, build_dir, output_dir)
    runtime.build()


def test_clean_prepare_destroys_build(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    builder.prepare()
    (build_dir / "node_modules").mkdir()
    (build_dir / ".next").mkdir()

    builder.prepare(clean=True)

    assert build_dir.exists()
    assert not (build_dir / "node_modules").exists()
    assert not (build_dir / ".next").exists()


def test_static_export_uses_directory_index_routes() -> None:
    config_path = Path(__file__).resolve().parents[1] / "template" / "next.config.mjs"
    content = config_path.read_text(encoding="utf-8")

    assert "output: 'export'" in content
    assert "trailingSlash: true" in content


def test_fix_asset_paths_rewrites_directory_routes_for_file_urls(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    (output_dir / "docs" / "installation").mkdir(parents=True)
    (output_dir / "docs" / "components").mkdir(parents=True)
    (output_dir / "docs" / "api-reference" / "folio").mkdir(parents=True)
    (output_dir / "_next" / "static" / "chunks").mkdir(parents=True)
    (output_dir / "media").mkdir(parents=True)

    (output_dir / "index.html").write_text("<h1>Home</h1>")
    (output_dir / "docs" / "installation" / "index.html").write_text("<h1>Install</h1>")
    (output_dir / "docs" / "components" / "index.html").write_text(
        "<h1>Components</h1>"
    )
    (output_dir / "docs" / "api-reference" / "folio" / "index.html").write_text(
        "<h1>API</h1>"
    )
    (output_dir / "icon.svg").write_text("<svg />")
    (output_dir / "_next" / "static" / "chunks" / "app.js").write_text(
        "console.log('ok')"
    )
    (output_dir / "media" / "folio-commercial-v2-poster.jpeg").write_text("poster")
    (output_dir / "media" / "folio-commercial-v2.mp4").write_text("video")
    (output_dir / "docs" / "index.html").write_text(
        '<a href="/">Home</a>'
        '<a href="/docs/">Docs</a>'
        '<a href="/docs/installation/">Install</a>'
        '<a href="/docs/components">Components</a>'
        '<a href="/docs/api-reference/folio#config">API</a>'
        '<a href="./installation/">Install relative</a>'
        '<button data-href="/docs/components">Components tree</button>'
        '<button data-href="/docs/components/index.html?panel=open#top">'
        "Components index</button>"
        '<a href="#local">Local anchor</a>'
        '<a href="https://example.com/docs/">External</a>'
        '<link rel="icon" href="/icon.svg?icon.hash.svg">'
        '<script src="/_next/static/chunks/app.js"></script>'
        '<video poster="/media/folio-commercial-v2-poster.jpeg">'
        '<source src="/media/folio-commercial-v2.mp4" type="video/mp4">'
        "</video>"
        '<script>self.__next_f.push([1,"I[1,[\\"/_next/static/chunks/app.js\\"],\\"Comp\\"]"])</script>'
        '<script>self.__next_f.push([1,"{\\"poster\\":\\"/media/folio-commercial-v2-poster.jpeg\\",'
        '\\"src\\":\\"/media/folio-commercial-v2.mp4\\"}"])</script>'
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (output_dir / "docs" / "index.html").read_text()
    assert 'href="../index.html"' in content
    assert 'href="index.html"' in content
    assert 'href="installation/index.html"' in content
    assert 'href="components/index.html"' in content
    assert 'href="api-reference/folio/index.html#config"' in content
    assert 'data-href="components/"' in content
    assert 'data-href="components/?panel=open#top"' in content
    assert 'data-href="components/index.html"' not in content
    assert 'href="#local"' in content
    assert 'href="https://example.com/docs/"' in content
    assert 'href="../icon.svg?icon.hash.svg"' in content
    assert 'src="../_next/static/chunks/app.js"' in content
    assert 'poster="../media/folio-commercial-v2-poster.jpeg"' in content
    assert 'src="../media/folio-commercial-v2.mp4"' in content
    assert '\\"/_next/static/chunks/app.js\\"' in content
    assert '\\"poster\\":\\"/media/folio-commercial-v2-poster.jpeg\\"' in content
    assert '\\"src\\":\\"/media/folio-commercial-v2.mp4\\"' in content


def test_fix_asset_paths_rewrites_root_relative_route_links(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    (output_dir / "docs").mkdir(parents=True)
    (output_dir / "docs" / "index.html").write_text("<h1>Docs</h1>")
    (output_dir / "index.html").write_text(
        '<a href="./">Home</a>'
        '<a href="./docs/">Docs</a>'
        '<a href="./docs">Docs no slash</a>'
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (output_dir / "index.html").read_text()
    assert 'href="index.html"' in content
    assert 'href="docs/index.html"' in content


def test_fix_asset_paths_rewrites_leaf_page_links_against_source_directory(
    tmp_path: Path,
) -> None:
    """A source page that publishes one level deeper than its own directory
    (docs/guide/kanban/agents.md at /docs/kanban/agents/)
    writes sibling links relative to its SOURCE directory. The link checker
    resolves them the same way and passes them, so the build stays green
    while the browser 404s unless the rewriter also falls back to the parent
    directory."""
    output_dir = tmp_path / "output"
    (output_dir / "docs" / "a" / "b").mkdir(parents=True)
    (output_dir / "docs" / "a" / "c").mkdir(parents=True)
    (output_dir / "docs" / "a" / "c" / "index.html").write_text("<h1>C</h1>")
    (output_dir / "docs" / "a" / "b" / "index.html").write_text(
        '<a href="./c#frag">Dot form</a>'
        '<a href="c#frag">Bare form</a>'
        '<button data-href="./c#frag">Tree</button>'
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (output_dir / "docs" / "a" / "b" / "index.html").read_text()
    assert content.count('href="../c/index.html#frag"') == 2
    assert 'data-href="../c/#frag"' in content


def test_fix_asset_paths_rewrites_leaf_page_parent_links_against_source_directory(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    (output_dir / "docs" / "a" / "b").mkdir(parents=True)
    (output_dir / "docs" / "x").mkdir(parents=True)
    (output_dir / "docs" / "x" / "index.html").write_text("<h1>X</h1>")
    (output_dir / "docs" / "a" / "b" / "index.html").write_text(
        '<a href="../x#frag">Up one</a>'
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (output_dir / "docs" / "a" / "b" / "index.html").read_text()
    assert 'href="../../x/index.html#frag"' in content


def test_fix_asset_paths_prefers_output_relative_resolution_on_index_pages(
    tmp_path: Path,
) -> None:
    """The parent-directory fallback never gets a say when the link already
    resolves against the page's own output directory, even where both levels
    hold a page of that name."""
    output_dir = tmp_path / "output"
    (output_dir / "docs" / "a" / "b").mkdir(parents=True)
    (output_dir / "docs" / "b").mkdir(parents=True)
    (output_dir / "docs" / "a" / "b" / "index.html").write_text("<h1>B</h1>")
    (output_dir / "docs" / "b" / "index.html").write_text("<h1>Decoy</h1>")
    (output_dir / "docs" / "a" / "index.html").write_text('<a href="b">B</a>')

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (output_dir / "docs" / "a" / "index.html").read_text()
    assert 'href="b/index.html"' in content


def test_fix_asset_paths_leaves_unresolvable_leaf_page_links_unchanged(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    (output_dir / "docs" / "a" / "b").mkdir(parents=True)
    (output_dir / "docs" / "a" / "b" / "index.html").write_text(
        '<a href="./nowhere#frag">Nowhere</a>'
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (output_dir / "docs" / "a" / "b" / "index.html").read_text()
    assert 'href="./nowhere#frag"' in content


def test_fix_asset_paths_rewrites_opengraph_images_to_png(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    docs_dir = output_dir / "docs"
    page_dir = docs_dir / "quickstart"
    page_dir.mkdir(parents=True)
    og_image = docs_dir / "opengraph-image"
    og_image.write_bytes(b"png")
    (page_dir / "index.html").write_text(
        '<meta property="og:image" '
        'content="https://example.com/docs/opengraph-image?abc123">'
        '<meta name="twitter:image" content="/docs/opengraph-image?abc123">'
        '<meta name="twitter:image" content="https://example.com/opengraph-image">'
        '<script>self.__next_f.push(["https://example.com/opengraph-image\\"])'
        "</script>",
        encoding="utf-8",
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    assert (docs_dir / "opengraph-image.png").read_bytes() == b"png"
    content = (page_dir / "index.html").read_text(encoding="utf-8")
    assert "https://example.com/docs/opengraph-image.png?abc123" in content
    assert 'content="/docs/opengraph-image.png?abc123"' in content
    assert "https://example.com/opengraph-image.png" in content
    assert "https://example.com/opengraph-image.png\\" in content
    assert "opengraph-image?abc123" not in content


def test_fix_asset_paths_preserves_next_static_chunks(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    chunk_dir = output_dir / "_next" / "static" / "chunks"
    pagefind_dir = output_dir / "_pagefind"
    chunk_dir.mkdir(parents=True)
    pagefind_dir.mkdir(parents=True)
    (pagefind_dir / "pagefind.js").write_text("export {}", encoding="utf-8")
    chunk = (
        'let t="/";'
        'async function load(){window.pagefind=await import(addBasePath("/_pagefind/pagefind.js"))}'
        'const image={path:"/_next/image"};'
    )
    (chunk_dir / "search.js").write_text(
        chunk,
        encoding="utf-8",
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (chunk_dir / "search.js").read_text(encoding="utf-8")
    assert content == chunk


def test_fix_asset_paths_makes_turbopack_runtime_prefix_portable(
    tmp_path: Path,
) -> None:
    """The prefix IIFE must read the script src ATTRIBUTE (relative, matching
    what this rewriter writes into every script tag) - resolving to the
    absolute .src property breaks the runtime's loaded-chunk matching and
    stalls hydration with no console error. The chunk-path function's minified
    NAME drifts between Turbopack releases (N, then q), so the patch must
    match by body shape, not name."""
    output_dir = tmp_path / "output"
    chunk_dir = output_dir / "_next" / "static" / "chunks"
    chunk_dir.mkdir(parents=True)
    runtime = (
        "(globalThis.TURBOPACK=[]).push([]),(()=>{"
        'let e;let t="/_next/",r=function(){'
        'let e=document?.currentScript?.getAttribute?.("src")??"";'
        'let t=e.indexOf("?");return t>=0?e.slice(t):""}();'
        'function F(e){if(e)return{src:e.getAttribute("src")}}'
        'function q(e){return`${t}${e.split("/").map(e=>encodeURIComponent(e)).join("/")}${r}`}'
        "})();"
    )
    (chunk_dir / "turbopack-runtime.js").write_text(runtime, encoding="utf-8")

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (chunk_dir / "turbopack-runtime.js").read_text(encoding="utf-8")
    assert 'let t="/_next/",' not in content
    assert 'document.currentScript.getAttribute("src")' in content
    assert 'return t?t[1]:"/_next/"' in content
    # The runtime's own attribute-based script matching must be preserved.
    assert 'return{src:e.getAttribute("src")}' in content
    assert "currentScript.src" not in content.replace(
        'document.currentScript.getAttribute("src")', ""
    )
    # Chunk-path function patched by shape with its minified name preserved.
    assert 'function q(e){let _fp=e.indexOf("/_next/")' in content


def test_fix_asset_paths_root_page_next_srcs_match_runtime_prefix_regex(
    tmp_path: Path,
) -> None:
    """Regression: pages at output-dir depth 0 (the landing "/") get bare
    "_next/..." srcs from os.path.relpath, which the injected runtime
    prefix regex used to reject (it required a "/" before "_next"). The
    runtime then fell back to prefix "/_next/", never matched the raw src
    attributes of the already-loaded chunks, and waited forever - the
    landing silently never hydrated while deeper pages ("../_next/...")
    worked. Both sides are pinned here: the rewriter emits an explicit
    "./" at depth 0, and the injected regex accepts every emitted form."""
    output_dir = tmp_path / "output"
    chunk_dir = output_dir / "_next" / "static" / "chunks"
    chunk_dir.mkdir(parents=True)
    (output_dir / "docs").mkdir()
    (chunk_dir / "app.js").write_text("console.log('ok')", encoding="utf-8")
    runtime = '(()=>{let t="/_next/",r="";function N(e){return`${t}${e}${r}`}})();'
    (chunk_dir / "turbopack-runtime.js").write_text(runtime, encoding="utf-8")
    (output_dir / "index.html").write_text(
        '<script src="/_next/static/chunks/app.js"></script>', encoding="utf-8"
    )
    (output_dir / "docs" / "index.html").write_text(
        '<script src="/_next/static/chunks/app.js"></script>', encoding="utf-8"
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    root_html = (output_dir / "index.html").read_text(encoding="utf-8")
    docs_html = (output_dir / "docs" / "index.html").read_text(encoding="utf-8")
    assert 'src="./_next/static/chunks/app.js"' in root_html
    assert 'src="../_next/static/chunks/app.js"' in docs_html

    runtime_js = (chunk_dir / "turbopack-runtime.js").read_text(encoding="utf-8")
    injected_js_regex = "e.match(/^((?:.*\\/)?_next\\/)static\\/chunks\\//)"
    assert injected_js_regex in runtime_js
    # Python mirror of the injected JS regex (identical semantics here): the
    # prefix detection must accept every src form this rewriter can emit,
    # including the pre-fix bare depth-0 form, and Next's original absolute
    # form (untouched HTML).
    prefix_re = re.compile(r"^((?:.*/)?_next/)static/chunks/")
    for src, expected_prefix in [
        ("./_next/static/chunks/app.js", "./_next/"),
        ("../_next/static/chunks/app.js", "../_next/"),
        ("../../_next/static/chunks/app.js", "../../_next/"),
        ("_next/static/chunks/app.js", "_next/"),
        ("/_next/static/chunks/app.js", "/_next/"),
    ]:
        match = prefix_re.match(src)
        assert match is not None, src
        assert match.group(1) == expected_prefix, src


def test_fix_asset_paths_patches_simple_chunk_path_function(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    chunk_dir = output_dir / "_next" / "static" / "chunks"
    chunk_dir.mkdir(parents=True)
    runtime = '(()=>{let t="/_next/",r="";function N(e){return`${t}${e}${r}`}})();'
    (chunk_dir / "turbopack-runtime.js").write_text(runtime, encoding="utf-8")

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (chunk_dir / "turbopack-runtime.js").read_text(encoding="utf-8")
    assert 'function N(e){let _fp=e.indexOf("/_next/")' in content


def test_fix_asset_paths_patches_next_16_3_chunk_path_function(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    chunk_dir = output_dir / "_next" / "static" / "chunks"
    chunk_dir.mkdir(parents=True)
    runtime = (
        '(()=>{let P="string"==typeof TURBOPACK_CHUNK_BASE_PATH?'
        'TURBOPACK_CHUNK_BASE_PATH:"/_next/",r="";'
        "let K=/[^A-Za-z0-9]/;"
        'function q(e,t=P){let n=K.test(e)?e.split("/")'
        '.map(encodeURIComponent).join("/"):e;return`${t}${n}${r}`}})();'
    )
    (chunk_dir / "turbopack-runtime.js").write_text(runtime, encoding="utf-8")

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (chunk_dir / "turbopack-runtime.js").read_text(encoding="utf-8")
    assert 'function q(e,t=P){let _fp=e.indexOf("/_next/")' in content
    assert "_fp>=0&&(e=e.slice(_fp+7));let n=K.test(e)?" in content
    assert '.map(encodeURIComponent).join("/"):e;return`${t}${n}${r}`' in content


def test_fix_asset_paths_warns_when_turbopack_runtime_shape_drifts(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    chunk_dir = output_dir / "_next" / "static" / "chunks"
    chunk_dir.mkdir(parents=True)
    runtime = '(()=>{let t="/_next/";loadChunkUnrecognizedShape(t)})();'
    (chunk_dir / "turbopack-runtime.js").write_text(runtime, encoding="utf-8")

    with pytest.warns(UserWarning, match="chunk-path function not found"):
        StaticAssetRewriter(output_dir).fix_asset_paths()


def test_fix_asset_paths_adds_file_search_fallback(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    fragment_dir = output_dir / "_pagefind" / "fragment"
    docs_dir = output_dir / "docs"
    fragment_dir.mkdir(parents=True)
    docs_dir.mkdir(parents=True)
    (docs_dir / "index.html").write_text(
        "<html><head></head><body>Docs</body></html>", encoding="utf-8"
    )
    fragment = {
        "url": "/docs/components/",
        "content": "Components Built-in UI components and live previews.",
        "meta": {"title": "Components"},
        "anchors": [],
    }
    (fragment_dir / "en_components.pf_fragment").write_bytes(
        gzip.compress(b"pagefind_dcd" + json.dumps(fragment).encode("utf-8"))
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    html = (docs_dir / "index.html").read_text(encoding="utf-8")
    fallback = (output_dir / "_folio-search.js").read_text(encoding="utf-8")
    assert '<script defer src="../_folio-search.js"></script>' in html
    assert "window.__folioStaticSearch" in fallback
    assert "docs/components/index.html" in fallback


def test_write_search_index_from_generated_content(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()
    builder.write_page(
        "configuration",
        "---\ntitle: Configuration\n---\n\n# Configuration\n\nSearch settings.",
    )
    builder.write_page(
        "api-reference/mylib/core",
        "# mylib.core\n\nCore API reference.",
    )

    builder.write_search_index()

    content = (build_dir / "lib" / "search-index.ts").read_text(encoding="utf-8")
    assert "export const folioSearchDocuments" in content
    assert '"/docs/configuration/"' in content
    assert '"Configuration"' in content
    assert '"/docs/api-reference/mylib/core/"' in content
    assert '"mylib.core"' in content


def test_write_search_index_uses_configured_docs_route_base(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        docs_route_base="/reference/docs",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()
    builder.write_page(
        "configuration",
        "---\ntitle: Configuration\n---\n\n# Configuration\n\nSearch settings.",
    )

    builder.write_search_index()

    content = (build_dir / "lib" / "search-index.ts").read_text(encoding="utf-8")
    assert '"/reference/docs/configuration/"' in content
    assert '"/docs/configuration/"' not in content


def test_remove_page(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    content_dir = build_dir / "content"
    content_dir.mkdir(parents=True)
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.write_page("api-reference/mylib/core", "# mylib.core")
    assert (content_dir / "api-reference" / "mylib" / "core.mdx").exists()

    builder.remove_page("api-reference/mylib/core")
    assert not (content_dir / "api-reference" / "mylib" / "core.mdx").exists()


def test_remove_page_nonexistent(tmp_path: Path) -> None:
    build_dir = tmp_path / "build"
    content_dir = build_dir / "content"
    content_dir.mkdir(parents=True)
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(tmp_path / "template"), str(build_dir))

    builder.remove_page("nonexistent")  # should not raise


def test_inject_og_image(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)

    # Add the OG image template files
    root_og = template_dir / "app" / "opengraph-image.tsx"
    root_og.write_text(
        "export default function OGImage() {\n"
        "  return <div>__PROJECT_NAME__ __PROJECT_MONOGRAM__ "
        "__PROJECT_DESCRIPTION__</div>\n"
        "}\n"
    )
    og_dir = template_dir / "app" / "docs"
    og_dir.mkdir(parents=True, exist_ok=True)
    (og_dir / "opengraph-image.tsx").write_text(
        "export default function OGImage() {\n"
        "  return <div>__PROJECT_NAME__ __PROJECT_MONOGRAM__</div>\n"
        "}\n"
    )

    build_dir = tmp_path / "build"
    config = Config(
        project_name="MyLib",
        output_dir=str(tmp_path / "output"),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    root_og_content = (build_dir / "app" / "opengraph-image.tsx").read_text()
    og_content = (build_dir / "app" / "docs" / "opengraph-image.tsx").read_text()
    for content in (root_og_content, og_content):
        assert "MyLib" in content
        assert "my" in content  # monogram
        assert "__PROJECT_NAME__" not in content
        assert "__PROJECT_MONOGRAM__" not in content
    assert "Documentation for MyLib" in root_og_content
    assert "__PROJECT_DESCRIPTION__" not in root_og_content


def test_default_favicon_uses_project_monogram(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    (template_dir / "app" / "icon.svg").write_text(
        "<svg><text>__PROJECT_MONOGRAM__</text></svg>"
    )

    build_dir = tmp_path / "build"
    config = Config(
        project_name="MyLib",
        output_dir=str(tmp_path / "output"),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    icon_content = (build_dir / "app" / "icon.svg").read_text()
    assert "__PROJECT_MONOGRAM__" not in icon_content
    assert "<text>my</text>" in icon_content


def test_custom_non_svg_favicon_replaces_default_icon(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    (template_dir / "app" / "icon.svg").write_text(
        "<svg><text>__PROJECT_MONOGRAM__</text></svg>"
    )
    favicon_src = tmp_path / "favicon.ico"
    favicon_src.write_bytes(b"icon-bytes")

    build_dir = tmp_path / "build"
    config = Config(
        project_name="MyLib",
        output_dir=str(tmp_path / "output"),
        favicon=str(favicon_src),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    assert (build_dir / "app" / "icon.ico").read_bytes() == b"icon-bytes"
    # The template default must not ship alongside the configured favicon.
    assert not (build_dir / "app" / "icon.svg").exists()


def test_root_metadata_uses_configured_site_url_for_metadata_base(
    tmp_path: Path,
) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="MyLib",
        output_dir=str(tmp_path / "output"),
        site_url="https://example.com/docs",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "layout.tsx").read_text()
    assert 'metadataBase: new URL("https://example.com/docs")' in content
    assert "__SITE_URL__" not in content


def test_docs_route_metadata_uses_configured_site_url(
    tmp_path: Path,
) -> None:
    template_dir = _make_template(tmp_path)
    docs_route_dir = template_dir / "app" / "docs" / "[[...mdxPath]]"
    docs_route_dir.mkdir(parents=True)
    (docs_route_dir / "page.jsx").write_text(
        'const configuredSiteUrl = "__SITE_URL__"\n'
        'const projectName = "__PROJECT_NAME__"\n'
        'const projectDescription = "__PROJECT_DESCRIPTION__"\n',
        encoding="utf-8",
    )
    build_dir = tmp_path / "build"
    config = Config(
        project_name="MyLib",
        output_dir=str(tmp_path / "output"),
        site_url="https://example.com/docs",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "docs" / "[[...mdxPath]]" / "page.jsx").read_text()
    assert 'const configuredSiteUrl = "https://example.com/docs"' in content
    assert 'const projectName = "MyLib"' in content
    assert 'const projectDescription = "Documentation for MyLib"' in content
    assert "__SITE_URL__" not in content
    assert "__PROJECT_NAME__" not in content
    assert "__PROJECT_DESCRIPTION__" not in content


def test_sitemap_and_robots_use_configured_site_url(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    app_dir = template_dir / "app"
    (app_dir / "sitemap.ts").write_text('const SITE_URL = "__SITE_URL__"\n')
    (app_dir / "robots.ts").write_text('const SITE_URL = "__SITE_URL__"\n')
    build_dir = tmp_path / "build"
    config = Config(
        project_name="MyLib",
        output_dir=str(tmp_path / "output"),
        site_url="https://example.com/docs",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    assert (
        'const SITE_URL = "https://example.com/docs"'
        in (build_dir / "app" / "sitemap.ts").read_text()
    )
    assert (
        'const SITE_URL = "https://example.com/docs"'
        in (build_dir / "app" / "robots.ts").read_text()
    )


def test_search_disabled_removes_pagefind_postbuild(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    (template_dir / "package.json").write_text(
        json.dumps(
            {
                "name": "test",
                "scripts": {
                    "build": "next build",
                    "postbuild": "pagefind --site out",
                },
            }
        ),
        encoding="utf-8",
    )
    build_dir = tmp_path / "build"
    config = Config(
        project_name="MyLib",
        output_dir=str(tmp_path / "output"),
        search_enabled=False,
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    package_json = json.loads((build_dir / "package.json").read_text(encoding="utf-8"))
    assert package_json["scripts"] == {"build": "next build"}


def test_inject_i18n_with_locales(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        i18n_default_locale="en",
        i18n_locales=[
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Espanol"},
        ],
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "next.config.mjs").read_text()
    assert "__I18N_CONFIG__" not in content
    assert "i18n:" in content
    assert "'en'" in content
    assert "'es'" in content
    assert "defaultLocale: 'en'" in content


def test_inject_i18n_without_locales(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "next.config.mjs").read_text()
    assert "__I18N_CONFIG__" not in content
    assert "__FOLIO_BASE_PATH__" not in content
    assert 'const configuredBasePath = ""' in content
    assert "i18n:" not in content


def test_inject_theme_config_uses_configured_preset(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    components_dir = template_dir / "components"
    (components_dir / "theme-configurator.tsx").write_text(
        'const configuredDefaultPresetId = "organic-editorial" // __FOLIO_THEME_PRESET__\n'
        "const DEFAULT_CONFIG = { presetId: configuredDefaultPresetId }\n"
    )
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        theme_preset="beacon",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "components" / "theme-configurator.tsx").read_text()
    assert 'const configuredDefaultPresetId = "beacon"' in content
    assert "__FOLIO_THEME_PRESET__" not in content


def test_inject_theme_config_writes_project_theme_contract(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    (template_dir / "theme").mkdir()
    (template_dir / "theme" / "project-theme.ts").write_text(
        "export const projectThemePreset = null\n"
        "export const projectThemeDefaultConfig = {}\n"
    )
    (template_dir / "app" / "docs" / "layout.tsx").write_text(
        'import { VersionSelector } from "@/components/version-selector"\n'
        'import { getPageMap } from "nextra/page-map"\n'
        "// __PROJECT_HEADER_ACTION_IMPORTS_START__\n"
        "// __PROJECT_HEADER_ACTION_IMPORTS_END__\n"
        "logo={\n"
        "  <span>\n"
        "    {/* __PROJECT_HEADER_LOGO_START__ */}\n"
        "    <span>__PROJECT_MONOGRAM__</span>\n"
        "    <span>__PROJECT_NAME__</span>\n"
        "    {/* __PROJECT_HEADER_LOGO_END__ */}\n"
        "  </span>\n"
        "}\n"
        "{/* __PROJECT_HEADER_ACTIONS_START__ */}\n"
        "<VersionSelector />\n"
        "{/* __PROJECT_HEADER_ACTIONS_END__ */}\n"
        'pageMap={await getPageMap("/docs")}\n'
        "footer={<Footer />}\n"
    )
    components_dir = template_dir / "components"
    (components_dir / "theme-configurator.tsx").write_text(
        'const configuredDefaultPresetId = "organic-editorial" // __FOLIO_THEME_PRESET__\n'
        "const DEFAULT_CONFIG = { presetId: configuredDefaultPresetId }\n"
    )
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        theme_preset="p2pfl",
        theme_name="P2PFL",
        theme_description="Operational docs theme",
        theme_scene="Maintainers inspect experiments, nodes, and APIs in one compact surface.",
        theme_preview={
            "light": "oklch(0.490 0.130 285)",
            "dark": "oklch(0.720 0.100 285)",
        },
        theme_radius="0.5rem",
        theme_tune={
            "fontId": "geist",
            "contentWidthId": "wide",
            "rhythmId": "compact",
            "codeTreatmentId": "terminal",
        },
        theme_style={
            "--folio-content-max-width": "74rem",
            "--folio-body-line-height": "1.58",
        },
        theme_header={
            "brand": "p2pfl",
            "badge": "Web Services",
            "repo": "https://github.com/pguijas/p2pfl",
            "theme_toggle": True,
            "action_label": "Dashboard",
            "action_href": "/dashboard",
            "search": False,
        },
        theme_tokens={
            "light": {
                "--background": "oklch(0.985 0.008 80)",
                "--foreground": "oklch(0.175 0.008 75)",
                "--status-running": "oklch(0.680 0.110 160)",
            },
            "dark": {
                "--background": "oklch(0.155 0.010 75)",
                "--foreground": "oklch(0.950 0.008 80)",
            },
        },
        theme_variants={
            "palette": {
                "label": "Palette",
                "description": "",
                "default": "default",
                "options": {
                    "default": {
                        "label": "Default",
                        "description": "",
                        "swatch": "oklch(0.490 0.130 285)",
                        "preview": {},
                        "style": {},
                        "tokens": {},
                    },
                    "midnight": {
                        "label": "Midnight",
                        "description": "",
                        "swatch": "oklch(0.680 0.180 200)",
                        "preview": {},
                        "style": {},
                        "tokens": {
                            "light": {
                                "--background": "oklch(0.985 0.008 250)",
                                "--primary": "oklch(0.480 0.160 200)",
                            },
                            "dark": {
                                "--background": "oklch(0.095 0.020 250)",
                                "--primary": "oklch(0.680 0.180 200)",
                            },
                        },
                    },
                    "ocean": {
                        "label": "Ocean",
                        "description": "",
                        "preview": {
                            "light": "oklch(0.480 0.140 245)",
                        },
                        "style": {},
                        "tokens": {},
                    },
                },
            },
        },
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    project_theme = (build_dir / "theme" / "project-theme.ts").read_text()
    configurator = (build_dir / "components" / "theme-configurator.tsx").read_text()
    docs_layout = (build_dir / "app" / "docs" / "layout.tsx").read_text()

    # Structural assertions against the emitted TS object literals. These parse
    # the JSON blocks that back each ``const`` so the test is robust to cosmetic
    # generator changes (indentation, key ordering, newlines).
    preset = _extract_ts_object(
        project_theme, 'const projectPresetConfig: Omit<ThemePreset, "resolve"> ='
    )
    variant_themes = _extract_ts_object(project_theme, "}>> = ")
    style_overrides = _extract_ts_object(
        project_theme, "const projectStyleOverrides: Record<string, string> = "
    )
    light_overrides = _extract_ts_object(
        project_theme, "const projectLightOverrides: ThemeVars = "
    )
    default_config = _extract_ts_object(project_theme, "} = ")

    # Preset identity and default options.
    assert preset["id"] == "p2pfl"
    assert preset["name"] == "P2PFL"
    assert preset["defaultOptions"] == {"palette": "default"}

    # Palette control and its options (including swatches on relevant options).
    palette_control = next(c for c in preset["controls"] if c["id"] == "palette")
    assert palette_control["label"] == "Palette"
    palette_options = {opt["value"]: opt for opt in palette_control["options"]}
    assert "midnight" in palette_options
    assert palette_options["midnight"]["swatch"] == "oklch(0.680 0.180 200)"
    assert "ocean" in palette_options

    # Variant themes: ocean carries no resolvable theme (single-sided preview,
    # no tokens/style) so it stays empty; midnight derives a preview from its
    # swatch and carries light/dark token overrides.
    palette_variants = variant_themes["palette"]
    assert palette_variants["ocean"] == {}
    assert "preview" not in palette_variants["ocean"]
    midnight_variant = palette_variants["midnight"]
    assert midnight_variant["preview"] == {
        "light": "oklch(0.680 0.180 200)",
        "dark": "oklch(0.680 0.180 200)",
    }
    assert midnight_variant["light"]["--primary"] == "oklch(0.480 0.160 200)"

    # Project-level token and style overrides.
    assert light_overrides["--status-running"] == "oklch(0.680 0.110 160)"
    assert style_overrides["--font-sans"] == "var(--font-geist-sans)"
    assert style_overrides["--font-mono"] == "var(--font-geist-mono)"
    assert style_overrides["--folio-code-font-family"].startswith(
        "var(--font-geist-mono),"
    )
    assert style_overrides["--folio-content-max-width"] == "74rem"

    # Default config module block.
    assert default_config["presetId"] == "p2pfl"
    assert default_config["optionsByPreset"]["p2pfl"] == {"palette": "default"}
    assert default_config["customization"]["fontId"] == "geist"
    assert default_config["customization"]["codeTreatmentId"] == "terminal"

    # Structural scaffolding that is not worth JSON-parsing: keep as substrings.
    assert "export const projectThemePreset: ThemePreset | null =" in project_theme
    assert "projectVariantThemes" in project_theme
    assert 'const projectPresetConfig: Omit<ThemePreset, "resolve"> =' in project_theme
    assert "satisfies Omit<ThemePreset" not in project_theme
    assert (
        "const selectedValue = options[control.id] ?? projectPresetConfig.defaultOptions[control.id]"
        in project_theme
    )
    assert "resolve(options) {" in project_theme
    assert "projectBaseStyle" in project_theme
    assert "projectBaseLight" in project_theme
    assert "projectBaseDark" in project_theme
    assert "projectThemeDefaultConfig" in project_theme
    assert 'const configuredDefaultPresetId = "p2pfl"' in configurator
    assert (
        'import { ProjectHeaderActions } from "@/components/project-header-actions"'
        in docs_layout
    )
    assert "<ProjectHeaderActions" in docs_layout
    assert 'repoHref={"https://github.com/pguijas/p2pfl"}' in docs_layout
    assert "themeToggle" in docs_layout
    assert 'actionHref={"/dashboard"}' in docs_layout
    assert 'actionLabel={"Dashboard"}' in docs_layout
    assert "search={null}" in docs_layout
    assert "p2pfl" in docs_layout
    assert "Web Services" in docs_layout
    assert "__PROJECT_HEADER_LOGO" not in docs_layout
    assert "__PROJECT_HEADER_ACTION" not in docs_layout


def test_customized_builtin_preset_generates_project_theme_with_builtin_id(
    tmp_path: Path,
) -> None:
    """A builtin theme.preset plus safe customizations (tokens/style) must
    generate a project preset that KEEPS the builtin id. Combined with the
    presets.ts registration order (builtins first, project preset last,
    last-wins registry), the customized preset replaces the builtin instead of
    being clobbered by it.
    """
    template_dir = _make_template(tmp_path)
    (template_dir / "theme").mkdir()
    (template_dir / "theme" / "project-theme.ts").write_text(
        "export const projectThemePreset = null\n"
        "export const projectThemeDefaultConfig = {}\n"
    )
    components_dir = template_dir / "components"
    (components_dir / "theme-configurator.tsx").write_text(
        'const configuredDefaultPresetId = "organic-editorial" // __FOLIO_THEME_PRESET__\n'
        "const DEFAULT_CONFIG = { presetId: configuredDefaultPresetId }\n"
    )
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        theme_preset="atlas",
        theme_tokens={
            "light": {"--primary": "oklch(0.51 0.14 170)"},
            "dark": {"--primary": "oklch(0.72 0.17 170)"},
        },
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    project_theme = (build_dir / "theme" / "project-theme.ts").read_text()
    preset = _extract_ts_object(
        project_theme, 'const projectPresetConfig: Omit<ThemePreset, "resolve"> ='
    )
    default_config = _extract_ts_object(project_theme, "} = ")

    # The builtin id is reused, not remapped to a synthetic project id: this
    # is what makes registry last-wins replace the builtin "atlas" with the
    # customized preset (exactly one configurator entry, under Project).
    assert preset["id"] == "atlas"
    assert default_config["presetId"] == "atlas"
    assert "export const projectThemePreset: ThemePreset | null =" in project_theme

    configurator = (build_dir / "components" / "theme-configurator.tsx").read_text()
    assert 'const configuredDefaultPresetId = "atlas"' in configurator


def test_theme_package_overlays_template_owned_theme_files(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    (template_dir / "theme").mkdir()
    (template_dir / "theme" / "project-theme.ts").write_text(
        "export const projectThemePreset = null\n"
        "export const projectThemeDefaultConfig = {}\n"
    )
    (template_dir / "components").mkdir(exist_ok=True)
    (template_dir / "components" / "theme-configurator.tsx").write_text(
        'const configuredDefaultPresetId = "organic-editorial" // __FOLIO_THEME_PRESET__\n'
    )
    (template_dir / "components" / "project-header-actions.tsx").write_text(
        "export function ProjectHeaderActions() { return null }\n"
    )
    (template_dir / "app" / "docs" / "layout.tsx").write_text(
        'import { VersionSelector } from "@/components/version-selector"\n'
        'import { getPageMap } from "nextra/page-map"\n'
        "// __PROJECT_HEADER_ACTION_IMPORTS_START__\n"
        "// __PROJECT_HEADER_ACTION_IMPORTS_END__\n"
        "{/* __PROJECT_HEADER_ACTIONS_START__ */}\n"
        "<VersionSelector />\n"
        "{/* __PROJECT_HEADER_ACTIONS_END__ */}\n"
        'pageMap={await getPageMap("/docs")}\n'
    )
    package_dir = tmp_path / "docs" / "theme" / "p2pfl"
    (package_dir / "theme").mkdir(parents=True)
    (package_dir / "components").mkdir()
    (package_dir / "app").mkdir()
    (package_dir / "theme" / "project-theme.ts").write_text(
        "export const projectThemePreset = { id: 'p2pfl-pack' }\n"
        "export const projectThemeDefaultConfig = { presetId: 'p2pfl-pack' }\n"
    )
    (package_dir / "components" / "theme-configurator.tsx").write_text(
        "export function ThemeConfigurator() { return <div data-p2pfl-theme /> }\n"
    )
    (package_dir / "components" / "project-header-actions.tsx").write_text(
        "export function ProjectHeaderActions() { return <a>Pack action</a> }\n"
    )
    (package_dir / "app" / "layout.tsx").write_text(
        "export default function RootLayout({ children }) { return children }\n"
    )

    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        theme_preset="p2pfl-pack",
        theme_package_path=str(package_dir),
        theme_header={"theme_toggle": True},
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    project_theme = (build_dir / "theme" / "project-theme.ts").read_text()
    configurator = (build_dir / "components" / "theme-configurator.tsx").read_text()
    header_actions = (
        build_dir / "components" / "project-header-actions.tsx"
    ).read_text()
    root_layout = (build_dir / "app" / "layout.tsx").read_text()
    docs_layout = (build_dir / "app" / "docs" / "layout.tsx").read_text()

    assert "p2pfl-pack" in project_theme
    assert "projectBaseStyle" not in project_theme
    assert "data-p2pfl-theme" in configurator
    assert "__FOLIO_THEME_PRESET__" not in configurator
    assert "Pack action" in header_actions
    assert "return children" in root_layout
    assert (
        'import { ProjectHeaderActions } from "@/components/project-header-actions"'
        in docs_layout
    )
    assert "<ProjectHeaderActions" in docs_layout


def test_theme_package_configurator_is_not_clobbered_by_injector(
    tmp_path: Path,
) -> None:
    template_dir = _make_template(tmp_path)
    (template_dir / "components").mkdir(exist_ok=True)
    (template_dir / "components" / "theme-configurator.tsx").write_text(
        'const configuredDefaultPresetId = "organic-editorial" // __FOLIO_THEME_PRESET__\n'
    )

    package_dir = tmp_path / "docs" / "theme" / "custom"
    (package_dir / "components").mkdir(parents=True)
    package_configurator = (
        'const configuredDefaultPresetId = "organic-editorial" // __FOLIO_THEME_PRESET__\n'
        "export function ThemeConfigurator() { return <div data-custom-pack /> }\n"
    )
    (package_dir / "components" / "theme-configurator.tsx").write_text(
        package_configurator
    )

    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        theme_preset="beacon",
        theme_package_path=str(package_dir),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    configurator = (build_dir / "components" / "theme-configurator.tsx").read_text()
    # The package-owned configurator must be preserved verbatim: neither its
    # distinctive content nor its marker may be rewritten by the injector.
    assert configurator == package_configurator
    assert "data-custom-pack" in configurator
    assert "__FOLIO_THEME_PRESET__" in configurator
    assert '"beacon"' not in configurator


def test_theme_package_owned_project_theme_does_not_freeze_generated_contract(
    tmp_path: Path,
) -> None:
    """The generated theme contract is regenerated even when a package owns
    theme/project-theme.ts.

    Skipping the whole theme-module write when the package ships
    project-theme.ts used to also skip theme-contract.generated.ts, freezing
    the contract at whatever version the template bundled.
    """
    from folio_docs.docs.theme_contract_codegen import generate_typescript_contract

    template_dir = _make_template(tmp_path)
    (template_dir / "theme").mkdir()
    (template_dir / "theme" / "theme-contract.generated.ts").write_text(
        "// STALE BUNDLED CONTRACT\n"
    )

    package_dir = tmp_path / "docs" / "theme" / "custom"
    (package_dir / "theme").mkdir(parents=True)
    (package_dir / "theme" / "project-theme.ts").write_text(
        "export const projectThemePreset = { id: 'pack-owned' }\n"
        "export const projectThemeDefaultConfig = { presetId: 'pack-owned' }\n"
    )

    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        theme_package_path=str(package_dir),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    # The package-owned preset module is preserved verbatim.
    project_theme = (build_dir / "theme" / "project-theme.ts").read_text()
    assert "pack-owned" in project_theme
    assert "projectBaseStyle" not in project_theme

    # The Folio-owned contract is regenerated, not frozen at the bundled copy.
    contract = (build_dir / "theme" / "theme-contract.generated.ts").read_text()
    assert "STALE BUNDLED CONTRACT" not in contract
    assert contract == generate_typescript_contract()


def test_build_rejects_package_shipping_generated_theme_contract(
    tmp_path: Path,
) -> None:
    """A package that ships only theme/theme-contract.generated.ts is rejected.

    It used to pass validation and then be silently clobbered by codegen.
    """
    template_dir = _make_template(tmp_path)
    package_dir = tmp_path / "theme_package"
    (package_dir / "theme").mkdir(parents=True)
    (package_dir / "theme" / "theme-contract.generated.ts").write_text(
        "export const stale = 1\n"
    )

    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        theme_package_path=str(package_dir),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    with pytest.raises(ValueError, match="theme/theme-contract.generated.ts"):
        builder.prepare()


def test_variant_option_style_keys_are_namespaced(tmp_path: Path) -> None:
    """Legacy style keys inside variant options get the --folio-* aliasing.

    Top-level theme.style already aliased documented legacy keys such as
    --content-max-width; variant option styles were emitted verbatim and
    silently no-op'd in the template.
    """
    from folio_docs.docs.template_workspace import _render_project_theme_module

    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        theme_preset="custom",
        theme_name="Custom",
        theme_variants={
            "density": {
                "label": "Density",
                "description": "",
                "default": "cozy",
                "options": {
                    "cozy": {
                        "label": "Cozy",
                        "description": "",
                        "preview": {},
                        "style": {
                            "--content-max-width": "70rem",
                            "--folio-body-line-height": "1.7",
                        },
                        "tokens": {},
                    },
                },
            },
        },
    )

    module = _render_project_theme_module(config)
    variant_themes = _extract_ts_object(module, "}>> = ")

    assert variant_themes["density"]["cozy"]["style"] == {
        "--folio-content-max-width": "70rem",
        "--folio-body-line-height": "1.7",
    }


def test_build_rejects_package_with_reserved_path(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    package_dir = tmp_path / "theme_package"
    package_dir.mkdir()
    (package_dir / "content").mkdir()
    (package_dir / "content" / "index.mdx").write_text("# Reserved")

    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        theme_package_path=str(package_dir),
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    with pytest.raises(ValueError, match="content/"):
        builder.prepare()

    assert not (build_dir / "content" / "index.mdx").exists()


def test_inject_next_config_derives_base_path_from_site_url(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        site_url="https://example.com/docs/v1/",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "next.config.mjs").read_text()
    assert 'const configuredBasePath = ""' in content


def test_inject_next_config_uses_explicit_deploy_base_path(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        site_url="https://example.com/docs/v1/",
        deploy_base_path="/published/docs",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "next.config.mjs").read_text()
    assert 'const configuredBasePath = "/published/docs"' in content


def test_inject_next_config_uses_folio_base_path_env(
    tmp_path: Path, monkeypatch
) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        deploy_base_path="/configured",
    )
    monkeypatch.setenv("FOLIO_BASE_PATH", "env-prefix")

    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "next.config.mjs").read_text()
    assert 'const configuredBasePath = "/env-prefix"' in content


def test_inject_next_config_infers_github_pages_project_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        deploy_provider="github-pages",
    )
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "octocat/project-docs")

    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "next.config.mjs").read_text()
    assert 'const configuredBasePath = "/project-docs"' in content


def test_inject_next_config_infers_github_pages_user_site_root(
    tmp_path: Path,
    monkeypatch,
) -> None:
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        deploy_provider="github-pages",
    )
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_REPOSITORY", "octocat/octocat.github.io")

    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "next.config.mjs").read_text()
    assert 'const configuredBasePath = ""' in content


def test_next_config_keeps_local_dev_server_at_root() -> None:
    root = Path(__file__).parents[1]
    next_config = (root / "template" / "next.config.mjs").read_text()

    assert "const isDevServer = process.env.NODE_ENV === 'development'" in next_config
    assert "const rawBasePath = isDevServer" in next_config
    assert "process.env.FOLIO_BASE_PATH?.trim() ?? ''" in next_config
    assert ": process.env.FOLIO_BASE_PATH?.trim() || configuredBasePath" in next_config


def test_inject_versions_includes_current_version_path(tmp_path: Path) -> None:
    template_dir = _make_template(tmp_path)
    components_dir = template_dir / "components"
    (components_dir / "version-selector.tsx").write_text(
        "const versions = __VERSIONS__\nconst current = __CURRENT_VERSION_PATH__\n"
    )
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        versions=[
            {"label": "v0.2.1 (latest)", "path": "latest"},
            {"label": "v0.1.0", "path": "v0.1", "default_path": "docs/"},
        ],
        current_version_path="v0.1",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "components" / "version-selector.tsx").read_text()
    assert '"label": "v0.2.1 (latest)", "path": "latest"' in content
    assert '"label": "v0.1.0", "path": "v0.1", "defaultPath": "docs/"' in content
    assert 'const current = "v0.1"' in content
    assert "__VERSIONS__" not in content
    assert "__CURRENT_VERSION_PATH__" not in content


def test_search_enabled_by_default(tmp_path: Path) -> None:
    """Search is enabled by default in Nextra's native search slot."""
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "docs" / "layout.tsx").read_text()
    assert 'import { SearchCommand } from "@/components/search-command"' in content
    assert "search={<SearchCommand />}" in content
    assert "search={null}" not in content


def test_search_disabled(tmp_path: Path) -> None:
    """When search is disabled, search={null} is injected."""
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        search_enabled=False,
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "docs" / "layout.tsx").read_text()
    assert "search={null}" in content
    assert "SearchCommand" not in content


def test_search_custom_placeholder(tmp_path: Path) -> None:
    """When a custom placeholder is set, SearchCommand receives it."""
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = Config(
        project_name="TestProject",
        output_dir=str(tmp_path / "output"),
        search_placeholder="Find something...",
    )
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    content = (build_dir / "app" / "docs" / "layout.tsx").read_text()
    assert 'import { SearchCommand } from "@/components/search-command"' in content
    assert '<SearchCommand placeholder="Find something..." />' in content
    assert 'import { Search } from "nextra/components"' not in content


def test_bundled_search_command_opens_with_cmd_k() -> None:
    """The bundled search wrapper uses Nextra's Cmd/Ctrl+K search."""
    component = (
        Path(__file__).parents[1] / "template" / "components" / "search-command.tsx"
    ).read_text()

    assert 'import { Search } from "nextra/components"' in component
    assert 'from "@/lib/search-index"' in component
    assert 'process.env.NODE_ENV === "production"' in component
    assert "data-folio-search" in component
    assert "metaKey" in component
    assert "ctrlKey" in component
    assert "input.focus({ preventScroll: true })" in component
    assert "placeholder={placeholder}" in component
    assert 'emptyResult="No matching docs or API pages."' in component
    assert 'errorText="Search index unavailable."' in component
    assert 'loading="Searching docs…"' in component
    assert 'role="dialog"' not in component
    assert 'aria-modal="true"' not in component


def test_project_theme_uses_contract_base_style():
    from folio_docs.schemas import theme_contract as tc
    from folio_docs.docs import template_workspace as tw

    assert tw._PROJECT_THEME_BASE_STYLE is tc.PROJECT_THEME_BASE_STYLE
    assert tw._PROJECT_THEME_TUNE_STYLE is tc.THEME_TUNE_STYLE_OVERRIDES
    assert tw._PROJECT_THEME_BASE_LIGHT is tc._PROJECT_THEME_BASE_LIGHT
    assert tw._PROJECT_THEME_BASE_DARK is tc._PROJECT_THEME_BASE_DARK
    # The radius scale is single-sourced from the shared contract schema.
    assert tw._THEME_RADIUS_OPTIONS is tc.THEME_RADIUS_OPTIONS


def test_theme_radius_index_falls_back_to_default_for_off_scale_value():
    from folio_docs.docs import template_workspace as tw
    from folio_docs.schemas import theme_contract as tc

    # Config validation rejects off-scale radii, so this fallback is defensive
    # only; it must resolve to the explicit 0.5rem default.
    assert tw._theme_radius_index("13px") == tc.THEME_RADIUS_OPTIONS.index("0.5rem")
    assert tw._theme_radius_index("0.75rem") == tc.THEME_RADIUS_OPTIONS.index("0.75rem")


def test_site_builder_read_meta_roundtrip(tmp_path) -> None:
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text('{"name": "test"}', encoding="utf-8")
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    # Absent meta reads as empty string.
    assert builder.read_meta("api") == ""

    builder.write_meta("api", 'export default { index: "Overview" }\n')
    assert builder.read_meta("api") == 'export default { index: "Overview" }\n'


def test_site_builder_register_route_and_emitted_routes(tmp_path) -> None:
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text('{"name": "test"}', encoding="utf-8")
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    assert builder.emitted_routes() == set()

    builder.register_route("api-reference/http")
    assert builder.emitted_routes() == {"api-reference/http"}

    # Returned set is a copy; mutating it does not affect internal state.
    builder.emitted_routes().add("mutated")
    assert builder.emitted_routes() == {"api-reference/http"}

    # write_page also records the route.
    builder.write_page("roadmap", "# Roadmap\n")
    assert builder.emitted_routes() == {"api-reference/http", "roadmap"}


def test_site_builder_prepare_resets_emitted_routes(tmp_path) -> None:
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text('{"name": "test"}', encoding="utf-8")
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    builder.register_route("roadmap")
    builder.prepare(clean=True)
    assert builder.emitted_routes() == set()


def test_page_assets_travel_with_the_page(tmp_path: Path) -> None:
    """A screenshot beside a doc page has to reach the content tree.

    MDX compiles `![alt](shot.png)` into `import __img0 from "shot.png"`,
    resolved against the generated .mdx. Without the file beside it the build
    does not lose the image, it fails: "Can't resolve 'shot.png'". Before this
    nothing copied doc assets, so no folio project could put a screenshot in
    its documentation.
    """
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    config = _make_config(tmp_path)
    builder = SiteBuilder(config, str(template_dir), str(build_dir))
    builder.prepare()

    source = tmp_path / "docs" / "guide"
    source.mkdir(parents=True)
    (source / "shot.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    builder.copy_page_asset("guide/page", "shot.png", source / "shot.png")
    assert (build_dir / "content" / "guide" / "shot.png").is_file()

    # An asset may not climb out of the content directory.
    with pytest.raises(ValueError, match="outside the content directory"):
        builder.copy_page_asset("guide/page", "../../escape.png", source / "shot.png")


def test_static_assets_are_published_and_republished(tmp_path: Path) -> None:
    """A plugin can put a file on the site without owning a page for it.

    `copy_page_asset` serves MDX imports; this serves readers. Warm builds
    keep the workspace, so an emitter that publishes a whole directory has to
    be able to clear it first — otherwise a file deleted from the project
    stays on the site forever.
    """
    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    builder = SiteBuilder(_make_config(tmp_path), str(template_dir), str(build_dir))
    builder.prepare()

    source = tmp_path / "cards" / "one-card"
    source.mkdir(parents=True)
    (source / "prototype.html").write_text("<p>x</p>", encoding="utf-8")

    builder.copy_static_asset(
        "_folio/kanban/one-card/prototype.html", source / "prototype.html"
    )
    published = build_dir / "public" / "_folio" / "kanban" / "one-card"
    assert (published / "prototype.html").read_text(encoding="utf-8") == "<p>x</p>"

    builder.remove_static_tree("_folio/kanban")
    assert not published.exists()

    # Neither may climb out of public/, and neither may take public/ itself.
    with pytest.raises(ValueError, match="outside the public directory"):
        builder.copy_static_asset("../escape.html", source / "prototype.html")
    with pytest.raises(ValueError, match="outside the public directory"):
        builder.remove_static_tree(".")
    assert (build_dir / "public").is_dir()


def test_copy_doc_assets_skips_remote_and_reports_missing(tmp_path: Path) -> None:
    """Only project-local files move; a broken path warns rather than crashes."""
    from folio_docs.build import _copy_doc_assets
    from folio_docs.parser.markdown_parser import MarkdownResult

    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    builder = SiteBuilder(_make_config(tmp_path), str(template_dir), str(build_dir))
    builder.prepare()

    source_dir = tmp_path / "docs"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "here.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    doc = MarkdownResult(
        content=(
            "![local](here.png)\n"
            "![remote](https://example.com/a.png)\n"
            "![rooted](/logo.png)\n"
            "![gone](missing.png)\n"
        ),
        route="page",
        source_file=str(source_dir / "page.md"),
    )
    missing = _copy_doc_assets(builder, doc)

    assert (build_dir / "content" / "here.png").is_file()
    assert not (build_dir / "content" / "logo.png").exists()
    assert missing == ["missing.png"]


def test_copy_doc_assets_ignores_image_syntax_inside_code(tmp_path: Path) -> None:
    """A page documenting Markdown must not have its examples treated as images.

    Documentation can show `![path](path)` inside backticks. Scanning raw
    content must not warn about a file nobody meant to reference.
    """
    from folio_docs.build import _copy_doc_assets
    from folio_docs.parser.markdown_parser import MarkdownResult

    template_dir = _make_template(tmp_path)
    build_dir = tmp_path / "build"
    builder = SiteBuilder(_make_config(tmp_path), str(template_dir), str(build_dir))
    builder.prepare()

    source_dir = tmp_path / "docs"
    source_dir.mkdir(parents=True, exist_ok=True)
    (source_dir / "real.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    doc = MarkdownResult(
        content=(
            "| `.. image:: path` | `![path](path)` |\n\n"
            "```md\n![fenced](also-not-real.png)\n```\n\n"
            "![real](real.png)\n"
        ),
        route="page",
        source_file=str(source_dir / "page.md"),
    )
    assert _copy_doc_assets(builder, doc) == []
    assert (build_dir / "content" / "real.png").is_file()


def test_article_prose_styles_do_not_reach_embedded_components() -> None:
    """`article h2 {}` is unlayered, so it beats every Tailwind utility.

    A board embedded in a Markdown page rendered its 11px mono column labels
    as 24px article headings with a 72px margin above them, and no class on
    the component could win — unlayered CSS outranks any layer whatever the
    specificity. Every article typography rule is scoped away from
    `.not-prose` subtrees, the way the table rules already were.
    """
    css = (Path(__file__).parents[1] / "template" / "app" / "globals.css").read_text()

    for selector in (
        "article h1",
        "article h2",
        "article h3",
        "article p",
        "article li",
        "article img",
        "article a",
        "article blockquote",
    ):
        assert f"{selector} {{" not in css, f"{selector} still styles every subtree"
        assert f"{selector}:not(.not-prose *) {{" in css


def test_injector_recognizes_plugin_view_owns_root(tmp_path: Path) -> None:
    """A plugin-owned root adjusts the docs canonical, sitemap, and wrapper."""

    # Create a minimal cardfile board
    board = tmp_path / "board"
    (board / "cards").mkdir(parents=True, exist_ok=True)
    (board / "board.yaml").write_text(
        'title: "Board"\ncolumns:\n  - id: backlog\n    title: Backlog\n'
        "  - id: done\n    title: Done\n",
        encoding="utf-8",
    )

    # Case 1: public: "/" → root owned
    template_dir = _make_template(tmp_path)
    # Add the docs catch-all page.jsx with the canonical marker
    docs_mdx_dir = template_dir / "app" / "docs" / "[[...mdxPath]]"
    docs_mdx_dir.mkdir(parents=True)
    (docs_mdx_dir / "page.jsx").write_text(
        'const docsIndexCanonicalPath = "__DOCS_INDEX_CANONICAL_PATH__"\n'
        "export default function DocsPage() { return null }\n",
        encoding="utf-8",
    )
    # Add sitemap.ts with the inclusion marker
    (template_dir / "app" / "sitemap.ts").write_text(
        'const INCLUDE_DOCS_INDEX: string = "__INCLUDE_DOCS_INDEX__"\n'
        "export default function sitemap() { return [] }\n",
        encoding="utf-8",
    )
    build_dir = tmp_path / "build-root-owned"
    config = Config(
        project_name="TestProject",
        project_dir=str(tmp_path),
        output_dir="output",
        landing_enabled=False,
        extra={"surface": {"routes": {"public": "/"}}},
    )
    resolved = config.resolve_paths(tmp_path)

    builder = SiteBuilder(resolved, str(template_dir), str(build_dir))
    builder.prepare()

    # Assert: app/page.tsx should NOT contain the docs-index wrapper
    # (the kanban plugin will write the actual view later via apply_extensions)
    page_path = build_dir / "app" / "page.tsx"
    assert page_path.exists()
    page_content = page_path.read_text(encoding="utf-8")
    # The wrapper imports DocsLayout and DocsPage - if root is owned, skip it
    assert "DocsLayout" not in page_content, (
        "Root-owned: app/page.tsx should skip docs wrapper"
    )
    assert "DocsPage" not in page_content, (
        "Root-owned: app/page.tsx should skip docs wrapper"
    )

    # Assert: docs catch-all carries canonical "/docs/"
    docs_page_path = build_dir / "app" / "docs" / "[[...mdxPath]]" / "page.jsx"
    assert docs_page_path.exists()
    docs_page_content = docs_page_path.read_text(encoding="utf-8")
    assert 'const docsIndexCanonicalPath = "/docs/"' in docs_page_content

    # Assert: sitemap.ts source has __INCLUDE_DOCS_INDEX__ replaced with "true"
    sitemap_path = build_dir / "app" / "sitemap.ts"
    assert sitemap_path.exists()
    sitemap_content = sitemap_path.read_text(encoding="utf-8")
    assert 'const INCLUDE_DOCS_INDEX: string = "true"' in sitemap_content

    # Case 2: public: true → current behavior (wrapper + canonical "/" + "false")
    tmp_path2 = tmp_path / "test2"
    tmp_path2.mkdir()
    template_dir2 = _make_template(tmp_path2)
    docs_mdx_dir2 = template_dir2 / "app" / "docs" / "[[...mdxPath]]"
    docs_mdx_dir2.mkdir(parents=True)
    (docs_mdx_dir2 / "page.jsx").write_text(
        'const docsIndexCanonicalPath = "__DOCS_INDEX_CANONICAL_PATH__"\n'
        "export default function DocsPage() { return null }\n",
        encoding="utf-8",
    )
    (template_dir2 / "app" / "sitemap.ts").write_text(
        'const INCLUDE_DOCS_INDEX: string = "__INCLUDE_DOCS_INDEX__"\n'
        "export default function sitemap() { return [] }\n",
        encoding="utf-8",
    )
    build_dir2 = tmp_path2 / "build-not-root-owned"
    # Need a board for the second test too
    board2 = tmp_path2 / "board"
    (board2 / "cards").mkdir(parents=True, exist_ok=True)
    (board2 / "board.yaml").write_text(
        'title: "Board"\ncolumns:\n  - id: backlog\n    title: Backlog\n'
        "  - id: done\n    title: Done\n",
        encoding="utf-8",
    )
    config2 = Config(
        project_name="TestProject",
        project_dir=str(tmp_path2),
        output_dir="output",
        landing_enabled=False,
        extra={"surface": {"routes": {"public": True}}},
    )
    resolved2 = config2.resolve_paths(tmp_path2)

    builder2 = SiteBuilder(resolved2, str(template_dir2), str(build_dir2))
    builder2.prepare()

    page_path2 = build_dir2 / "app" / "page.tsx"
    assert page_path2.exists()
    page_content2 = page_path2.read_text(encoding="utf-8")
    # When not root-owned and landing disabled, wrapper is written
    assert "DocsLayout" in page_content2, (
        "Not root-owned: app/page.tsx keeps docs wrapper"
    )
    assert "DocsPage" in page_content2, (
        "Not root-owned: app/page.tsx keeps docs wrapper"
    )

    docs_page_path2 = build_dir2 / "app" / "docs" / "[[...mdxPath]]" / "page.jsx"
    assert docs_page_path2.exists()
    docs_page_content2 = docs_page_path2.read_text(encoding="utf-8")
    assert 'const docsIndexCanonicalPath = "/"' in docs_page_content2

    sitemap_path2 = build_dir2 / "app" / "sitemap.ts"
    assert sitemap_path2.exists()
    sitemap_content2 = sitemap_path2.read_text(encoding="utf-8")
    assert 'const INCLUDE_DOCS_INDEX: string = "false"' in sitemap_content2

    # Case 3: public: "/board" (non-root path) → not root-owned, wrapper kept
    tmp_path3 = tmp_path / "test3"
    tmp_path3.mkdir()
    template_dir3 = _make_template(tmp_path3)
    docs_mdx_dir3 = template_dir3 / "app" / "docs" / "[[...mdxPath]]"
    docs_mdx_dir3.mkdir(parents=True)
    (docs_mdx_dir3 / "page.jsx").write_text(
        'const docsIndexCanonicalPath = "__DOCS_INDEX_CANONICAL_PATH__"\n'
        "export default function DocsPage() { return null }\n",
        encoding="utf-8",
    )
    (template_dir3 / "app" / "sitemap.ts").write_text(
        'const INCLUDE_DOCS_INDEX: string = "__INCLUDE_DOCS_INDEX__"\n'
        "export default function sitemap() { return [] }\n",
        encoding="utf-8",
    )
    build_dir3 = tmp_path3 / "build-non-root-path"
    board3 = tmp_path3 / "board"
    (board3 / "cards").mkdir(parents=True, exist_ok=True)
    (board3 / "board.yaml").write_text(
        'title: "Board"\ncolumns:\n  - id: backlog\n    title: Backlog\n'
        "  - id: done\n    title: Done\n",
        encoding="utf-8",
    )
    config3 = Config(
        project_name="TestProject",
        project_dir=str(tmp_path3),
        output_dir="output",
        landing_enabled=False,
        extra={"surface": {"routes": {"public": "/board"}}},
    )
    resolved3 = config3.resolve_paths(tmp_path3)

    builder3 = SiteBuilder(resolved3, str(template_dir3), str(build_dir3))
    builder3.prepare()

    page_path3 = build_dir3 / "app" / "page.tsx"
    assert page_path3.exists()
    page_content3 = page_path3.read_text(encoding="utf-8")
    # Non-root path should keep wrapper
    assert "DocsLayout" in page_content3, "Non-root path: app/page.tsx keeps wrapper"
    assert "DocsPage" in page_content3, "Non-root path: app/page.tsx keeps wrapper"

    docs_page_path3 = build_dir3 / "app" / "docs" / "[[...mdxPath]]" / "page.jsx"
    assert docs_page_path3.exists()
    docs_page_content3 = docs_page_path3.read_text(encoding="utf-8")
    assert 'const docsIndexCanonicalPath = "/"' in docs_page_content3

    sitemap_path3 = build_dir3 / "app" / "sitemap.ts"
    assert sitemap_path3.exists()
    sitemap_content3 = sitemap_path3.read_text(encoding="utf-8")
    assert 'const INCLUDE_DOCS_INDEX: string = "false"' in sitemap_content3


def test_root_ownership_check_survives_garbage_and_spelling(tmp_path: Path) -> None:
    """A project plugin may overwrite its normalized config after configure with
    anything at all. Garbage must not crash prepare, and a non-normalized
    root spelling must still count as root — the registration re-normalizes
    it, so the injector has to agree with what actually gets registered."""
    from folio_docs.config import Config
    from folio_docs.docs.template_workspace import TemplateConfigInjector

    def owns(plugin_section) -> bool:
        config = Config(project_name="X")
        if plugin_section is not None:
            config.extra["surface"] = plugin_section
        return TemplateConfigInjector(config, tmp_path)._plugin_view_owns_root()

    assert owns(None) is False
    assert owns("not a dict") is False
    assert owns({"routes": True}) is False
    assert owns({"routes": {"public": True}}) is False
    assert owns({"routes": {"public": ""}}) is False
    assert owns({"routes": {"public": "/board"}}) is False
    assert owns({"routes": {"public": "/"}}) is True
    assert owns({"routes": {"public": " / "}}) is True
