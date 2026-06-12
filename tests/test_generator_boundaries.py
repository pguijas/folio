from pathlib import Path

from folio.extensions import ExtensionRegistry
from folio.config import Config
from folio.generator.extension_emitter import ExtensionEmitter
from folio.generator.next_runtime import NextRuntime
from folio.generator.static_rewriter import StaticAssetRewriter
from folio.generator.template_workspace import TemplateConfigInjector, TemplateWorkspace


def test_extension_emitter_writes_mdx_components_without_site_builder(
    tmp_path: Path,
) -> None:
    build_dir = tmp_path / "build"
    (build_dir / "components").mkdir(parents=True)
    (build_dir / "mdx-components.tsx").write_text(
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return {\n"
        "    // __FOLIO_COMPONENT_ENTRIES__\n"
        "    ...components,\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source = source_dir / "hero.tsx"
    source.write_text(
        "export function Hero() { return <section /> }\n", encoding="utf-8"
    )

    registry = ExtensionRegistry()
    registry.register_component(
        "Hero",
        import_path="@/components/__folio_components/hero",
        export_name="Hero",
        source_path=source,
    )

    ExtensionEmitter(build_dir).apply(registry)

    assert (build_dir / "components" / "__folio_components" / "hero.tsx").exists()
    mdx = (build_dir / "mdx-components.tsx").read_text(encoding="utf-8")
    assert 'import { Hero } from "@/components/__folio_components/hero"' in mdx
    assert "    Hero," in mdx


def test_static_asset_rewriter_rewrites_output_without_site_builder(
    tmp_path: Path,
) -> None:
    output_dir = tmp_path / "output"
    (output_dir / "docs" / "guide").mkdir(parents=True)
    (output_dir / "_next" / "static").mkdir(parents=True)
    (output_dir / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")
    (output_dir / "docs" / "guide" / "index.html").write_text(
        "<h1>Guide</h1>", encoding="utf-8"
    )
    (output_dir / "_next" / "static" / "app.js").write_text(
        "console.log('ok')", encoding="utf-8"
    )
    (output_dir / "docs" / "index.html").write_text(
        '<a href="/">Home</a>'
        '<a href="/docs/guide/">Guide</a>'
        '<script src="/_next/static/app.js"></script>',
        encoding="utf-8",
    )

    StaticAssetRewriter(output_dir).fix_asset_paths()

    content = (output_dir / "docs" / "index.html").read_text(encoding="utf-8")
    assert 'href="../index.html"' in content
    assert 'href="guide/index.html"' in content
    assert 'src="../_next/static/app.js"' in content


def test_template_workspace_prepares_build_dir_without_site_builder(
    tmp_path: Path,
) -> None:
    template_dir = tmp_path / "template"
    (template_dir / "app").mkdir(parents=True)
    (template_dir / "content" / "demo").mkdir(parents=True)
    (template_dir / "app" / "page.tsx").write_text("demo", encoding="utf-8")
    (template_dir / "content" / "demo" / "index.mdx").write_text(
        "# Demo", encoding="utf-8"
    )
    build_dir = tmp_path / "build"

    TemplateWorkspace(template_dir, build_dir).prepare()

    assert (build_dir / "app" / "page.tsx").exists()
    assert (build_dir / "content").is_dir()
    assert not (build_dir / "content" / "demo" / "index.mdx").exists()


def test_template_config_injector_updates_placeholders_without_site_builder(
    tmp_path: Path,
) -> None:
    build_dir = tmp_path / "build"
    (build_dir / "app" / "docs").mkdir(parents=True)
    (build_dir / "components").mkdir()
    (build_dir / "app" / "layout.tsx").write_text(
        '"__PROJECT_NAME__" "__PROJECT_DESCRIPTION__"',
        encoding="utf-8",
    )
    (build_dir / "app" / "docs" / "layout.tsx").write_text(
        'import { getPageMap } from "nextra/page-map"\n'
        '"__PROJECT_NAME__" "__PROJECT_MONOGRAM__"\n'
        'pageMap={await getPageMap("/docs")}\n',
        encoding="utf-8",
    )
    (build_dir / "app" / "page.tsx").write_text(
        "const name = __PROJECT_NAME_JSON__\n",
        encoding="utf-8",
    )
    (build_dir / "next.config.mjs").write_text(
        "const configuredBasePath = '' // __FOLIO_BASE_PATH__\n__I18N_CONFIG__\n",
        encoding="utf-8",
    )
    (build_dir / "app" / "sitemap.ts").write_text(
        'const SITE_URL: string = "__SITE_URL__"\n'
        'if (!SITE_URL || !SITE_URL.startsWith("http")) return []\n',
        encoding="utf-8",
    )
    (build_dir / "components" / "landing-navbar.tsx").write_text(
        "const name = __PROJECT_NAME_JSON__\n",
        encoding="utf-8",
    )

    TemplateConfigInjector(
        Config(
            project_name="BoundaryDocs",
            output_dir=str(tmp_path / "out"),
            site_url="https://example.com/docs",
        ),
        build_dir,
    ).inject()

    layout = (build_dir / "app" / "layout.tsx").read_text(encoding="utf-8")
    docs_layout = (build_dir / "app" / "docs" / "layout.tsx").read_text(
        encoding="utf-8"
    )
    page = (build_dir / "app" / "page.tsx").read_text(encoding="utf-8")
    next_config = (build_dir / "next.config.mjs").read_text(encoding="utf-8")
    sitemap = (build_dir / "app" / "sitemap.ts").read_text(encoding="utf-8")
    assert '"BoundaryDocs"' in layout
    assert '"Documentation for BoundaryDocs"' in layout
    assert '"BoundaryDocs" "bo"' in docs_layout
    assert "search={<SearchCommand />}" in docs_layout
    assert 'const name = "BoundaryDocs"' in page
    assert 'const configuredBasePath = ""' in next_config
    assert "__I18N_CONFIG__" not in next_config
    assert 'const SITE_URL: string = "https://example.com/docs"' in sitemap
    assert '!SITE_URL.startsWith("http")' in sitemap


def test_next_runtime_installs_dependencies_without_site_builder(
    tmp_path: Path, monkeypatch
) -> None:
    template_dir = tmp_path / "template"
    build_dir = tmp_path / "build"
    template_dir.mkdir()
    build_dir.mkdir()
    (template_dir / "pnpm-lock.yaml").write_text("lock", encoding="utf-8")
    (build_dir / "pnpm-lock.yaml").write_text("lock", encoding="utf-8")
    (build_dir / "node_modules").mkdir()

    monkeypatch.setattr(NextRuntime, "_check_dependencies", lambda self: None)
    calls = []

    def fake_run(*args, **kwargs):
        assert not (build_dir / "node_modules").exists()
        calls.append((args, kwargs))

    monkeypatch.setattr("folio.generator.next_runtime.subprocess.run", fake_run)

    runtime = NextRuntime(template_dir, build_dir, tmp_path / "out")
    assert runtime.install_deps() is True
    assert calls
