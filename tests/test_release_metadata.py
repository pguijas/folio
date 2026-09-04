from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on Python 3.10
    import tomli as tomllib

import pytest
import yaml

import folio
from folio.config import load_config
from scripts import check_release_version


ROOT = Path(__file__).parents[1]
ACTION_SHA_RE = r"uses: [\w.-]+/[\w.-]+(?:/[\w.-]+)?@[0-9a-f]{40}"


def test_release_version_is_consistent() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    config = load_config(ROOT / "docs.yaml")

    assert pyproject["project"]["version"] == "0.3.0"
    assert folio.__version__ == "0.3.0"
    assert config.project_version == "0.3.0"


def test_release_version_check_accepts_manual_dispatch_from_main(monkeypatch) -> None:
    monkeypatch.setenv("RELEASE_VERSION", folio.__version__)
    monkeypatch.setenv("GITHUB_REF_TYPE", "branch")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")

    check_release_version.main()


def test_release_version_check_rejects_manual_dispatch_from_non_main(
    monkeypatch,
) -> None:
    monkeypatch.setenv("RELEASE_VERSION", folio.__version__)
    monkeypatch.setenv("GITHUB_REF_TYPE", "branch")
    monkeypatch.setenv("GITHUB_REF_NAME", "feature-branch")

    with pytest.raises(SystemExit) as exc_info:
        check_release_version.main()

    assert "workflow_dispatch releases must run from main" in str(exc_info.value)


def test_project_docs_are_configured_for_multi_version_builds() -> None:
    config = yaml.safe_load((ROOT / "docs.yaml").read_text())

    assert config["versions"] == [
        {"label": "v0.3.0 (latest)", "path": "latest"},
        {
            "label": "v0.2.1",
            "path": "v0.2",
            "ref": "v0.2.1",
        },
        {
            "label": "v0.1.0",
            "path": "v0.1",
            "ref": "v0.1.0",
        },
        {
            "label": "v0.0.1",
            "path": "v0.0",
            "ref": "v0.0.1",
            "default_path": "docs/",
        },
    ]


def test_wheel_includes_bundled_template_workspace() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    wheel_target = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]
    force_include = wheel_target["force-include"]

    assert force_include["template/package.json"] == "folio/template/package.json"
    assert force_include["template/pnpm-lock.yaml"] == "folio/template/pnpm-lock.yaml"
    assert force_include["template/pnpm-workspace.yaml"] == (
        "folio/template/pnpm-workspace.yaml"
    )
    assert force_include["template/app"] == "folio/template/app"
    assert force_include["template/components"] == "folio/template/components"
    assert force_include["template/theme"] == "folio/template/theme"
    assert "template" not in force_include
    # The template must install inside the folio package, never as a generic
    # top-level `template` directory in site-packages.
    assert all(
        target.startswith("folio/template/") for target in force_include.values()
    )


def test_forced_includes_are_safe_for_clean_checkouts() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    wheel_target = pyproject["tool"]["hatch"]["build"]["targets"]["wheel"]
    force_include = wheel_target["force-include"]

    missing_sources = [
        source for source in force_include if not (ROOT / source).exists()
    ]
    assert missing_sources == []

    git_probe = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    if git_probe.returncode != 0:
        return

    ignored_sources = []
    for source in force_include:
        check_ignore = subprocess.run(
            ["git", "-C", str(ROOT), "check-ignore", source],
            capture_output=True,
            text=True,
            check=False,
        )
        if check_ignore.returncode == 0:
            ignored_sources.append(source)
        else:
            assert check_ignore.returncode == 1, check_ignore.stderr

    assert ignored_sources == []


def test_sdist_includes_template_workspace_metadata() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    sdist_target = pyproject["tool"]["hatch"]["build"]["targets"]["sdist"]

    assert "/template/pnpm-workspace.yaml" in sdist_target["only-include"]


def test_template_workspace_pins_allowed_build_scripts() -> None:
    workspace = yaml.safe_load((ROOT / "template/pnpm-workspace.yaml").read_text())

    assert workspace["allowBuilds"] == {
        "msw": False,
        "sharp": True,
        "unrs-resolver": True,
    }
    assert workspace["onlyBuiltDependencies"] == ["sharp", "unrs-resolver"]
    assert workspace["ignoredBuiltDependencies"] == ["msw"]


