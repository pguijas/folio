from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Any

import yaml

from folio.generator.sidebar import _slugify, _title_case, meta_to_ts
from folio.plugin import hookimpl

FOLIO_PLUGIN_API = "1.1"

OPENAPI_TYPES = (
    "export interface OpenApiOperation {\n"
    "  method: string\n"
    "  path: string\n"
    "  summary: string\n"
    "  description: string\n"
    "  operationId: string\n"
    "  tags: string[]\n"
    "}\n\n"
    "export interface OpenApiSource {\n"
    "  title: string\n"
    "  version: string\n"
    "  description: string\n"
    "  route: string\n"
    "  servers: string[]\n"
    "  operations: OpenApiOperation[]\n"
    "  schemas: string[]\n"
    "}\n"
)

HTTP_METHODS = ("get", "post", "put", "patch", "delete", "head", "options", "trace")
# Matches the opening of a top-level entry in a generated _meta.ts: exactly
# two spaces of indentation, a double-quoted key (escapes allowed), a colon.
_META_TOP_LEVEL_KEY_RE = re.compile(r'^  "((?:[^"\\]|\\.)*)"\s*:')
# ``[`` / ``]`` are escaped so a spec/config title cannot smuggle a markdown
# link (e.g. ``[click](javascript:...)``) into the generated heading.
_MDX_TEXT_SPECIALS_RE = re.compile(r"([\\`{}<>\[\]])")


@hookimpl
def config_keys() -> list[str]:
    return ["openapi"]


@hookimpl
def configure(config: Any, raw_config: dict[str, Any]) -> None:
    project_dir = Path(getattr(config, "project_dir", "") or ".")
    config.extra["openapi"] = normalize_openapi(
        raw_config.get("openapi", {}),
        project_dir=project_dir,
    )


@hookimpl
def register_extensions(registry: Any, config: Any) -> None:
    openapi = get_openapi(config)
    registry.register_component(
        "OpenApiReference",
        import_path="@/components/openapi-reference",
        expose_mdx=True,
    )
    registry.write_data_module(
        "openapi",
        export_name="openApiSources",
        data=[public_source_data(source) for source in openapi["sources"]],
        type_source=OPENAPI_TYPES,
        type_annotation="OpenApiSource[]",
        module_path="openapi-data",
    )


@hookimpl
def emit_assets(builder: Any, config: Any) -> None:
    for source in get_openapi(config)["sources"]:
        route = source.get("route", "")
        if not route:
            continue
        # Declare the route as live even when the page persists from a prior
        # build, so internal links to it are not flagged broken.
        builder.register_route(route)
        content = docs_page_mdx(source)
        # Write-if-changed: rewrite the page whenever the desired content
        # differs from what is on disk, so warm builds cannot serve a page
        # that is stale relative to the regenerated openapi data module.
        if _existing_page(builder, route) != content:
            builder.write_page(route, content)
        _write_route_meta(builder, route, str(source.get("title") or "OpenAPI"))


def normalize_openapi(raw_openapi: Any, *, project_dir: Path) -> dict[str, Any]:
    if not isinstance(raw_openapi, dict):
        return {"sources": []}

    raw_sources = raw_openapi.get("sources", [])
    if isinstance(raw_sources, dict):
        raw_sources = [raw_sources]
    if not isinstance(raw_sources, list):
        raw_sources = []

    sources = [
        source
        for raw_source in raw_sources
        if (source := normalize_source(raw_source, project_dir=project_dir)) is not None
    ]
    return {"sources": sources}


def normalize_source(
    raw_source: Any,
    *,
    project_dir: Path,
) -> dict[str, Any] | None:
    if not isinstance(raw_source, dict):
        return None

    spec = _load_spec(raw_source, project_dir=project_dir)
    if not isinstance(spec, dict):
        warnings.warn(
            f"openapi: ignoring source {_source_label(raw_source)}: "
            "the spec did not parse to a mapping "
            f"(got {type(spec).__name__})",
            stacklevel=2,
        )
        return None

    info = spec.get("info", {})
    if not isinstance(info, dict):
        info = {}

    configured_title = raw_source.get("title")
    title = (
        configured_title.strip()
        if isinstance(configured_title, str) and configured_title.strip()
        else str(info.get("title") or "OpenAPI")
    )
    route = _normalize_route(raw_source.get("route"), title)

    return {
        "title": title,
        "version": str(info.get("version") or ""),
        "description": str(
            raw_source.get("description") or info.get("description") or ""
        ),
        "route": route,
        "servers": _servers(spec),
        "operations": _operations(spec),
        "schemas": _schemas(spec),
        "spec": spec,
    }


