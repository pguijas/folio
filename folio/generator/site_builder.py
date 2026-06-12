from __future__ import annotations

import json
import os
import re
import shutil
from pathlib import Path

from folio.config import Config
from folio.generator.extension_emitter import ExtensionEmitter
from folio.generator.next_runtime import NextRuntime
from folio.generator.static_rewriter import StaticAssetRewriter
from folio.generator.template_workspace import (
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
        TemplateWorkspace(
            self.template_dir,
            self.build_dir,
            self.content_dir,
        ).prepare(clean=clean)
        TemplateConfigInjector(self.config, self.build_dir).inject()

    def apply_extensions(self, registry: object) -> None:
        ExtensionEmitter(self.build_dir).apply(registry)

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

    def page_exists(self, route: str) -> bool:
        target = self._page_path(route)
        target = target.resolve()
        if not target.is_relative_to(self.content_dir.resolve()):
            raise ValueError(f"Route would access outside content directory: {route}")
        return target.exists()

    def page_markdown_exists(self, route: str) -> bool:
        target = self._page_markdown_path(route).resolve()
        if not target.is_relative_to(self._page_markdown_dir().resolve()):
            raise ValueError(
                f"Route would access outside page markdown directory: {route}"
            )
        return target.exists()

    def remove_page(self, route: str) -> None:
        target = self._page_path(route)
        target = target.resolve()
        if not target.is_relative_to(self.content_dir.resolve()):
            raise ValueError(f"Route would access outside content directory: {route}")
        if target.exists():
            target.unlink()
        markdown_target = self._page_markdown_path(route).resolve()
        if not markdown_target.is_relative_to(self._page_markdown_dir().resolve()):
            raise ValueError(
                f"Route would access outside page markdown directory: {route}"
            )
        if markdown_target.exists():
            markdown_target.unlink()

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
        self, llms_txt: str | None = None, llms_full_txt: str | None = None
    ) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._write_or_remove_llm_file("llms.txt", llms_txt)
        self._write_or_remove_llm_file("llms-full.txt", llms_full_txt)

    def _write_or_remove_llm_file(self, name: str, content: str | None) -> None:
        target = self.output_dir / name
        if content is None:
            if target.exists():
                target.unlink()
            return
        target.write_text(content, encoding="utf-8")

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
        from folio.build import run_build

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
        return self.build_dir / "public" / "_folio" / "markdown"

    def _page_markdown_path(self, route: str) -> Path:
        if route == "index" or route == "":
            return self._page_markdown_dir() / "index.md"
        return self._page_markdown_dir() / f"{route}.md"

    def _write_page_markdown(self, route: str, content: str) -> None:
        target = self._page_markdown_path(route).resolve()
        markdown_root = self._page_markdown_dir().resolve()
        if not target.is_relative_to(markdown_root):
            raise ValueError(
                f"Route would write outside page markdown directory: {route}"
            )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self._mdx_to_markdown(content), encoding="utf-8")

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
        markdown = re.sub(r"\A---\n.*?\n---\n?", "", content, flags=re.DOTALL)
        markdown = re.sub(r"^import\s+.+$", "", markdown, flags=re.MULTILINE)
        markdown = re.sub(r"^export\s+.+$", "", markdown, flags=re.MULTILINE)
        markdown = re.sub(r"</?[A-Z][A-Za-z0-9]*(?:\s+[^<>]*)?>", "", markdown)
        markdown = re.sub(r"<[A-Z][A-Za-z0-9]*(?:\s+[^<>]*)?/>", "", markdown)
        markdown = re.sub(r"\n{3,}", "\n\n", markdown)
        return markdown.strip() + "\n"

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

    @staticmethod
    def _content_route_to_docs_url(route: str) -> str:
        if route in ("", "index"):
            return "/docs/"
        if route.endswith("/index"):
            route = route.removesuffix("/index")
        return f"/docs/{route}/"

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

    def _fix_asset_paths(self) -> None:
        StaticAssetRewriter(self.output_dir).fix_asset_paths()

    @staticmethod
    def kill_port(port: int) -> bool:
        return NextRuntime.kill_port(port)

    def serve(self, port: int = 4321, *, kill_existing: bool = False):
        return self._runtime().serve(port, kill_existing=kill_existing)
