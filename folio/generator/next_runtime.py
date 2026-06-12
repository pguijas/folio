from __future__ import annotations

import hashlib
import os
import shutil
import socket
import subprocess
from pathlib import Path
from typing import Callable

from folio.generator.static_rewriter import StaticAssetRewriter


class NextRuntime:
    def __init__(
        self,
        template_dir: str | Path,
        build_dir: str | Path,
        output_dir: str | Path,
        *,
        verbose: bool = False,
    ) -> None:
        self.template_dir = Path(template_dir)
        self.build_dir = Path(build_dir)
        self.output_dir = Path(output_dir)
        self.verbose = verbose

    def install_deps(self) -> bool:
        """Install dependencies if needed. Returns True if install ran."""
        self._check_dependencies()

        node_modules = self.build_dir / "node_modules"
        template_lock = self.template_dir / "pnpm-lock.yaml"
        build_lock = self.build_dir / "pnpm-lock.yaml"
        has_complete_node_modules = node_modules.exists() and self._has_working_next()

        needs_install = not has_complete_node_modules or self._file_hash(
            template_lock
        ) != self._file_hash(build_lock)

        if needs_install:
            if node_modules.exists() and not has_complete_node_modules:
                shutil.rmtree(node_modules)
            try:
                subprocess.run(
                    ["pnpm", "install", "--frozen-lockfile"],
                    cwd=self.build_dir,
                    check=True,
                    capture_output=not self.verbose,
                )
            except subprocess.CalledProcessError as e:
                stderr = e.stderr.decode() if e.stderr else ""
                stdout = e.stdout.decode() if e.stdout else ""
                raise RuntimeError(f"pnpm install failed:\n{stderr}\n{stdout}") from e

        self._patch_nextra_schema()
        self._patch_nextra_generated_content_timestamps()
        return needs_install

    def build(
        self,
        *,
        log_path: str | Path | None = None,
        output_callback: Callable[[str], None] | None = None,
    ) -> None:
        log_path = Path(log_path) if log_path else self.build_dir / ".folio-build.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        self._remove_stale_build_artifacts()
        output_parts: list[str] = []
        with log_path.open("w", encoding="utf-8") as log_file:
            proc = subprocess.Popen(
                ["pnpm", "run", "build"],
                cwd=self.build_dir,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            if proc.stdout is not None:
                for line in proc.stdout:
                    output_parts.append(line)
                    log_file.write(line)
                    log_file.flush()
                    if output_callback is not None:
                        output_callback(line)
                    elif self.verbose:
                        print(line, end="")
            returncode = proc.wait()
        if returncode:
            output = "".join(output_parts)
            raise RuntimeError(f"pnpm build failed:\n{output}\nFull log: {log_path}")
        self.copy_static_output()

    def _remove_stale_build_artifacts(self) -> None:
        for path in [self.build_dir / "out", self.build_dir / ".next" / "dev"]:
            if path.exists():
                shutil.rmtree(path)

    def copy_static_output(self) -> None:
        out_dir = self.build_dir / "out"
        if not out_dir.exists():
            return
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        shutil.copytree(out_dir, self.output_dir)
        StaticAssetRewriter(self.output_dir).fix_asset_paths()

    def serve(
        self,
        port: int = 4321,
        *,
        kill_existing: bool = False,
    ) -> subprocess.Popen:
        if self.is_port_in_use(port):
            if kill_existing:
                self.kill_port(port)
            else:
                raise RuntimeError(
                    f"Port {port} is already in use. Stop the existing process "
                    "or rerun with --kill-existing."
                )
        self._remove_stale_build_artifacts()
        return subprocess.Popen(
            ["pnpm", "exec", "next", "dev", "--turbopack", "--port", str(port)],
            cwd=self.build_dir,
        )

    def _check_dependencies(self) -> None:
        if not shutil.which("node"):
            raise RuntimeError(
                "Node.js is required but not found. Install it from https://nodejs.org/"
            )
        if not shutil.which("pnpm"):
            raise RuntimeError(
                "pnpm is required but not found. Install it with: npm install -g pnpm"
            )

    def _has_next_binary(self) -> bool:
        binary = "next.cmd" if os.name == "nt" else "next"
        return (self.build_dir / "node_modules" / ".bin" / binary).exists()

    def _has_working_next(self) -> bool:
        if not self._has_next_binary():
            return False
        try:
            result = subprocess.run(
                ["pnpm", "exec", "next", "--version"],
                cwd=self.build_dir,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.SubprocessError):
            return False
        return result.returncode == 0

    def _patch_nextra_schema(self) -> None:
        """Patch nextra-theme-docs Zod schema bug where children is validated
        as nonoptional but has already been destructured out of props.
        """
        nm = self.build_dir / "node_modules"
        for schema_path in nm.rglob("nextra-theme-docs/dist/schemas.js"):
            content = schema_path.read_text(encoding="utf-8")
            patched = content.replace(
                "children: reactNode,", "children: reactNode.optional(),", 1
            )
            if patched != content:
                schema_path.write_text(patched, encoding="utf-8")

    def _patch_nextra_generated_content_timestamps(self) -> None:
        """Skip Git timestamp lookups for Folio-generated MDX content."""
        nm = self.build_dir / "node_modules"
        target = (
            "const lastCommitTime = IS_PRODUCTION ? "
            "await getLastCommitTime(resourcePath) : NOW;"
        )
        replacement = (
            "const isGeneratedFolioContent = resourcePath.includes(`${CWD}/content/`);\n"
            "  const lastCommitTime = IS_PRODUCTION ? isGeneratedFolioContent ? "
            "void 0 : await getLastCommitTime(resourcePath) : NOW;"
        )
        for loader_path in nm.rglob("nextra/dist/server/loader.js"):
            content = loader_path.read_text(encoding="utf-8")
            if "isGeneratedFolioContent" in content:
                continue
            patched = content.replace(target, replacement, 1)
            if patched != content:
                loader_path.write_text(patched, encoding="utf-8")

    @staticmethod
    def _file_hash(path: Path) -> str:
        if not path.exists():
            return ""
        return hashlib.sha256(path.read_bytes()).hexdigest()

    @staticmethod
    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            return probe.connect_ex(("localhost", port)) == 0

    @staticmethod
    def kill_port(port: int) -> bool:
        """Kill any process listening on the given port. Returns True if a process was killed."""
        import signal

        try:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True,
            )
            pids = result.stdout.strip().split()
            if not pids or not pids[0]:
                return False
            for pid in pids:
                os.kill(int(pid), signal.SIGKILL)
            return True
        except (OSError, ValueError):
            return False
