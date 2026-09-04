"""Read a board branch through an isolated Git worktree."""

from __future__ import annotations

import hashlib
from pathlib import Path
import re
import subprocess
import warnings


def sync_board_worktree(project_dir: Path, ref: str) -> Path:
    """Return a clean detached worktree at the current board ref.

    A local branch wins so a repository with a dedicated board worktree can
    preview its latest committed state without pushing. CI normally has no
    local board branch, so it fetches the named branch from ``origin`` and
    checks out that remote commit instead.
    """
    project_root = _git_output(project_dir, "rev-parse", "--show-toplevel")
    repo = Path(project_root).resolve()
    branch = _branch_name(ref)
    commit = _resolve_commit(repo, branch)
    worktree = repo / ".worktrees" / _worktree_name(branch)

    if worktree.exists():
        actual_root = _git_output(worktree, "rev-parse", "--show-toplevel")
        if Path(actual_root).resolve() != worktree.resolve():
            raise ValueError(
                f"kanban: managed worktree path '{worktree}' is not a Git worktree"
            )
        dirty = _git_output(worktree, "status", "--porcelain")
        if dirty:
            raise ValueError(
                f"kanban: managed worktree '{worktree}' has local changes; "
                "remove them or delete that disposable worktree"
            )
        _git(worktree, "checkout", "--detach", "--quiet", commit)
        return worktree

    worktree.parent.mkdir(parents=True, exist_ok=True)
    _git(repo, "worktree", "prune")
    _git(repo, "worktree", "add", "--detach", "--quiet", str(worktree), commit)
    return worktree


def _branch_name(ref: str) -> str:
    branch = ref.strip()
    if not branch:
        raise ValueError("kanban: `ref` needs a branch name")
    probe = subprocess.run(
        ["git", "check-ref-format", "--branch", branch],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise ValueError(f"kanban: invalid board branch name {branch!r}")
    return branch


def _resolve_commit(repo: Path, branch: str) -> str:
    local = _try_commit(repo, f"refs/heads/{branch}")
    if local:
        return local

    remote_ref = f"refs/remotes/origin/{branch}"
    fetch = subprocess.run(
        [
            "git",
            "-C",
            str(repo),
            "fetch",
            "--quiet",
            "origin",
            f"+refs/heads/{branch}:{remote_ref}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    remote = _try_commit(repo, remote_ref)
    if remote:
        if fetch.returncode != 0:
            warnings.warn(
                f"kanban: could not refresh origin/{branch}; using the cached ref",
                stacklevel=2,
            )
        return remote

    detail = fetch.stderr.strip() or fetch.stdout.strip() or "branch not found"
    raise ValueError(
        f"kanban: cannot resolve board branch {branch!r}: {detail}"
    )


def _try_commit(repo: Path, ref: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", f"{ref}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _worktree_name(branch: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", branch.lower()).strip("-") or "board"
    digest = hashlib.sha256(branch.encode()).hexdigest()[:8]
    return f"folio-kanban-{slug}-{digest}"


def _git(cwd: Path, *args: str) -> None:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git failed"
        raise ValueError(f"kanban: could not prepare board worktree: {detail}")


def _git_output(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "git failed"
        raise ValueError(f"kanban: board refs require a Git repository: {detail}")
    return result.stdout.strip()
