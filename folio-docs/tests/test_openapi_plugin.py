from __future__ import annotations

import json
from pathlib import Path

import pytest

from folio_docs.config import Config
from folio_docs.extensions import ExtensionRegistry, register_builtin_extensions


class _MetaBuilder:
    """Minimal AssetBuilder stand-in for exercising _meta.ts merging."""

    def __init__(self, meta: dict[str, str] | None = None) -> None:
        self.meta: dict[str, str] = dict(meta or {})

    def read_meta(self, directory: str) -> str:
        return self.meta.get(directory, "")

    def write_meta(self, directory: str, content: str) -> None:
        self.meta[directory] = content


def _write_cookie_caper_spec(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "openapi": "3.1.0",
                "info": {
                    "title": "Cookie Caper API",
                    "version": "0.1.0",
                    "description": "Coordinate snack retrieval without waking the baker.",
                },
                "servers": [{"url": "https://api.cookie-caper.test"}],
                "paths": {
                    "/cookies": {
                        "get": {
                            "summary": "List cookies",
                            "operationId": "listCookies",
                            "tags": ["Cookies"],
                            "responses": {"200": {"description": "Cookie ledger"}},
                        }
                    },
                    "/heists": {
                        "post": {
                            "summary": "Schedule a heist",
                            "operationId": "scheduleHeist",
                            "tags": ["Heists"],
                            "responses": {"201": {"description": "Heist scheduled"}},
                        }
                    },
                },
                "components": {
                    "schemas": {
                        "Cookie": {"type": "object"},
                        "HeistPlan": {"type": "object"},
                    }
                },
            }
        ),
        encoding="utf-8",
    )


def test_openapi_plugin_registers_extension_data_and_docs_page(tmp_path: Path) -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    spec_path = tmp_path / "openapi.json"
    _write_cookie_caper_spec(spec_path)
    config = Config(project_name="Cookie Caper", project_dir=str(tmp_path), extra={})

    openapi_plugin.configure(
        config=config,
        raw_config={
            "openapi": {
                "sources": [
                    {
                        "title": "Cookie Caper API",
                        "path": "openapi.json",
                        "route": "api-reference/http",
                    }
                ]
            }
        },
    )

    registry = ExtensionRegistry()
    register_builtin_extensions(registry)
    openapi_plugin.register_extensions(registry=registry, config=config)

    source = config.extra["openapi"]["sources"][0]
    assert source["title"] == "Cookie Caper API"
    assert source["route"] == "api-reference/http"
    assert source["spec"]["info"]["title"] == "Cookie Caper API"
    assert source["operations"] == [
        {
            "method": "GET",
            "path": "/cookies",
            "summary": "List cookies",
            "description": "",
            "operationId": "listCookies",
            "tags": ["Cookies"],
        },
        {
            "method": "POST",
            "path": "/heists",
            "summary": "Schedule a heist",
            "description": "",
            "operationId": "scheduleHeist",
            "tags": ["Heists"],
        },
    ]
    assert source["schemas"] == ["Cookie", "HeistPlan"]

    assert registry.components["OpenApiReference"].import_path == (
        "@/components/openapi-reference"
    )
    data_module = registry.data_modules["openapi"]
    assert data_module.export_name == "openApiSources"
    assert data_module.module_path == "openapi-data"
    assert data_module.type_annotation == "OpenApiSource[]"
    assert "spec" not in data_module.data[0]

    class Builder:
        def __init__(self) -> None:
            self.pages: dict[str, str] = {}
            self.routes: set[str] = set()
            self.meta: dict[str, str] = {
                "api-reference": (
                    "export default {\n"
                    '  "index": {\n'
                    '    "display": "hidden",\n'
                    "  },\n"
                    '  "cookie_caper_api": "Cookie Caper Api",\n'
                    "}"
                )
            }

        def page_exists(self, route: str) -> bool:
            return route in self.pages

        def write_page(self, route: str, content: str) -> None:
            self.pages[route] = content

        def register_route(self, route: str) -> None:
            self.routes.add(route)

        def read_meta(self, directory: str) -> str:
            return self.meta.get(directory, "")

        def write_meta(self, directory: str, content: str) -> None:
            self.meta[directory] = content

    builder = Builder()
    openapi_plugin.emit_assets(builder=builder, config=config)

    assert builder.pages["api-reference/http"] == (
        'import { OpenApiReference } from "@/components/openapi-reference"\n\n'
        "# Cookie Caper API\n\n"
        '<OpenApiReference sourceTitle="Cookie Caper API" />\n'
    )
    assert '"cookie_caper_api": "Cookie Caper Api"' in builder.meta["api-reference"]
    assert '"http": "Cookie Caper API"' in builder.meta["api-reference"]
    assert '\n  "display": "hidden"' not in builder.meta["api-reference"]
    # The emitted route is registered for link-checking.
    assert "api-reference/http" in builder.routes


