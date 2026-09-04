from __future__ import annotations

import hashlib
import io
import json
import shutil
from pathlib import Path

import pytest
from folio import __version__
import folio.build as build_module
from folio.build import run_build
from folio.config import Config
from folio.generator.site_builder import SiteBuilder
from folio.parser.markdown_parser import MarkdownResult
from rich.console import Console


# Injection markers the workspace preparation must resolve; none of these should
# survive in the prepared .build tree.
_RESIDUAL_INJECTION_MARKERS = [
    "__PROJECT_NAME__",
    "__PROJECT_DESCRIPTION__",
    "__PROJECT_MONOGRAM__",
    "__PROJECT_REPO__",
    "__PROJECT_REPO_IMPORTS_START__",
    "__PROJECT_REPO_IMPORTS_END__",
    "__PROJECT_REPO_LINK_START__",
    "__PROJECT_REPO_LINK_END__",
    "__PROJECT_HEADER_LOGO_START__",
    "__PROJECT_HEADER_ACTIONS_START__",
    "__SITE_URL__",
    "__VERSIONS__",
    "__CURRENT_VERSION_PATH__",
    "__I18N_CONFIG__",
    "__FOLIO_BASE_PATH__",
    "__FOLIO_DOCS_ROUTE_BASE__",
    "__LANDING_TAGLINE__",
    "__LANDING_SECTIONS__",
    "__LANDING_FEATURES__",
]


_CUSTOM_TEMPLATE_COMPONENTS = [
    "ApiReferenceIndex",
    "Callout",
    "ClassOverview",
    "Mermaid",
    "ParamTable",
    "SourceLink",
    "TabItem",
    "Tabs",
]


def _write_custom_template(
    template_dir: Path,
    *,
    include_mdx_contract: bool = True,
) -> None:
    (template_dir / "app" / "docs" / "[[...mdxPath]]").mkdir(parents=True)
    (template_dir / "content").mkdir()
    (template_dir / "lib").mkdir()
    (template_dir / "public").mkdir()
    (template_dir / "components").mkdir()
    (template_dir / "package.json").write_text(
        '{"scripts":{"build":"next build"}}',
        encoding="utf-8",
    )
    (template_dir / "pnpm-lock.yaml").write_text("lockfile", encoding="utf-8")
    (template_dir / "next.config.mjs").write_text(
        "const configuredBasePath = '' // __FOLIO_BASE_PATH__\n"
        'const nextConfig = { output: "export" }\nexport default nextConfig\n',
        encoding="utf-8",
    )
    if include_mdx_contract:
        component_declarations = "\n".join(
            f"function {name}() {{ return null }}"
            for name in _CUSTOM_TEMPLATE_COMPONENTS
        )
        component_entries = "\n".join(
            f"    {name}," for name in _CUSTOM_TEMPLATE_COMPONENTS
        )
        mdx_components = (
            f"{component_declarations}\n\n"
            "export function useMDXComponents(components = {}) {\n"
            "  return {\n"
            f"{component_entries}\n"
            "    ...components,\n"
            "  }\n"
            "}\n"
        )
    else:
        mdx_components = (
            "export function useMDXComponents(components = {}) { return components }\n"
        )
    (template_dir / "mdx-components.tsx").write_text(
        mdx_components,
        encoding="utf-8",
    )
    (template_dir / "app" / "layout.tsx").write_text(
        "export const metadata = {\n"
        '  title: "__PROJECT_NAME__",\n'
        '  description: "__PROJECT_DESCRIPTION__",\n'
        '  siteUrl: "__SITE_URL__",\n'
        "}\n"
        "export default function RootLayout({ children }) { return children }\n",
        encoding="utf-8",
    )
    (template_dir / "app" / "docs" / "layout.tsx").write_text(
        "// __PROJECT_NAME__ docs layout\n"
        "export default function DocsLayout({ children }) { return children }\n",
        encoding="utf-8",
    )
    (template_dir / "app" / "docs" / "[[...mdxPath]]" / "page.jsx").write_text(
        "// __PROJECT_NAME__ : __PROJECT_DESCRIPTION__\n"
        '// site: "__SITE_URL__"\n'
        '// canonical: "__DOCS_INDEX_CANONICAL_PATH__"\n'
        "export default function DocsPage() { return null }\n",
        encoding="utf-8",
    )
    (template_dir / "content" / "stale.mdx").write_text(
        "# Template demo content\n",
        encoding="utf-8",
    )
    (template_dir / "custom-marker.txt").write_text("custom", encoding="utf-8")


