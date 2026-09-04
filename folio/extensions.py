from __future__ import annotations

import re
import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")

_COMPONENT_ORIGINS = ("builtin", "config", "plugin")


@dataclass(frozen=True)
class ComponentDefinition:
    name: str
    import_path: str
    export_name: str | None = None
    expose_mdx: bool = True
    source_path: Path | None = None
    props: Mapping[str, str] = field(default_factory=dict)
    required: bool = False
    category: str = "general"
    contract: bool = False
    source_label: str = ""
    origin: str = "plugin"

    @property
    def imported_name(self) -> str:
        return self.export_name or self.name


@dataclass(frozen=True)
class LayoutDefinition:
    name: str
    import_path: str
    export_name: str
    slots: tuple[str, ...] = ("main",)


@dataclass(frozen=True)
class DataModuleDefinition:
    name: str
    export_name: str
    data: Any
    type_source: str = ""
    type_annotation: str = ""
    module_path: str = ""


@dataclass(frozen=True)
class ViewBlock:
    component: str
    props: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ViewDefinition:
    path: str
    layout: str
    slots: dict[str, tuple[ViewBlock, ...]]
    title: str = ""
    props: dict[str, Any] = field(default_factory=dict)


class ExtensionRegistry:
    def __init__(self) -> None:
        self.components: dict[str, ComponentDefinition] = {}
        self.layouts: dict[str, LayoutDefinition] = {}
        self.data_modules: dict[str, DataModuleDefinition] = {}
        self.views: dict[str, ViewDefinition] = {}

    def register_component(
        self,
        name: str,
        *,
        import_path: str,
        export_name: str | None = None,
        expose_mdx: bool = True,
        source_path: str | Path | None = None,
        props: Mapping[str, str] | None = None,
        required: bool = False,
        category: str = "general",
        contract: bool = False,
        source_label: str = "",
        origin: str = "plugin",
    ) -> ComponentDefinition:
        self._validate_identifier(name, "component name")
        if export_name is not None:
            self._validate_identifier(export_name, "component export")
        if origin not in _COMPONENT_ORIGINS:
            raise ValueError(
                f"Invalid component origin: {origin!r} "
                f"(expected one of {', '.join(_COMPONENT_ORIGINS)})"
            )
        existing = self.components.get(name)
        if existing is not None:
            if existing.origin == "builtin" and origin != "builtin":
                warnings.warn(
                    f"Component '{name}' overrides the Folio builtin of the same name",
                    UserWarning,
                    stacklevel=2,
                )
            else:
                raise ValueError(
                    f"Component already registered: {name} "
                    f"(existing origin: {existing.origin}; new origin: {origin})"
                )
        component = ComponentDefinition(
            name=name,
            import_path=import_path,
            export_name=export_name,
            expose_mdx=expose_mdx,
            source_path=Path(source_path) if source_path is not None else None,
            props=dict(props) if props is not None else {},
            required=required,
            category=category,
            contract=contract,
            source_label=source_label,
            origin=origin,
        )
        self.components[name] = component
        return component

    def register_layout(
        self,
        name: str,
        *,
        import_path: str,
        export_name: str,
        slots: list[str] | tuple[str, ...] = ("main",),
    ) -> LayoutDefinition:
        if name in self.layouts:
            raise ValueError(f"Layout already registered: {name}")
        self._validate_identifier(export_name, "layout export")
        if not slots:
            raise ValueError("Layout must define at least one slot")
        for slot in slots:
            self._validate_identifier(slot, "layout slot")
        layout = LayoutDefinition(
            name=name,
            import_path=import_path,
            export_name=export_name,
            slots=tuple(slots),
        )
        self.layouts[name] = layout
        return layout

    def write_data_module(
        self,
        name: str,
        *,
        export_name: str,
        data: Any,
        type_source: str = "",
        type_annotation: str = "",
        module_path: str = "",
    ) -> DataModuleDefinition:
        self._validate_identifier(export_name, "data export")
        if name in self.data_modules:
            raise ValueError(f"Data module already registered: {name}")
        module = DataModuleDefinition(
            name=name,
            export_name=export_name,
            data=data,
            type_source=type_source,
            type_annotation=type_annotation,
            module_path=module_path,
        )
        self.data_modules[name] = module
        return module

    def add_view(
        self,
        *,
        path: str,
        layout: str,
        slots: dict[str, list[dict[str, Any]] | tuple[ViewBlock, ...]],
        title: str = "",
        props: dict[str, Any] | None = None,
    ) -> ViewDefinition:
        normalized_path = self._normalize_view_path(path)
        if normalized_path in self.views:
            raise ValueError(f"View path already registered: {normalized_path}")
        if layout not in self.layouts:
            raise ValueError(f"Unknown layout for view {normalized_path}: {layout}")

        layout_slots = set(self.layouts[layout].slots)
        normalized_slots: dict[str, tuple[ViewBlock, ...]] = {}
        for slot, blocks in slots.items():
            if slot not in layout_slots:
                raise ValueError(f"Unknown slot for layout {layout}: {slot}")
            normalized_blocks: list[ViewBlock] = []
            for block in blocks:
                if isinstance(block, ViewBlock):
                    component_name = block.component
                    block_props = block.props
                else:
                    component_name = str(block.get("component", ""))
                    block_props = block.get("props", {})
                if component_name not in self.components:
                    raise ValueError(
                        f"Unknown component for view {normalized_path}: {component_name}"
                    )
                normalized_blocks.append(
                    ViewBlock(
                        component=component_name,
                        props=block_props if isinstance(block_props, dict) else {},
                    )
                )
            normalized_slots[slot] = tuple(normalized_blocks)

        view = ViewDefinition(
            path=normalized_path,
            layout=layout,
            slots=normalized_slots,
            title=title,
            props=props or {},
        )
        self.views[normalized_path] = view
        return view

    @staticmethod
    def _normalize_view_path(path: str) -> str:
        normalized = "/" + path.strip("/")
        return "/" if normalized == "/" else normalized

    @staticmethod
    def _validate_identifier(value: str, label: str) -> None:
        if not _IDENTIFIER_RE.match(value):
            raise ValueError(f"Invalid {label}: {value}")


