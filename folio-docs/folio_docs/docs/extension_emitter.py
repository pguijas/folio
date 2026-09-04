from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from folio_docs.extensions import (
    ComponentDefinition,
    DataModuleDefinition,
    ExtensionRegistry,
    LayoutDefinition,
    ViewDefinition,
)
from folio_docs.agent_output.contract import (
    has_component_entry,
    import_statements,
    strip_import_statements,
    strip_js_comments,
)


class ExtensionEmitter:
    def __init__(
        self,
        build_dir: str | Path,
        *,
        inject_builtins: bool = True,
        project_dir: str = "",
    ) -> None:
        """Emit registry extensions into ``build_dir``.

        ``inject_builtins=False`` keeps builtin-origin components out of
        ``mdx-components.tsx`` — used for custom ``template.path`` builds that
        do not bundle the builtin component files. ``project_dir`` anchors
        relative component ``source_path`` values (instead of the process CWD).
        """
        self.build_dir = Path(build_dir)
        self.inject_builtins = inject_builtins
        self.project_dir = project_dir

    def apply(self, registry: ExtensionRegistry) -> None:
        self._copy_components(registry)
        self._write_data_modules(registry)
        self._inject_mdx_components(registry)
        self._write_views(registry)

    def _copy_components(self, registry: ExtensionRegistry) -> None:
        for component in registry.components.values():
            source_path = component.source_path
            if source_path is None:
                continue
            source = Path(source_path)
            if not source.is_absolute() and self.project_dir:
                source = Path(self.project_dir) / source
            if not source.is_file():
                raise FileNotFoundError(f"Component source not found: {source}")
            target = self._component_target(component, source)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)

    def _component_target(self, component: ComponentDefinition, source: Path) -> Path:
        import_path = component.import_path
        if import_path.startswith("@/"):
            rel_path = Path(*import_path.removeprefix("@/").split("/"))
            if rel_path.suffix == "":
                rel_path = rel_path.with_suffix(source.suffix)
            target = (self.build_dir / rel_path).resolve()
        else:
            target = (
                self.build_dir / "components" / "__folio_components" / source.name
            ).resolve()

        if not target.is_relative_to(self.build_dir.resolve()):
            raise ValueError(
                f"Component import path would write outside build directory: {import_path}"
            )
        return target

    def _write_data_modules(self, registry: ExtensionRegistry) -> None:
        for module in registry.data_modules.values():
            self._write_data_module(module)

    def _write_data_module(self, module: DataModuleDefinition) -> None:
        module_path = module.module_path or f"__folio_data/{module.name}"
        rel_path = Path(module_path)
        if rel_path.is_absolute() or ".." in rel_path.parts:
            raise ValueError(f"Data module path must stay inside lib: {module_path}")
        if rel_path.suffix != ".ts":
            rel_path = rel_path.with_suffix(".ts")
        target = (self.build_dir / "lib" / rel_path).resolve()
        lib_dir = (self.build_dir / "lib").resolve()
        if not target.is_relative_to(lib_dir):
            raise ValueError(f"Data module path would write outside lib: {module_path}")
        target.parent.mkdir(parents=True, exist_ok=True)
        type_source = module.type_source
        if type_source and not type_source.endswith("\n"):
            type_source += "\n"
        data = json.dumps(module.data, ensure_ascii=True, indent=2)
        type_annotation = module.type_annotation
        annotation = f": {type_annotation}" if type_annotation else ""
        target.write_text(
            f"{type_source}export const {module.export_name}{annotation} = {data}\n",
            encoding="utf-8",
        )

    def _inject_mdx_components(self, registry: ExtensionRegistry) -> None:
        mdx_path = self.build_dir / "mdx-components.tsx"
        if not mdx_path.exists():
            return
        components = [
            component
            for component in registry.components.values()
            if component.expose_mdx
            and (self.inject_builtins or component.origin != "builtin")
        ]
        if not components:
            return

        content = mdx_path.read_text(encoding="utf-8")
        # Skip components already wired into the template (e.g. bundled
        # builtins). The probe is structural, not textual: an entry counts as
        # present when the name appears as a components-mapping entry (any
        # indentation, `Name,`/`Name:` or an `as Name` re-export) outside
        # comments and imports, and an import counts as present when any
        # existing import statement already binds the symbol — regardless of
        # quoting, path, or formatting. Re-injecting a wired component would
        # duplicate identifiers, especially for multi-export modules whose
        # template import combines several names
        # (`import { Tabs, TabItem } from ...`).
        code = strip_js_comments(content)
        imports_text = "\n".join(import_statements(code))
        entry_code = strip_import_statements(code)
        pending = [
            component
            for component in components
            if not has_component_entry(entry_code, component.name)
        ]
        import_lines = [
            self._component_import_line(component)
            for component in pending
            if not re.search(rf"\b{re.escape(component.name)}\b", imports_text)
        ]
        entry_lines = [f"    {component.name}," for component in pending]

        # Nothing to inject (e.g. only bundled builtins were registered): leave
        # the file — including the placeholder comments — untouched so the build
        # output is unchanged and later injections still find the markers.
        if not import_lines and not entry_lines:
            return

        if import_lines:
            imports = "\n".join(import_lines)
            if "__FOLIO_COMPONENT_IMPORTS__" in content:
                content = content.replace("// __FOLIO_COMPONENT_IMPORTS__", imports)
            else:
                content = f"{imports}\n{content}"

        if entry_lines:
            entries = "\n".join(entry_lines)
            if "__FOLIO_COMPONENT_ENTRIES__" in content:
                content = content.replace("    // __FOLIO_COMPONENT_ENTRIES__", entries)
            elif "...components," in content:
                content = content.replace(
                    "    ...components,", f"{entries}\n    ...components,", 1
                )

        mdx_path.write_text(content, encoding="utf-8")

    def _write_views(self, registry: ExtensionRegistry) -> None:
        for view in registry.views.values():
            self._write_view(view, registry)

    def _write_view(self, view: ViewDefinition, registry: ExtensionRegistry) -> None:
        # Compute depth from the view's normalized route before _app_route_path
        # processes it. This keeps the normalization consistent with the route
        # path computation below.
        normalized = view.path.strip("/")
        if not normalized:
            depth = 0
        else:
            depth = len([s for s in normalized.split("/") if s])
        path_to_root = "." if depth == 0 else "../" * depth
        path_to_root = path_to_root.rstrip("/")

        page_path = self._app_route_path(view.path)
        page_path.parent.mkdir(parents=True, exist_ok=True)
        layout = registry.layouts[view.layout]
        components = registry.components
        imports = [self._layout_import_line(layout)]
        used_components = {
            block.component for blocks in view.slots.values() for block in blocks
        }
        imports.extend(
            self._component_import_line(components[name])
            for name in sorted(used_components)
        )

        layout_props = dict(view.props)
        title = view.title
        if title:
            layout_props.setdefault("title", title)
        # pathToRoot lands in every view's layoutProps. Only the folio_docs.public
        # layout uses it today; other layouts ignore unknown props.
        layout_props["pathToRoot"] = path_to_root

        prop_constants: list[str] = []
        rendered_blocks: list[str] = []
        index = 0
        for slot_name, blocks in view.slots.items():
            if slot_name != "main":
                rendered_blocks.append(f"        {{/* Slot: {slot_name} */}}")
            for block in blocks:
                component_name = block.component
                props = block.props
                if props:
                    const_name = f"block{index}Props"
                    prop_constants.append(
                        f"const {const_name} = {json.dumps(props, ensure_ascii=True, indent=2)}"
                    )
                    rendered_blocks.append(
                        f"        <{component_name} {{...{const_name}}} />"
                    )
                else:
                    rendered_blocks.append(f"        <{component_name} />")
                index += 1

        component_body = "\n".join(rendered_blocks) or "        {null}"
        constants = "\n\n".join(
            [
                f"const layoutProps = {json.dumps(layout_props, ensure_ascii=True, indent=2)}"
            ]
            + prop_constants
        )
        # The view title becomes the browser tab title; without this every
        # public view inherits the root layout's bare project name.
        metadata_export = (
            f"export const metadata = {{ title: {json.dumps(title, ensure_ascii=True)} }}\n\n"
            if title
            else ""
        )
        content = (
            "\n".join(imports)
            + "\n\n"
            + constants
            + "\n\n"
            + metadata_export
            + "export default function FolioExtensionView() {\n"
            + "  return (\n"
            + f"    <{layout.export_name} {{...layoutProps}}>\n"
            + component_body
            + "\n"
            + f"    </{layout.export_name}>\n"
            + "  )\n"
            + "}\n"
        )
        page_path.write_text(content, encoding="utf-8")

    def _app_route_path(self, route: str) -> Path:
        normalized = route.strip("/")
        if not normalized:
            target = self.build_dir / "app" / "page.tsx"
        else:
            rel = Path(*normalized.split("/"))
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError(f"Route would write outside app directory: {route}")
            target = self.build_dir / "app" / rel / "page.tsx"
        target = target.resolve()
        app_dir = (self.build_dir / "app").resolve()
        if not target.is_relative_to(app_dir):
            raise ValueError(f"Route would write outside app directory: {route}")
        return target

    @staticmethod
    def _component_import_line(component: ComponentDefinition) -> str:
        name = component.name
        export_name = component.export_name
        import_path = component.import_path
        imported_name = export_name or name
        if imported_name == "default":
            return f'import {name} from "{import_path}"'
        if imported_name == name:
            return f'import {{ {name} }} from "{import_path}"'
        return f'import {{ {imported_name} as {name} }} from "{import_path}"'

    @staticmethod
    def _layout_import_line(layout: LayoutDefinition) -> str:
        export_name = layout.export_name
        import_path = layout.import_path
        if export_name == "default":
            return f'import Layout from "{import_path}"'
        return f'import {{ {export_name} }} from "{import_path}"'