def test_readiness_docs_cover_runtime_requirements() -> None:
    readme = (ROOT / "README.md").read_text()
    quickstart = (ROOT / "docs/guide/quickstart.md").read_text()

    for content in (readme, quickstart):
        assert "Node.js 20.19+" in content
        assert "pnpm 10" in content
    assert "Python CLI" in readme
    assert "Nextra/Next.js template" in readme
    assert "Python 3.10+" in quickstart


def test_standalone_installer_is_documented_and_valid_shell() -> None:
    installer = ROOT / "install.sh"
    # Served from the site itself by docs/plugins/install_script.py.
    install_url = "https://pguijas.github.io/folio/install.sh"
    readme = (ROOT / "README.md").read_text()
    installation = (ROOT / "docs/guide/installation.md").read_text()
    quickstart = (ROOT / "docs/guide/quickstart.md").read_text()

    assert installer.exists()
    assert installer.stat().st_mode & 0o111
    subprocess.run(["sh", "-n", str(installer)], check=True)

    for content in (readme, installation):
        assert f"curl -LsSf {install_url} | less" in content
        assert f"curl -LsSf -o install-folio.sh {install_url}" in content
        assert f"curl -LsSf {install_url} | sh" not in content

    assert "uv tool install folio-docs" in quickstart
    assert f"curl -LsSf {install_url} | sh" not in quickstart


def test_installation_guide_keeps_dependencies_compact_and_installer_centered() -> None:
    installation = (ROOT / "docs/guide/installation.md").read_text()

    assert "uv tool install folio-docs" in installation
    assert "The standalone installer requires `uv`" in installation
    assert "`Node.js 20.19+`" in installation
    assert "`pnpm 10`" in installation
    assert "`folio build` and `folio serve`" in installation
    assert "corepack prepare pnpm@10 --activate" in installation
    assert "folio serve" in installation
    assert "uv run folio serve" not in installation
    assert "pnpm run dev" not in installation
    assert "run the template dev server directly" not in installation
    assert "python3 --version" not in installation
    assert "pnpm --version" not in installation
    assert "nvm install --lts" not in installation


def test_standalone_installer_requires_uv_and_validates_runtime_tools() -> None:
    installer = (ROOT / "install.sh").read_text()

    assert "https://astral.sh/uv/install.sh" in installer
    assert "uv tool install --force" in installer
    assert "FOLIO_VERSION" in installer
    assert "corepack prepare pnpm@10 --activate" in installer
    assert "pnpm@latest" not in installer
    assert "Node.js 20.19+" in installer
    assert "FOLIO_BOOTSTRAP_UV" in installer
    assert "FOLIO_SKIP_PNPM_SETUP" in installer
    assert "pnpm_is_supported" in installer
    assert "Dependencies:" in installer
    assert "uv: required; install from" in installer
    assert (
        "Node.js 20.19+: required for build/serve; checked by this script" in installer
    )
    assert "pnpm 10: activated with Corepack when possible" in installer


def test_docs_use_publishable_distribution_name() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    installer = (ROOT / "install.sh").read_text()
    docs_yaml = (ROOT / "docs.yaml").read_text()
    checked_paths = [
        ROOT / "README.md",
        ROOT / "docs/guide/index.md",
        ROOT / "docs/guide/installation.md",
        ROOT / "docs/guide/quickstart.md",
        ROOT / "docs/guide/deployment/index.md",
        ROOT / "docs/guide/deployment/static-hosts.md",
        ROOT / "docs/guide/deployment/ci-cd.md",
    ]

    assert pyproject["project"]["name"] == "folio-docs"
    assert "FOLIO_PACKAGE=${FOLIO_PACKAGE:-folio-docs}" in installer
    assert (
        '- "curl -LsSf https://pguijas.github.io/folio/install.sh | sh"' in docs_yaml
    )
    for path in checked_paths:
        content = path.read_text()
        assert "folio-docs" in content
        assert "pypi.org/project/folio/" not in content
        assert "uv add folio\n" not in content
        assert "uv tool install folio\n" not in content
        assert "pip install folio\n" not in content


