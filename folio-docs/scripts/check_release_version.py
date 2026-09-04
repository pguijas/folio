from __future__ import annotations

import os
from pathlib import Path

import yaml

import folio_docs

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 fallback
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]


def _load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _fail(message: str) -> None:
    raise SystemExit(message)


def main() -> None:
    pyproject = _load_toml(ROOT / "pyproject.toml")
    docs_config = yaml.safe_load(
        (ROOT.parent / "docs.yaml").read_text(encoding="utf-8")
    )
    lock_path = ROOT / "uv.lock"
    if not lock_path.is_file():
        lock_path = ROOT.parent / "uv.lock"
    lock = _load_toml(lock_path)

    project = pyproject["project"]
    package_name = project["name"]
    version = project["version"]
    expected_tag = f"docs-v{version}"

    if folio_docs.__version__ != version:
        _fail(
            f"folio_docs.__version__ is {folio_docs.__version__}, expected {version}"
        )

    if str(docs_config["project"]["version"]) != version:
        _fail(
            "docs.yaml project.version is "
            f"{docs_config['project']['version']}, expected {version}"
        )

    lock_packages = {
        package["name"]: package["version"] for package in lock.get("package", [])
    }
    if lock_packages.get(package_name) != version:
        _fail(f"uv.lock does not pin {package_name}=={version}")

    requested_version = os.environ.get("RELEASE_VERSION", "").strip().removeprefix("v")
    ref_type = os.environ.get("GITHUB_REF_TYPE", "")
    ref_name = os.environ.get("GITHUB_REF_NAME", "")

    if ref_type == "tag":
        if ref_name != expected_tag:
            _fail(f"release tag {ref_name!r} does not match {expected_tag!r}")
        return

    if not ref_type and not requested_version:
        return

    if ref_type == "branch" and ref_name != "main":
        _fail(f"workflow_dispatch releases must run from main, got {ref_name!r}")

    if requested_version != version:
        _fail(
            f"workflow_dispatch version {requested_version!r} does not match {version!r}"
        )


if __name__ == "__main__":
    main()
