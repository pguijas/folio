"""The kanban operations module: the write path every surface shares.

Each op is a direct call — no CLI in between — and every assertion lands on
the artifact a caller consumes: the card file's bytes, the commit in git,
the OpResult contract.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from folio_agents.ops import (
    ExpectationError,
    OpError,
    add_card,
    comment_card,
    move_card,
    update_card,
)

DOCS_YAML = """\
project:
  name: "Demo"
  repo: "https://github.com/acme/demo"
kanban:
  routes:
    public: false
    docs: false
  source: board
"""

BOARD_YAML = """\
title: "Demo Board"
columns:
  - id: backlog
    title: "Backlog"
  - id: doing
    title: "Doing"
    limit: 1
  - id: done
    title: "Done"
"""


def _card(project: Path, card_id: str, front: str, body: str = "") -> Path:
    path = project / "board" / "cards" / f"{card_id}.md"
    path.write_text(f"---\n{front}\n---\n{body}", encoding="utf-8")
    return path


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "demo"
    (project / "board" / "cards").mkdir(parents=True)
    (project / "docs.yaml").write_text(DOCS_YAML, encoding="utf-8")
    (project / "board" / "board.yaml").write_text(BOARD_YAML, encoding="utf-8")
    _card(project, "alpha", "title: Alpha\nstatus: backlog")
    _card(project, "beta", "title: Beta\nstatus: doing\norder: 100")
    _card(project, "gamma", "title: Gamma\nstatus: done")
    return project


def _git(project: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "Tester"], cwd=project, check=True)
    subprocess.run(["git", "add", "."], cwd=project, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "seed"], cwd=project, check=True)
    return project


def _last_commit(project: Path) -> tuple[str, list[str]]:
    """(subject, touched paths) of HEAD."""
    out = subprocess.run(
        ["git", "log", "-1", "--name-only", "--pretty=%s"],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    return out[0], [line for line in out[1:] if line.strip()]


def _clean(project: Path) -> bool:
    out = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return not out.strip()


def test_move_writes_the_status_line_and_commits_only_the_card(
    tmp_path: Path,
) -> None:
    project = _git(_project(tmp_path))
    result = move_card(project / "board", "alpha", "done")
    assert "status: done" in (project / "board/cards/alpha.md").read_text()
    assert result.card_id == "alpha"
    assert result.path == project / "board" / "cards" / "alpha.md"
    assert result.committed is True
    assert result.message == "board: alpha backlog -> done"
    subject, paths = _last_commit(project)
    assert subject == result.message
    assert paths == ["board/cards/alpha.md"]
    assert _clean(project)


def test_move_with_a_stale_expectation_refuses_without_writing(
    tmp_path: Path,
) -> None:
    project = _git(_project(tmp_path))
    before = (project / "board/cards/alpha.md").read_text()
    with pytest.raises(ExpectationError):
        move_card(project / "board", "alpha", "done", expect_status="doing")
    assert (project / "board/cards/alpha.md").read_text() == before
    assert _clean(project)


def test_move_refuses_unknown_column_and_unknown_card(tmp_path: Path) -> None:
    project = _git(_project(tmp_path))
    with pytest.raises(OpError, match="unknown status"):
        move_card(project / "board", "alpha", "nowhere")
    with pytest.raises(OpError, match="no card"):
        move_card(project / "board", "missing", "done")
    assert _clean(project)


def test_move_without_commit_leaves_the_change_in_the_tree(
    tmp_path: Path,
) -> None:
    project = _git(_project(tmp_path))
    result = move_card(project / "board", "alpha", "done", commit=False)
    assert result.committed is False
    assert result.message == "board: alpha backlog -> done"
    assert not _clean(project)


def test_move_after_places_by_rank_midpoint(tmp_path: Path) -> None:
    project = _git(_project(tmp_path))
    result = move_card(project / "board", "alpha", "doing", after="beta")
    text = (project / "board/cards/alpha.md").read_text()
    assert "order: 200" in text
    assert result.committed is True
    with pytest.raises(OpError, match="--after"):
        move_card(project / "board", "gamma", "backlog", after="alpha")


def test_update_sets_a_scalar_and_a_comma_assignee_list(tmp_path: Path) -> None:
    project = _git(_project(tmp_path))
    result = update_card(project / "board", "alpha", "priority", "high")
    assert "priority: high" in (project / "board/cards/alpha.md").read_text()
    assert result.message == "board: update alpha"
    _, paths = _last_commit(project)
    assert paths == ["board/cards/alpha.md"]
    update_card(project / "board", "alpha", "assignee", "ana, bo")
    assert "assignee: [ana, bo]" in (project / "board/cards/alpha.md").read_text()


def test_update_sets_the_release_track(tmp_path: Path) -> None:
    project = _git(_project(tmp_path))

    update_card(project / "board", "alpha", "track", "agents")

    assert "track: agents" in (project / "board/cards/alpha.md").read_text()


def test_update_refuses_bad_fields_and_sizes_untouched(tmp_path: Path) -> None:
    project = _git(_project(tmp_path))
    before = (project / "board/cards/alpha.md").read_text()
    with pytest.raises(OpError, match="cannot set"):
        update_card(project / "board", "alpha", "status", "done")
    with pytest.raises(OpError, match="size must be"):
        update_card(project / "board", "alpha", "size", "huge")
    assert (project / "board/cards/alpha.md").read_text() == before
    assert _clean(project)


def test_comment_appends_to_the_thread_and_commits_narrow(
    tmp_path: Path,
) -> None:
    project = _git(_project(tmp_path))
    result = comment_card(project / "board", "alpha", "shipping this", actor="ana")
    text = (project / "board/cards/alpha.md").read_text()
    assert "## Comments" in text
    assert "@ana: shipping this" in text
    assert result.message == "board: comment on alpha"
    subject, paths = _last_commit(project)
    assert subject == "board: comment on alpha"
    assert paths == ["board/cards/alpha.md"]


def test_add_creates_a_loadable_card_and_commits_it(tmp_path: Path) -> None:
    project = _git(_project(tmp_path))
    result = add_card(
        project / "board",
        "Fresh Card",
        status="backlog",
        tags=["core"],
        priority="high",
    )
    assert result.card_id == "fresh-card"
    text = (project / "board/cards/fresh-card.md").read_text()
    assert "title: Fresh Card" in text
    assert "tags: [core]" in text
    assert "priority: high" in text
    subject, paths = _last_commit(project)
    assert subject == "board: add fresh-card"
    assert paths == ["board/cards/fresh-card.md"]


def test_add_defaults_to_the_first_column_and_refuses_duplicates(
    tmp_path: Path,
) -> None:
    project = _git(_project(tmp_path))
    result = add_card(project / "board", "Inbox Item", commit=False)
    assert "status: backlog" in (project / "board/cards/inbox-item.md").read_text()
    assert result.committed is False
    with pytest.raises(OpError, match="already exists"):
        add_card(project / "board", "Inbox Item", commit=False)
    with pytest.raises(OpError, match="unknown status"):
        add_card(project / "board", "Elsewhere", status="nowhere", commit=False)