def test_community_files_are_present() -> None:
    expected = [
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        ".github/ISSUE_TEMPLATE/bug_report.yml",
        ".github/ISSUE_TEMPLATE/docs.yml",
        ".github/ISSUE_TEMPLATE/feature_request.yml",
        ".github/pull_request_template.md",
    ]

    for relative_path in expected:
        path = ROOT / relative_path
        assert path.exists()
        assert path.read_text().strip()


def test_readme_ci_badge_matches_available_workflow() -> None:
    readme = (ROOT / "README.md").read_text()
    ci_workflow = ROOT / ".github/workflows/ci.yml"

    if ci_workflow.exists():
        assert (
            "actions/workflow/status/pguijas/folio/ci.yml" in readme
            or "CI-pending" in readme
        )
    else:
        assert "CI-pending" in readme
        assert "actions/workflow/status/pguijas/folio/ci.yml" not in readme


def test_python_package_metadata_is_configured() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    project = pyproject["project"]

    assert project["name"] == "folio-docs"
    assert project["readme"] == "README.md"
    assert project["authors"] == [{"name": "pguijas"}]
    assert "documentation" in project["keywords"]
    assert "static-site-generator" in project["keywords"]
    assert "Framework :: Pytest" not in project["classifiers"]
    assert (
        "License :: OSI Approved :: GNU Affero General Public License v3"
        in project["classifiers"]
    )
    assert "Programming Language :: Python :: 3.10" in project["classifiers"]
    assert "Programming Language :: Python :: 3.13" in project["classifiers"]
    assert project["urls"]["Homepage"] == "https://github.com/pguijas/folio"
    assert project["urls"]["Documentation"] == "https://pguijas.github.io/folio/"
    assert project["urls"]["Issues"] == "https://github.com/pguijas/folio/issues"
    assert "Typing :: Typed" in project["classifiers"]
    assert (ROOT / "folio" / "py.typed").exists()


def test_build_backend_is_bounded_for_release() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert pyproject["build-system"]["requires"] == ["hatchling>=1.27,<2"]


def test_source_distribution_excludes_generated_outputs() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    sdist = pyproject["tool"]["hatch"]["build"]["targets"]["sdist"]

    for included in [
        "/.github",
        "/folio",
        "/template/app",
        "/template/package.json",
        "/template/pnpm-lock.yaml",
        "/scripts",
        "/README.md",
        "/LICENSE",
        "/pyproject.toml",
    ]:
        assert included in sdist["only-include"]

    assert "/template" not in sdist["only-include"]

    for excluded in [
        "/.build",
        "/_site",
        "/dist",
        "/node_modules",
        "/template/node_modules",
        "/template/.next",
    ]:
        assert excluded in sdist["exclude"]


def test_planning_notes_stay_out_of_tracked_docs() -> None:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "docs/superpowers"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        pytest.skip("requires a git checkout (not available in sdist)")

    assert result.stdout.splitlines() == []


def test_dev_tooling_dependencies_include_ruff() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())

    assert "dependency-groups" in pyproject
    assert "pytest>=8.0" in pyproject["dependency-groups"]["dev"]
    assert "ruff>=0.8.0" in pyproject["dependency-groups"]["dev"]


def test_ci_runs_python_and_template_checks() -> None:
    workflow_path = ROOT / ".github" / "workflows" / "ci.yml"
    workflow_text = workflow_path.read_text()
    workflow = yaml.safe_load(workflow_text)

    assert workflow["name"] == "CI"
    assert "push" in workflow_text
    assert "pull_request" in workflow_text
    # Pushes only trigger on main; PR branches are covered by pull_request,
    # so the same commit does not run CI twice.
    assert "branches: [main]" in workflow_text

    checks_job = workflow["jobs"]["checks"]
    assert "strategy" not in checks_job

    steps = checks_job["steps"]
    step_text = "\n".join(str(step) for step in steps)
    python_step = next(step for step in steps if step["name"] == "Set up Python")

    assert python_step["with"]["python-version"] == "3.12"
    assert "matrix.python-version" not in step_text
    assert "node-version': 24" in step_text
    assert "astral-sh/setup-uv" in step_text
    assert "pnpm/action-setup" in step_text
    assert "uv sync --all-groups --locked" in step_text
    assert "uv run --locked ruff check ." in step_text
    assert "uv run --locked pytest" in step_text
    assert "uv build" in step_text
    assert "uv run --locked folio build --clean" in step_text
    assert "pnpm install --frozen-lockfile" in step_text
    assert "pnpm lint" in step_text
    assert "pnpm typecheck" in step_text
    assert workflow["permissions"] == {"contents": "read"}
    assert re.search(ACTION_SHA_RE, workflow_text) is None
    assert "actions/checkout@v4" in workflow_text
    assert "actions/setup-python@v5" in workflow_text
    assert "astral-sh/setup-uv@v5" in workflow_text
    assert "pnpm/action-setup@v4" in workflow_text
    assert "actions/setup-node@v4" in workflow_text