def register_builtin_extensions(registry: ExtensionRegistry) -> None:
    if "folio.public" not in registry.layouts:
        registry.register_layout(
            "folio.public",
            import_path="@/components/folio-view-layouts",
            export_name="PublicLayout",
        )


def register_config_components(registry: ExtensionRegistry, config: Any) -> None:
    """Register docs.yaml ``components:`` entries into the registry.

    Directory entries are expanded first (each top-level ``.tsx``/``.jsx``
    file becomes a component named after its PascalCased stem), then named
    specs are registered. Both share the same import-stem deduplication, so a
    directory file and a ``from:`` spec with the same filename stem get
    distinct generated import paths.
    """
    specs = _component_dir_specs(config) + list(getattr(config, "component_specs", []))
    source_stem_counts: dict[str, int] = {}
    for spec in specs:
        source = spec.get("from", spec.get("path"))
        if isinstance(source, str):
            source_stem = Path(source).stem
            source_stem_counts[source_stem] = source_stem_counts.get(source_stem, 0) + 1

    used_import_stems: set[str] = set()
    for spec in specs:
        name = spec.get("name")
        source = spec.get("from", spec.get("path"))
        if not isinstance(name, str) or not isinstance(source, str):
            raise ValueError("Component specs require string 'name' and 'from' fields")

        export_name = spec.get("export", name)
        if not isinstance(export_name, str):
            raise ValueError(f"Component export must be a string: {name}")

        expose = spec.get("expose", {})
        if not isinstance(expose, dict):
            expose = {}

        source_path = Path(source)
        import_stem = _component_import_stem(
            source_path.stem,
            name,
            duplicate_source_stem=source_stem_counts.get(source_path.stem, 0) > 1,
            used_import_stems=used_import_stems,
        )
        registry.register_component(
            name,
            import_path=f"@/components/__folio_components/{import_stem}",
            export_name=export_name,
            expose_mdx=bool(expose.get("mdx", True)),
            source_path=source_path,
            origin="config",
        )


_COMPONENT_FILE_SUFFIXES = (".tsx", ".jsx")


def _component_dir_specs(config: Any) -> list[dict[str, Any]]:
    """Expand ``components:`` directory entries into named component specs.

    Relative directories are anchored to the project directory (mirroring how
    the emitter anchors relative ``source_path`` values). A missing directory
    fails the build loudly; a directory without component files warns so a
    typo'd but existing path does not silently register nothing.
    """
    project_dir = str(getattr(config, "project_dir", "") or "")
    specs: list[dict[str, Any]] = []
    for raw_dir in getattr(config, "component_dirs", []):
        directory = Path(raw_dir)
        if not directory.is_absolute() and project_dir:
            directory = Path(project_dir) / directory
        if not directory.is_dir():
            raise ValueError(f"Component directory not found: {directory}")
        files = sorted(
            path
            for path in directory.iterdir()
            if path.is_file() and path.suffix in _COMPONENT_FILE_SUFFIXES
        )
        if not files:
            warnings.warn(
                f"Component directory contains no .tsx/.jsx files: {directory}",
                UserWarning,
                stacklevel=2,
            )
            continue
        for path in files:
            name = _component_name_from_stem(path.stem)
            if not _IDENTIFIER_RE.match(name):
                raise ValueError(f"Cannot derive a component name from file: {path}")
            specs.append({"name": name, "from": str(path)})
    return specs


def _component_name_from_stem(stem: str) -> str:
    """Derive a PascalCase component name from a file stem.

    ``hero.tsx`` -> ``Hero``; ``my-chart.tsx`` -> ``MyChart``. The file must
    export a named export matching the derived name (same default as the
    ``export:`` field of a named spec).
    """
    parts = [part for part in re.split(r"[^A-Za-z0-9]+", stem) if part]
    return "".join(part[:1].upper() + part[1:] for part in parts)


def _component_import_stem(
    source_stem: str,
    component_name: str,
    *,
    duplicate_source_stem: bool,
    used_import_stems: set[str],
) -> str:
    base = source_stem
    component_segment = _component_file_segment(component_name)
    if duplicate_source_stem:
        base = f"{source_stem}-{component_segment}"

    candidate = base
    if candidate in used_import_stems:
        candidate = f"{base}-{component_segment}"

    index = 2
    while candidate in used_import_stems:
        candidate = f"{base}-{component_segment}-{index}"
        index += 1

    used_import_stems.add(candidate)
    return candidate


def _component_file_segment(value: str) -> str:
    segment = re.sub(r"[^A-Za-z0-9_-]", "_", value).strip("_")
    return segment or "component"