class _PageBuilder:
    """AssetBuilder stand-in that also supports reading page content."""

    def __init__(
        self,
        pages: dict[str, str] | None = None,
        meta: dict[str, str] | None = None,
        *,
        readable: bool = True,
    ) -> None:
        self.pages: dict[str, str] = dict(pages or {})
        self.written_pages: list[str] = []
        self.meta: dict[str, str] = dict(meta or {})
        if not readable:
            self.read_page = None  # type: ignore[assignment]

    def page_exists(self, route: str) -> bool:
        return route in self.pages

    def read_page(self, route: str) -> str:
        return self.pages[route]

    def write_page(self, route: str, content: str) -> None:
        self.written_pages.append(route)
        self.pages[route] = content

    def register_route(self, route: str) -> None:
        pass

    def read_meta(self, directory: str) -> str:
        return self.meta.get(directory, "")

    def write_meta(self, directory: str, content: str) -> None:
        self.meta[directory] = content


def _cookie_caper_config(tmp_path: Path) -> Config:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    spec_path = tmp_path / "openapi.json"
    _write_cookie_caper_spec(spec_path)
    config = Config(project_name="Cookie Caper", project_dir=str(tmp_path), extra={})
    openapi_plugin.configure(
        config=config,
        raw_config={
            "openapi": {
                "sources": [
                    {
                        "title": "Cookie Caper API",
                        "path": "openapi.json",
                        "route": "api-reference/http",
                    }
                ]
            }
        },
    )
    return config


def test_openapi_plugin_rewrites_stale_docs_page_and_refreshes_meta(
    tmp_path: Path,
) -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    config = _cookie_caper_config(tmp_path)
    builder = _PageBuilder(
        pages={"api-reference/http": "# Existing HTTP API\n"},
        meta={
            "api-reference": ('export default {\n  "index": {"display": "hidden"},\n}')
        },
    )
    openapi_plugin.emit_assets(builder=builder, config=config)

    # The on-disk page differed from the desired content, so it is rewritten
    # instead of persisting stale content on warm builds.
    assert builder.written_pages == ["api-reference/http"]
    assert builder.pages["api-reference/http"] == openapi_plugin.docs_page_mdx(
        config.extra["openapi"]["sources"][0]
    )
    assert '"http": "Cookie Caper API"' in builder.meta["api-reference"]


def test_openapi_plugin_skips_rewrite_when_page_content_is_current(
    tmp_path: Path,
) -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    config = _cookie_caper_config(tmp_path)
    desired = openapi_plugin.docs_page_mdx(config.extra["openapi"]["sources"][0])
    builder = _PageBuilder(pages={"api-reference/http": desired})
    openapi_plugin.emit_assets(builder=builder, config=config)

    assert builder.written_pages == []
    assert builder.pages["api-reference/http"] == desired


def test_openapi_plugin_rewrites_page_when_builder_cannot_read_pages(
    tmp_path: Path,
) -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    config = _cookie_caper_config(tmp_path)
    desired = openapi_plugin.docs_page_mdx(config.extra["openapi"]["sources"][0])
    builder = _PageBuilder(pages={"api-reference/http": desired}, readable=False)
    openapi_plugin.emit_assets(builder=builder, config=config)

    # Without read_page the existing content is unknown, so the page is
    # rewritten to guarantee it cannot be stale.
    assert builder.written_pages == ["api-reference/http"]


def test_merge_meta_entry_preserves_nested_and_escaped_entries() -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    existing = (
        "export default {\n"
        '  "index": {\n'
        '    "display": "hidden",\n'
        "  },\n"
        '  "guides": {\n'
        '    "title": "Guides \\"advanced\\"",\n'
        '    "theme": {\n'
        '      "collapsed": true,\n'
        "    },\n"
        "  },\n"
        '  "faq": "Questions & \\"Answers\\"",\n'
        "}"
    )
    builder = _MetaBuilder({"api-reference": existing})

    openapi_plugin._merge_meta_entry(
        builder, "api-reference", "http", "HTTP API", hidden_index=True
    )

    # The plugin entry is appended before the closing brace and every other
    # line — nested objects, escaped quotes — survives byte-for-byte.
    expected = existing[: existing.rfind("}")] + '  "http": "HTTP API",\n}'
    assert builder.meta["api-reference"] == expected