def test_github_pages_workflow_builds_and_deploys_folio_docs() -> None:
    workflow_dir = ROOT / ".github" / "workflows"
    workflow_path = workflow_dir / "pages.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)

    assert not (workflow_dir / "folio-pages.yml").exists()
    assert workflow["name"] == "Deploy Docs"
    assert "workflow_call" not in workflow["on"]
    assert "actions/upload-pages-artifact@" in workflow_text
    assert "actions/deploy-pages@" in workflow_text

    assert workflow["permissions"] == {"contents": "read"}
    # Single job by deliberate choice: simpler to maintain for the repo's own
    # docs deploy. The workflow generated for users (folio/workflows.py) keeps
    # the hardened two-job build/deploy split.
    assert list(workflow["jobs"]) == ["deploy"]
    deploy_job = workflow["jobs"]["deploy"]
    steps = deploy_job["steps"]
    step_text = "\n".join(str(step) for step in steps)
    assert "uv sync --all-groups --locked" in step_text
    assert "uv run --locked folio build --clean" in step_text
    assert "FOLIO_BASE_PATH" in step_text
    assert "actions/configure-pages@v5" in workflow_text
    assert "folio-pages-state" in step_text
    assert "previews" in step_text
    assert "folio github-pages preserve-previews" in step_text
    assert "folio github-pages prune-previews" in step_text
    assert "folio github-pages write-previews-data" in step_text
    assert "folio github-pages render-previews-index" not in step_text
    assert "folio github-pages save-state" in step_text
    assert "folio github-pages verify-url" in step_text
    assert "python - <<'PY'" not in workflow_text
    assert "env" not in workflow
    assert "github.event.repository.name" not in workflow_text
    assert deploy_job["environment"]["name"] == "github-pages"
    assert deploy_job["permissions"] == {
        "contents": "write",
        "pages": "write",
        "id-token": "write",
        "pull-requests": "read",
    }
    assert "Verify and print deployment URL" in step_text
    assert "steps.deployment.outputs.page_url" in step_text
    assert "Previews index" in step_text
    assert "Verified deployment and previews index with HTTP 200" in step_text
    assert re.search(ACTION_SHA_RE, workflow_text) is None
    assert "actions/upload-pages-artifact@v3" in workflow_text
    assert "actions/deploy-pages@v4" in workflow_text


