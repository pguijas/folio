from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import typer


app = typer.Typer(no_args_is_help=True)

STATE_BRANCH = "folio-pages-state"
BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
COMMENT_MARKER = "<!-- folio-branch-preview -->"
MAX_PREVIEW_ID_LENGTH = 80
_PREVIEW_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PREVIEW_METADATA_FILE = ".folio-preview.json"
PREVIEWS_DATA_FILE = "previews.json"
# Files at the root of `previews/` that the build/CI own and regenerate; they
# must never be clobbered by preview directories restored from the state branch.
RESERVED_PREVIEW_FILES = {"index.html", PREVIEWS_DATA_FILE}


@dataclass(frozen=True)
class PreviewPath:
    safe_branch: str
    base_path: str
    url: str


def safe_preview_branch(head_ref: str, pr_number: str) -> str:
    digest = hashlib.sha1(f"{pr_number}:{head_ref}".encode()).hexdigest()[:8]
    safe_pr = re.sub(r"[^a-z0-9]+", "-", pr_number.lower()).strip("-") or "unknown"
    if len(safe_pr) > 24:
        safe_pr = f"{safe_pr[:15].strip('-') or 'id'}-{digest}"
    safe_branch = re.sub(r"[^a-z0-9]+", "-", head_ref.lower()).strip("-")
    safe_branch = re.sub(r"-+", "-", safe_branch)
    preview_id = f"pr-{safe_pr}"
    if safe_branch:
        preview_id = f"{preview_id}-{safe_branch}"
    if len(preview_id) <= MAX_PREVIEW_ID_LENGTH:
        return preview_id

    prefix = f"pr-{safe_pr}-"
    suffix = f"-{digest}"
    branch_length = MAX_PREVIEW_ID_LENGTH - len(prefix) - len(suffix)
    safe_branch = safe_branch[: max(branch_length, 1)].strip("-") or "branch"
    return f"{prefix}{safe_branch}{suffix}"


def compute_preview_path(
    *,
    head_ref: str,
    pr_number: str,
    pages_base_path: str,
    pages_base_url: str,
) -> PreviewPath:
    safe_branch = safe_preview_branch(head_ref, pr_number)
    base_prefix = pages_base_path.rstrip("/")
    base_path = f"{base_prefix}/previews/{safe_branch}"
    if not base_path.startswith("/"):
        base_path = f"/{base_path}"
    url = f"{pages_base_url.rstrip('/')}/previews/{safe_branch}/"
    return PreviewPath(safe_branch=safe_branch, base_path=base_path, url=url)


def _remove_path(path: Path) -> None:
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    elif path.exists():
        path.unlink()


def _copy_contents(
    source: Path,
    destination: Path,
    *,
    exclude_names: set[str] | None = None,
) -> None:
    exclude_names = exclude_names or set()
    if not source.is_dir():
        raise FileNotFoundError(f"Source directory not found: {source}")
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.name in exclude_names:
            continue
        target = destination / item.name
        _remove_path(target)
        if item.is_dir() and not item.is_symlink():
            shutil.copytree(item, target, symlinks=True)
        else:
            shutil.copy2(item, target, follow_symlinks=False)


def _clear_directory(path: Path, *, keep_names: set[str] | None = None) -> None:
    keep_names = keep_names or set()
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.name in keep_names:
            continue
        _remove_path(child)


def _run(command: list[str], *, cwd: Path | None = None, check: bool = True):
    return subprocess.run(command, cwd=cwd, text=True, check=check)


def _state_has_artifact(state_dir: Path) -> bool:
    return (state_dir / "index.html").is_file()


def _validate_preview_id(preview_id: str) -> str:
    if len(preview_id) > MAX_PREVIEW_ID_LENGTH or not _PREVIEW_ID_RE.fullmatch(
        preview_id
    ):
        raise ValueError(f"Invalid preview id: {preview_id}")
    return preview_id


def _remote_branch_exists(git_repo: Path, state_branch: str) -> bool:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(git_repo),
            "ls-remote",
            "--exit-code",
            "--heads",
            "origin",
            state_branch,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode == 0:
        return True
    if result.returncode == 2:
        return False
    result.check_returncode()
    return False


def _fetch_state_worktree(
    *,
    git_repo: Path,
    state_dir: Path,
    state_branch: str = STATE_BRANCH,
) -> bool:
    if not _remote_branch_exists(git_repo, state_branch):
        return False
    _run(["git", "-C", str(git_repo), "fetch", "origin", state_branch])
    _run(
        [
            "git",
            "-C",
            str(git_repo),
            "worktree",
            "add",
            "--detach",
            str(state_dir),
            "FETCH_HEAD",
        ]
    )
    return True


