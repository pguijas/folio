from __future__ import annotations

from pathlib import Path

import pytest

from folio.build import _apply_extensions, build_registry
from folio.config import Config
from folio.generator.site_builder import SiteBuilder
from folio.plugin import PluginDocument, PluginHookError, PluginManager, hookimpl


def test_build_registry_fail_fast_on_register_extensions() -> None:
    class Boom:
        @hookimpl
        def register_extensions(self, registry, config) -> None:
            raise ValueError("boom")

    pm = PluginManager()
    pm.register(Boom(), name="boom-plugin")

    with pytest.raises(PluginHookError) as excinfo:
        build_registry(pm, Config(project_name="X"))
    assert "boom-plugin" in str(excinfo.value)


def test_apply_extensions_warn_skips_emit_assets_failure(tmp_path: Path) -> None:
    class Boom:
        @hookimpl
        def emit_assets(self, builder, config) -> None:
            raise RuntimeError("emit boom")

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text("{}", encoding="utf-8")
    build_dir = tmp_path / "build"
    (build_dir / "content").mkdir(parents=True)
    config = Config(project_name="X", output_dir=str(tmp_path / "out"))
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    pm = PluginManager()
    pm.register(Boom(), name="boom-plugin")

    # emit_assets failure must NOT abort the build; it warns and skips.
    with pytest.warns(UserWarning, match="boom-plugin"):
        _apply_extensions(builder, pm, config)


def test_failed_emit_assets_rolls_back_half_registered_routes(
    tmp_path: Path,
) -> None:
    """A plugin that crashes between register_route and write_page must not
    leave its route whitelisted for the link checker."""

    class RegistersThenBooms:
        @hookimpl
        def emit_assets(self, builder, config) -> None:
            builder.register_route("ghost-page")
            raise RuntimeError("emit boom")

    class Healthy:
        @hookimpl
        def emit_assets(self, builder, config) -> None:
            builder.register_route("live-page")

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text("{}", encoding="utf-8")
    build_dir = tmp_path / "build"
    (build_dir / "content").mkdir(parents=True)
    config = Config(project_name="X", output_dir=str(tmp_path / "out"))
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    pm = PluginManager()
    pm.register(RegistersThenBooms(), name="boom-plugin")
    pm.register(Healthy(), name="healthy-plugin")

    with pytest.warns(UserWarning, match="boom-plugin"):
        _apply_extensions(builder, pm, config)

    # The failed plugin's route was rolled back; the healthy plugin's kept.
    assert "ghost-page" not in builder.emitted_routes()
    assert "live-page" in builder.emitted_routes()


def test_empty_project_gate_counts_plugin_views(tmp_path: Path) -> None:
    """A repo whose only content is a plugin view is not an empty project.

    The gate ran before plugins registered, so a board-only site was told to
    "check source paths in docs.yaml" — paths it had never set, for content it
    does not have by design.
    """
    from folio.build import _parse_project_sources

    config = Config(project_name="X").resolve_paths(tmp_path)

    with pytest.raises(RuntimeError, match="No Python modules or documentation"):
        _parse_project_sources(config, verbose=False)

    sources = _parse_project_sources(config, verbose=False, plugin_views=1)
    assert sources.modules == []
    assert sources.docs == []


def test_collect_docs_enters_the_normal_source_pipeline(tmp_path: Path) -> None:
    """Plugin Markdown is parsed like project docs before page generation."""
    from folio.build import _parse_project_sources

    artifact = tmp_path / "board" / "cards" / "demo" / "report.md"
    artifact.parent.mkdir(parents=True)
    artifact.write_text("# Report\n\nBuilt beside the card.\n", encoding="utf-8")
    aside = tmp_path / "board" / "cards" / "demo" / "aside.md"
    aside.write_text("# Aside\n", encoding="utf-8")

    class Documents:
        @hookimpl
        def collect_docs(self, config):
            return [
                PluginDocument(
                    source=artifact,
                    route="kanban/demo/report",
                ),
                PluginDocument(
                    source=aside,
                    route="kanban/demo/aside",
                    unlisted=True,
                ),
            ]

    pm = PluginManager()
    pm.register(Documents(), name="documents-plugin")

    sources = _parse_project_sources(
        Config(project_name="X").resolve_paths(tmp_path),
        verbose=False,
        plugin_views=0,
        plugin_manager=pm,
    )

    assert len(sources.docs) == 2
    assert sources.docs[0].route == "kanban/demo/report"
    assert sources.docs[0].frontmatter["title"] == "Report"
    assert sources.docs[0].source_file == str(artifact)
    # The delist flag rides the same pipeline: default listed, opt-out carried.
    assert sources.docs[0].unlisted is False
    assert sources.docs[1].unlisted is True