def get_openapi(config: Any) -> dict[str, Any]:
    openapi = getattr(config, "extra", {}).get("openapi")
    if isinstance(openapi, dict) and isinstance(openapi.get("sources"), list):
        return openapi
    return {"sources": []}


def public_source_data(source: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in source.items() if key != "spec"}


def docs_page_mdx(source: dict[str, Any]) -> str:
    title = str(source.get("title") or "OpenAPI")
    return (
        'import { OpenApiReference } from "@/components/openapi-reference"\n\n'
        f"# {_escape_mdx_text(title)}\n\n"
        f'<OpenApiReference sourceTitle="{_escape_mdx_attr(title)}" />\n'
    )


def _existing_page(builder: Any, route: str) -> str | None:
    """Return the page content currently on disk, or None when unknown.

    Builders are not required to expose ``read_page``; when it is missing the
    content is treated as unknown so the page gets rewritten, which keeps warm
    builds from serving stale pages.
    """
    if not builder.page_exists(route):
        return None
    read_page = getattr(builder, "read_page", None)
    if not callable(read_page):
        return None
    return read_page(route)


def _write_route_meta(builder: Any, route: str, title: str) -> None:
    parts = [part for part in route.strip("/").split("/") if part]
    if not parts:
        return

    if len(parts) > 1:
        root_title = (
            "API Reference" if parts[0] == "api-reference" else _title_case(parts[0])
        )
        _merge_meta_entry(builder, "", parts[0], root_title)

    directory = "/".join(parts[:-1])
    slug = parts[-1]
    _merge_meta_entry(
        builder,
        directory,
        slug,
        title,
        hidden_index=directory == "api-reference",
    )


def _merge_meta_entry(
    builder: Any,
    directory: str,
    slug: str,
    title: str,
    *,
    hidden_index: bool = False,
) -> None:
    """Insert or replace a single ``_meta.ts`` entry non-destructively.

    Only the plugin's own entry (and, when requested, a missing hidden
    ``index`` entry) is touched; every other line — including nested object
    entries written by the sidebar generator — is preserved verbatim.
    """
    existing = builder.read_meta(directory)
    if not existing.strip():
        meta: dict[str, Any] = {}
        if hidden_index:
            meta["index"] = {"display": "hidden"}
        meta[slug] = title
        builder.write_meta(directory, meta_to_ts(meta))
        return

    lines = existing.splitlines()
    open_index = next(
        (i for i, line in enumerate(lines) if line.strip() == "export default {"),
        None,
    )
    close_index = next(
        (i for i in range(len(lines) - 1, -1, -1) if lines[i].strip() == "}"),
        None,
    )
    entry_lines = _meta_entry_lines({slug: title})
    if open_index is None or close_index is None or close_index <= open_index:
        # Unrecognizable structure: append a well-formed entry instead of
        # rewriting (and potentially losing) what is already there.
        builder.write_meta(
            directory,
            existing.rstrip("\n") + "\n" + "\n".join(entry_lines) + "\n",
        )
        return

    body = lines[open_index + 1 : close_index]
    merged: list[str] = []
    replaced = False
    escaped_slug = _escape_meta_key(slug)
    position = 0
    while position < len(body):
        line = body[position]
        match = _META_TOP_LEVEL_KEY_RE.match(line)
        if match and match.group(1) == escaped_slug and not replaced:
            # Skip every line of the existing entry (may span multiple lines
            # for object values) and emit the fresh entry in its place.
            depth = _brace_delta(line)
            position += 1
            while depth > 0 and position < len(body):
                depth += _brace_delta(body[position])
                position += 1
            merged.extend(entry_lines)
            replaced = True
            continue
        merged.append(line)
        position += 1
    if not replaced:
        merged.extend(entry_lines)
    if hidden_index and not _has_top_level_key(body, "index"):
        merged = _meta_entry_lines({"index": {"display": "hidden"}}) + merged

    serialized = "\n".join(lines[: open_index + 1] + merged + lines[close_index:])
    if existing.endswith("\n"):
        serialized += "\n"
    builder.write_meta(directory, serialized)


