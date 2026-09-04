from __future__ import annotations

import json
from pathlib import Path
import subprocess

from typer.testing import CliRunner

from folio.cli import app
from folio._github_pages import (
    COMMENT_MARKER,
    PREVIEW_METADATA_FILE,
    PREVIEWS_DATA_FILE,
    compute_preview_path,
    copy_branch_preview,
    prepare_pages_artifact,
    preview_comment_body,
    prune_previews,
    upsert_preview_comment,
    write_preview_metadata,
    write_previews_data,
)


runner = CliRunner()


def test_compute_preview_path_normalizes_branch_and_base_path() -> None:
    preview = compute_preview_path(
        head_ref="Feature/Foo",
        pr_number="17",
        pages_base_path="/folio/",
        pages_base_url="https://pguijas.github.io/folio/",
    )

    assert preview.safe_branch == "pr-17-feature-foo"
    assert preview.base_path == "/folio/previews/pr-17-feature-foo"
    assert (
        preview.url == "https://pguijas.github.io/folio/previews/pr-17-feature-foo/"
    )


def test_compute_preview_path_falls_back_to_pr_number_for_empty_slug() -> None:
    preview = compute_preview_path(
        head_ref="---",
        pr_number="23",
        pages_base_path="/",
        pages_base_url="https://example.com/project",
    )

    assert preview.safe_branch == "pr-23"
    assert preview.base_path == "/previews/pr-23"
    assert preview.url == "https://example.com/project/previews/pr-23/"


def test_compute_preview_path_avoids_branch_slug_collisions() -> None:
    first = compute_preview_path(
        head_ref="Feature/API",
        pr_number="17",
        pages_base_path="/folio/",
        pages_base_url="https://pguijas.github.io/folio/",
    )
    second = compute_preview_path(
        head_ref="feature_api",
        pr_number="18",
        pages_base_path="/folio/",
        pages_base_url="https://pguijas.github.io/folio/",
    )

    assert first.safe_branch == "pr-17-feature-api"
    assert second.safe_branch == "pr-18-feature-api"
    assert first.safe_branch != second.safe_branch


def test_compute_preview_path_limits_long_branch_slugs() -> None:
    preview = compute_preview_path(
        head_ref="feature/" + ("very-long-branch-name-" * 12),
        pr_number="17",
        pages_base_path="/folio/",
        pages_base_url="https://pguijas.github.io/folio/",
    )

    assert preview.safe_branch.startswith("pr-17-feature-")
    assert len(preview.safe_branch) <= 80


def test_compute_preview_path_limits_long_pr_number_slugs(tmp_path: Path) -> None:
    preview = compute_preview_path(
        head_ref="Feature/Foo",
        pr_number="17" * 60,
        pages_base_path="/folio/",
        pages_base_url="https://pguijas.github.io/folio/",
    )
    preview_site = tmp_path / "preview" / "_site"
    preview_site.mkdir(parents=True)
    (preview_site / "index.html").write_text("preview", encoding="utf-8")
    artifact_dir = tmp_path / "_pages-artifact"

    assert preview.safe_branch.startswith("pr-")
    assert len(preview.safe_branch) <= 80
    copy_branch_preview(
        preview_site=preview_site,
        artifact_dir=artifact_dir,
        preview_id=preview.safe_branch,
    )

    assert (artifact_dir / "previews" / preview.safe_branch / "index.html").read_text(
        encoding="utf-8"
    ) == "preview"


def _make_preview(previews: Path, name: str, metadata: dict | None = None) -> Path:
    preview = previews / name
    preview.mkdir(parents=True)
    (preview / "index.html").write_text("x", encoding="utf-8")
    if metadata is not None:
        (preview / PREVIEW_METADATA_FILE).write_text(
            json.dumps(metadata), encoding="utf-8"
        )
    return preview