def test_branch_preview_workflow_deploys_folio_docs_to_github_pages() -> None:
    workflow_path = ROOT / ".github" / "workflows" / "branch-previews.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)

    assert workflow["name"] == "Deploy Branch Preview Docs"
    assert "push" not in workflow["on"]
    assert workflow["on"]["pull_request_target"]["types"] == [
        "opened",
        "synchronize",
        "reopened",
        "ready_for_review",
    ]
    assert "pull_request_review" not in workflow["on"]
    assert "workflow_call" not in workflow["on"]
    assert workflow["permissions"] == {
        "contents": "read",
        "pull-requests": "read",
    }
    assert "concurrency" not in workflow
    assert list(workflow["jobs"]) == ["validate", "build-preview", "deploy"]

    validate_job = workflow["jobs"]["validate"]
    assert validate_job["permissions"] == {
        "contents": "read",
        "pull-requests": "read",
    }
    assert "enabled" in validate_job["outputs"]
    assert "head_sha" in validate_job["outputs"]
    assert "head_ref" in validate_job["outputs"]
    assert "pr_number" in validate_job["outputs"]
    assert "pr_title" in validate_job["outputs"]

    build_job = workflow["jobs"]["build-preview"]
    assert build_job["needs"] == "validate"
    assert build_job["permissions"] == {"contents": "read"}
    build_text = "\n".join(str(step) for step in build_job["steps"])
    assert "Check out preview branch" in build_text
    assert "persist-credentials': False" in build_text
    assert "Configure GitHub Pages" not in build_text
    assert "steps.pages.outputs" not in build_text
    assert "GITHUB_OWNER" in build_text
    assert "pages_base_path" in build_text
    assert "Compute preview path" in build_text
    assert "Build preview docs" in build_text
    assert "uv sync --all-groups --locked" in build_text
    assert "uv run --locked folio build --clean" in build_text
    assert "actions/upload-artifact@v4" in workflow_text

    deploy_job = workflow["jobs"]["deploy"]
    assert deploy_job["needs"] == ["validate", "build-preview"]
    assert deploy_job["concurrency"] == {
        "group": "pages",
        "cancel-in-progress": False,
    }
    assert "environment" not in deploy_job
    assert deploy_job["permissions"] == {
        "contents": "write",
        "issues": "write",
        "pages": "write",
        "id-token": "write",
        "pull-requests": "write",
    }
    step_text = "\n".join(str(step) for step in deploy_job["steps"])
    assert "Revalidate preview PR" in step_text
    assert 'gh api --method GET "repos/${GITHUB_REPOSITORY}/pulls/${PR_NUMBER}"' in (
        workflow_text
    )
    assert "head has not caught up" in step_text
    assert "trusted approval" not in step_text
    assert "author_association" not in step_text
    assert "/reviews" not in step_text
    assert "Check out production branch" in step_text
    assert "Check out preview branch" not in step_text
    assert "actions/download-artifact@v4" in workflow_text
    assert "Configure GitHub Pages" in step_text
    assert "actions/configure-pages@v5" in workflow_text
    assert "Compute preview path" in step_text
    assert "Build production docs" in step_text
    assert "Build preview docs" not in step_text
    assert "folio-pages-state" in step_text
    assert "folio github-pages prepare-artifact" in step_text
    assert "folio github-pages copy-branch-preview" in step_text
    assert "folio github-pages write-preview-metadata" in step_text
    assert "folio github-pages prune-previews" in step_text
    assert "folio github-pages write-previews-data" in step_text
    assert "folio github-pages render-previews-index" not in step_text
    assert step_text.index("write-preview-metadata") < (
        step_text.index("write-previews-data")
    )
    # Metadata is enriched with repository/author context for the site cards.
    assert "--author" in step_text
    assert "github.event.pull_request.user.avatar_url" in workflow_text
    assert "folio github-pages save-state" in step_text
    assert "folio github-pages verify-url" in step_text
    assert "uv sync --all-groups --locked" in step_text
    assert "uv run --locked folio build --clean" in step_text
    assert "FOLIO_BASE_PATH" in step_text
    assert "python - <<'PY'" not in workflow_text
    assert "actions/upload-pages-artifact@v3" in workflow_text
    assert "actions/deploy-pages@v4" in workflow_text
    assert "Verify and print preview URL" in step_text
    assert "Comment preview URL" in step_text
    assert "GH_TOKEN" in step_text
    assert "folio github-pages comment-preview" in step_text
    assert "--repo" in step_text
    assert "--pr-number" in step_text
    assert "--preview-url" in step_text
    assert '--branch "$BRANCH"' in step_text
    assert "Preview URL" in step_text
    assert "Previews index" in step_text
    assert "Verified preview and index with HTTP 200" in step_text
    assert "CLOUDFLARE" not in workflow_text
    assert (
        "${{ github.event.pull_request.head.sha || github.sha }}" not in workflow_text
    )
    assert re.search(ACTION_SHA_RE, workflow_text) is None


def test_branch_previews_are_garbage_collected_on_deploy() -> None:
    # Cleanup is a garbage-collection step on every deploy (no separate
    # close-triggered workflow), so stale previews cannot accumulate.
    assert not (ROOT / ".github" / "workflows" / "branch-preview-cleanup.yml").exists()

    for name in ("pages.yml", "branch-previews.yml"):
        workflow_text = (ROOT / ".github" / "workflows" / name).read_text(
            encoding="utf-8"
        )
        assert "gh pr list --state open" in workflow_text
        assert "folio github-pages prune-previews" in workflow_text


