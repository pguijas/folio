from __future__ import annotations

import os
from pathlib import Path

import folio_agents

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))[
        "project"
    ]
    version = str(project["version"])
    if folio_agents.__version__ != version:
        raise SystemExit(
            f"folio_agents.__version__ is {folio_agents.__version__}, expected {version}"
        )

    requested = os.environ.get("RELEASE_VERSION", "").strip().removeprefix("v")
    ref_type = os.environ.get("GITHUB_REF_TYPE", "")
    ref_name = os.environ.get("GITHUB_REF_NAME", "")
    expected_tag = f"agents-v{version}"
    if ref_type == "tag":
        if ref_name != expected_tag:
            raise SystemExit(f"release tag {ref_name!r} does not match {expected_tag!r}")
        return
    if ref_type == "branch" and ref_name != "main":
        raise SystemExit("workflow_dispatch releases must run from main")
    if requested and requested != version:
        raise SystemExit(
            f"workflow_dispatch version {requested!r} does not match {version!r}"
        )


if __name__ == "__main__":
    main()
