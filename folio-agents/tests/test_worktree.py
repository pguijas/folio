from __future__ import annotations

from pathlib import Path
import subprocess

from folio_agents.worktree import sync_board_worktree


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_board_ref_is_read_through_a_detached_worktree(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("code\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-m", "code")
    _git(repo, "checkout", "-b", "board")
    (repo / "board.txt").write_text("planning\n", encoding="utf-8")
    _git(repo, "add", "board.txt")
    _git(repo, "commit", "-m", "board")
    _git(repo, "checkout", "main")

    worktree = sync_board_worktree(repo, "board")

    assert (worktree / "board.txt").read_text(encoding="utf-8") == "planning\n"
    assert not (repo / "board.txt").exists()
    branch = subprocess.run(
        ["git", "-C", str(worktree), "symbolic-ref", "-q", "HEAD"],
        check=False,
        capture_output=True,
    )
    assert branch.returncode != 0