def _meta_entry_lines(meta: dict[str, Any]) -> list[str]:
    """Serialize entries with folio's exact ``_meta.ts`` formatting."""
    return meta_to_ts(meta).splitlines()[1:-1]


def _escape_meta_key(key: str) -> str:
    return key.replace("\\", "\\\\").replace('"', '\\"')


def _has_top_level_key(body: list[str], key: str) -> bool:
    escaped = _escape_meta_key(key)
    for line in body:
        match = _META_TOP_LEVEL_KEY_RE.match(line)
        if match and match.group(1) == escaped:
            return True
    return False


def _brace_delta(line: str) -> int:
    """Net brace/bracket depth change, ignoring braces in string literals."""
    depth = 0
    in_string = False
    escaped = False
    for char in line:
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
    return depth


def _load_spec(raw_source: dict[str, Any], *, project_dir: Path) -> Any:
    content = raw_source.get("content", raw_source.get("spec"))
    if isinstance(content, dict):
        return content
    if isinstance(content, str) and content.strip():
        return yaml.safe_load(content)

    raw_path = raw_source.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    path = Path(raw_path)
    if not path.is_absolute():
        path = project_dir / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(
            f"openapi source {_source_label(raw_source)}: spec file not found "
            f"at '{path}' (path '{raw_path}' resolved against project "
            f"directory '{project_dir.resolve()}')"
        )
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _normalize_route(raw_route: Any, title: str) -> str:
    if isinstance(raw_route, str) and raw_route.strip():
        return raw_route.strip().strip("/")
    return f"api-reference/{_slugify(title) or 'openapi'}"


def _source_label(raw_source: dict[str, Any]) -> str:
    for key in ("title", "path"):
        value = raw_source.get(key)
        if isinstance(value, str) and value.strip():
            return repr(value.strip())
    return "<inline content>"


def _servers(spec: dict[str, Any]) -> list[str]:
    servers = spec.get("servers", [])
    if not isinstance(servers, list):
        return []
    urls = []
    for server in servers:
        if isinstance(server, dict) and isinstance(server.get("url"), str):
            urls.append(server["url"])
    return urls


def _operations(spec: dict[str, Any]) -> list[dict[str, Any]]:
    paths = spec.get("paths", {})
    if not isinstance(paths, dict):
        return []

    operations: list[dict[str, Any]] = []
    for path, path_item in paths.items():
        if not isinstance(path, str) or not isinstance(path_item, dict):
            continue
        for method in HTTP_METHODS:
            operation = path_item.get(method)
            if not isinstance(operation, dict):
                continue
            operations.append(
                {
                    "method": method.upper(),
                    "path": path,
                    "summary": str(operation.get("summary") or ""),
                    "description": str(operation.get("description") or ""),
                    "operationId": str(operation.get("operationId") or ""),
                    "tags": _string_list(operation.get("tags", [])),
                }
            )
    return operations


def _schemas(spec: dict[str, Any]) -> list[str]:
    components = spec.get("components", {})
    if not isinstance(components, dict):
        return []
    schemas = components.get("schemas", {})
    if not isinstance(schemas, dict):
        return []
    return [key for key in schemas if isinstance(key, str)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _escape_mdx_attr(value: str) -> str:
    return value.replace("&", "&amp;").replace('"', "&quot;")


def _escape_mdx_text(value: str) -> str:
    """Backslash-escape characters MDX treats as syntax in body text.

    Braces open ES expressions, angle brackets open JSX elements, and
    backticks open code spans; a raw backslash could form escapes itself.
    """
    return _MDX_TEXT_SPECIALS_RE.sub(r"\\\1", value)