def test_run_build_recreates_missing_page_even_when_manifest_matches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    index_doc = docs_dir / "index.md"
    index_doc.write_text("# Overview\n\nWelcome.")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n'
    )

    build_dir = tmp_path / ".build"
    build_dir.mkdir()
    file_hash = hashlib.sha256(index_doc.read_bytes()).hexdigest()
    (build_dir / ".folio-manifest.json").write_text(
        json.dumps({"sources": {str(index_doc): {"hash": file_hash, "route": "index"}}})
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    generated = build_dir / "content" / "index.mdx"
    assert generated.exists()
    assert "# Overview" in generated.read_text()


def test_run_build_uses_configured_custom_template(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "CustomTemplateDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  path: "docs-template"\n'
        "  params:\n"
        '    navbarVariant: "dense"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, clean=True)

    build_dir = tmp_path / ".build"
    assert (build_dir / "custom-marker.txt").read_text(encoding="utf-8") == "custom"
    assert not (build_dir / "content" / "stale.mdx").exists()
    assert (build_dir / "content" / "index.mdx").exists()
    template_context = (build_dir / "lib" / "folio-template.ts").read_text(
        encoding="utf-8"
    )
    assert "CustomTemplateDemo" in template_context
    assert '"navbarVariant": "dense"' in template_context


def test_prepared_custom_template_workspace_is_coherent(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "CoherentTemplateDemo"\n'
        '  repo: "https://github.com/acme/demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  path: "docs-template"\n'
        "  params:\n"
        '    navbarVariant: "dense"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    # Only the real Next/pnpm steps are mocked; the workspace preparation
    # (copy + injection) runs for real so we can assert on the result.
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, clean=True)

    build_dir = tmp_path / ".build"

    # No residual injection markers anywhere in the prepared tree.
    offenders: list[str] = []
    for path in build_dir.rglob("*"):
        if not path.is_file():
            continue
        if "node_modules" in path.parts:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, ValueError):
            continue
        for marker in _RESIDUAL_INJECTION_MARKERS:
            if marker in text:
                offenders.append(f"{path.relative_to(build_dir)}: {marker}")
    assert offenders == []

    # The Folio template/MDX contract modules are written for the template.
    assert (build_dir / "lib" / "folio-template.ts").exists()
    assert (build_dir / "lib" / "folio-mdx-contract.ts").exists()
    template_context = (build_dir / "lib" / "folio-template.ts").read_text(
        encoding="utf-8"
    )
    assert "CoherentTemplateDemo" in template_context
    assert '"navbarVariant": "dense"' in template_context

    # Custom template content was copied into the workspace.
    assert (build_dir / "custom-marker.txt").read_text(encoding="utf-8") == "custom"
    assert (build_dir / "next.config.mjs").exists()
    assert (build_dir / "mdx-components.tsx").exists()
    # Generated docs content is present; stale template content is not.
    assert (build_dir / "content" / "index.mdx").exists()
    assert not (build_dir / "content" / "stale.mdx").exists()


def test_template_can_consume_folio_template_params(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """template.params survive into .build and parse with the expected fields.

    This pins the consumption contract documented in custom-templates.md: the
    validated params are emitted verbatim into ``lib/folio-template.ts`` as the
    ``folioTemplateParams`` export, so a template can branch on a field.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "ParamsDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  path: "docs-template"\n'
        "  params:\n"
        '    navbarVariant: "dense"\n'
        '    productName: "Acme SDK"\n'
        "    showBetaBadge: true\n"
        "    nested:\n"
        "      depth: 2\n"
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, clean=True)

    template_context = (tmp_path / ".build" / "lib" / "folio-template.ts").read_text(
        encoding="utf-8"
    )

    # The params are emitted as a frozen `as const` object literal. Extract that
    # block and parse it as JSON to prove the values survived intact and a
    # template could branch on them.
    marker = "export const folioTemplateParams = "
    start = template_context.index(marker) + len(marker)
    end = template_context.index(" as const", start)
    params = json.loads(template_context[start:end])

    assert params == {
        "navbarVariant": "dense",
        "productName": "Acme SDK",
        "showBetaBadge": True,
        "nested": {"depth": 2},
    }
    # A template branching on a field reads the expected value.
    assert params["navbarVariant"] == "dense"
    assert params["nested"]["depth"] == 2


def test_run_build_rejects_custom_template_outside_project(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    outside_template = tmp_path.parent / f"{tmp_path.name}-template"
    _write_custom_template(outside_template)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "OutsideTemplateDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        f'  path: "{outside_template}"\n',
        encoding="utf-8",
    )

    try:
        with pytest.raises(ValueError, match="template.path must stay"):
            run_build(tmp_path, clean=True)
    finally:
        shutil.rmtree(outside_template)


def test_run_build_reports_missing_custom_template_files(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs-template").mkdir()
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "IncompleteTemplateDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  path: "docs-template"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing required Next/Nextra files"):
        run_build(tmp_path, clean=True)


def test_run_build_reports_missing_custom_template_mdx_contract(
    tmp_path: Path,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir, include_mdx_contract=False)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "MissingContractDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  path: "docs-template"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="missing Folio MDX contract components"):
        run_build(tmp_path, clean=True)


def test_run_build_reports_missing_required_injection_marker(
    tmp_path: Path,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)
    # Drop a load-bearing marker from a required file so injection would have
    # silently no-op'd; the build must now fail fast and name the file + marker.
    layout_path = template_dir / "app" / "layout.tsx"
    layout_path.write_text(
        layout_path.read_text(encoding="utf-8").replace("__SITE_URL__", ""),
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "MissingMarkerDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  path: "docs-template"\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=r"missing required Folio injection markers: __SITE_URL__ in app/layout.tsx",
    ):
        run_build(tmp_path, clean=True)


def test_validate_template_marker_contract_collects_all_missing(
    tmp_path: Path,
) -> None:
    from folio.generator.template_workspace import validate_template_marker_contract

    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)
    # Remove a marker from one required file and delete another required file
    # entirely; both failures must be reported in a single pass.
    layout_path = template_dir / "app" / "layout.tsx"
    layout_path.write_text(
        layout_path.read_text(encoding="utf-8").replace("__PROJECT_DESCRIPTION__", ""),
        encoding="utf-8",
    )
    (template_dir / "next.config.mjs").unlink()

    missing = validate_template_marker_contract(template_dir)

    assert ("app/layout.tsx", "__PROJECT_DESCRIPTION__") in missing
    assert (
        "next.config.mjs",
        "const configuredBasePath = '' // __FOLIO_BASE_PATH__",
    ) in missing


def test_validate_template_marker_contract_accepts_bundled_template() -> None:
    from folio.generator.template_workspace import validate_template_marker_contract

    template_dir = build_module._find_template_dir()
    assert validate_template_marker_contract(template_dir) == []


def test_resolve_template_dir_rejects_path_inside_build(tmp_path: Path) -> None:
    template_dir = tmp_path / ".build" / "docs-template"
    template_dir.mkdir(parents=True)
    config = Config(
        project_name="Demo",
        template_path=str(template_dir),
        output_dir=str(tmp_path / "_site"),
    )

    with pytest.raises(
        ValueError, match="template.path cannot point inside the .build directory"
    ):
        build_module._resolve_template_dir(tmp_path, config)


def test_resolve_template_dir_rejects_path_inside_output_dir(tmp_path: Path) -> None:
    output_dir = tmp_path / "_site"
    template_dir = output_dir / "docs-template"
    template_dir.mkdir(parents=True)
    config = Config(
        project_name="Demo",
        template_path=str(template_dir),
        output_dir=str(output_dir),
    )

    with pytest.raises(
        ValueError, match="template.path cannot point inside the output directory"
    ):
        build_module._resolve_template_dir(tmp_path, config)


def test_resolve_template_dir_consumes_resolve_paths_output(tmp_path: Path) -> None:
    """Config.resolve_paths owns absolutization; _resolve_template_dir consumes it.

    resolve_paths turns the relative ``template.path`` into an absolute path, and
    _resolve_template_dir accepts that absolute path verbatim (it no longer
    re-resolves relative paths itself). This pins the single-owner contract.
    """
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)
    config = Config(
        project_name="Demo",
        template_path="docs-template",
        output_dir="_site",
    )

    resolved = config.resolve_paths(tmp_path)
    assert resolved.template_path == str(tmp_path / "docs-template")

    assert (
        build_module._resolve_template_dir(tmp_path, resolved) == template_dir.resolve()
    )


def test_resolve_template_dir_reports_missing_path(tmp_path: Path) -> None:
    template_dir = tmp_path / "does-not-exist"
    config = Config(
        project_name="Demo",
        template_path=str(template_dir),
        output_dir=str(tmp_path / "_site"),
    )

    with pytest.raises(
        FileNotFoundError, match=r"template.path does not exist: .*does-not-exist"
    ):
        build_module._resolve_template_dir(tmp_path, config)


def test_resolve_template_dir_bundled_template_passes_drift_guard(
    tmp_path: Path,
) -> None:
    config = Config(project_name="Demo", output_dir=str(tmp_path / "_site"))

    assert (
        build_module._resolve_template_dir(tmp_path, config)
        == build_module._find_template_dir()
    )


def test_resolve_template_dir_fails_on_unknown_bundled_template_entry(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A component wired into the bundled template but absent from the builtin
    manifest must fail the build instead of silently shadowing plugins."""
    real_dir = build_module._find_template_dir()
    fake_dir = tmp_path / "bundled-template"
    fake_dir.mkdir()
    content = (real_dir / "mdx-components.tsx").read_text(encoding="utf-8")
    (fake_dir / "mdx-components.tsx").write_text(
        content.replace("    ...components,", "    RogueWidget,\n    ...components,"),
        encoding="utf-8",
    )
    monkeypatch.setattr(build_module, "_find_template_dir", lambda: fake_dir)
    config = Config(project_name="Demo", output_dir=str(tmp_path / "_site"))

    with pytest.raises(ValueError, match="RogueWidget"):
        build_module._resolve_template_dir(tmp_path, config)


def test_resolve_template_dir_fails_when_builtin_missing_from_bundled_template(
    tmp_path: Path,
    monkeypatch,
) -> None:
    real_dir = build_module._find_template_dir()
    fake_dir = tmp_path / "bundled-template"
    fake_dir.mkdir()
    content = (real_dir / "mdx-components.tsx").read_text(encoding="utf-8")
    (fake_dir / "mdx-components.tsx").write_text(
        content.replace("    ParamTable,\n", ""), encoding="utf-8"
    )
    monkeypatch.setattr(build_module, "_find_template_dir", lambda: fake_dir)
    config = Config(project_name="Demo", output_dir=str(tmp_path / "_site"))

    with pytest.raises(ValueError, match="ParamTable"):
        build_module._resolve_template_dir(tmp_path, config)


def test_run_build_template_overlay_overrides_single_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """An overlay providing ONE component overrides only that file.

    The remaining files come from the bundled template, proving the opt-in
    layered overlay falls back to the bundled template for anything the user did
    not provide.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")

    overlay_dir = tmp_path / "overlay"
    (overlay_dir / "components").mkdir(parents=True)
    sentinel = "// FOLIO_OVERLAY_SENTINEL custom Callout\n"
    (overlay_dir / "components" / "callout.tsx").write_text(
        sentinel + "export function Callout() { return null }\n",
        encoding="utf-8",
    )

    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "OverlayDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  overlay_path: "overlay"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, clean=True)

    build_dir = tmp_path / ".build"
    bundled = build_module._find_template_dir()

    # The overridden file is the user's version.
    overridden = (build_dir / "components" / "callout.tsx").read_text(encoding="utf-8")
    assert "FOLIO_OVERLAY_SENTINEL" in overridden

    # A file the overlay did not provide falls back to the bundled template
    # verbatim (the injector does not touch param-table.tsx).
    param_table = (build_dir / "components" / "param-table.tsx").read_text(
        encoding="utf-8"
    )
    assert param_table == (bundled / "components" / "param-table.tsx").read_text(
        encoding="utf-8"
    )
    assert "FOLIO_OVERLAY_SENTINEL" not in param_table

    # Normal injection still ran on the merged template.
    assert (build_dir / "content" / "index.mdx").exists()
    template_context = (build_dir / "lib" / "folio-template.ts").read_text(
        encoding="utf-8"
    )
    assert "OverlayDemo" in template_context


def test_run_build_template_overlay_rejects_path_outside_project(
    tmp_path: Path,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    outside_overlay = tmp_path.parent / f"{tmp_path.name}-overlay"
    (outside_overlay / "components").mkdir(parents=True)
    (outside_overlay / "components" / "callout.tsx").write_text("x", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "OutsideOverlayDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        f'  overlay_path: "{outside_overlay}"\n',
        encoding="utf-8",
    )

    try:
        with pytest.raises(
            ValueError, match="template.overlay_path must stay within the project"
        ):
            run_build(tmp_path, clean=True)
    finally:
        shutil.rmtree(outside_overlay)


def test_run_build_template_overlay_rejects_symlinks(
    tmp_path: Path,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")

    secret = tmp_path / "secret.txt"
    secret.write_text("top secret", encoding="utf-8")
    overlay_dir = tmp_path / "overlay"
    (overlay_dir / "components").mkdir(parents=True)
    (overlay_dir / "components" / "leak.txt").symlink_to(secret)

    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "SymlinkOverlayDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  overlay_path: "overlay"\n',
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError, match="template.overlay_path must not contain symlinks"
    ):
        run_build(tmp_path, clean=True)


def test_run_build_keeps_llm_files_after_static_export(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "llm:\n"
        "  generate_llms_txt: true\n"
        "  generate_llms_full_txt: true\n"
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)

    def fake_static_export(builder: SiteBuilder, **kwargs) -> None:
        if builder.output_dir.exists():
            shutil.rmtree(builder.output_dir)
        builder.output_dir.mkdir(parents=True)
        (builder.output_dir / "index.html").write_text("ok")

    monkeypatch.setattr(SiteBuilder, "build", fake_static_export)

    run_build(tmp_path)

    assert (tmp_path / "_site" / "llms.txt").exists()
    assert (tmp_path / "_site" / "llms-full.txt").exists()


def test_run_build_serve_writes_llm_files_to_public(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "llm:\n"
        "  generate_llms_txt: true\n"
        "  generate_llms_full_txt: true\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(build_module, "_start_dev_server", lambda **kwargs: None)

    run_build(tmp_path, serve=True)

    public_dir = tmp_path / ".build" / "public"
    assert (public_dir / "llms.txt").exists()
    assert (public_dir / "llms-full.txt").exists()
    assert not (tmp_path / "_site" / "llms.txt").exists()


def test_run_build_respects_individual_llm_flags(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "llm:\n"
        "  generate_llms_txt: true\n"
        "  generate_llms_full_txt: false\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)

    def fake_static_export(builder: SiteBuilder, **kwargs) -> None:
        if builder.output_dir.exists():
            shutil.rmtree(builder.output_dir)
        builder.output_dir.mkdir(parents=True)
        (builder.output_dir / "index.html").write_text("ok")

    monkeypatch.setattr(SiteBuilder, "build", fake_static_export)

    run_build(tmp_path)

    assert (tmp_path / "_site" / "llms.txt").exists()
    assert not (tmp_path / "_site" / "llms-full.txt").exists()


def test_check_generated_links_does_not_treat_disabled_docs_as_valid(
    tmp_path: Path,
) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "index.mdx").write_text(
        "# Overview\n\n[Versioning](./versioning)\n",
        encoding="utf-8",
    )

    docs = [
        MarkdownResult(content="# Overview", frontmatter={}, route="index"),
        MarkdownResult(content="# Versioning", frontmatter={}, route="versioning"),
    ]

    class FakeBuilder:
        # emitted_routes is part of the AssetBuilder protocol and the link
        # checker calls it directly.
        def emitted_routes(self) -> set[str]:
            return set()

    builder = FakeBuilder()
    builder.build_dir = tmp_path
    builder.content_dir = content_dir

    broken = build_module._check_generated_links(builder, [], docs)

    assert len(broken) == 1
    assert broken[0].source_page == "index"
    assert broken[0].target == "./versioning"


def test_run_build_banner_uses_folio_version(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  version: "9.9.9"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    monkeypatch.setattr(build_module, "_start_dev_server", lambda **kwargs: None)

    run_build(tmp_path, serve=True)

    output = capsys.readouterr().out
    assert f"v{__version__}" in output
    assert "v9.9.9" not in output


def test_run_build_serve_banner_omits_news_line(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    monkeypatch.setattr(build_module, "_start_dev_server", lambda **kwargs: None)

    run_build(tmp_path, serve=True)

    output = capsys.readouterr().out
    assert "⚡" not in output


def test_print_banner_without_news_leaves_trailing_spacer(monkeypatch) -> None:
    buffer = io.StringIO()
    test_console = Console(file=buffer, width=80, color_system=None)
    monkeypatch.setattr(build_module, "console", test_console)

    build_module._print_banner(None, include_news=False)

    assert buffer.getvalue().endswith("\n\n")


def test_print_banner_with_news_leaves_trailing_spacer(monkeypatch) -> None:
    buffer = io.StringIO()
    test_console = Console(file=buffer, width=80, color_system=None)
    monkeypatch.setattr(build_module, "console", test_console)

    build_module._print_banner(None, include_news=True)

    assert "·" in buffer.getvalue()
    assert buffer.getvalue().endswith("\n\n")


def test_run_build_serve_banner_keeps_spacing_after_logo(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    monkeypatch.setattr(build_module, "_start_dev_server", lambda **kwargs: None)

    run_build(tmp_path, serve=True)

    output = capsys.readouterr().out
    lines = output.splitlines()
    logo_version_line = next(
        index for index, line in enumerate(lines) if f"v{__version__}" in line
    )

    assert lines[logo_version_line + 1 : logo_version_line + 3] == ["", ""]


def test_run_build_banner_omits_news_line_and_keeps_spacing_after_logo(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    output = capsys.readouterr().out
    lines = output.splitlines()
    logo_version_line = next(
        index for index, line in enumerate(lines) if f"v{__version__}" in line
    )

    assert "⚡" not in output
    assert lines[logo_version_line + 1 : logo_version_line + 3] == ["", ""]


def test_run_build_serve_prints_structured_done_step(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    test_console = Console(record=True, width=80, color_system=None)

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    monkeypatch.setattr(build_module, "_start_dev_server", lambda **kwargs: None)

    run_build(tmp_path, serve=True)

    output = test_console.export_text()

    assert "✓ Done" in output
    assert "Export" not in output
    assert "06  Done" not in output
    assert "07  Done" not in output
    assert "Build complete" not in output


def test_step_description_omits_number_and_left_margin() -> None:
    description = build_module._step_description("Export", "building static site")

    assert "06" not in description
    assert description.startswith("[bold cyan]Export")
    assert "›" in description
    assert "building static site" in description


def test_export_step_detail_omits_full_log_toggle() -> None:
    assert build_module._export_step_detail() == "building static site"


def test_build_output_stream_records_lines_without_live_repaint(monkeypatch) -> None:
    class FakeLive:
        def __init__(self, *args, **kwargs) -> None:
            raise AssertionError("build output should not use a live repainting panel")

    monkeypatch.setattr(build_module, "Live", FakeLive, raising=False)

    stream = build_module._BuildOutputStream()
    with stream:
        stream.record("Creating an optimized production build ...\n")
        stream.record("Compiled successfully\n")

    assert stream.lines == [
        "Creating an optimized production build ...\n",
        "Compiled successfully\n",
    ]


def test_pages_progress_starts_before_meta_pages(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    state = {"pages_active": False, "meta_called": False}

    class TrackingProgress:
        console = Console(file=io.StringIO(), color_system=None)

        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self) -> "TrackingProgress":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            state["pages_active"] = False

        def add_task(self, description: str, total=None) -> int:
            if "Pages" in description:
                state["pages_active"] = True
            return 1

        def advance(self, task_id: int) -> None:
            pass

        def update(self, task_id: int, **kwargs) -> None:
            pass

    def fake_write_meta_pages(*args, **kwargs) -> None:
        state["meta_called"] = True
        assert state["pages_active"]

    monkeypatch.setattr(build_module, "Progress", TrackingProgress)
    monkeypatch.setattr(build_module, "_write_meta_pages", fake_write_meta_pages)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    assert state["meta_called"]


def test_run_build_shows_progress_for_post_page_work(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "examples").mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    test_console = Console(record=True, width=100, color_system=None)

    state = {
        "active": "",
        "preview_called": False,
        "links_called": False,
    }
    descriptions: list[str] = []

    class TrackingProgress:
        console = Console(file=io.StringIO(), color_system=None)

        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self) -> "TrackingProgress":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            state["active"] = ""

        def add_task(self, description: str, total=None) -> int:
            state["active"] = description
            descriptions.append(description)
            return 1

        def advance(self, task_id: int) -> None:
            pass

        def update(self, task_id: int, **kwargs) -> None:
            pass

    def fake_write_preview_examples(self: SiteBuilder, examples_dir: Path) -> None:
        state["preview_called"] = True
        assert "Previews" in state["active"]

    def fake_check_generated_links(*args, **kwargs) -> list:
        state["links_called"] = True
        assert "Links" in state["active"]
        return []

    monkeypatch.setattr(build_module, "Progress", TrackingProgress)
    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(
        SiteBuilder, "write_preview_examples", fake_write_preview_examples
    )
    monkeypatch.setattr(
        build_module, "_check_generated_links", fake_check_generated_links
    )
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    output = test_console.export_text()

    assert state["preview_called"]
    assert state["links_called"]
    assert any("Finalize" in description for description in descriptions)
    assert any("Previews" in description for description in descriptions)
    assert any("Links" in description for description in descriptions)
    assert "✓ Previews" in output


def test_run_build_prints_structured_steps(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    test_console = Console(record=True, width=100, color_system=None)

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)

    def fake_build(self: SiteBuilder, **kwargs) -> None:
        assert kwargs["log_path"].name == ".folio-build.log"
        assert callable(kwargs["output_callback"])
        kwargs["output_callback"]("Creating an optimized production build ...\n")
        kwargs["output_callback"]("Compiled successfully\n")

    monkeypatch.setattr(SiteBuilder, "build", fake_build)

    run_build(tmp_path)

    output = test_console.export_text()
    expected_steps = [
        "✓ Sources",
        "✓ Template",
        "✓ Pages",
        "✓ Links",
        "✓ Dependencies",
        "✓ Export",
        "Build output",
        "✓ Done",
        "✓ Site ready",
    ]
    positions = [output.index(step) for step in expected_steps]

    assert positions == sorted(positions)
    assert "  ✓ Sources" not in output
    assert "01  Sources" not in output
    assert "06  Export" not in output
    assert "Build complete" not in output
    assert "Static site ready at" not in output
    assert "Build output" in output
    assert output.count("Build output") == 1
    assert "Creating an optimized production build ..." in output
    assert "Compiled successfully" in output
    assert "Ctrl+O" not in output
    assert "Site export completed" in output
    assert "Next.js build completed" not in output
    assert "ready in" not in output
    assert "page in" in output
    assert "_site/" in output


def test_run_build_prints_rst_warning_as_structured_step(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (docs_dir / "legacy.rst").write_text("Legacy docs\n===========\n", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    test_console = Console(record=True, width=100, color_system=None)

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    captured = capsys.readouterr()
    output = test_console.export_text()

    assert "✓ Sources" in output
    assert "01  Sources" not in output
    assert "source.docs supports Markdown build inputs only" in output
    assert "UserWarning" not in captured.err


def test_run_build_preview_examples_do_not_print_nested_banners(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    example_docs = tmp_path / "docs" / "examples" / "sample" / "docs"
    example_docs.mkdir(parents=True)
    (example_docs / "index.md").write_text("# Example\n\nPreview.", encoding="utf-8")
    (example_docs.parent / "docs.yaml").write_text(
        'project:\n  name: "Sample"\nsource:\n  docs:\n    - "docs/"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    buffer = io.StringIO()
    test_console = Console(
        file=buffer,
        force_terminal=True,
        width=100,
        color_system=None,
    )

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    output = buffer.getvalue()

    assert output.count(f"v{__version__}") == 1
    assert (tmp_path / ".build" / "public" / "_folio" / "examples" / "sample").exists()


def test_run_build_quiet_suppresses_tty_output(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )
    buffer = io.StringIO()
    test_console = Console(
        file=buffer,
        force_terminal=True,
        width=100,
        color_system=None,
    )

    monkeypatch.setattr(build_module, "console", test_console)
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, quiet=True)

    assert buffer.getvalue() == ""
    assert (tmp_path / ".build" / "content" / "index.mdx").exists()


def test_run_build_regenerates_source_pages_when_config_changes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package_dir = tmp_path / "demo"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "core.py").write_text(
        'def hello() -> str:\n    """Return a greeting."""\n    return "hello"\n',
        encoding="utf-8",
    )
    config_path = tmp_path / "docs.yaml"
    config_path.write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  repo: "https://github.com/acme/old"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "demo/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    generated = tmp_path / ".build" / "content" / "api-reference" / "demo" / "core.mdx"
    assert "https://github.com/acme/old/blob/main/demo/core.py" in generated.read_text()

    config_path.write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  repo: "https://github.com/acme/new"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "demo/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    run_build(tmp_path)

    content = generated.read_text()
    assert "https://github.com/acme/new/blob/main/demo/core.py" in content
    assert "https://github.com/acme/old/blob/main/demo/core.py" not in content


def test_run_build_uses_configured_source_ref_for_source_links(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package_dir = tmp_path / "demo"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "core.py").write_text(
        'def hello() -> str:\n    """Return a greeting."""\n    return "hello"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  repo: "https://github.com/acme/demo"\n'
        '  repo_ref: "release/2.x"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "demo/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)

    generated = tmp_path / ".build" / "content" / "api-reference" / "demo" / "core.mdx"
    content = generated.read_text()
    assert "https://github.com/acme/demo/blob/release/2.x/demo/core.py" in content
    assert "/blob/main/" not in content


def test_run_build_source_ref_override_wins_for_source_links(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package_dir = tmp_path / "demo"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "core.py").write_text(
        'def hello() -> str:\n    """Return a greeting."""\n    return "hello"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        '  repo: "https://github.com/acme/demo"\n'
        '  repo_ref: "main"\n'
        "source:\n"
        "  python:\n"
        "    paths:\n"
        '      - "demo/"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, source_ref_override="v0.1.0")

    generated = tmp_path / ".build" / "content" / "api-reference" / "demo" / "core.mdx"
    content = generated.read_text()
    assert "https://github.com/acme/demo/blob/v0.1.0/demo/core.py" in content
    assert "/blob/main/" not in content


def test_run_build_omits_version_metadata_by_default(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "Demo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        'output: "_site"\n'
        "versions:\n"
        '  - label: "latest"\n'
        '    path: "latest"\n'
        '  - label: "v0.1"\n'
        '    path: "v0.1"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)
    run_build(tmp_path)

    output = capsys.readouterr().out
    assert "Current version only" not in output

    selector = tmp_path / ".build" / "components" / "version-selector.tsx"
    content = selector.read_text(encoding="utf-8")
    assert "const versions: Version[] = []" in content
    assert 'const configuredCurrentPath: string = ""' in content
    assert "latest" not in content
    assert "v0.1" not in content


def test_warm_rebuild_prunes_orphan_after_template_file_removed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Removing a file from template.path prunes its orphan on a warm rebuild.

    prepare() overlays the template with copytree(dirs_exist_ok=True) and never
    removes vanished files. A warm rebuild (no --clean) must detect the changed
    template signature and drop the orphan, while preserving the expensive
    node_modules/.next dirs and the generated content/ tree.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)
    orphan = template_dir / "orphan-marker.txt"
    orphan.write_text("orphan", encoding="utf-8")
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "OrphanDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  path: "docs-template"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    # First warm build produces .build/ containing the orphan.
    run_build(tmp_path)
    build_dir = tmp_path / ".build"
    assert (build_dir / "orphan-marker.txt").read_text(encoding="utf-8") == "orphan"

    # Seed the preserved-entry sentinels so we can prove the scoped prune keeps
    # node_modules/.next/content instead of nuking the whole tree.
    (build_dir / "node_modules").mkdir(exist_ok=True)
    (build_dir / "node_modules" / "keep.txt").write_text("dep", encoding="utf-8")
    (build_dir / ".next").mkdir(exist_ok=True)
    (build_dir / ".next" / "keep.txt").write_text("cache", encoding="utf-8")
    content_sentinel = build_dir / "content" / "index.mdx"
    assert content_sentinel.exists()

    # Remove the file from the template source, then warm rebuild.
    orphan.unlink()
    run_build(tmp_path)

    # The orphan is gone; the preserved entries survive.
    assert not (build_dir / "orphan-marker.txt").exists()
    assert (build_dir / "node_modules" / "keep.txt").read_text(
        encoding="utf-8"
    ) == "dep"
    assert (build_dir / ".next" / "keep.txt").read_text(encoding="utf-8") == "cache"
    assert content_sentinel.exists()
    # A file still in the template remains present.
    assert (build_dir / "custom-marker.txt").read_text(encoding="utf-8") == "custom"


def test_warm_rebuild_unchanged_template_does_not_wipe_build(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """An unchanged template signature must not trigger a scoped clean.

    A hand-placed sentinel under .build/ (outside the preserved set) survives a
    warm rebuild, proving warm builds stay incremental and do not pay a needless
    full clean.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "StableDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  path: "docs-template"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)
    build_dir = tmp_path / ".build"

    # A sentinel outside the preserved set that no template/theme input touches.
    sentinel = build_dir / "warm-sentinel.txt"
    sentinel.write_text("survives", encoding="utf-8")

    run_build(tmp_path)

    assert sentinel.read_text(encoding="utf-8") == "survives"


def test_warm_rebuild_prunes_when_theme_package_changes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Removing a file from theme.package prunes its orphan on a warm rebuild.

    theme.package is overlaid with copytree(dirs_exist_ok=True) just like the
    template, so a changed theme signature must trigger the same scoped prune.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")

    theme_dir = tmp_path / "my-theme"
    (theme_dir / "components").mkdir(parents=True)
    (theme_dir / "components" / "theme-widget.tsx").write_text(
        "export function ThemeWidget() { return null }\n",
        encoding="utf-8",
    )
    theme_orphan = theme_dir / "theme-orphan.txt"
    theme_orphan.write_text("theme-orphan", encoding="utf-8")

    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "ThemePruneDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "theme:\n"
        '  package: "my-theme"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path)
    build_dir = tmp_path / ".build"
    assert (build_dir / "theme-orphan.txt").read_text(
        encoding="utf-8"
    ) == "theme-orphan"

    theme_orphan.unlink()
    run_build(tmp_path)

    assert not (build_dir / "theme-orphan.txt").exists()
    # A theme file that is still present remains copied in.
    assert (build_dir / "components" / "theme-widget.tsx").exists()


def test_warm_rebuild_nested_docs_route_base_does_not_nest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Warm rebuilds with a route base nested under /docs must stay idempotent.

    With docs_route_base like /docs/v2 the relocation target lives inside the
    relocation source (app/docs). A second warm build re-merges the template's
    app/docs over the .build tree that still holds the previously relocated
    v2/ dir; without residue cleanup the relocation would nest one level deeper
    on every warm rebuild (app/docs/v2/v2/...).
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)
    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "NestedRouteDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  path: "docs-template"\n'
        '  docs_route_base: "/docs/v2"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    build_dir = tmp_path / ".build"
    relocated_page = build_dir / "app" / "docs" / "v2" / "[[...mdxPath]]" / "page.jsx"

    run_build(tmp_path)
    assert relocated_page.exists()

    # Two further warm builds into the same .build/: the relocated route stays
    # at app/docs/v2 and no nested app/docs/v2/v2 residue ever appears.
    for _ in range(2):
        run_build(tmp_path)
        assert relocated_page.exists()
        assert not (build_dir / "app" / "docs" / "v2" / "v2").exists()
        assert not (build_dir / "app" / "docs" / "[[...mdxPath]]").exists()


def test_warm_rebuild_removes_previous_route_dir_when_route_base_changes(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Changing docs_route_base between warm builds unpublishes the old route.

    The previously relocated route dir is not overwritten by prepare (which
    only re-copies app/docs), so the build must remove it explicitly or the old
    URL stays published alongside the new one.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    template_dir = tmp_path / "docs-template"
    _write_custom_template(template_dir)

    def write_config(route_base: str) -> None:
        (tmp_path / "docs.yaml").write_text(
            "project:\n"
            '  name: "RouteChangeDemo"\n'
            "source:\n"
            "  docs:\n"
            '    - "docs/"\n'
            "template:\n"
            '  path: "docs-template"\n'
            f'  docs_route_base: "{route_base}"\n'
            'output: "_site"\n',
            encoding="utf-8",
        )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    build_dir = tmp_path / ".build"

    write_config("/guide")
    run_build(tmp_path)
    assert (build_dir / "app" / "guide" / "[[...mdxPath]]" / "page.jsx").exists()
    assert not (build_dir / "app" / "docs").exists()

    write_config("/reference/docs")
    run_build(tmp_path)

    # The old relocated dir is gone; the new route dir is fully populated.
    assert not (build_dir / "app" / "guide").exists()
    assert (
        build_dir / "app" / "reference" / "docs" / "[[...mdxPath]]" / "page.jsx"
    ).exists()

    # Changing back also drops app/reference (including the now-empty parent).
    write_config("/guide")
    run_build(tmp_path)
    assert not (build_dir / "app" / "reference").exists()
    assert (build_dir / "app" / "guide" / "[[...mdxPath]]" / "page.jsx").exists()


def test_run_build_template_overlay_rejects_overlay_inside_staging_dir(
    tmp_path: Path,
) -> None:
    """template.overlay_path may not live inside the recreated staging dir.

    The staging dir (.build-template) is deleted and rebuilt on every overlay
    build; an overlay stored inside it would be destroyed before it is read.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")

    overlay_dir = tmp_path / ".build-template" / "overlay"
    (overlay_dir / "components").mkdir(parents=True)
    (overlay_dir / "components" / "callout.tsx").write_text(
        "export function Callout() { return null }\n", encoding="utf-8"
    )

    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "StagingOverlayDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  overlay_path: ".build-template/overlay"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="cannot point inside the template staging"):
        run_build(tmp_path, clean=True)

    # The user's overlay data survives the failed build.
    assert (overlay_dir / "components" / "callout.tsx").exists()


def test_run_build_refuses_to_delete_unmarked_staging_dir(
    tmp_path: Path,
) -> None:
    """A pre-existing .build-template not created by Folio is never rmtree'd.

    Only staging dirs carrying the Folio staging marker file may be deleted;
    anything else is user data and the build must fail with guidance instead.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")

    overlay_dir = tmp_path / "overlay"
    (overlay_dir / "components").mkdir(parents=True)
    (overlay_dir / "components" / "callout.tsx").write_text(
        "export function Callout() { return null }\n", encoding="utf-8"
    )

    # User data at the staging path, without the Folio marker.
    staging_dir = tmp_path / ".build-template"
    staging_dir.mkdir()
    user_file = staging_dir / "precious.txt"
    user_file.write_text("user data", encoding="utf-8")

    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "UnmarkedStagingDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  overlay_path: "overlay"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="not created by Folio"):
        run_build(tmp_path, clean=True)

    assert user_file.read_text(encoding="utf-8") == "user data"


def test_run_build_template_overlay_recreates_marked_staging_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A staging dir created by a previous Folio build is safely recreated."""
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")

    overlay_dir = tmp_path / "overlay"
    (overlay_dir / "components").mkdir(parents=True)
    (overlay_dir / "components" / "callout.tsx").write_text(
        "export function Callout() { return null }\n", encoding="utf-8"
    )

    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "MarkedStagingDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  overlay_path: "overlay"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, clean=True)
    staging_dir = tmp_path / ".build-template"
    assert (staging_dir / ".folio-staging").exists()

    # Second build finds the marked staging dir and rebuilds it without error.
    run_build(tmp_path, clean=True)
    assert (staging_dir / ".folio-staging").exists()
    assert (tmp_path / ".build" / "content" / "index.mdx").exists()
    # The marker is a staging-dir implementation detail; it never propagates
    # into the build workspace.
    assert not (tmp_path / ".build" / ".folio-staging").exists()


def test_materialize_overlay_marker_survives_interrupted_copy(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """An interrupted bundled copy must not brick subsequent overlay builds.

    The staging marker is written before the bundled copytree, so a staging
    dir left behind by a Ctrl-C or disk-full during the copy still carries the
    marker and the next build can safely delete and rebuild it.
    """
    bundled_dir = tmp_path / "bundled"
    bundled_dir.mkdir()
    (bundled_dir / "bundled.txt").write_text("bundled", encoding="utf-8")

    overlay_dir = tmp_path / "overlay"
    overlay_dir.mkdir()
    (overlay_dir / "overlay.txt").write_text("overlay", encoding="utf-8")

    staging_dir = tmp_path / ".build-template"

    real_copytree = shutil.copytree
    calls = {"count": 0}

    def interrupted_copytree(src, dst, **kwargs):
        calls["count"] += 1
        if calls["count"] == 1:
            raise KeyboardInterrupt
        return real_copytree(src, dst, **kwargs)

    monkeypatch.setattr(shutil, "copytree", interrupted_copytree)

    with pytest.raises(KeyboardInterrupt):
        build_module._materialize_overlay_template(
            bundled_dir, overlay_dir, staging_dir
        )

    # The partially-built staging dir is already marked as Folio-owned...
    assert (staging_dir / ".folio-staging").exists()

    # ...so the retry rebuilds it instead of refusing with the marker error.
    merged = build_module._materialize_overlay_template(
        bundled_dir, overlay_dir, staging_dir
    )
    assert merged == staging_dir
    assert (staging_dir / "bundled.txt").read_text(encoding="utf-8") == "bundled"
    assert (staging_dir / "overlay.txt").read_text(encoding="utf-8") == "overlay"
    assert (staging_dir / ".folio-staging").exists()


def test_run_build_overlay_content_symlink_is_never_copied(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """A symlink under the overlay's content/ is neither copied nor fatal.

    content/ is excluded from both the symlink scan and the copy (the scan and
    copy share one ignore list), so a symlink there can never be dereferenced
    into the staging dir or the published site.
    """
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")

    secret = tmp_path / "secret.txt"
    secret.write_text("top secret", encoding="utf-8")
    overlay_dir = tmp_path / "overlay"
    (overlay_dir / "content").mkdir(parents=True)
    (overlay_dir / "content" / "leak.txt").symlink_to(secret)
    (overlay_dir / "components").mkdir()
    (overlay_dir / "components" / "callout.tsx").write_text(
        "export function Callout() { return null }\n", encoding="utf-8"
    )

    (tmp_path / "docs.yaml").write_text(
        "project:\n"
        '  name: "ContentSymlinkDemo"\n'
        "source:\n"
        "  docs:\n"
        '    - "docs/"\n'
        "template:\n"
        '  overlay_path: "overlay"\n'
        'output: "_site"\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(SiteBuilder, "build", lambda self, **kwargs: None)

    run_build(tmp_path, clean=True)

    staging_dir = tmp_path / ".build-template"
    assert not (staging_dir / "content" / "leak.txt").exists()
    assert not (tmp_path / ".build" / "content" / "leak.txt").exists()


def test_run_build_serve_writes_doc_preview_examples(
    tmp_path: Path,
    monkeypatch,
) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "index.md").write_text("# Overview\n\nWelcome.", encoding="utf-8")
    example_dir = tmp_path / "docs" / "examples" / "sample"
    example_dir.mkdir(parents=True)
    (example_dir / "docs.yaml").write_text(
        'project:\n  name: "Sample"\nsource:\n  docs:\n    - "docs/"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs.yaml").write_text(
        'project:\n  name: "Demo"\nsource:\n  docs:\n    - "docs/"\noutput: "_site"\n',
        encoding="utf-8",
    )

    preview_calls: list[Path] = []
    monkeypatch.setattr(SiteBuilder, "install_deps", lambda self: False)
    monkeypatch.setattr(
        SiteBuilder,
        "write_preview_examples",
        lambda self, examples_dir: preview_calls.append(Path(examples_dir)),
    )
    monkeypatch.setattr(
        build_module,
        "_start_dev_server",
        lambda **kwargs: None,
    )

    run_build(tmp_path, serve=True)

    assert preview_calls == [tmp_path / "docs" / "examples"]


def test_build_registry_includes_builtins() -> None:
    from folio.build import build_registry
    from folio.config import Config
    from folio.plugin import PluginManager

    pm = PluginManager()
    resolved = Config(project_name="Demo")

    registry = build_registry(pm, resolved)

    assert "Callout" in registry.components
    assert "ParamTable" in registry.components
    # Builtins register first, before config components and plugin hooks.
    assert list(registry.components)[0] == "ParamTable"


def test_check_generated_links_includes_plugin_emitted_routes(tmp_path: Path) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "index.mdx").write_text(
        "# Overview\n\n[HTTP API](./api-reference/http)\n",
        encoding="utf-8",
    )
    docs = [MarkdownResult(content="# Overview", frontmatter={}, route="index")]

    class FakeBuilder:
        def emitted_routes(self) -> set[str]:
            return {"api-reference/http"}

    builder = FakeBuilder()
    builder.build_dir = tmp_path
    builder.content_dir = content_dir

    broken = build_module._check_generated_links(builder, [], docs)
    assert broken == []


def test_check_generated_links_flags_link_to_unemitted_plugin_route(
    tmp_path: Path,
) -> None:
    content_dir = tmp_path / "content"
    content_dir.mkdir()
    (content_dir / "index.mdx").write_text(
        "# Overview\n\n[Missing](./api-reference/missing)\n",
        encoding="utf-8",
    )
    docs = [MarkdownResult(content="# Overview", frontmatter={}, route="index")]

    class FakeBuilder:
        def emitted_routes(self) -> set[str]:
            return set()

    builder = FakeBuilder()
    builder.build_dir = tmp_path
    builder.content_dir = content_dir

    broken = build_module._check_generated_links(builder, [], docs)
    assert len(broken) == 1
    assert broken[0].target == "./api-reference/missing"


def test_check_generated_links_includes_emitted_static_assets(tmp_path: Path) -> None:
    build_dir = tmp_path / ".build"
    content_dir = build_dir / "content"
    content_dir.mkdir(parents=True)
    (content_dir / "index.mdx").write_text(
        "# Overview\n\n[Prototype](/_folio/kanban/demo/prototype.html)\n",
        encoding="utf-8",
    )
    asset = build_dir / "public" / "_folio" / "kanban" / "demo" / "prototype.html"
    asset.parent.mkdir(parents=True)
    asset.write_text("<!doctype html>", encoding="utf-8")
    docs = [MarkdownResult(content="# Overview", frontmatter={}, route="index")]

    class FakeBuilder:
        def emitted_routes(self) -> set[str]:
            return set()

    builder = FakeBuilder()
    builder.build_dir = build_dir
    builder.content_dir = content_dir

    assert build_module._check_generated_links(builder, [], docs) == []