def test_merge_meta_entry_replaces_only_its_own_entry() -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    existing = (
        "export default {\n"
        '  "http": {\n'
        '    "title": "Old {HTTP} title",\n'
        '    "theme": {\n'
        '      "collapsed": true,\n'
        "    },\n"
        "  },\n"
        '  "guides": {\n'
        '    "title": "Guides",\n'
        '    "theme": {\n'
        '      "collapsed": true,\n'
        "    },\n"
        "  },\n"
        "}\n"
    )
    builder = _MetaBuilder({"api-reference": existing})

    openapi_plugin._merge_meta_entry(builder, "api-reference", "http", "New API")

    assert builder.meta["api-reference"] == (
        "export default {\n"
        '  "http": "New API",\n'
        '  "guides": {\n'
        '    "title": "Guides",\n'
        '    "theme": {\n'
        '      "collapsed": true,\n'
        "    },\n"
        "  },\n"
        "}\n"
    )


def test_merge_meta_entry_adds_hidden_index_only_when_missing() -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    builder = _MetaBuilder(
        {"api-reference": 'export default {\n  "petstore": "Petstore",\n}\n'}
    )

    openapi_plugin._merge_meta_entry(
        builder, "api-reference", "http", "HTTP API", hidden_index=True
    )

    assert builder.meta["api-reference"] == (
        "export default {\n"
        '  "index": {\n'
        '    "display": "hidden",\n'
        "  },\n"
        '  "petstore": "Petstore",\n'
        '  "http": "HTTP API",\n'
        "}\n"
    )


def test_merge_meta_entry_writes_fresh_meta_when_file_is_empty() -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    builder = _MetaBuilder()

    openapi_plugin._merge_meta_entry(
        builder, "api-reference", "http", "HTTP API", hidden_index=True
    )

    assert builder.meta["api-reference"] == (
        "export default {\n"
        '  "index": {\n'
        '    "display": "hidden",\n'
        "  },\n"
        '  "http": "HTTP API",\n'
        "}"
    )


def test_merge_meta_entry_appends_when_structure_is_unrecognized() -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    existing = "// hand-written meta\nexport default someHelper({})\n"
    builder = _MetaBuilder({"": existing})

    openapi_plugin._merge_meta_entry(builder, "", "api-reference", "API Reference")

    updated = builder.meta[""]
    assert updated.startswith(existing.rstrip("\n"))
    assert '  "api-reference": "API Reference",' in updated


def test_load_spec_error_names_source_and_resolved_path(tmp_path: Path) -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    with pytest.raises(FileNotFoundError) as excinfo:
        openapi_plugin.normalize_source(
            {"title": "Ghost API", "path": "missing/spec.yaml"},
            project_dir=tmp_path,
        )

    message = str(excinfo.value)
    assert "'Ghost API'" in message
    assert str((tmp_path / "missing" / "spec.yaml").resolve()) in message
    assert str(tmp_path.resolve()) in message


def test_normalize_source_warns_when_spec_is_not_a_mapping(tmp_path: Path) -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    (tmp_path / "broken.yaml").write_text("- just\n- a\n- list\n", encoding="utf-8")

    with pytest.warns(UserWarning, match=r"'broken\.yaml'"):
        result = openapi_plugin.normalize_source(
            {"path": "broken.yaml"}, project_dir=tmp_path
        )

    assert result is None


def test_docs_page_mdx_escapes_title_in_heading() -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    page = openapi_plugin.docs_page_mdx({"title": "Payments <v2> {beta} `raw`"})

    assert "# Payments \\<v2\\> \\{beta\\} \\`raw\\`\n" in page
    assert 'sourceTitle="Payments <v2> {beta} `raw`"' in page


def test_default_route_uses_sidebar_slug_rules() -> None:
    from folio_docs.docs.integrations import openapi as openapi_plugin

    # Shared through folio_docs.slugs.slugify so nav slugs and plugin
    # routes agree (apostrophes are stripped, not dashed).
    assert (
        openapi_plugin._normalize_route(None, "Cookie's API")
        == "api-reference/cookies-api"
    )
    assert openapi_plugin._normalize_route(None, "!!!") == "api-reference/openapi"


def test_openapi_reference_component_uses_plugin_data() -> None:
    root = Path(__file__).parents[1]
    component = (root / "template" / "components" / "openapi-reference.tsx").read_text(
        encoding="utf-8"
    )

    assert 'from "@/lib/openapi-data"' in component
    assert "type OpenApiSource" in component
    assert "methodStyles" in component
    assert "OpenAPI" in component


def test_template_ships_empty_openapi_data_for_disabled_plugin_builds() -> None:
    root = Path(__file__).parents[1]
    data_module = (root / "template" / "lib" / "openapi-data.ts").read_text(
        encoding="utf-8"
    )

    assert "export interface OpenApiSource" in data_module
    assert "export const openApiSources: OpenApiSource[] = []" in data_module
