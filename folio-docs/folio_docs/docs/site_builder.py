from __future__ import annotations

import json
import os
import re
import shutil
from collections.abc import Iterable
from pathlib import Path

from folio_docs.agent_output.artifacts import AgentArtifacts
from folio_docs.config import Config
from folio_docs.extensions import ComponentDefinition
from folio_docs.docs.extension_emitter import ExtensionEmitter
from folio_docs.agent_output.contract import (
    render_mdx_contract_module,
)
from folio_docs.agent_output.markdown import mdx_to_markdown
from folio_docs.docs.next_runtime import NextRuntime
from folio_docs.docs.template_workspace import (
    TemplateConfigInjector,
    TemplateWorkspace,
    resolve_base_path,
)


class SiteBuilder:
    def __init__(
        self, config: Config, template_dir: str, build_dir: str, verbose: bool = False
    ) -> None:
        self.config = config
        self.template_dir = Path(template_dir)
        self.build_dir = Path(build_dir)
        self.content_dir = self.build_dir / "content"
        self.output_dir = Path(config.output_dir)
        self.verbose = verbose
        self._emitted_routes: set[str] = set()
        self.agents = AgentArtifacts(
            config,
            build_dir=self.build_dir,
            output_dir=self.output_dir,
            base_path=resolve_base_path(config),
        )
        # Set by apply_extensions once the registry exists. Until then the
        # contract falls back to the builtin manifest.
        self._contract_components: tuple[ComponentDefinition, ...] | None = None

    @property
    def manifest_path(self) -> Path:
        return self.build_dir / ".folio-manifest.json"

    def load_manifest(self) -> dict:
        if self.manifest_path.exists():
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        return {"sources": {}}

    def save_manifest(self, manifest: dict) -> None:
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def prepare(self, clean: bool = False) -> None:
        self._emitted_routes = set()
        TemplateWorkspace(
            self.template_dir,
            self.build_dir,
            self.content_dir,
        ).prepare(clean=clean)
        TemplateConfigInjector(self.config, self.build_dir).inject()

    def view_routes(self) -> set[str]:
        """Site-absolute routes of registry views (e.g. {"/roadmap"}).

        Recorded by apply_extensions; valid link targets for check_links.
        """
        return set(getattr(self, "_view_routes", set()))

    def apply_extensions(self, registry: object) -> None:
        # A custom ``template.path`` frontend replaces the bundled template and
        # does not ship the builtin component files, so builtin-origin
        # components must not be injected into its mdx-components.tsx. The
        # bundled template and ``template.overlay_path`` merges (bundled base,
        # user files on top) keep builtin injection enabled. ``project_dir``
        # anchors relative component source paths to the project instead of
        # the process CWD.
        uses_custom_template = bool(self.config.template_path) and not bool(
            self.config.template_overlay_path
        )
        ExtensionEmitter(
            self.build_dir,
            inject_builtins=not uses_custom_template,
            project_dir=self.config.project_dir,
        ).apply(registry)
        self._view_routes = set(getattr(registry, "views", {}))
        self._write_mdx_contract_module(registry.components.values())

    def _write_mdx_contract_module(
        self, components: Iterable[ComponentDefinition]
    ) -> None:
        """Rewrite lib/folio-mdx-contract.ts from the live registry.

        Template preparation writes the module before any plugin has run, so
        the version it writes can only describe the builtin manifest. Once the
        registry exists, the config and plugin components flagged
        ``contract=True`` belong in it too — and the same set is what
        ``write_authoring_contract`` publishes.
        """
        self._contract_components = tuple(components)
        lib_dir = self.build_dir / "lib"
        lib_dir.mkdir(parents=True, exist_ok=True)
        (lib_dir / "folio-mdx-contract.ts").write_text(
            render_mdx_contract_module(self._contract_components),
            encoding="utf-8",
        )

    def write_authoring_contract(
        self,
        config_keys: Iterable[str],
        generated_at: str,
    ) -> Path:
        """Publish the authoring contract as a static file in the export.

        Written under the workspace ``public/`` directory, which the Next
        static export carries through unchanged — the same route the per-page
        Markdown mirrors take. Call it after the extensions are applied, so
        the component list and the emitted routes are complete.
        """
        return self.agents.write_authoring_contract(
            generated_at=generated_at,
            components=self._contract_components,
            config_keys=config_keys,
            routes=[
                self._content_route_to_docs_url(route)
                for route in self.emitted_routes()
            ],
        )

    def _runtime(self) -> NextRuntime:
        return NextRuntime(
            self.template_dir,
            self.build_dir,
            self.output_dir,
            verbose=self.verbose,
        )

    def write_page(self, route: str, content: str) -> None:
        target = self._page_path(route)
        target = target.resolve()
        if not target.is_relative_to(self.content_dir.resolve()):
            raise ValueError(f"Route would write outside content directory: {route}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        self._write_page_markdown(route, content)
        self.register_route(route)

    def copy_page_asset(self, route: str, relative: str, source: Path) -> None:
        """Copy a file a page references to sit beside the generated page.

        MDX compiles ``![alt](shot.png)`` into ``import __img0 from
        "shot.png"``, resolved relative to the generated ``.mdx``. Without the
        file beside it the build does not merely lose the image, it fails:
        "Module not found: Can't resolve 'shot.png'". So a documentation page
        that shows a screenshot has to carry the screenshot into the content
        tree, at the same relative path the author wrote.
        """
        target = (self._page_path(route).parent / relative).resolve()
        if not target.is_relative_to(self.content_dir.resolve()):
            raise ValueError(
                f"Asset would be written outside the content directory: "
                f"{relative} (from route {route})"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def copy_static_asset(self, relative: str, source: Path) -> None:
        """Copy a file into ``public/``, where the site serves it verbatim.

        ``copy_page_asset`` puts a file beside a generated page so MDX can
        import it; this puts a file on the site so a reader can open it. It is
        how a plugin publishes something it does not own a page for, in the
        same tree as ``/_folio/markdown/<route>.md`` and the preview examples.
        The file is served exactly as it is on disk, so nothing here renders,
        rewrites, or interprets it.
        """
        public_root = (self.build_dir / "public").resolve()
        target = (public_root / relative).resolve()
        if target == public_root or not target.is_relative_to(public_root):
            raise ValueError(
                f"Static asset would be written outside the public directory: "
                f"{relative}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    def remove_static_tree(self, relative: str) -> None:
        """Drop a subtree of ``public/`` before republishing it.

        Warm builds keep the workspace, so a file that stopped existing in the
        project would otherwise stay on the site forever — deleted from the
        repository and still served. Emitters that publish a whole directory
        clear it first and write what exists now.
        """
        public_root = (self.build_dir / "public").resolve()
        target = (public_root / relative).resolve()
        if target == public_root or not target.is_relative_to(public_root):
            raise ValueError(
                f"Static tree would be removed outside the public directory: {relative}"
            )
        if target.is_dir():
            shutil.rmtree(target)

    def register_route(self, route: str) -> None:
        """Record a route as a live page so link-checking treats it as valid.

        Plugins should call this for every page they own — even when they skip
        ``write_page`` because the page already exists from a prior build — so
        internal links to plugin pages are not flagged as broken.
        """
        self._emitted_routes.add(route)

    def emitted_routes(self) -> set[str]:
        """Routes recorded via write_page/register_route since the last prepare()."""
        return set(self._emitted_routes)

    def restore_emitted_routes(self, routes: set[str]) -> None:
        """Reset the emitted-routes set to a snapshot taken via emitted_routes().

        Used by the build core to roll back routes half-registered by a failed
        ``emit_assets`` hookimpl: a plugin that crashed between
        ``register_route`` and ``write_page`` must not leave a missing page
        whitelisted for the link checker.
        """
        self._emitted_routes = set(routes)

    def page_exists(self, route: str) -> bool:
        target = self._page_path(route)
        target = target.resolve()
        if not target.is_relative_to(self.content_dir.resolve()):
            raise ValueError(f"Route would access outside content directory: {route}")
        return target.exists()

    def read_page(self, route: str) -> str:
        """Return the current on-disk content of a page in the content dir.

        Plugins use this on warm builds for write-if-changed refreshes of
        pages they generated on a prior build (e.g. the openapi and kanban
        plugins compare the existing page against the regenerated content
        before rewriting it).
        """
        target = self._page_path(route).resolve()
        if not target.is_relative_to(self.content_dir.resolve()):
            raise ValueError(f"Route would access outside content directory: {route}")
        return target.read_text(encoding="utf-8")

    def page_markdown_exists(self, route: str) -> bool:
        return self.agents.markdown_mirror_exists(route)

    def list_pages(self, prefix: str) -> list[str]:
        """Routes of the pages currently on disk under a content-dir prefix.

        The counterpart of ``remove_page`` for plugins that generate a
        variable set of pages: a warm build keeps the workspace, so a page
        generated for something that no longer exists has to be found before
        it can be dropped, and only its owner knows which marker to look for.
        """
        content_root = self.content_dir.resolve()
        base = (content_root / prefix).resolve() if prefix else content_root
        if not base.is_relative_to(content_root):
            raise ValueError(f"Prefix would list outside content directory: {prefix}")
        if not base.is_dir():
            return []
        routes = []
        for page in sorted(base.rglob("*.mdx")):
            routes.append(page.relative_to(content_root).with_suffix("").as_posix())
        return routes

    def remove_page(self, route: str) -> None:
        target = self._page_path(route)
        target = target.resolve()
        if not target.is_relative_to(self.content_dir.resolve()):
            raise ValueError(f"Route would access outside content directory: {route}")
        if target.exists():
            target.unlink()
        self.agents.remove_markdown_mirror(route)

    def write_meta(self, directory: str, meta_json: str) -> None:
        if directory:
            meta_dir = self.content_dir / directory
        else:
            meta_dir = self.content_dir
        meta_dir = meta_dir.resolve()
        if not meta_dir.is_relative_to(self.content_dir.resolve()):
            raise ValueError(
                f"Directory would write outside content directory: {directory}"
            )
        meta_dir.mkdir(parents=True, exist_ok=True)
        (meta_dir / "_meta.ts").write_text(meta_json, encoding="utf-8")

    def read_meta(self, directory: str) -> str:
        if directory:
            meta_dir = self.content_dir / directory
        else:
            meta_dir = self.content_dir
        meta_dir = meta_dir.resolve()
        if not meta_dir.is_relative_to(self.content_dir.resolve()):
            raise ValueError(
                f"Directory would access outside content directory: {directory}"
            )
        meta_path = meta_dir / "_meta.ts"
        if not meta_path.exists():
            return ""
        return meta_path.read_text(encoding="utf-8")

    def remove_meta_tree(self, directory: str) -> None:
        if directory:
            meta_dir = self.content_dir / directory
        else:
            meta_dir = self.content_dir
        meta_dir = meta_dir.resolve()
        if not meta_dir.is_relative_to(self.content_dir.resolve()):
            raise ValueError(
                f"Directory would access outside content directory: {directory}"
            )
        if not meta_dir.exists():
            return
        for meta_path in sorted(meta_dir.rglob("_meta.ts")):
            meta_path.unlink()

    def write_llm_files(
        self,
        llms_txt: str | None = None,
        llms_full_txt: str | None = None,
        *,
        serve: bool = False,
    ) -> None:
        self.agents.write_llm_files(
            llms_txt,
            llms_full_txt,
            serve=serve,
        )

    def write_preview_examples(self, examples_dir: str | Path) -> None:
        """Build named documentation preview examples into public static assets."""
        examples_path = Path(examples_dir)
        target_root = self.build_dir / "public" / "_folio" / "examples"
        if target_root.exists():
            shutil.rmtree(target_root)
        if not examples_path.exists():
            return

        for example_dir in sorted(
            path for path in examples_path.iterdir() if path.is_dir()
        ):
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", example_dir.name):
                continue

            config_path = example_dir / "docs.yaml"
            if not config_path.is_file():
                continue

            target_dir = target_root / example_dir.name
            target_dir.parent.mkdir(parents=True, exist_ok=True)
            self._build_preview_example_project(example_dir, target_dir)
            self._write_preview_example_manifest(example_dir, target_dir)

    def _build_preview_example_project(
        self, example_dir: Path, target_dir: Path
    ) -> None:
        from folio_docs.build import run_build

        example_build_dir = self.build_dir / ".preview-examples" / example_dir.name
        self._reset_preview_example_workspace(example_build_dir)
        original_base_path = os.environ.get("FOLIO_BASE_PATH")
        os.environ["FOLIO_BASE_PATH"] = self._preview_example_base_path(
            example_dir.name
        )
        try:
            run_build(
                example_dir,
                serve=False,
                verbose=False,
                config_file="docs.yaml",
                clean=False,
                output_override=str(target_dir),
                include_versions=False,
                build_dir_override=str(example_build_dir),
                quiet=True,
            )
        finally:
            if original_base_path is None:
                os.environ.pop("FOLIO_BASE_PATH", None)
            else:
                os.environ["FOLIO_BASE_PATH"] = original_base_path

    @staticmethod
    def _reset_preview_example_workspace(example_build_dir: Path) -> None:
        for name in [
            ".folio-build.log",
            ".folio-manifest.json",
            ".next",
            "content",
            "out",
            "public",
        ]:
            path = example_build_dir / name
            if path.is_dir():
                shutil.rmtree(path)
            elif path.exists():
                path.unlink()

    def _preview_example_base_path(self, example_name: str) -> str:
        parent_base = resolve_base_path(self.config).rstrip("/")
        return f"{parent_base}/_folio/examples/{example_name}"

    def _write_preview_example_manifest(
        self, example_dir: Path, target_dir: Path
    ) -> None:
        target_files_dir = target_dir / "files"
        manifest_files = []
        for source_path in self._preview_example_source_paths(example_dir):
            rel_path = source_path.relative_to(example_dir)
            target_path = target_files_dir / rel_path
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
            rel_url = rel_path.as_posix()
            manifest_files.append(
                {
                    "path": rel_url,
                    "url": f"/_folio/examples/{example_dir.name}/files/{rel_url}",
                    "language": self._preview_example_language(rel_path),
                }
            )

        (target_dir / "manifest.json").write_text(
            json.dumps({"files": manifest_files}, ensure_ascii=True, indent=2) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _preview_example_source_paths(example_dir: Path) -> list[Path]:
        ignored_dirs = {
            ".build",
            ".git",
            ".next",
            "__pycache__",
            "_site",
            "node_modules",
            "out",
        }
        ignored_files = {"design-reference.html", "preview.html"}
        source_paths = []
        for source_path in sorted(
            path for path in example_dir.rglob("*") if path.is_file()
        ):
            rel_path = source_path.relative_to(example_dir)
            if source_path.name in ignored_files:
                continue
            if any(
                part in ignored_dirs or part.startswith(".") for part in rel_path.parts
            ):
                continue
            source_paths.append(source_path)
        return source_paths

    def _page_path(self, route: str) -> Path:
        if route == "index" or route == "":
            return self.content_dir / "index.mdx"
        return self.content_dir / f"{route}.mdx"

    def _page_markdown_dir(self) -> Path:
        return self.agents.markdown_root

    def _page_markdown_path(self, route: str) -> Path:
        return self.agents.markdown_path(route)

    def _write_page_markdown(self, route: str, content: str) -> None:
        self.agents.write_markdown_mirror(route, content)

    @staticmethod
    def _preview_example_language(path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in {".md", ".mdx"}:
            return "markdown"
        if suffix in {".yml", ".yaml"}:
            return "yaml"
        if suffix == ".py":
            return "python"
        if suffix in {".ts", ".tsx"}:
            return "tsx"
        if suffix == ".json":
            return "json"
        return suffix.removeprefix(".") or "text"

    @staticmethod
    def _mdx_to_markdown(content: str) -> str:
        return mdx_to_markdown(content)

    def write_search_index(self) -> None:
        """Write a lightweight search index for `folio serve` development mode."""
        index_path = self.build_dir / "lib" / "search-index.ts"
        index_path.parent.mkdir(parents=True, exist_ok=True)

        documents = []
        if self.config.search_enabled and self.content_dir.exists():
            for page_path in sorted(self.content_dir.rglob("*.mdx")):
                if page_path.name.startswith("_"):
                    continue
                raw = page_path.read_text(encoding="utf-8")
                route = (
                    page_path.relative_to(self.content_dir).with_suffix("").as_posix()
                )
                url = self._content_route_to_docs_url(route)
                documents.append(
                    {
                        "url": url,
                        "title": self._mdx_search_title(raw, route),
                        "content": self._mdx_search_content(raw),
                    }
                )

        index_path.write_text(
            "export interface FolioSearchDocument {\n"
            "  url: string\n"
            "  title: string\n"
            "  content: string\n"
            "}\n\n"
            "export const folioSearchDocuments: FolioSearchDocument[] = "
            f"{json.dumps(documents, ensure_ascii=True, indent=2)}\n",
            encoding="utf-8",
        )

    def _content_route_to_docs_url(self, route: str) -> str:
        docs_route_base = self.config.docs_route_base.rstrip("/") or "/docs"
        if route in ("", "index"):
            return f"{docs_route_base}/"
        if route.endswith("/index"):
            route = route.removesuffix("/index")
        return f"{docs_route_base}/{route}/"

    @classmethod
    def _mdx_search_title(cls, raw: str, route: str) -> str:
        frontmatter = re.match(r"\A---\n(?P<body>.*?)\n---", raw, re.DOTALL)
        if frontmatter:
            title_match = re.search(
                r"^title:\s*(?P<title>.+?)\s*$", frontmatter.group("body"), re.MULTILINE
            )
            if title_match:
                return (
                    cls._clean_search_text(title_match.group("title")).strip("\"'")
                    or route
                )

        heading_match = re.search(r"^#\s+(?P<title>.+?)\s*$", raw, re.MULTILINE)
        if heading_match:
            return cls._clean_search_text(heading_match.group("title")) or route

        return route.removesuffix("/index").split("/")[-1] or "Docs"

    @classmethod
    def _mdx_search_content(cls, raw: str) -> str:
        without_frontmatter = re.sub(r"\A---\n.*?\n---", " ", raw, flags=re.DOTALL)
        without_code = re.sub(r"```.*?```", " ", without_frontmatter, flags=re.DOTALL)
        without_jsx = re.sub(r"<[^>]+>", " ", without_code)
        without_expressions = re.sub(r"\{[^{}]*\}", " ", without_jsx)
        return cls._clean_search_text(without_expressions)

    @staticmethod
    def _clean_search_text(value: str) -> str:
        text = re.sub(r"[\[\]()`*_#>|]", " ", value)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def install_deps(self) -> bool:
        return self._runtime().install_deps()

    def build(self, **kwargs) -> None:
        self._runtime().build(**kwargs)

    @staticmethod
    def kill_port(port: int) -> bool:
        return NextRuntime.kill_port(port)

    def serve(self, port: int = 4321, *, kill_existing: bool = False):
        return self._runtime().serve(port, kill_existing=kill_existing)
