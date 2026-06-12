import gzip
import json
import os
import re
from pathlib import Path
import subprocess

import pytest

from folio.build import _build_manifest_context, _generate_content_pages
from folio.config import Config, load_config
from folio.generator.site_builder import SiteBuilder
from folio.generator.static_rewriter import StaticAssetRewriter
from folio.ir import DocstringIR, ModuleIR
from folio.parser.markdown_parser import MarkdownResult


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
        config_path=config_path,
        template_dir=template_dir,
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
        isDisabledMdxPath(["plugins"]),
        "disabled docs routes should be recognized",
      )
      assert(
        isDisabledMdxPath(["plugins", "index.html"]),
        "disabled index.html aliases should be recognized",
      )
      assert(
        isDisabledMdxPath(["api-reference", "folio", "plugins", "roadmap"]),
        "disabled API routes should be recognized",
      )
      assert(
        isDisabledMdxPath(["api-reference", "folio", "extensions"]),
        "disabled extension API route should be recognized",
      )
      assert(
        isDisabledMdxPath(["api-reference", "folio", "generator", "extension_emitter"]),
        "disabled extension emitter API route should be recognized",
      )
      assert(
        !isDisabledMdxPath(["configuration"]),
        "enabled docs routes should not be marked disabled",
      )

      const params = expandStaticParams(
        [
          {{ mdxPath: [""] }},
          {{ mdxPath: ["components"] }},
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
            param.lang === "en" &&
            JSON.stringify(param.mdxPath) === JSON.stringify(["guide", "index.html"]),
        ),
        "locale params should keep their non-route fields on aliases",
      )
      assert(
        params.some(
          (param) => JSON.stringify(param.mdxPath) === JSON.stringify(["plugins"]),
        ),
        "disabled docs route should be included for dev export requests",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["plugins", "index.html"]),
        ),
        "disabled docs route index.html alias should be included for dev",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["api-reference", "folio", "plugins", "roadmap"]),
        ),
        "disabled API route should be included for dev export requests",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["api-reference", "folio", "extensions"]),
        ),
        "disabled extension API route should be included for dev export requests",
      )
      assert(
        params.some(
          (param) =>
            JSON.stringify(param.mdxPath) ===
            JSON.stringify(["api-reference", "folio", "generator", "extension_emitter"]),
        ),
        "disabled extension emitter API route should be included for dev export requests",
      )

      const productionParams = expandStaticParams(
        [{{ mdxPath: [""] }}, {{ mdxPath: ["components"] }}],
        {{ includeIndexHtmlAliases: false, includeDisabledParams: false }},
      )
      assert(
        !productionParams.some((param) => param.mdxPath.includes("index.html")),
        "index.html aliases should stay out of production static exports",
      )
      assert(
        !productionParams.some((param) => param.mdxPath.includes("plugins")),
        "disabled params should stay out of production static exports",
      )
    """

    subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=True,
        cwd=Path(__file__).parents[1],
    )


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

    assert "import { normalizeLandingHref }" in navbar
    assert "const secondaryCtaLink: string | null = null" in navbar
    assert "secondaryCtaLink?.startsWith" not in navbar
    assert "const normalizedSecondaryCtaLink = secondaryCtaLink" in navbar
    assert "? normalizeLandingHref(secondaryCtaLink)" in navbar


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


def test_bundled_landing_footer_uses_folio_identity() -> None:
    page = (Path(__file__).parents[1] / "template" / "app" / "page.tsx").read_text()

    assert "Made with Folio" in page
    assert "Built with __PROJECT_NAME__" not in page


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
    assert "const primaryCtaLink = __LANDING_CTA_PRIMARY_LINK_JSON__" in navbar
    assert "const secondaryCtaText = __LANDING_CTA_SECONDARY_TEXT_JSON__" in navbar
    assert 'aria-label="GitHub repository"' not in navbar


def test_bundled_landing_includes_competitive_evidence_table() -> None:
    root = Path(__file__).parents[1]
    page = (root / "template" / "app" / "page.tsx").read_text()
    sections = (
        root / "template" / "components" / "landing" / "sections.tsx"
    ).read_text()
    comparison_component_path = (
        root / "template" / "components" / "comparison-matrix.tsx"
    )
    docs_index = (root / "docs" / "guide" / "index.md").read_text()
    mdx_components = (root / "template" / "mdx-components.tsx").read_text()

    assert "__LANDING_SHOW_COMPARISON__" not in page
    assert "sections={landingSections}" in page
    assert comparison_component_path.exists()
    comparison_component = comparison_component_path.read_text()
    page = page + sections + comparison_component
    comparison_data = comparison_component[
        comparison_component.index(
            "const comparisonFrameworks"
        ) : comparison_component.index("function ComparisonCell")
    ]
    comparison_matrix_markup = comparison_component[
        comparison_component.index("export function ComparisonMatrix") :
    ]
    comparison_markup = sections[
        sections.index("function ComparisonSection") : sections.index(
            "function OutputSection"
        )
    ]
    globals_css = (root / "template" / "app" / "globals.css").read_text()
    comparison_evidence_styles = globals_css[
        globals_css.index(".comparison-evidence {") : globals_css.index(
            ".comparison-evidence-surface"
        )
    ]
    folio_row_styles = globals_css[
        globals_css.index(
            '.comparison-table-row[data-comparison-framework="folio"] > th'
        ) : globals_css.index(
            '.comparison-table-row[data-comparison-framework="folio"] {'
        )
    ]
    expected_headers = [
        "Tool",
        "Python API",
        "Guides",
        "Static export",
        "LLM friendly",
        "Extensibility",
        "Open source",
        "Git + CI",
    ]
    expected_tools = ["Folio", "pdoc", "Sphinx", "MkDocs", "Mintlify", "GitBook"]

    assert "const comparisonFeatureRows" in page
    assert "const comparisonFrameworks" in page
    assert '<ComparisonMatrix className="mt-6" />' in docs_index
    assert "| Tool | Python API |" not in docs_index
    assert (
        'import { ComparisonMatrix } from "@/components/comparison-matrix"'
        in mdx_components
    )
    assert "ComparisonMatrix," in mdx_components
    assert '<ComparisonMatrix className="mt-10" includeSurface={false} />' in sections
    assert "comparison-evidence-surface" in comparison_markup
    assert "background:" not in comparison_evidence_styles
    assert ".comparison-evidence-surface" in globals_css
    assert "var(--comparison-win-soft) 24%, var(--card)" in folio_row_styles
    assert "var(--comparison-win-soft) 24%, transparent" not in folio_row_styles
    for header in expected_headers:
        assert header in comparison_component
    for header in expected_headers[1:]:
        assert header in comparison_data
    for tool in expected_tools:
        assert tool in comparison_data
    for cell in ["Yes", "Some", "No"]:
        assert cell in comparison_component
    assert "Source-first docs, without the portal tax." in comparison_markup
    assert "ROADMAP" not in comparison_markup
    assert "readme" not in comparison_data
    assert "redocly" not in comparison_data
    assert "scalar" not in comparison_data
    assert "fern" not in comparison_data
    assert "ReadMe" not in comparison_data
    assert "Redocly" not in comparison_data
    assert "Scalar" not in comparison_data
    assert "Fern" not in comparison_data
    assert "min-w-[720px]" in page
    assert "mx-auto w-fit max-w-full" in comparison_matrix_markup
    assert (
        "comparison-table-shell mx-auto w-fit max-w-full overflow-x-auto bg-card"
        in comparison_matrix_markup
    )
    assert (
        "overflow-x-auto border border-border bg-card" not in comparison_matrix_markup
    )
    assert "table-fixed" in comparison_matrix_markup
    assert "min-w-[1260px]" not in comparison_matrix_markup
    assert "Auto API from source" not in comparison_data
    assert "Markdown docs" not in comparison_data
    assert "Google-style docstrings" not in comparison_data
    assert "MkDocs + Material" not in comparison_data
    assert "Guides + API" not in comparison_data
    assert "Local + CI" not in comparison_data
    assert "Local + static" not in comparison_data
    assert "Local dev" not in comparison_data
    assert "Static site" not in comparison_data
    assert "Static deploy" not in comparison_data
    assert 'feature: "API playground"' not in comparison_data
    assert 'feature: "Visual editor"' not in comparison_data
    assert 'feature: "Versions"' not in comparison_data
    assert "Source links" not in comparison_data
    assert "Quality gates" not in comparison_data
    assert "Custom MDX" not in comparison_data
    assert "Plugins" not in comparison_data
    assert "Sphinx migration" not in comparison_data
    assert "API portal" not in comparison_data
    assert "Default polish" not in comparison_data
    assert "Own static" not in comparison_data
    assert "Full site" not in comparison_data
    assert "LLM-ready" not in comparison_data
    assert "Hosted AI" not in comparison_data
    assert "Deep publishing" not in comparison_data
    assert "Python docs without the tradeoff." not in comparison_markup
    assert "Folio fills the matrix." not in comparison_markup
    assert "Green is coverage. Empty is scope." not in comparison_markup
    assert "Some" in page
    assert "Out of scope" not in comparison_data
    assert "pdoc" in comparison_data
    assert "GitBook" in comparison_data
    assert "MkDocs" in comparison_data
    assert "Docusaurus" not in comparison_data
    assert "Sphinx" in comparison_data
    assert "Mintlify" in comparison_data
    assert "Managed docs" not in comparison_data
    assert "Verdict" not in comparison_data
    assert "verdict:" not in comparison_data
    assert "Hosted AI docs" not in comparison_data
    assert "Starts simple" not in comparison_data
    assert "Tool" in comparison_matrix_markup
    assert '<span className="sr-only">Feature</span>' not in comparison_matrix_markup
    assert "Signal" not in comparison_data
    assert "data-comparison-framework={framework.key}" in comparison_matrix_markup
    assert "comparisonFeatureRows.map((feature)" in comparison_matrix_markup
    assert "ComparisonCell" in comparison_matrix_markup
    assert "comparison-evidence" in comparison_markup
    assert "comparison-matrix-cell" in page
    assert "comparison-matrix-cell-roadmap" not in comparison_matrix_markup
    assert (
        "comparison-empty: oklch"
        in (Path(__file__).parents[1] / "template" / "app" / "globals.css").read_text()
    )
    assert "comparison-matrix-value" in page
    assert "comparisonLegend" not in page
    assert "ComparisonMark" not in page
    assert "comparison-status" not in page
    assert "ComparisonCoverage" not in page
    assert "comparison-coverage-cell" not in page
    assert (
        "box-shadow: none;"
        in (Path(__file__).parents[1] / "template" / "app" / "globals.css").read_text()
    )
    assert 'data-comparison-cell-status="roadmap"' not in page
    assert "Run the default flow" not in page
    assert "Generate a complete Nextra site" not in page
    assert "API reference, guides, landing, and search" not in page
    assert "Honest sales angle" not in page
    assert "Honest alternative" not in page
    assert "Sales line" not in page


def test_landing_default_routes_are_shared() -> None:
    root = Path(__file__).parents[1]
    defaults_path = root / "template" / "components" / "landing" / "defaults.ts"
    hero = (root / "template" / "components" / "landing" / "hero.tsx").read_text()
    sections = (
        root / "template" / "components" / "landing" / "sections.tsx"
    ).read_text()

    assert defaults_path.exists()
    defaults = defaults_path.read_text()
    assert "export const defaultRoutes: LandingRouteItem[]" in defaults
    assert 'from "@/components/landing/defaults"' in hero
    assert 'from "@/components/landing/defaults"' in sections
    assert "const routeCards = [" not in hero
    assert "const defaultRoutes: LandingRouteItem[] = [" not in sections


def test_landing_hero_copy_is_shared() -> None:
    hero = (
        Path(__file__).parents[1] / "template" / "components" / "landing" / "hero.tsx"
    ).read_text()

    assert "function LandingHeroCopy" in hero
    assert hero.count("landing-kicker") == 1
    assert hero.count("<LandingActions") == 1
    assert hero.count("<LandingCommand") == 1


def test_project_roadmap_includes_competitive_gaps() -> None:
    docs_yaml = (Path(__file__).parents[1] / "docs.yaml").read_text()

    assert 'id: "api-portal"' in docs_yaml
    assert 'title: "API Portal"' in docs_yaml
    assert 'status: "next"' in docs_yaml
    assert "OpenAPI import" in docs_yaml
    assert "API playground" in docs_yaml
    assert "SDK snippets" in docs_yaml
    assert "API changelog" in docs_yaml
    assert 'id: "team-authoring"' in docs_yaml
    assert 'title: "Team Authoring"' in docs_yaml
    assert 'status: "later"' in docs_yaml
    assert "Visual editor" in docs_yaml
    assert "Git sync" in docs_yaml
    assert "Docs MCP" in docs_yaml
    assert "Access control" in docs_yaml


def test_bundled_roadmap_is_source_defined_and_read_only() -> None:
    component = (
        Path(__file__).parents[1] / "template" / "components" / "roadmap.tsx"
    ).read_text()

    assert 'from "@/lib/roadmap-data"' in component
    assert "useState" not in component
    assert "localStorage" not in component
    assert "draggable" not in component
    assert "onDrag" not in component
    assert "onDrop" not in component
    assert "Edit" not in component
    assert "Move" not in component


def test_roadmap_plugin_emits_data_and_public_page(tmp_path: Path) -> None:
    from folio.extensions import ExtensionRegistry, register_builtin_extensions
    from folio.plugins import roadmap as roadmap_plugin

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
    assert 'import { Roadmap } from "@/components/roadmap"' in public_page
    assert "<Roadmap />" in public_page


def test_apply_extensions_generates_mdx_component_imports(tmp_path: Path) -> None:
    from folio.extensions import ExtensionRegistry

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
    from folio.extensions import ExtensionRegistry

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


def test_apply_extensions_copies_components_to_import_paths(tmp_path: Path) -> None:
    from folio.extensions import ExtensionRegistry

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
    from folio.extensions import ExtensionRegistry

    template_dir = _make_template(tmp_path)
    (template_dir / "mdx-components.tsx").write_text(
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return { ...components }\n"
        "}\n"
    )
    build_dir = tmp_path / "build"
    registry = ExtensionRegistry()
    registry.register_layout(
        "folio.public",
        import_path="@/components/folio-view-layouts",
        export_name="PublicLayout",
    )
    registry.register_component("Roadmap", import_path="@/components/roadmap")
    registry.add_view(
        path="/roadmap",
        layout="folio.public",
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
    docs_yaml = (Path(__file__).parents[1] / "docs.yaml").read_text()

    assert "DocsMapLandingHero" in page
    assert "SourcePipelineLandingHero" in page
    assert '"@/components/landing/hero"' in page
    assert '"@/components/landing/sections"' in page
    assert "const LandingHero =" in page
    assert 'landingHeroVariant === "source-pipeline"' in page
    assert "export function DocsMapLandingHero" in hero
    assert "export function SourcePipelineLandingHero" in hero
    assert "Documentation routes" in hero
    assert "Build pipeline overview" in hero
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
    ]:
        assert f'"{section_type}"' in types
        assert f'"{section_type}"' in sections
    assert 'variant: "source-pipeline"' in docs_yaml


def test_roadmap_tracks_layout_level_theme_work() -> None:
    roadmap = (Path(__file__).parents[1] / "docs" / "guide" / "roadmap.md").read_text()

    assert "<Roadmap />" not in roadmap
    assert "FastAPI" in roadmap
    assert "layout-level theme presets" in roadmap
    assert "ThemeLanding" in roadmap
    assert "ThemeDocsLayout" in roadmap
    assert "MDX/frontmatter" in roadmap
    assert "docs.yaml" in roadmap
    assert "component registry" in roadmap
    assert "Organic Editorial" in roadmap


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
    assert '"--workspace-shell-padding"' in preset_types
    assert "export const presets" in presets
    assert 'id: "workshop"' in presets
    assert 'name: "Workshop"' in presets
    assert 'id: "canopy"' in presets
    assert 'name: "Canopy"' in presets
    assert "resolveSourceWorkspace" in presets
    assert "const sourceWorkspaceFrames" in presets
    assert 'label: "Borders"' in presets
    assert '"--workspace-shell-padding": "22px"' in presets
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
    assert "const selectPreset" in configurator
    assert "function PresetVisualTile" in configurator
    assert "theme-visual-preview" in configurator
    assert "preset.controls.map" in configurator
    assert "data-preset-control" in configurator
    assert "data-preset-option" in configurator
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
    assert 'label: "Workspace"' in configurator
    assert 'label: "Product Docs"' in configurator
    assert 'label: "Reference"' in configurator
    assert 'label: "Expressive"' in configurator
    assert configurator.index('label: "Expressive"') < configurator.index(
        'label: "Workspace"'
    )
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
    assert "--heading-font-family" in preset_types
    assert "--body-font-family" in preset_types
    assert "--code-font-family" in preset_types
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
    assert "theme-drawer-trigger-icon" in configurator
    assert "const ActiveModeIcon = isDark ? Moon02Icon : Sun03Icon" in configurator
    assert "icon={ActiveModeIcon}" in configurator
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
    assert ".landing-shell" in configurator
    assert ".landing-navbar" in configurator
    assert re.search(
        r"\.landing-navbar\s*\{[^}]*border: var\(--workspace-shell-border\)",
        configurator,
    )
    assert ".theme-floating-panel" not in css
    assert ".theme-navbar-panel" not in css
    assert ".theme-drawer-control" in css
    assert ".theme-drawer-panel" in css
    assert ".theme-drawer-trigger" in css
    assert ".theme-drawer-trigger-icon" in css
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
    assert "--workspace-shell-padding: 0px" in css
    assert "padding: var(--workspace-shell-padding)" in css
    assert "body > div:has(> .nextra-sidebar)" in css
    assert re.search(
        r"\.nextra-sidebar\s*\{[^}]*z-index:\s*60\s*!important;",
        css,
        re.DOTALL,
    )
    assert (
        'className="theme-drawer-panel absolute left-0 bottom-full mb-2' in configurator
    )
    assert "top: var(--workspace-shell-padding)" in css
    assert ".landing-shell" in css
    assert "min-height: calc(100vh - (var(--workspace-shell-padding) * 2))" in css
    assert ".landing-navbar" in css
    assert "width: calc(100% - (var(--workspace-shell-padding) * 2))" in css
    assert re.search(
        r"\.landing-navbar\s*\{[^}]*border: var\(--workspace-shell-border\)", css
    )
    assert "ThemeConfigurator" not in navbar


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
        "folio.generator.template_workspace.is_feature_enabled",
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


def test_bundled_docs_compact_h2_spacing_after_explicit_separators() -> None:
    css = (Path(__file__).parents[1] / "template" / "app" / "globals.css").read_text()

    assert re.search(
        r"article hr \+ h2\s*\{[^}]*margin-top: min\(1\.5rem, var\(--section-gap\)\);",
        css,
        re.DOTALL,
    )


def test_bundled_docs_toc_sticky_offset_accounts_for_shell_padding() -> None:
    css = (Path(__file__).parents[1] / "template" / "app" / "globals.css").read_text()
    configurator = (
        Path(__file__).parents[1] / "template" / "components" / "theme-configurator.tsx"
    ).read_text()

    for source in (css, configurator):
        assert re.search(
            r"\.nextra-toc > div\s*\{[^}]*top: calc\(var\(--nextra-navbar-height\) \+ var\(--workspace-shell-padding\)\) !important;",
            source,
            re.DOTALL,
        )
        assert re.search(
            r"\.nextra-toc > div\s*\{[^}]*max-height: calc\(100dvh - var\(--nextra-navbar-height\) - \(var\(--workspace-shell-padding\) \* 2\)\) !important;",
            source,
            re.DOTALL,
        )


def test_bundled_shell_header_uses_solid_mobile_chrome() -> None:
    template_dir = Path(__file__).parents[1] / "template"
    css = (template_dir / "app" / "globals.css").read_text()
    configurator = (template_dir / "components" / "theme-configurator.tsx").read_text()
    presets = (template_dir / "theme" / "presets.ts").read_text()

    assert "--workspace-shell-topbar: var(--background);" in css
    assert '"--workspace-shell-topbar": "var(--background)"' in presets
    assert "--workspace-shell-topbar: transparent" not in css
    assert '"--workspace-shell-topbar": "transparent"' not in presets

    for source in (css, configurator):
        assert "html {\n  background: var(--workspace-shell-topbar);" in source
        assert re.search(
            r"body > \.nextra-navbar\s*\{[^}]*background: var\(--workspace-shell-topbar\) !important;",
            source,
            re.DOTALL,
        )
        assert "backdrop-filter: none !important;" in source
        assert "-webkit-backdrop-filter: none !important;" in source
        assert "@media (max-width: 767px)" in source
        assert re.search(
            r"@media \(max-width: 767px\)\s*\{[^}]*body > \.nextra-navbar\s*\{[^}]*top: 0 !important;[^}]*margin-right: calc\(var\(--workspace-shell-padding\) \* -1\);[^}]*margin-left: calc\(var\(--workspace-shell-padding\) \* -1\);[^}]*width: calc\(100% \+ \(var\(--workspace-shell-padding\) \* 2\)\) !important;",
            source,
            re.DOTALL,
        )


def test_bundled_code_blocks_use_light_tokenized_surfaces() -> None:
    template_dir = Path(__file__).parents[1] / "template"
    css = (template_dir / "app" / "globals.css").read_text()
    next_config = (template_dir / "next.config.mjs").read_text()
    presets = (template_dir / "theme" / "presets.ts").read_text()
    docs = (
        Path(__file__).parents[1] / "docs" / "guide" / "components" / "code-blocks.md"
    ).read_text()

    assert "--code-bg: color-mix(in oklch, var(--muted) 86%, var(--background));" in css
    assert "article pre code.nextra-code span" in css
    assert "defaultShowCopyCode: true" in next_config
    assert "FOLIO_BASE_PATH" in next_config
    assert "__FOLIO_BASE_PATH__" in next_config
    assert "configuredBasePath" in next_config
    assert "assetPrefix: basePath" in next_config
    assert "Copy controls appear when readers hover over or focus a code block." in docs
    assert (
        '"--code-bg": "color-mix(in oklch, var(--muted) 86%, var(--background))"'
        in presets
    )
    assert '"--code-bg": "var(--foreground)"' not in presets


def test_theme_configurator_docs_explain_custom_presets_and_ai_prompt() -> None:
    docs = (
        Path(__file__).parents[1]
        / "docs"
        / "guide"
        / "components"
        / "theme-configurator.md"
    ).read_text()

    assert "### Create a Custom Preset" in docs
    assert "template/theme/presets.ts" in docs
    assert "template/theme/preset-types.ts" in docs
    assert "export const notebookPreset" in docs
    assert "### Generate a Preset with ChatGPT" in docs
    assert "Paste this prompt into ChatGPT" in docs
    assert "No gradients, no neon, no glow" in docs
    assert "Add the exported preset to `presets`" in docs
    assert "### Theme Flow" in docs
    assert "| Workshop |" in docs
    assert "| Canopy |" in docs
    assert "Borders control" in docs
    assert "| Beacon |" in docs
    assert "| Atlas |" in docs
    assert "| Aperture |" in docs
    assert "| Organic Editorial |" in docs
    assert "| Carbon |" in docs
    assert "### Preset Library" in docs
    assert "Workspace" in docs
    assert "Product Docs" in docs
    assert "Reference" in docs
    assert "Expressive" in docs
    assert "current theme summary" in docs
    assert "carousel row" in docs
    assert "Customize" in docs
    assert "Typography" in docs
    assert "Surface color" in docs
    assert "Accent color" in docs
    assert "Shell spacing" in docs
    assert "Content width" in docs
    assert "Reading rhythm" in docs
    assert "Code blocks" in docs
    assert "Corner radius" in docs
    assert "Color mode" not in docs
    assert "Switch between Light and Dark" not in docs
    assert (
        "The Back button returns readers from Customize to the grouped library." in docs
    )
    assert "flavor" not in docs.lower()


def test_organic_editorial_image_prompt_component_is_registered() -> None:
    template_dir = Path(__file__).parents[1] / "template"
    component = (
        template_dir / "components" / "organic-editorial-image-prompt.tsx"
    ).read_text()
    mdx_components = (template_dir / "mdx-components.tsx").read_text()
    docs = (
        Path(__file__).parents[1]
        / "docs"
        / "guide"
        / "components"
        / "organic-editorial-image-prompt.md"
    ).read_text()
    index = (
        Path(__file__).parents[1] / "template" / "components" / "component-index.tsx"
    ).read_text()

    assert "export function OrganicEditorialImagePrompt" in component
    assert "DEFAULT_ORGANIC_EDITORIAL_PROMPT" in component
    assert "cobalt blue organic forms" in component
    assert "no typography, no logos, no UI" in component
    assert "navigator.clipboard.writeText" in component
    assert (
        'import { OrganicEditorialImagePrompt } from "@/components/organic-editorial-image-prompt"'
        in mdx_components
    )
    assert "OrganicEditorialImagePrompt," in mdx_components
    assert "# OrganicEditorialImagePrompt" in docs
    assert "Organic Editorial" in docs
    assert "<OrganicEditorialImagePrompt" in docs
    assert "image-generation model" in docs
    assert 'title: "OrganicEditorialImagePrompt"' in index


def test_documentation_quality_components_are_registered_and_documented() -> None:
    root = Path(__file__).parents[1]
    template_dir = root / "template"
    mdx_components = (template_dir / "mdx-components.tsx").read_text()
    component_index = (template_dir / "components" / "component-index.tsx").read_text()
    sidebar = (root / "folio" / "generator" / "sidebar.py").read_text()

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


def test_terminal_session_uses_square_internal_code_surface() -> None:
    component = (
        Path(__file__).parents[1] / "template" / "components" / "terminal-session.tsx"
    ).read_text()

    assert component.startswith('"use client"')
    assert "CopyCheckIcon" in component
    assert "CopyIcon" in component
    assert "navigator.clipboard?.writeText" in component
    assert 'document.execCommand("copy")' in component
    assert "void copyText(command).then" in component
    assert "aria-label={`Copy command: ${title}`}" in component
    assert 'title={copied ? "Copied command" : "Copy command"}' in component
    assert (
        '<figure className="my-6 overflow-hidden rounded-lg border border-border bg-card">'
        in component
    )
    assert (
        'className="m-0 overflow-x-auto !rounded-none !border-0 bg-transparent p-4 font-mono text-sm leading-6 !shadow-none"'
        in component
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
    sidebar = (root / "folio" / "generator" / "sidebar.py").read_text()
    agents = (root / "AGENTS.md").read_text()

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


def test_quickstart_uses_visual_doc_previews_instead_of_large_sample_package() -> None:
    root = Path(__file__).parents[1]
    quickstart = (root / "docs" / "guide" / "quickstart.md").read_text()

    assert quickstart.count("<DocPreview") == 1
    assert 'example="generated-site"' in quickstart
    assert 'example="landing-page"' not in quickstart
    assert "These frames" not in quickstart
    assert 'example="guide-overview"' not in quickstart
    assert 'example="cli-reference"' not in quickstart
    assert 'example="configuration-guide"' not in quickstart
    assert 'example="api-reference"' not in quickstart
    assert 'example="component-catalog"' not in quickstart
    assert 'src="/"' not in quickstart
    assert 'src="/docs/api-reference/folio/config"' not in quickstart
    assert "landing:\n  enabled: false" not in quickstart
    assert "## Optional Step 7: Add a Landing Page" not in quickstart
    assert "[Landing Page](./landing)" not in quickstart
    assert "git clone https://github.com/pguijas/folio.git" in quickstart
    assert "Create `src/mymath/__init__.py`" not in quickstart
    assert "Create `src/mymath/arithmetic.py`" not in quickstart
    assert "Create `src/mymath/geometry.py`" not in quickstart


def test_quickstart_uses_plain_shell_blocks_for_setup_commands() -> None:
    root = Path(__file__).parents[1]
    quickstart = (root / "docs" / "guide" / "quickstart.md").read_text()

    assert "<TerminalSession" not in quickstart
    for command in [
        "git clone https://github.com/pguijas/folio.git && cd folio",
        "uv run folio build --clean",
    ]:
        assert f"```bash\n{command}\n```" in quickstart
    assert (
        "```bash\nuv add folio-docs\nuv run folio init\nuv run folio serve\n```"
        in quickstart
    )
    assert "uv run folio serve --verbose" not in quickstart
    assert "Ready to build the documentation site." not in quickstart


def test_public_guide_command_snippets_avoid_terminal_session_chrome() -> None:
    root = Path(__file__).parents[1]
    pages = [
        root / "docs" / "guide" / "quickstart.md",
        root / "docs" / "guide" / "cli.md",
    ]

    for page in pages:
        text = page.read_text()
        assert "<TerminalSession" not in text
        assert "output={`" not in text
        assert "✓ Sources" not in text
        assert "Watching Python and Markdown sources" not in text


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
    readme = (root / "README.md").read_text()
    sidebar = (root / "folio" / "generator" / "sidebar.py").read_text()
    agents = (root / "AGENTS.md").read_text()

    assert "**MVP-disabled features**" in configuration
    assert "### landing" not in configuration
    assert "### roadmap" not in configuration
    assert "### plugins" not in configuration
    assert "### components" not in configuration
    assert "### versions" not in configuration
    assert "folio roadmap" not in cli
    assert "build-versions" not in cli
    assert "--versions" not in cli
    assert '("landing", "Landing Page")' not in sidebar
    assert '("plugins", "Plugins (Beta)")' not in sidebar
    assert '("versioning", "Versioning (Alpha)")' not in sidebar
    assert '("i18n", "Internationalization (Experimental)")' not in sidebar
    assert '("roadmap", "Roadmap (Experimental)")' not in sidebar
    assert "[**Landing Page**](./landing)" not in overview
    assert "[**Plugins (Beta)**](./plugins)" not in overview
    assert "[**Versioning (Alpha)**](./versioning)" not in overview
    assert "**Plugin system**" not in overview
    assert "**Plugin system**" not in readme
    assert "Write a pluggy plugin" not in migration
    assert "pluggy-based (early)" not in migration
    assert "**Disabled feature surfaces**" in agents
    assert "**Experimental feature docs**" not in agents


def test_disabled_feature_docs_are_not_generated(tmp_path: Path) -> None:
    page = _write_generated_doc_page(
        tmp_path=tmp_path,
        route="roadmap",
        content="# Roadmap\n\nThis guide explains the experimental feature.",
        title="Roadmap",
    )

    assert not page.exists()


def test_disabled_api_modules_are_not_generated(tmp_path: Path) -> None:
    source_dir = tmp_path / "folio" / "plugins"
    source_dir.mkdir(parents=True)
    source_file = source_dir / "roadmap.py"
    source_file.write_text('"""Roadmap plugin internals."""\n', encoding="utf-8")
    extensions_file = tmp_path / "folio" / "extensions.py"
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
    stale_route = "api-reference/folio/plugins/roadmap"
    builder.write_page("api-reference/index", "# Stale API index\n")
    builder.write_page(stale_route, "# Stale roadmap API\n")
    builder.write_meta("api-reference", 'export default { "folio": "Folio" }')
    builder.write_meta("api-reference/folio", 'export default { "plugins": "Plugins" }')
    stale_extensions_route = "api-reference/folio/extensions"
    builder.write_page(stale_extensions_route, "# Stale extensions API\n")

    _generate_content_pages(
        builder=builder,
        config=config,
        modules=[
            ModuleIR(
                name="folio.plugins.roadmap",
                docstring=DocstringIR(short_description="Roadmap plugin internals."),
                classes=[],
                functions=[],
                constants=[],
                source_file=str(source_file),
            ),
            ModuleIR(
                name="folio.extensions",
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
        config_path=config_path,
        template_dir=template_dir,
        clean=True,
        verbose=False,
    )

    assert not (build_dir / "content" / "api-reference" / "index.mdx").exists()
    assert not (build_dir / "content" / "api-reference" / "_meta.ts").exists()
    assert not (build_dir / "content" / "api-reference" / "folio" / "_meta.ts").exists()
    assert not (build_dir / ".folio" / "pages" / "api-reference" / "index.md").exists()
    assert not (
        build_dir / "content" / "api-reference" / "folio" / "plugins" / "roadmap.mdx"
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
        route="roadmap",
        content="# Roadmap\n\nExperimental guide content.",
        title="Roadmap",
    )

    assert not page.exists()


def test_landing_guide_is_not_generated(tmp_path: Path) -> None:
    page = _write_generated_doc_page(
        tmp_path=tmp_path,
        route="landing",
        content="# Landing Page\n\nConfigure the optional homepage.",
    )

    assert not page.exists()


def test_manifest_context_tracks_disabled_feature_state(tmp_path: Path) -> None:
    config_path = tmp_path / "docs.yaml"
    config_path.write_text('project:\n  name: "TestProject"\n', encoding="utf-8")
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text('{"name": "test"}', encoding="utf-8")

    context = _build_manifest_context(config_path, template_dir, "main")

    assert context["experimental_features"] == "disabled"


def test_warning_callouts_use_warning_tone_not_destructive_tone() -> None:
    root = Path(__file__).parents[1]
    callout = (root / "template" / "components" / "callout.tsx").read_text()
    warning_block = re.search(r"warning:\s*\{(?P<body>.*?)\n\s*\},", callout, re.DOTALL)
    danger_block = re.search(r"danger:\s*\{(?P<body>.*?)\n\s*\},", callout, re.DOTALL)

    assert warning_block is not None
    assert danger_block is not None

    warning_styles = warning_block.group("body")
    danger_styles = danger_block.group("body")

    assert "amber" in warning_styles
    assert "destructive" not in warning_styles
    assert "destructive" in danger_styles


def test_doc_preview_can_toggle_to_page_source() -> None:
    root = Path(__file__).parents[1]
    component = (root / "template" / "components" / "doc-preview.tsx").read_text()
    docs = (root / "docs" / "guide" / "components" / "doc-preview.md").read_text()

    assert '"use client"' in component
    assert "type PreviewMode" in component
    assert "sourceUrlForPreview" in component
    assert "exampleUrlForPreview" in component
    assert "loadExampleWorkspace" in component
    assert "manifest.json" in component
    assert "index.html" in component
    assert "syncPreviewFrameTheme" in component
    assert "previewFrameRef" in component
    assert "contentDocument" in component
    assert "--background" in component
    assert "--foreground" in component
    assert "--accent" in component
    assert "MutationObserver" in component
    assert "document.head" in component
    assert "onLoad={syncPreviewTheme}" in component
    assert 'role="tablist"' in component
    assert 'aria-selected={mode === "preview"}' in component
    assert 'aria-selected={mode === "source"}' in component
    assert 'fetch(sourceUrl, { cache: "no-store" })' in component
    assert 'fetch(exampleManifestUrl(exampleName), { cache: "no-store" })' in component
    assert '"/_folio/markdown/"' in component
    assert "Open source" in component
    assert "Live preview" not in component
    assert "const previewModeTabs" in component
    assert "source view" in docs


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


def test_doc_preview_source_mode_uses_file_explorer_workspace() -> None:
    root = Path(__file__).parents[1]
    component = (root / "template" / "components" / "doc-preview.tsx").read_text()
    docs = (root / "docs" / "guide" / "components" / "doc-preview.md").read_text()

    assert "type SourceFile" in component
    assert "type SourceTreeNode" in component
    assert "loadSourceWorkspace" in component
    assert "sourceFilesUrl" not in component
    assert '"/_folio/source-files.json"' not in component
    assert "buildSourceTree" in component
    assert "folderPathsForSourceFiles" in component
    assert ".flatMap(folderPathsForSourceFile)" in component
    assert "setExpandedFolders(new Set(folderPathsForSourceFiles(files)))" in component
    assert "expandedFolders" in component
    assert "toggleSourceFolder" in component
    assert "source-file-drawer" in component
    assert "source-folder-row" in component
    assert "source-file-row" in component
    assert 'aria-label="Source files"' in component
    assert "aria-expanded" in component
    assert 'role="group"' in component
    assert "content/${route}.mdx" in component
    assert "source-code-preview" in component
    assert "line-number" in component
    assert "lintSourceCode" not in component
    assert "No lint issues" not in component
    assert "collapsible file drawer" in docs
    assert "focused source file" in docs
    assert "line-numbered code preview" in docs


def test_components_index_uses_richer_catalog_component() -> None:
    root = Path(__file__).parents[1]
    docs_index = (root / "docs" / "guide" / "components" / "index.md").read_text()
    mdx_components = (root / "template" / "mdx-components.tsx").read_text()
    component_index = (
        root / "template" / "components" / "component-index.tsx"
    ).read_text()

    assert "<ComponentIndex />" in docs_index
    assert "CardGrid" not in docs_index
    assert (
        'import { ComponentIndex } from "@/components/component-index"'
        in mdx_components
    )
    assert "ComponentIndex," in mdx_components
    assert "export function ComponentIndex" in component_index
    assert "component-index-hero" in component_index
    assert "Workflow Components" in component_index
    assert "Interactive Components" in component_index
    assert "API Reference Components" in component_index


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
    assert "Python API catalog" in api_index


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


def test_docs_page_header_uses_single_page_actions_button() -> None:
    root = Path(__file__).parents[1]
    page = (
        root / "template" / "app" / "docs" / "[[...mdxPath]]" / "page.jsx"
    ).read_text()
    actions = (root / "template" / "components" / "page-actions-button.tsx").read_text()
    docs = (root / "docs" / "guide" / "components" / "copy-page-button.md").read_text()

    assert (
        'import { PageActionsButton } from "@/components/page-actions-button"' in page
    )
    assert "CopyPageButton" not in page
    assert "OpenAssistantButton" not in page
    assert "Copy page" in actions
    assert "View Markdown" in actions
    assert "Ask AI" in actions
    assert "ChatGPT" in actions
    assert "Claude" not in actions
    assert "Gemini" not in actions
    assert "MCP JSON" in actions
    assert "/icons/chatgpt.svg" in actions
    assert "src={withFolioBasePath(action.icon)}" in actions
    assert "NEXT_PUBLIC_FOLIO_BASE_PATH" in actions
    assert "function withFolioBasePath(path: string)" in actions
    assert "return `${FOLIO_BASE_PATH}${path}`" in actions
    assert "withFolioBasePath(`/_folio/markdown/${getDocsRoute()}.md`)" in actions
    assert "buildAssistantUrl(action, text)" in actions
    assert "href={assistantHref}" in actions
    assert 'target="_blank"' not in actions
    assert "window.open(buildAssistantUrl(action, text)" not in actions
    assert 'promptParam: "q"' in actions
    assert "Read from ${getMarkdownUrl()} so I can ask questions about it." in actions
    assert "canExternalAssistantFetchPage" not in actions
    assert "return createAssistantReadPrompt()" in actions
    assert "url.searchParams.set(action.promptParam, prompt)" in actions
    assert "createAssistantReadPrompt" in actions
    assert "Prompt opened" in actions
    assert "Prompt copied" not in actions
    assert "Page Actions" in docs
    assert "PageActionsButton" in docs
    assert "current page's Markdown URL" in docs
    assert "configured deploy base paths" in docs
    assert "ChatGPT-only" in docs
    assert "localhost or file URLs" not in docs
    assert "copies the full page prompt" not in docs
    assert "Claude" not in docs
    assert "Gemini" not in docs


def test_page_actions_markdown_url_uses_configured_base_path() -> None:
    root = Path(__file__).parents[1]
    actions = (root / "template" / "components" / "page-actions-button.tsx").read_text()
    next_config = (root / "template" / "next.config.mjs").read_text()

    assert 'NEXT_PUBLIC_FOLIO_BASE_PATH: basePath ?? ""' in next_config
    assert "const FOLIO_BASE_PATH = process.env.NEXT_PUBLIC_FOLIO_BASE_PATH" in actions
    assert "function withFolioBasePath(path: string)" in actions
    assert "withFolioBasePath(`/_folio/markdown/${getDocsRoute()}.md`)" in actions


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

    monkeypatch.setattr("folio.build.run_build", fake_run_build)
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
    from folio.generator.next_runtime import NextRuntime

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

    monkeypatch.setattr("folio.generator.next_runtime.subprocess.run", fake_run)

    assert builder.install_deps() is True
    assert calls


def test_install_deps_repairs_broken_next_runtime(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio.generator.next_runtime import NextRuntime

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

    monkeypatch.setattr("folio.generator.next_runtime.subprocess.run", fake_run)

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
    from folio.generator.next_runtime import NextRuntime

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

    monkeypatch.setattr("folio.generator.next_runtime.subprocess.Popen", fake_popen)

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
    from folio.generator.next_runtime import NextRuntime

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
    from folio.generator.next_runtime import NextRuntime

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

    monkeypatch.setattr("folio.generator.next_runtime.subprocess.Popen", fake_popen)

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


def test_template_ui_components_avoid_unused_icon_has_data_variants() -> None:
    template_root = Path(__file__).parents[1] / "template"
    component_paths = [
        template_root / "components" / "ui" / "badge.tsx",
        template_root / "components" / "ui" / "button.tsx",
        template_root / "components" / "ui" / "tabs.tsx",
    ]

    for path in component_paths:
        content = path.read_text(encoding="utf-8")
        assert "has-data-[icon=" not in content, path


def test_next_runtime_patches_nextra_loader_to_skip_generated_git_timestamps(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from folio.generator.next_runtime import NextRuntime

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
    from folio.generator.next_runtime import NextRuntime

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

    monkeypatch.setattr("folio.generator.next_runtime.subprocess.Popen", fake_popen)
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
    from folio.generator.next_runtime import NextRuntime

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

    monkeypatch.setattr("folio.generator.next_runtime.subprocess.Popen", fake_popen)
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

    config = Config(project_name="TestProject", output_dir=str(output_dir))
    builder = SiteBuilder(config, str(tmp_path / "template"), str(tmp_path / "build"))

    builder._fix_asset_paths()

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

    config = Config(project_name="TestProject", output_dir=str(output_dir))
    builder = SiteBuilder(config, str(tmp_path / "template"), str(tmp_path / "build"))

    builder._fix_asset_paths()

    content = (output_dir / "index.html").read_text()
    assert 'href="index.html"' in content
    assert 'href="docs/index.html"' in content


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

    config = Config(project_name="TestProject", output_dir=str(output_dir))
    builder = SiteBuilder(config, str(tmp_path / "template"), str(tmp_path / "build"))

    builder._fix_asset_paths()

    content = (chunk_dir / "search.js").read_text(encoding="utf-8")
    assert content == chunk


def test_fix_asset_paths_makes_turbopack_runtime_prefix_portable(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    chunk_dir = output_dir / "_next" / "static" / "chunks"
    chunk_dir.mkdir(parents=True)
    runtime = (
        "(globalThis.TURBOPACK=[]).push([]),(()=>{"
        'let e,t="/_next/",r="?v=1";'
        'let suffix=function(){let e=document?.currentScript?.getAttribute?.("src")??"";return e}();'
        'function F(e){if(e)return{src:e.getAttribute("src")}}'
        "function N(e){return`${t}${e}${r}`}"
        "})();"
    )
    (chunk_dir / "turbopack-runtime.js").write_text(runtime, encoding="utf-8")

    config = Config(project_name="TestProject", output_dir=str(output_dir))
    builder = SiteBuilder(config, str(tmp_path / "template"), str(tmp_path / "build"))

    builder._fix_asset_paths()

    content = (chunk_dir / "turbopack-runtime.js").read_text(encoding="utf-8")
    assert 'let e,t="/_next/",r="?v=1";' not in content
    assert "document.currentScript" in content
    assert 'getAttribute?.("src")' not in content
    assert 'getAttribute("src")' not in content
    assert "currentScript?.src" in content
    assert "return{src:e.src}" in content
    assert 'e.indexOf("/_next/")' in content
    assert 'return t?t[1]:"/_next/"' in content


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

    config = Config(project_name="TestProject", output_dir=str(output_dir))
    builder = SiteBuilder(config, str(tmp_path / "template"), str(tmp_path / "build"))

    builder._fix_asset_paths()

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
    assert 'loading="Searching docs..."' in component
    assert 'role="dialog"' not in component
    assert 'aria-modal="true"' not in component
