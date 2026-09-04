"""Publication boundary for Folio for Agents artifacts."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from folio_docs import __version__
from folio_docs.agent_output.contract import (
    FOLIO_AUTHORING_CONTRACT_PATH,
    render_authoring_contract,
)
from folio_docs.agent_output.markdown import mdx_to_markdown
from folio_docs.config import Config
from folio_docs.extensions import ComponentDefinition


class AgentArtifacts:
    """Write machine-readable artifacts beside the Folio Docs site.

    The class owns only agent-facing output. It receives resolved site paths
    from the shared build pipeline and never builds the human frontend.
    """

    def __init__(
        self,
        config: Config,
        *,
        build_dir: str | Path,
        output_dir: str | Path,
        base_path: str = "",
    ) -> None:
        self.config = config
        self.build_dir = Path(build_dir)
        self.output_dir = Path(output_dir)
        self.base_path = base_path

    @property
    def markdown_root(self) -> Path:
        return self.build_dir / "public" / "_folio" / "markdown"

    def markdown_path(self, route: str) -> Path:
        if route in {"", "index"}:
            return self.markdown_root / "index.md"
        return self.markdown_root / f"{route}.md"

    def write_markdown_mirror(self, route: str, content: str) -> Path:
        target = self.markdown_path(route).resolve()
        root = self.markdown_root.resolve()
        if not target.is_relative_to(root):
            raise ValueError(f"Route would write outside page markdown directory: {route}")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(mdx_to_markdown(content), encoding="utf-8")
        return target

    def markdown_mirror_exists(self, route: str) -> bool:
        target = self.markdown_path(route).resolve()
        root = self.markdown_root.resolve()
        if not target.is_relative_to(root):
            raise ValueError(f"Route would access outside page markdown directory: {route}")
        return target.exists()

    def remove_markdown_mirror(self, route: str) -> None:
        target = self.markdown_path(route).resolve()
        root = self.markdown_root.resolve()
        if not target.is_relative_to(root):
            raise ValueError(f"Route would access outside page markdown directory: {route}")
        if target.exists():
            target.unlink()

    def write_authoring_contract(
        self,
        *,
        generated_at: str,
        components: Iterable[ComponentDefinition] | None,
        config_keys: Iterable[str],
        routes: Iterable[str],
    ) -> Path:
        target = self.build_dir / "public" / Path(FOLIO_AUTHORING_CONTRACT_PATH)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(
            render_authoring_contract(
                folio_version=__version__,
                generated_at=generated_at,
                components=components,
                config_keys=config_keys,
                routes=routes,
            ),
            encoding="utf-8",
        )
        return target

    def write_llm_files(
        self,
        llms_txt: str | None = None,
        llms_full_txt: str | None = None,
        *,
        serve: bool = False,
    ) -> None:
        destination = self.build_dir / "public" if serve else self.output_dir
        destination.mkdir(parents=True, exist_ok=True)
        self._write_or_remove(destination, "llms.txt", llms_txt)
        self._write_or_remove(destination, "llms-full.txt", llms_full_txt)
        self._point_robots_at_files(
            destination,
            [
                name
                for name, content in (
                    ("llms.txt", llms_txt),
                    ("llms-full.txt", llms_full_txt),
                )
                if content is not None
            ],
        )

    @staticmethod
    def _write_or_remove(destination: Path, name: str, content: str | None) -> None:
        target = destination / name
        if content is None:
            if target.exists():
                target.unlink()
            return
        target.write_text(content, encoding="utf-8")

    def _point_robots_at_files(self, destination: Path, names: list[str]) -> None:
        robots_path = destination / "robots.txt"
        if not names or not robots_path.exists():
            return

        content = robots_path.read_text(encoding="utf-8")
        lines = [
            f"# {name}: {self._artifact_url(name)}"
            for name in names
            if f"# {name}:" not in content
        ]
        if not lines:
            return
        if content and not content.endswith("\n"):
            content += "\n"
        robots_path.write_text(content + "\n".join(lines) + "\n", encoding="utf-8")

    def _artifact_url(self, name: str) -> str:
        site_url = self.config.site_url.rstrip("/")
        if not site_url.startswith("http"):
            site_url = self.base_path.rstrip("/")
        return f"{site_url}/{name}"