def test_write_previews_data_writes_json_with_metadata(tmp_path: Path) -> None:
    previews = tmp_path / "previews"
    _make_preview(
        previews,
        "pr-17-feature-foo",
        {
            "pr_number": "17",
            "title": "Add cool feature",
            "branch": "feature/foo",
            "commit": "abcdef1",
            "commit_url": "https://github.com/acme/widgets/commit/abcdef1",
            "pr_url": "https://github.com/acme/widgets/pull/17",
            "author": "octocat",
            "avatar_url": "https://avatars.example/octocat.png",
            "updated_at": "2026-07-01T12:00:00Z",
        },
    )
    # A directory without index.html is not a preview and must be skipped.
    (previews / "no-index").mkdir()

    entries = write_previews_data(previews)

    assert len(entries) == 1
    entry = entries[0]
    assert entry["name"] == "pr-17-feature-foo"
    assert entry["href"] == "./pr-17-feature-foo/"
    assert entry["title"] == "Add cool feature"
    assert entry["author"] == "octocat"
    assert entry["commit_url"].endswith("/commit/abcdef1")

    on_disk = json.loads((previews / PREVIEWS_DATA_FILE).read_text(encoding="utf-8"))
    assert on_disk == entries


def test_write_previews_data_defaults_to_name_without_metadata(tmp_path: Path) -> None:
    previews = tmp_path / "previews"
    _make_preview(previews, "pr-3-bare")

    entries = write_previews_data(previews)

    assert entries[0]["title"] == "pr-3-bare"
    assert entries[0]["pr_number"] == ""


def test_write_previews_data_orders_newest_first(tmp_path: Path) -> None:
    previews = tmp_path / "previews"
    _make_preview(previews, "pr-1-old", {"updated_at": "2026-01-01T00:00:00Z"})
    _make_preview(previews, "pr-2-new", {"updated_at": "2026-07-01T00:00:00Z"})

    entries = write_previews_data(previews)

    assert [e["name"] for e in entries] == ["pr-2-new", "pr-1-old"]


def test_write_previews_data_empty_writes_empty_array(tmp_path: Path) -> None:
    previews = tmp_path / "previews"

    entries = write_previews_data(previews)

    assert entries == []
    assert json.loads((previews / PREVIEWS_DATA_FILE).read_text()) == []