def preserve_branch_previews(
    *,
    site_dir: Path,
    git_repo: Path,
    state_dir: Path,
    state_branch: str = STATE_BRANCH,
    fetch_state: bool = True,
) -> None:
    site_dir = site_dir.resolve()
    git_repo = git_repo.resolve()
    state_dir = state_dir.resolve()
    if fetch_state:
        _remove_path(state_dir)
        _fetch_state_worktree(
            git_repo=git_repo,
            state_dir=state_dir,
            state_branch=state_branch,
        )
    previews = state_dir / "previews"
    if previews.is_dir():
        _copy_contents(
            previews, site_dir / "previews", exclude_names=RESERVED_PREVIEW_FILES
        )
    site_dir.mkdir(parents=True, exist_ok=True)
    (site_dir / ".nojekyll").touch()


def prepare_pages_artifact(
    *,
    production_site: Path,
    artifact_dir: Path,
    git_repo: Path,
    state_dir: Path,
    state_branch: str = STATE_BRANCH,
    fetch_state: bool = True,
) -> None:
    production_site = production_site.resolve()
    artifact_dir = artifact_dir.resolve()
    git_repo = git_repo.resolve()
    state_dir = state_dir.resolve()
    if fetch_state:
        _remove_path(state_dir)
        _fetch_state_worktree(
            git_repo=git_repo,
            state_dir=state_dir,
            state_branch=state_branch,
        )
    _remove_path(artifact_dir)
    artifact_dir.mkdir(parents=True)
    if _state_has_artifact(state_dir):
        _copy_contents(state_dir, artifact_dir, exclude_names={".git"})
    else:
        _copy_contents(production_site, artifact_dir)
        previews = state_dir / "previews"
        if previews.is_dir():
            _copy_contents(
                previews,
                artifact_dir / "previews",
                exclude_names=RESERVED_PREVIEW_FILES,
            )
    (artifact_dir / ".nojekyll").touch()


def _resolve_preview_dir(artifact_dir: Path, preview_id: str) -> Path:
    preview_id = _validate_preview_id(preview_id)
    previews_dir = (artifact_dir / "previews").resolve()
    preview_dir = (previews_dir / preview_id).resolve()
    if preview_dir.parent != previews_dir:
        raise ValueError(f"Invalid preview id: {preview_id}")
    return preview_dir


def copy_branch_preview(
    *,
    preview_site: Path,
    artifact_dir: Path,
    preview_id: str,
) -> None:
    preview_dir = _resolve_preview_dir(artifact_dir, preview_id)
    _remove_path(preview_dir)
    preview_dir.mkdir(parents=True, exist_ok=True)
    _copy_contents(preview_site, preview_dir)


def write_preview_metadata(
    *,
    artifact_dir: Path,
    preview_id: str,
    pr_number: str,
    title: str,
    branch: str,
    commit: str,
    pr_url: str,
    updated_at: str,
    repo: str = "",
    author: str = "",
    author_url: str = "",
    avatar_url: str = "",
) -> None:
    """Write a metadata sidecar so the site can render rich preview cards."""
    preview_dir = _resolve_preview_dir(artifact_dir, preview_id)
    if not preview_dir.is_dir():
        raise FileNotFoundError(f"Preview directory not found: {preview_dir}")
    repo_url = f"https://github.com/{repo}" if repo else ""
    commit_url = f"{repo_url}/commit/{commit}" if repo_url and commit else ""
    metadata = {
        "pr_number": pr_number,
        "title": title,
        "branch": branch,
        "commit": commit[:12],
        "commit_url": commit_url,
        "pr_url": pr_url,
        "repo": repo,
        "repo_url": repo_url,
        "author": author,
        "author_url": author_url,
        "avatar_url": avatar_url,
        "updated_at": updated_at,
    }
    payload = json.dumps(metadata, indent=2, sort_keys=True, ensure_ascii=False)
    (preview_dir / PREVIEW_METADATA_FILE).write_text(f"{payload}\n", encoding="utf-8")


# String fields copied verbatim from a preview's metadata sidecar into the
# `previews.json` entry consumed by the site's `/previews/` route.
_PREVIEW_ENTRY_FIELDS = (
    "pr_number",
    "branch",
    "commit",
    "commit_url",
    "pr_url",
    "repo",
    "repo_url",
    "author",
    "author_url",
    "avatar_url",
    "updated_at",
)