def test_release_workflow_publishes_to_pypi_with_trusted_publishing() -> None:
    workflow_path = ROOT / ".github" / "workflows" / "release.yml"
    workflow_text = workflow_path.read_text(encoding="utf-8")
    workflow = yaml.safe_load(workflow_text)

    assert workflow["name"] == "Release"
    assert "v*" in workflow_text
    assert workflow["permissions"] == {"contents": "read"}

    jobs = workflow["jobs"]
    assert list(jobs) == ["build", "publish"]
    build_text = "\n".join(str(step) for step in jobs["build"]["steps"])
    publish_text = "\n".join(str(step) for step in jobs["publish"]["steps"])
    assert "version" in workflow["on"]["workflow_dispatch"]["inputs"]
    assert "uv sync --all-groups --locked" in build_text
    assert "uv run --locked python scripts/check_release_version.py" in build_text
    assert "uv run --locked ruff check ." in build_text
    assert "uv run --locked pytest" in build_text
    assert "node-version': 24" in build_text
    assert "uv run --locked folio build --clean" in build_text
    assert "rm -rf dist" in build_text
    assert "uv build" in build_text
    assert jobs["publish"]["needs"] == "build"
    assert jobs["publish"]["environment"] == "pypi"
    assert jobs["publish"]["permissions"] == {
        "contents": "read",
        "id-token": "write",
    }
    assert "actions/download-artifact@" in publish_text
    assert "uv publish --trusted-publishing always" in publish_text
    assert "dist/*" in publish_text
    pinned_actions = re.findall(ACTION_SHA_RE, workflow_text)
    assert len(pinned_actions) == 8
    assert "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02" in (
        build_text
    )
    assert "actions/download-artifact@d3f86a106a0bac45b974a628896c90dbdf5c8093" in (
        publish_text
    )


def test_deployment_docs_use_static_site_artifact_consistently() -> None:
    deployment = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [
            ROOT / "docs/guide/deployment/index.md",
            ROOT / "docs/guide/deployment/static-hosts.md",
            ROOT / "docs/guide/deployment/github-pages.md",
            ROOT / "docs/guide/deployment/ci-cd.md",
        ]
    )

    assert "_site/" in deployment
    assert "generated `.build/` directory" not in deployment
    assert "Root Directory**: `.build`" not in deployment
    assert 'base = ".build"' not in deployment
    assert 'publish = ".build/.next"' not in deployment
    assert "COPY .build/ ." not in deployment


def test_branch_preview_docs_explain_trusted_deploy_boundary() -> None:
    ci_cd = (ROOT / "docs/guide/deployment/ci-cd.md").read_text(encoding="utf-8")
    deployment = (ROOT / "docs/guide/deployment/github-pages.md").read_text(
        encoding="utf-8"
    )

    for content in (ci_cd, deployment):
        assert "unprivileged job" in content
        assert "privileged deploy job" in content
        assert "static `_site/`" in content
        assert "/previews/pr-<number>-<branch>/" in content
        assert "Branch pushes can trigger" not in content
        assert "builds the PR branch under `/previews/<branch>/`" not in content


def test_root_social_image_is_configured() -> None:
    layout = (ROOT / "template/app/layout.tsx").read_text(encoding="utf-8")
    docs_layout = (ROOT / "template/app/docs/layout.tsx").read_text(encoding="utf-8")
    root_og = ROOT / "template/app/opengraph-image.tsx"

    assert root_og.exists()
    assert "openGraph" in layout
    assert "alternates" in layout
    assert "canonical" in layout
    assert "SoftwareApplication" in layout
    assert "images" in layout
    assert "twitter" in layout
    assert "images" in layout.split("twitter:", 1)[1]
    assert "pageMetadata" in (
        ROOT / "template/app/docs/[[...mdxPath]]/page.jsx"
    ).read_text(encoding="utf-8")
    assert "/docs/opengraph-image" in docs_layout


def test_pagefind_only_indexes_public_docs_pages() -> None:
    package_json = json.loads((ROOT / "template/package.json").read_text())
    postbuild = package_json["scripts"]["postbuild"]

    assert "--glob" in postbuild
    assert "index.html" in postbuild
    assert "docs/**/*.html" in postbuild
    assert "_folio" not in postbuild


def test_sensitive_local_files_are_ignored() -> None:
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    for pattern in [
        ".env",
        ".env.*",
        ".pypirc",
        ".npmrc",
        "/.pnpm-store/",
        "*.key",
        "*.pem",
    ]:
        assert pattern in gitignore