def test_write_preview_metadata_writes_enriched_sidecar(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "_pages-artifact"
    preview_dir = artifact_dir / "previews" / "pr-17-feature-foo"
    preview_dir.mkdir(parents=True)
    (preview_dir / "index.html").write_text("preview", encoding="utf-8")

    write_preview_metadata(
        artifact_dir=artifact_dir,
        preview_id="pr-17-feature-foo",
        pr_number="17",
        title="Add feature",
        branch="feature/foo",
        commit="abcdef1234567890",
        pr_url="https://github.com/acme/widgets/pull/17",
        updated_at="2026-07-01T12:00:00Z",
        repo="acme/widgets",
        author="octocat",
        author_url="https://github.com/octocat",
        avatar_url="https://avatars.example/octocat.png",
    )

    metadata = json.loads(
        (preview_dir / PREVIEW_METADATA_FILE).read_text(encoding="utf-8")
    )
    assert metadata["pr_number"] == "17"
    assert metadata["title"] == "Add feature"
    assert metadata["commit"] == "abcdef123456"  # truncated to 12 chars
    assert metadata["repo_url"] == "https://github.com/acme/widgets"
    assert metadata["commit_url"] == (
        "https://github.com/acme/widgets/commit/abcdef1234567890"
    )
    assert metadata["author"] == "octocat"
    assert metadata["avatar_url"] == "https://avatars.example/octocat.png"


def test_write_preview_metadata_rejects_path_traversal(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "_pages-artifact"
    (artifact_dir / "previews").mkdir(parents=True)

    try:
        write_preview_metadata(
            artifact_dir=artifact_dir,
            preview_id="../outside",
            pr_number="17",
            title="",
            branch="",
            commit="",
            pr_url="",
            updated_at="2026-07-01T12:00:00Z",
        )
    except ValueError as exc:
        assert "Invalid preview id" in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("Expected path traversal preview id to be rejected")


def test_prune_previews_removes_stale_and_keeps_open(tmp_path: Path) -> None:
    previews = tmp_path / "previews"
    _make_preview(previews, "pr-1-foo")
    _make_preview(previews, "pr-2-bar")
    _make_preview(previews, "pr-9-gone")
    (previews / PREVIEWS_DATA_FILE).write_text("[]", encoding="utf-8")

    removed = prune_previews(previews, {"pr-1-foo", "pr-2-bar"})

    assert removed == ["pr-9-gone"]
    assert (previews / "pr-1-foo").is_dir()
    assert (previews / "pr-2-bar").is_dir()
    assert not (previews / "pr-9-gone").exists()
    # Reserved top-level files are untouched by the garbage collector.
    assert (previews / PREVIEWS_DATA_FILE).is_file()


def test_prune_previews_command_computes_ids_from_open_prs(tmp_path: Path) -> None:
    previews = tmp_path / "previews"
    _make_preview(previews, "pr-1-foo")
    _make_preview(previews, "pr-2-bar")
    output_path = tmp_path / "github-output"

    result = runner.invoke(
        app,
        [
            "github-pages",
            "prune-previews",
            "--previews-dir",
            str(previews),
            "--open-prs-json",
            json.dumps([{"number": 1, "headRefName": "foo"}]),
        ],
        env={"GITHUB_OUTPUT": str(output_path)},
    )

    assert result.exit_code == 0, result.output
    assert output_path.read_text(encoding="utf-8") == "removed=1\n"
    assert (previews / "pr-1-foo").is_dir()
    assert not (previews / "pr-2-bar").exists()


def test_prepare_pages_artifact_preserves_existing_previews(tmp_path: Path) -> None:
    production_site = tmp_path / "production" / "_site"
    production_site.mkdir(parents=True)
    (production_site / "index.html").write_text("production", encoding="utf-8")
    state_dir = tmp_path / "_pages-state"
    (state_dir / "previews" / "old-preview").mkdir(parents=True)
    (state_dir / "previews" / "old-preview" / "index.html").write_text(
        "old",
        encoding="utf-8",
    )

    artifact_dir = tmp_path / "_pages-artifact"
    prepare_pages_artifact(
        production_site=production_site,
        artifact_dir=artifact_dir,
        state_dir=state_dir,
        git_repo=tmp_path,
        fetch_state=False,
    )

    assert (artifact_dir / "index.html").read_text(encoding="utf-8") == "production"
    assert (artifact_dir / "previews" / "old-preview" / "index.html").read_text(
        encoding="utf-8"
    ) == "old"
    assert (artifact_dir / ".nojekyll").exists()


def test_prepare_pages_artifact_preserves_saved_production_root(
    tmp_path: Path,
) -> None:
    production_site = tmp_path / "production" / "_site"
    production_site.mkdir(parents=True)
    (production_site / "index.html").write_text("rebuilt main", encoding="utf-8")
    state_dir = tmp_path / "_pages-state"
    state_dir.mkdir()
    (state_dir / ".git").write_text("gitdir: ignored\n", encoding="utf-8")
    (state_dir / "index.html").write_text("already deployed", encoding="utf-8")
    (state_dir / "previews" / "old-preview").mkdir(parents=True)
    (state_dir / "previews" / "old-preview" / "index.html").write_text(
        "old",
        encoding="utf-8",
    )

    artifact_dir = tmp_path / "_pages-artifact"
    prepare_pages_artifact(
        production_site=production_site,
        artifact_dir=artifact_dir,
        state_dir=state_dir,
        git_repo=tmp_path,
        fetch_state=False,
    )

    assert (artifact_dir / "index.html").read_text(encoding="utf-8") == (
        "already deployed"
    )
    assert not (artifact_dir / ".git").exists()
    assert (artifact_dir / "previews" / "old-preview" / "index.html").read_text(
        encoding="utf-8"
    ) == "old"


def test_copy_branch_preview_replaces_existing_preview(tmp_path: Path) -> None:
    preview_site = tmp_path / "preview" / "_site"
    preview_site.mkdir(parents=True)
    (preview_site / "index.html").write_text("new", encoding="utf-8")
    artifact_dir = tmp_path / "_pages-artifact"
    old_preview = artifact_dir / "previews" / "feature-a"
    old_preview.mkdir(parents=True)
    (old_preview / "stale.html").write_text("stale", encoding="utf-8")

    copy_branch_preview(
        preview_site=preview_site,
        artifact_dir=artifact_dir,
        preview_id="feature-a",
    )

    assert (old_preview / "index.html").read_text(encoding="utf-8") == "new"
    assert not (old_preview / "stale.html").exists()


def test_copy_branch_preview_rejects_path_traversal(tmp_path: Path) -> None:
    preview_site = tmp_path / "preview" / "_site"
    preview_site.mkdir(parents=True)
    (preview_site / "index.html").write_text("new", encoding="utf-8")
    artifact_dir = tmp_path / "_pages-artifact"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sentinel.txt").write_text("keep", encoding="utf-8")

    try:
        copy_branch_preview(
            preview_site=preview_site,
            artifact_dir=artifact_dir,
            preview_id="../outside",
        )
    except ValueError as exc:
        assert "Invalid preview id" in str(exc)
    else:  # pragma: no cover - assertion branch
        raise AssertionError("Expected path traversal preview id to be rejected")

    assert (outside / "sentinel.txt").read_text(encoding="utf-8") == "keep"


def test_github_pages_compute_preview_path_command_writes_github_output(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "github-output"

    result = runner.invoke(
        app,
        [
            "github-pages",
            "compute-preview-path",
            "--head-ref",
            "Feature/Foo",
            "--pr-number",
            "17",
            "--pages-base-path",
            "/folio/",
            "--pages-base-url",
            "https://pguijas.github.io/folio/",
        ],
        env={"GITHUB_OUTPUT": str(output_path)},
    )

    assert result.exit_code == 0, result.output
    assert output_path.read_text(encoding="utf-8") == (
        "safe_branch=pr-17-feature-foo\n"
        "base_path=/folio/previews/pr-17-feature-foo\n"
        "url=https://pguijas.github.io/folio/previews/pr-17-feature-foo/\n"
    )


def test_preview_comment_body_contains_sticky_marker_and_urls() -> None:
    body = preview_comment_body(
        preview_url="https://example.com/previews/feature-a/",
        index_url="https://example.com/previews/",
        branch="Feature/A",
        head_sha="1234567890abcdef",
    )

    assert body.startswith(f"{COMMENT_MARKER}\n")
    assert "### Branch preview" in body
    assert "[Preview](https://example.com/previews/feature-a/)" in body
    assert "[Preview index](https://example.com/previews/)" in body
    assert "`Feature/A`" in body
    assert "`1234567`" in body


def test_upsert_preview_comment_updates_existing_comment(monkeypatch) -> None:
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        if command[:3] == ["gh", "api", "repos/acme/widgets/issues/17/comments"]:
            return subprocess.CompletedProcess(command, 0, stdout="12345\n")
        return subprocess.CompletedProcess(command, 0, stdout="")

    monkeypatch.setattr("folio._github_pages.subprocess.run", fake_run)

    result = upsert_preview_comment(
        repo="acme/widgets",
        pr_number="17",
        body=f"{COMMENT_MARKER}\nupdated",
    )

    assert result == "updated"
    assert calls[1][0] == [
        "gh",
        "api",
        "--method",
        "PATCH",
        "repos/acme/widgets/issues/comments/12345",
        "-f",
        f"body={COMMENT_MARKER}\nupdated",
    ]
    assert any('.user.login == "github-actions[bot]"' in part for part in calls[0][0])


def test_upsert_preview_comment_creates_comment_when_missing(monkeypatch) -> None:
    calls = []

    def fake_run(command, **kwargs):
        calls.append((command, kwargs))
        return subprocess.CompletedProcess(command, 0, stdout="")

    monkeypatch.setattr("folio._github_pages.subprocess.run", fake_run)

    result = upsert_preview_comment(
        repo="acme/widgets",
        pr_number="17",
        body=f"{COMMENT_MARKER}\ncreated",
    )

    assert result == "created"
    assert calls[1][0] == [
        "gh",
        "api",
        "--method",
        "POST",
        "repos/acme/widgets/issues/17/comments",
        "-f",
        f"body={COMMENT_MARKER}\ncreated",
    ]