def _read_preview_entry(path: Path) -> dict[str, str]:
    name = path.name
    entry = {"name": name, "href": f"./{name}/", "title": name}
    for field in _PREVIEW_ENTRY_FIELDS:
        entry[field] = ""
    metadata_file = path / PREVIEW_METADATA_FILE
    if not metadata_file.is_file():
        return entry
    try:
        metadata = json.loads(metadata_file.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return entry
    if not isinstance(metadata, dict):
        return entry
    for field in _PREVIEW_ENTRY_FIELDS:
        value = metadata.get(field)
        if isinstance(value, str):
            entry[field] = value
    title = metadata.get("title")
    if isinstance(title, str) and title.strip():
        entry["title"] = title
    return entry


def _iter_preview_dirs(previews_dir: Path):
    for path in previews_dir.iterdir():
        if path.is_dir() and (path / "index.html").is_file():
            yield path


def write_previews_data(previews_dir: Path) -> list[dict[str, str]]:
    """Collect preview metadata into `previews.json` for the site to render.

    The `/previews/` route (built with the full site chrome) fetches this file
    at runtime, so the shell is compiled once and only the data changes per
    deploy. Entries are sorted newest-first.
    """
    previews_dir.mkdir(parents=True, exist_ok=True)
    entries = [_read_preview_entry(path) for path in _iter_preview_dirs(previews_dir)]
    entries.sort(key=lambda e: e["name"])
    entries.sort(key=lambda e: e["updated_at"], reverse=True)
    payload = json.dumps(entries, indent=2, ensure_ascii=False)
    (previews_dir / PREVIEWS_DATA_FILE).write_text(f"{payload}\n", encoding="utf-8")
    return entries


def prune_previews(previews_dir: Path, keep_ids: set[str]) -> list[str]:
    """Delete preview directories whose id is not in `keep_ids`.

    This is the garbage collector: `keep_ids` is the set of preview ids for the
    currently open pull requests, so previews for merged/closed PRs (and any
    historically accumulated ones) are removed on the next deploy. Returns the
    ids that were removed.
    """
    if not previews_dir.is_dir():
        return []
    removed = []
    for path in sorted(p for p in previews_dir.iterdir() if p.is_dir()):
        if path.name not in keep_ids:
            _remove_path(path)
            removed.append(path.name)
    return removed


def save_pages_state(
    *,
    artifact_dir: Path,
    git_repo: Path,
    state_dir: Path,
    commit_message: str,
    state_branch: str = STATE_BRANCH,
) -> None:
    artifact_dir = artifact_dir.resolve()
    git_repo = git_repo.resolve()
    state_dir = state_dir.resolve()
    if not state_dir.is_dir():
        _run(
            [
                "git",
                "-C",
                str(git_repo),
                "worktree",
                "add",
                "--detach",
                str(state_dir),
            ]
        )
        _run(["git", "-C", str(state_dir), "switch", "--orphan", state_branch])

    _clear_directory(state_dir, keep_names={".git"})
    _copy_contents(artifact_dir, state_dir)
    _run(["git", "-C", str(state_dir), "config", "user.name", BOT_NAME])
    _run(["git", "-C", str(state_dir), "config", "user.email", BOT_EMAIL])
    _run(["git", "-C", str(state_dir), "add", "-A"])
    diff = subprocess.run(
        ["git", "-C", str(state_dir), "diff", "--cached", "--quiet"],
        check=False,
    )
    if diff.returncode == 0:
        print("Pages state is already current.")
        return
    if diff.returncode != 1:
        diff.check_returncode()
    _run(["git", "-C", str(state_dir), "commit", "-m", commit_message])
    _run(["git", "-C", str(state_dir), "push", "origin", f"HEAD:{state_branch}"])


def _http_status(url: str, *, timeout: float = 10.0) -> int | None:
    try:
        with urlopen(url, timeout=timeout) as response:
            return response.status
    except (OSError, URLError):
        return None


def verify_urls(
    *,
    url: str,
    index_url: str,
    attempts: int = 24,
    sleep_seconds: float = 5.0,
) -> bool:
    for _attempt in range(attempts):
        if _http_status(url) == 200 and _http_status(index_url) == 200:
            return True
        time.sleep(sleep_seconds)
    return False


def preview_comment_body(
    *,
    preview_url: str,
    index_url: str,
    branch: str,
    head_sha: str,
) -> str:
    short_sha = head_sha[:7]
    return "\n".join(
        [
            COMMENT_MARKER,
            "### Branch preview",
            "",
            f"Preview: [Preview]({preview_url})",
            "",
            f"Preview index: [Preview index]({index_url})",
            "",
            f"Branch: `{branch}`",
            f"Commit: `{short_sha}`",
        ]
    )


def _find_preview_comment_id(*, repo: str, pr_number: str) -> str | None:
    result = subprocess.run(
        [
            "gh",
            "api",
            f"repos/{repo}/issues/{pr_number}/comments",
            "--paginate",
            "--jq",
            (
                f'.[] | select(.user.login == "{BOT_NAME}" '
                f'and (.body | startswith("{COMMENT_MARKER}"))) | .id'
            ),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return next(
        (line.strip() for line in result.stdout.splitlines() if line.strip()),
        None,
    )


def upsert_preview_comment(*, repo: str, pr_number: str, body: str) -> str:
    comment_id = _find_preview_comment_id(repo=repo, pr_number=pr_number)
    if comment_id:
        _run(
            [
                "gh",
                "api",
                "--method",
                "PATCH",
                f"repos/{repo}/issues/comments/{comment_id}",
                "-f",
                f"body={body}",
            ]
        )
        return "updated"

    _run(
        [
            "gh",
            "api",
            "--method",
            "POST",
            f"repos/{repo}/issues/{pr_number}/comments",
            "-f",
            f"body={body}",
        ]
    )
    return "created"


def _append_env_file(env_name: str, lines: list[str]) -> None:
    path = os.environ.get(env_name)
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as file:
        for line in lines:
            file.write(f"{line}\n")


def _write_outputs(values: dict[str, str]) -> None:
    output_lines = [f"{key}={value}" for key, value in values.items()]
    _append_env_file("GITHUB_OUTPUT", output_lines)
    if not os.environ.get("GITHUB_OUTPUT"):
        for line in output_lines:
            print(line)


def _write_summary(lines: list[str]) -> None:
    _append_env_file("GITHUB_STEP_SUMMARY", lines)


@app.command("compute-preview-path")
def compute_preview_path_command(
    head_ref: str = typer.Option(..., "--head-ref"),
    pr_number: str = typer.Option(..., "--pr-number"),
    pages_base_path: str = typer.Option(..., "--pages-base-path"),
    pages_base_url: str = typer.Option(..., "--pages-base-url"),
) -> None:
    preview = compute_preview_path(
        head_ref=head_ref,
        pr_number=pr_number,
        pages_base_path=pages_base_path,
        pages_base_url=pages_base_url,
    )
    _write_outputs(
        {
            "safe_branch": preview.safe_branch,
            "base_path": preview.base_path,
            "url": preview.url,
        }
    )


@app.command("preserve-previews")
def preserve_previews_command(
    site_dir: Path = typer.Option(..., "--site-dir"),
    git_repo: Path = typer.Option(..., "--git-repo"),
    state_dir: Path = typer.Option(..., "--state-dir"),
    state_branch: str = typer.Option(STATE_BRANCH, "--state-branch"),
) -> None:
    preserve_branch_previews(
        site_dir=site_dir,
        git_repo=git_repo,
        state_dir=state_dir,
        state_branch=state_branch,
    )


@app.command("prepare-artifact")
def prepare_artifact_command(
    production_site: Path = typer.Option(..., "--production-site"),
    artifact_dir: Path = typer.Option(..., "--artifact-dir"),
    git_repo: Path = typer.Option(..., "--git-repo"),
    state_dir: Path = typer.Option(..., "--state-dir"),
    state_branch: str = typer.Option(STATE_BRANCH, "--state-branch"),
) -> None:
    prepare_pages_artifact(
        production_site=production_site,
        artifact_dir=artifact_dir,
        git_repo=git_repo,
        state_dir=state_dir,
        state_branch=state_branch,
    )


@app.command("copy-branch-preview")
def copy_branch_preview_command(
    preview_site: Path = typer.Option(..., "--preview-site"),
    artifact_dir: Path = typer.Option(..., "--artifact-dir"),
    preview_id: str = typer.Option(..., "--preview-id"),
) -> None:
    copy_branch_preview(
        preview_site=preview_site,
        artifact_dir=artifact_dir,
        preview_id=preview_id,
    )


@app.command("write-preview-metadata")
def write_preview_metadata_command(
    artifact_dir: Path = typer.Option(..., "--artifact-dir"),
    preview_id: str = typer.Option(..., "--preview-id"),
    pr_number: str = typer.Option(..., "--pr-number"),
    title: str = typer.Option("", "--title"),
    branch: str = typer.Option("", "--branch"),
    commit: str = typer.Option("", "--commit"),
    pr_url: str = typer.Option("", "--pr-url"),
    updated_at: str = typer.Option(..., "--updated-at"),
    repo: str = typer.Option("", "--repo"),
    author: str = typer.Option("", "--author"),
    author_url: str = typer.Option("", "--author-url"),
    avatar_url: str = typer.Option("", "--avatar-url"),
) -> None:
    write_preview_metadata(
        artifact_dir=artifact_dir,
        preview_id=preview_id,
        pr_number=pr_number,
        title=title,
        branch=branch,
        commit=commit,
        pr_url=pr_url,
        updated_at=updated_at,
        repo=repo,
        author=author,
        author_url=author_url,
        avatar_url=avatar_url,
    )


@app.command("write-previews-data")
def write_previews_data_command(
    previews_dir: Path = typer.Option(..., "--previews-dir"),
) -> None:
    entries = write_previews_data(previews_dir)
    print(f"Wrote metadata for {len(entries)} preview(s).")


@app.command("prune-previews")
def prune_previews_command(
    previews_dir: Path = typer.Option(..., "--previews-dir"),
    open_prs_json: str = typer.Option(..., "--open-prs-json"),
) -> None:
    open_prs = json.loads(open_prs_json)
    keep_ids: set[str] = set()
    for pr in open_prs:
        number = str(pr.get("number", "")).strip()
        head_ref = str(pr.get("headRefName", "")).strip()
        if number:
            keep_ids.add(safe_preview_branch(head_ref, number))
    removed = prune_previews(previews_dir, keep_ids)
    for name in removed:
        print(f"Removed stale preview: {name}")
    _write_outputs({"removed": str(len(removed))})


@app.command("save-state")
def save_state_command(
    artifact_dir: Path = typer.Option(..., "--artifact-dir"),
    git_repo: Path = typer.Option(..., "--git-repo"),
    state_dir: Path = typer.Option(..., "--state-dir"),
    commit_message: str = typer.Option(..., "--commit-message"),
    state_branch: str = typer.Option(STATE_BRANCH, "--state-branch"),
) -> None:
    save_pages_state(
        artifact_dir=artifact_dir,
        git_repo=git_repo,
        state_dir=state_dir,
        commit_message=commit_message,
        state_branch=state_branch,
    )


@app.command("verify-url")
def verify_url_command(
    url: str = typer.Option(..., "--url"),
    index_url: str = typer.Option(..., "--index-url"),
    summary_heading: str = typer.Option(..., "--summary-heading"),
    primary_label: str = typer.Option(..., "--primary-label"),
    index_label: str = typer.Option(..., "--index-label"),
    success_message: str = typer.Option(..., "--success-message"),
    error_message: str = typer.Option(..., "--error-message"),
    attempts: int = typer.Option(24, "--attempts"),
    sleep_seconds: float = typer.Option(5.0, "--sleep-seconds"),
) -> None:
    print(f"{primary_label}: {url}")
    print(f"{index_label}: {index_url}")
    _write_summary(
        [
            f"### {summary_heading}",
            "",
            f"{primary_label}: {url}",
            f"{index_label}: {index_url}",
        ]
    )
    if verify_urls(
        url=url,
        index_url=index_url,
        attempts=attempts,
        sleep_seconds=sleep_seconds,
    ):
        print(success_message)
        _write_summary(["", success_message])
        return
    print(f"::error::{error_message}: {url} {index_url}")
    raise typer.Exit(1)


@app.command("comment-preview")
def comment_preview_command(
    repo: str = typer.Option(..., "--repo"),
    pr_number: str = typer.Option(..., "--pr-number"),
    preview_url: str = typer.Option(..., "--preview-url"),
    index_url: str = typer.Option(..., "--index-url"),
    branch: str = typer.Option(..., "--branch"),
    head_sha: str = typer.Option(..., "--head-sha"),
) -> None:
    body = preview_comment_body(
        preview_url=preview_url,
        index_url=index_url,
        branch=branch,
        head_sha=head_sha,
    )
    result = upsert_preview_comment(repo=repo, pr_number=pr_number, body=body)
    print(f"Preview PR comment {result}.")
