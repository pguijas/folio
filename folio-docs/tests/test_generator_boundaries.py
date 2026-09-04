from pathlib import Path

import pytest

from folio_docs.builtins import register_builtin_components
from folio_docs.extensions import ExtensionRegistry, register_config_components
from folio_docs.config import Config
from folio_docs.docs.extension_emitter import ExtensionEmitter
from folio_docs.docs.next_runtime import NextRuntime
from folio_docs.docs.static_rewriter import StaticAssetRewriter
from folio_docs.docs.template_workspace import TemplateConfigInjector, TemplateWorkspace


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


def test_extension_emitter_skips_components_already_wired_in_template(
    tmp_path: Path,
) -> None:
    """Builtins already present in the bundled template must not be re-injected.

    The template ships ``import { Tabs, TabItem } from "@/components/tabs"`` as a
    single combined import. Registering Tabs/TabItem (as builtins now are) must
    not add separate ``import { Tabs } ...`` lines or duplicate entries.
    """
    build_dir = tmp_path / "build"
    (build_dir / "components").mkdir(parents=True)
    (build_dir / "mdx-components.tsx").write_text(
        'import { Tabs, TabItem } from "@/components/tabs"\n'
        "// __FOLIO_COMPONENT_IMPORTS__\n"
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return {\n"
        "    Tabs,\n"
        "    TabItem,\n"
        "    // __FOLIO_COMPONENT_ENTRIES__\n"
        "    ...components,\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )

    registry = ExtensionRegistry()
    # Builtins (already in the template) — multi-export from one module.
    registry.register_component("Tabs", import_path="@/components/tabs")
    registry.register_component("TabItem", import_path="@/components/tabs")
    # A genuine plugin component that is NOT in the template yet.
    registry.register_component("Hero", import_path="@/components/hero")

    ExtensionEmitter(build_dir).apply(registry)

    mdx = (build_dir / "mdx-components.tsx").read_text(encoding="utf-8")
    # No duplicate single-name import lines for the bundled multi-export module.
    assert 'import { Tabs } from "@/components/tabs"' not in mdx
    assert 'import { TabItem } from "@/components/tabs"' not in mdx
    # Entries are not duplicated.
    assert mdx.count("    Tabs,") == 1
    assert mdx.count("    TabItem,") == 1
    # The genuine plugin component IS injected.
    assert 'import { Hero } from "@/components/hero"' in mdx
    assert "    Hero," in mdx


def test_extension_emitter_recognizes_entries_regardless_of_formatting(
    tmp_path: Path,
) -> None:
    """The dedup probe must be structural, not textual: 2-space indentation,
    `Name: Custom` mapping entries, and single-quoted/relative imports all
    count as wired, so nothing is re-injected."""
    build_dir = tmp_path / "build"
    (build_dir / "components").mkdir(parents=True)
    original = (
        "import { Tabs, TabItem } from '@/components/tabs'\n"
        "import CustomParamTable from './local/param-table'\n"
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return {\n"
        "  Tabs,\n"
        "  TabItem,\n"
        "  ParamTable: CustomParamTable,\n"
        "  ...components,\n"
        "  }\n"
        "}\n"
    )
    (build_dir / "mdx-components.tsx").write_text(original, encoding="utf-8")

    registry = ExtensionRegistry()
    registry.register_component("Tabs", import_path="@/components/tabs")
    registry.register_component("TabItem", import_path="@/components/tabs")
    registry.register_component("ParamTable", import_path="@/components/param-table")

    ExtensionEmitter(build_dir).apply(registry)

    assert (build_dir / "mdx-components.tsx").read_text(encoding="utf-8") == original


def test_extension_emitter_skips_import_when_symbol_already_bound(
    tmp_path: Path,
) -> None:
    """A template that already imports the symbol (any quoting/path) must not
    receive a second, conflicting import — only the missing map entry."""
    build_dir = tmp_path / "build"
    (build_dir / "components").mkdir(parents=True)
    (build_dir / "mdx-components.tsx").write_text(
        "import Hero from './local/hero'\n"
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return {\n"
        "    // __FOLIO_COMPONENT_ENTRIES__\n"
        "    ...components,\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )

    registry = ExtensionRegistry()
    registry.register_component("Hero", import_path="@/components/hero")

    ExtensionEmitter(build_dir).apply(registry)

    mdx = (build_dir / "mdx-components.tsx").read_text(encoding="utf-8")
    assert 'import { Hero } from "@/components/hero"' not in mdx
    assert mdx.count("import Hero from './local/hero'") == 1
    assert "    Hero," in mdx


def test_extension_emitter_inject_builtins_false_skips_builtin_components(
    tmp_path: Path,
) -> None:
    """Custom templates that do not bundle the builtin component files must
    not receive builtin imports/entries; plugin components still inject."""
    build_dir = tmp_path / "build"
    (build_dir / "components").mkdir(parents=True)
    (build_dir / "mdx-components.tsx").write_text(
        "// __FOLIO_COMPONENT_IMPORTS__\n"
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return {\n"
        "    // __FOLIO_COMPONENT_ENTRIES__\n"
        "    ...components,\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )

    registry = ExtensionRegistry()
    register_builtin_components(registry)
    registry.register_component("Hero", import_path="@/components/hero")

    ExtensionEmitter(build_dir, inject_builtins=False).apply(registry)

    mdx = (build_dir / "mdx-components.tsx").read_text(encoding="utf-8")
    assert "ParamTable" not in mdx
    assert "TerminalSession" not in mdx
    assert 'import { Hero } from "@/components/hero"' in mdx
    assert "    Hero," in mdx


def test_extension_emitter_resolves_relative_source_against_project_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    build_dir = tmp_path / "build"
    (build_dir / "components").mkdir(parents=True)
    (build_dir / "mdx-components.tsx").write_text(
        "export function useMDXComponents(components?: Record<string, React.ComponentType>) {\n"
        "  return {\n"
        "    ...components,\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )
    project_dir = tmp_path / "project"
    (project_dir / "docs" / "components").mkdir(parents=True)
    (project_dir / "docs" / "components" / "hero.tsx").write_text(
        "export function Hero() { return <section /> }\n", encoding="utf-8"
    )

    registry = ExtensionRegistry()
    registry.register_component(
        "Hero",
        import_path="@/components/__folio_components/hero",
        source_path="docs/components/hero.tsx",
    )

    with pytest.raises(FileNotFoundError):
        ExtensionEmitter(build_dir).apply(registry)

    ExtensionEmitter(build_dir, project_dir=str(project_dir)).apply(registry)

    assert (build_dir / "components" / "__folio_components" / "hero.tsx").exists()


def test_extension_emitter_copies_config_dir_and_spec_components(
    tmp_path: Path,
) -> None:
    """Regression: project_dir anchoring works for dir entries and from: specs.

    Directory entries are resolved at registration time (register_config_components
    anchors the relative directory to config.project_dir and stores absolute
    source paths); relative spec paths stay relative until the emitter anchors
    them to its own project_dir. Both must land in the build workspace.
    """
    build_dir = tmp_path / "build"
    (build_dir / "components").mkdir(parents=True)
    project_dir = tmp_path / "project"
    components_dir = project_dir / "docs" / "components"
    components_dir.mkdir(parents=True)
    (components_dir / "hero.tsx").write_text(
        "export function Hero() { return <section /> }\n", encoding="utf-8"
    )
    (project_dir / "banner.tsx").write_text(
        "export function Banner() { return <aside /> }\n", encoding="utf-8"
    )

    config = Config(
        project_name="Demo",
        component_dirs=["docs/components"],
        component_specs=[{"name": "Banner", "from": "banner.tsx"}],
        project_dir=str(project_dir),
    )
    registry = ExtensionRegistry()
    register_config_components(registry, config)

    ExtensionEmitter(build_dir, project_dir=str(project_dir)).apply(registry)

    assert (build_dir / "components" / "__folio_components" / "hero.tsx").exists()
    assert (build_dir / "components" / "__folio_components" / "banner.tsx").exists()


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


def test_template_workspace_prepare_rejects_symlinks(tmp_path: Path) -> None:
    template_dir = tmp_path / "template"
    (template_dir / "app").mkdir(parents=True)
    (template_dir / "app" / "page.tsx").write_text("demo", encoding="utf-8")
    secret = tmp_path / "secret.txt"
    secret.write_text("secret", encoding="utf-8")
    (template_dir / "leak.txt").symlink_to(secret)
    build_dir = tmp_path / "build"

    with pytest.raises(ValueError, match="template.path must not contain symlinks"):
        TemplateWorkspace(template_dir, build_dir).prepare()


def test_apply_theme_package_rejects_symlinks(tmp_path: Path) -> None:
    package_dir = tmp_path / "theme-pkg"
    package_dir.mkdir()
    secret = tmp_path / "secret.txt"
    secret.write_text("secret", encoding="utf-8")
    (package_dir / "leak.txt").symlink_to(secret)
    build_dir = tmp_path / "build"
    build_dir.mkdir()

    config = Config(project_name="Demo", theme_package_path=str(package_dir))
    injector = TemplateConfigInjector(config, build_dir)

    with pytest.raises(ValueError, match="theme.package must not contain symlinks"):
        injector._apply_theme_package()


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

    monkeypatch.setattr("folio_docs.docs.next_runtime.subprocess.run", fake_run)

    runtime = NextRuntime(template_dir, build_dir, tmp_path / "out")
    assert runtime.install_deps() is True
    assert calls


def test_preflight_passes_with_modern_toolchain(monkeypatch):
    from folio_docs.docs import next_runtime as nr

    monkeypatch.setattr(nr.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        nr,
        "_tool_version_output",
        lambda cmd: "v22.14.0" if cmd[0] == "node" else "10.28.2",
    )

    nr.preflight_check()  # must not raise


def test_preflight_reports_missing_node_and_pnpm_together(monkeypatch):
    import pytest

    from folio_docs.docs import next_runtime as nr

    monkeypatch.setattr(nr.shutil, "which", lambda name: None)

    with pytest.raises(RuntimeError) as excinfo:
        nr.preflight_check()

    message = str(excinfo.value)
    assert "Node.js was not found" in message
    assert "pnpm was not found" in message
    assert "nodejs.org" in message


def test_preflight_rejects_old_node_version(monkeypatch):
    import pytest

    from folio_docs.docs import next_runtime as nr

    monkeypatch.setattr(nr.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        nr,
        "_tool_version_output",
        lambda cmd: "v18.20.4" if cmd[0] == "node" else "10.28.2",
    )

    with pytest.raises(RuntimeError, match="Node.js v18.20.4 is too old"):
        nr.preflight_check()


def test_preflight_rejects_old_pnpm_version(monkeypatch):
    import pytest

    from folio_docs.docs import next_runtime as nr

    monkeypatch.setattr(nr.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(
        nr,
        "_tool_version_output",
        lambda cmd: "v22.14.0" if cmd[0] == "node" else "9.15.0",
    )

    with pytest.raises(RuntimeError, match="pnpm 9.15.0 is too old"):
        nr.preflight_check()


def test_preflight_tolerates_unparseable_version_output(monkeypatch):
    from folio_docs.docs import next_runtime as nr

    monkeypatch.setattr(nr.shutil, "which", lambda name: f"/usr/bin/{name}")
    monkeypatch.setattr(nr, "_tool_version_output", lambda cmd: "")

    # Unknown version output must not block the build (the real failure
    # will surface with full context at pnpm install time instead).
    nr.preflight_check()