def test_collect_docs_rejects_canonical_route_collisions(tmp_path: Path) -> None:
    """A flat page and folder index may never claim the same public URL."""
    from folio.build import _parse_project_sources

    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("# First\n", encoding="utf-8")
    second.write_text("# Second\n", encoding="utf-8")

    class First:
        @hookimpl
        def collect_docs(self, config):
            return [PluginDocument(first, "kanban/card/report")]

    class Second:
        @hookimpl
        def collect_docs(self, config):
            return [PluginDocument(second, "kanban/card/report/index")]

    pm = PluginManager()
    pm.register(First(), name="first-plugin")
    pm.register(Second(), name="second-plugin")

    with pytest.raises(ValueError, match="kanban/card/report") as excinfo:
        _parse_project_sources(
            Config(project_name="X").resolve_paths(tmp_path),
            verbose=False,
            plugin_manager=pm,
        )

    message = str(excinfo.value)
    assert str(first) in message
    assert str(second) in message
    assert "kanban/card/report/index" in message


def test_collect_docs_rejects_router_alias_collisions(tmp_path: Path) -> None:
    """The docs router maps underscores to hyphens outside API routes."""
    from folio.build import _parse_project_sources

    first = tmp_path / "first.md"
    second = tmp_path / "second.md"
    first.write_text("# First\n", encoding="utf-8")
    second.write_text("# Second\n", encoding="utf-8")

    class Documents:
        @hookimpl
        def collect_docs(self, config):
            return [
                PluginDocument(first, "kanban/card/foo_bar"),
                PluginDocument(second, "kanban/card/foo-bar"),
            ]

    pm = PluginManager()
    pm.register(Documents(), name="documents-plugin")

    with pytest.raises(ValueError, match="kanban/card/foo-bar") as excinfo:
        _parse_project_sources(
            Config(project_name="X").resolve_paths(tmp_path),
            verbose=False,
            plugin_manager=pm,
        )

    assert "kanban/card/foo_bar" in str(excinfo.value)


def test_collect_docs_rejects_a_collision_with_project_docs(tmp_path: Path) -> None:
    """Plugin and core documents share one canonical route namespace."""
    from folio.build import _parse_project_sources

    docs = tmp_path / "docs"
    docs.mkdir()
    core = docs / "guide.md"
    plugin = tmp_path / "plugin.md"
    core.write_text("# Core\n", encoding="utf-8")
    plugin.write_text("# Plugin\n", encoding="utf-8")

    class Documents:
        @hookimpl
        def collect_docs(self, config):
            return [PluginDocument(plugin, "guide/index")]

    pm = PluginManager()
    pm.register(Documents(), name="documents-plugin")

    config = Config(project_name="X", doc_sources=["docs"]).resolve_paths(tmp_path)
    with pytest.raises(ValueError, match="guide/index") as excinfo:
        _parse_project_sources(config, verbose=False, plugin_manager=pm)

    message = str(excinfo.value)
    assert str(core) in message
    assert str(plugin) in message


def test_apply_extensions_reuses_a_prebuilt_registry(tmp_path: Path) -> None:
    """The build assembles the registry once, before the gate, and reuses it.

    Rebuilding it here would run every plugin's register_extensions a second
    time per build.
    """
    calls: list[int] = []

    class Counts:
        @hookimpl
        def register_extensions(self, registry, config) -> None:
            calls.append(1)

    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "package.json").write_text("{}", encoding="utf-8")
    build_dir = tmp_path / "build"
    (build_dir / "content").mkdir(parents=True)
    config = Config(project_name="X", output_dir=str(tmp_path / "out"))
    builder = SiteBuilder(config, str(template_dir), str(build_dir))

    pm = PluginManager()
    pm.register(Counts(), name="counting-plugin")

    registry = build_registry(pm, config)
    assert len(calls) == 1
    _apply_extensions(builder, pm, config, registry)
    assert len(calls) == 1
