"""The ``folio board`` plugin: write path over a cardfile board."""

from __future__ import annotations

import subprocess
from pathlib import Path

import typer
from typer.testing import CliRunner

from folio_agents.cli_commands import register
from folio_agents.loader import load_board_dir

app = typer.Typer(name="folio")
register(app)
runner = CliRunner()

AGENTS_YAML = """\
project:
  name: "Demo"
  repo: "https://github.com/acme/demo"
board:
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
    (project / "agents.yaml").write_text(AGENTS_YAML, encoding="utf-8")
    (project / "board" / "board.yaml").write_text(BOARD_YAML, encoding="utf-8")
    _card(project, "alpha", "title: Alpha\nstatus: backlog")
    _card(project, "beta", "title: Beta\nstatus: doing\norder: 100")
    _card(project, "gamma", "title: Gamma\nstatus: done")
    return project


def _invoke(project: Path, *args: str):
    return runner.invoke(app, ["board", *args, "--project-dir", str(project)])


def _board_card(project: Path, card_id: str) -> dict:
    """The card as the board consumes it — derived artifacts included."""
    board = load_board_dir(project / "board", project_dir=project)
    for column in board["columns"]:
        for card in column["cards"]:
            if card["id"] == card_id:
                return card
    raise AssertionError(f"card '{card_id}' not on the loaded board")


def test_show_table_lists_ids_and_blockers(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _card(project, "delta", "title: Delta\nstatus: backlog\nblocked_by: [alpha]")
    result = _invoke(project)
    assert result.exit_code == 0
    assert "Demo Board" in result.output
    assert "alpha" in result.output
    assert "blocked by" in result.output


def test_check_passes_and_fails(tmp_path: Path) -> None:
    project = _project(tmp_path)
    assert _invoke(project, "check").exit_code == 0
    ok = _invoke(project, "check").output
    assert "Board OK: 3 cards" in ok
    # no roadmap section in agents.yaml → the milestone registry stays silent
    assert "matches no roadmap phase" not in ok

    _card(project, "broken", "title: Broken\nstatus: nope")
    result = _invoke(project, "check")
    assert result.exit_code == 1
    # the console wraps the error at terminal width, so compare unwrapped text
    assert "has status 'nope'" in " ".join(result.output.split())


def test_check_warns_yellow_on_unclaimed_milestones_and_stays_green(
    tmp_path: Path,
) -> None:
    """check replays the roadmap resolution the build runs in configure()."""
    project = _project(tmp_path)
    (project / "agents.yaml").write_text(
        AGENTS_YAML
        + """\
roadmap:
  phases:
    - id: "foundation"
      version: "0.1"
      title: "Foundation"
""",
        encoding="utf-8",
    )
    _card(project, "future", 'title: Future\nstatus: backlog\nmilestone: "0.9"')
    result = _invoke(project, "check")
    assert result.exit_code == 0
    # the console wraps warnings at terminal width, so compare unwrapped text
    flat = " ".join(result.output.split())
    assert "milestone '0.9' matches no roadmap phase" in flat
    assert "cards: future" in flat
    assert "known: 0.1" in flat
    assert "Board OK" in result.output


def test_add_creates_card_and_refuses_duplicates(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = _invoke(
        project,
        "add",
        "Ship it fast",
        "--status",
        "backlog",
        "--tags",
        "cli,core",
        "--priority",
        "high",
        "--track",
        "docs",
        "--milestone",
        "docs-0.3",
        "--description",
        "Body.",
    )
    assert result.exit_code == 0, result.output
    text = (project / "board" / "cards" / "ship-it-fast.md").read_text(encoding="utf-8")
    assert "title: Ship it fast" in text
    assert "status: backlog" in text
    assert "tags: [cli, core]" in text
    assert "priority: high" in text
    assert "track: docs" in text
    assert "milestone: docs-0.3" in text
    assert text.endswith("Body.\n")

    again = _invoke(project, "add", "Ship it fast")
    assert again.exit_code == 1
    assert "already exists" in again.output


def test_add_rejects_unknown_status(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = _invoke(project, "add", "X", "--status", "nope")
    assert result.exit_code == 1
    assert "unknown status" in result.output


def test_move_edits_one_line_and_warns_on_wip(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = _invoke(project, "move", "alpha", "doing")
    assert result.exit_code == 0, result.output
    assert "WIP" in result.output  # doing already holds beta at limit 1
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "status: doing" in text
    assert "moved: alpha backlog → doing" in result.output


def test_move_rejects_unknown_column_before_editing(tmp_path: Path) -> None:
    project = _project(tmp_path)
    before = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    result = _invoke(project, "move", "alpha", "nope")
    assert result.exit_code == 1
    assert (project / "board" / "cards" / "alpha.md").read_text(
        encoding="utf-8"
    ) == before


def test_move_after_computes_rank(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = _invoke(project, "move", "alpha", "doing", "--after", "beta")
    assert result.exit_code == 0, result.output
    assert "order: 200" in (project / "board" / "cards" / "alpha.md").read_text(
        encoding="utf-8"
    )


def test_move_after_requires_ranked_anchor(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = _invoke(project, "move", "alpha", "done", "--after", "gamma")
    assert result.exit_code == 1
    assert "order" in result.output


def test_update_sets_scalars_and_rejects_status(tmp_path: Path) -> None:
    project = _project(tmp_path)
    ok = _invoke(
        project,
        "update",
        "alpha",
        "--set",
        "assignee=claude",
        "--set",
        "priority=high",
    )
    assert ok.exit_code == 0, ok.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "assignee: claude" in text
    assert "priority: high" in text

    denied = _invoke(project, "update", "alpha", "--set", "status=done")
    assert denied.exit_code == 1
    assert "move" in denied.output


def test_update_sets_milestone(tmp_path: Path) -> None:
    project = _project(tmp_path)
    ok = _invoke(project, "update", "alpha", "--set", "milestone=0.6")
    assert ok.exit_code == 0, ok.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert 'milestone: "0.6"' in text


def test_update_dangling_parent_rolls_back(tmp_path: Path) -> None:
    project = _project(tmp_path)
    before = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    result = _invoke(project, "update", "alpha", "--set", "parent=ghost")
    assert result.exit_code == 1
    assert "rolled back" in result.output
    assert (project / "board" / "cards" / "alpha.md").read_text(
        encoding="utf-8"
    ) == before


def test_trail_appends_canonical_entry(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = _invoke(
        project,
        "trail",
        "alpha",
        "--note",
        "did work",
        "--ref",
        "abc1234",
        "--actor",
        "claude",
    )
    assert result.exit_code == 0, result.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "## Trail\n- " in text
    assert "@claude (abc1234): did work" in text


def test_attach_url_and_a_missing_doc_warns_at_check(tmp_path: Path) -> None:
    project = _project(tmp_path)
    ok = _invoke(
        project, "attach", "alpha", "--url", "https://example.com", "--label", "Spec"
    )
    assert ok.exit_code == 0, ok.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "  - url: https://example.com\n    label: Spec" in text

    # A missing target is a warning, not topology: the attach lands, and
    # `check` surfaces the loader's warning naming the card and the path.
    missing = _invoke(project, "attach", "alpha", "--doc", "research/gone.md")
    assert missing.exit_code == 0, missing.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "  - doc: research/gone.md" in text
    checked = _invoke(project, "check")
    assert checked.exit_code == 0
    unwrapped = " ".join(checked.output.split())
    assert "resolves to no file" in unwrapped
    assert "research/gone.md" in unwrapped

    two = _invoke(project, "attach", "alpha", "--url", "https://a.io", "--pr", "7")
    assert two.exit_code == 1
    assert "exactly one artifact" in two.output


def test_write_commands_refuse_without_a_board_directory(tmp_path: Path) -> None:
    """A kanban section without `source:` is refused with the same message
    the build gives — the CLI can never bless what the build rejects."""
    project = tmp_path / "nosource"
    project.mkdir()
    (project / "agents.yaml").write_text(
        'project:\n  name: "Demo"\nboard:\n  routes:\n    public: true\n',
        encoding="utf-8",
    )
    result = _invoke(project, "move", "alpha", "doing")
    assert result.exit_code == 1
    assert "`board.source:` pointing at a board directory" in result.output
    assert "board.yaml + cards/" in result.output


def test_check_refuses_a_columns_key_like_the_build_does(tmp_path: Path) -> None:
    """The check-blesses-what-build-rejects hole: a valid cardfile board with
    BOTH a `columns:` key in agents.yaml used to pass check but fail the build."""
    project = tmp_path / "withcolumns"
    (project / "board" / "cards").mkdir(parents=True)
    (project / "board" / "board.yaml").write_text(BOARD_YAML, encoding="utf-8")
    (project / "agents.yaml").write_text(
        'project:\n  name: "Demo"\nboard:\n  source: board\n  columns: []\n',
        encoding="utf-8",
    )
    result = _invoke(project, "check")
    assert result.exit_code == 1
    assert "inline `columns:` boards were removed" in result.output


def test_source_naming_a_file_is_refused_with_the_file_message(tmp_path: Path) -> None:
    """A source that resolves to a file gets its own distinct error message,
    not the generic 'not a directory' message."""
    project = tmp_path / "fileboard"
    project.mkdir()
    (project / "board.yaml").write_text(BOARD_YAML, encoding="utf-8")
    (project / "agents.yaml").write_text(
        'project:\n  name: "Demo"\nboard:\n  source: board.yaml\n', encoding="utf-8"
    )
    result = _invoke(project, "move", "alpha", "doing")
    assert result.exit_code == 1
    assert "is a file" in result.output
    assert "directory of cards" in result.output


def test_source_naming_a_missing_path_is_refused(tmp_path: Path) -> None:
    """A source that doesn't exist gets a distinct message from a file."""
    project = tmp_path / "missing"
    project.mkdir()
    (project / "agents.yaml").write_text(
        'project:\n  name: "Demo"\nboard:\n  source: nonexistent\n', encoding="utf-8"
    )
    result = _invoke(project, "move", "alpha", "doing")
    assert result.exit_code == 1
    assert "no board directory at" in result.output


def test_show_reports_a_legacy_config_without_a_traceback(tmp_path: Path) -> None:
    """A agents.yaml with inline columns used to escape as a traceback; now
    _show catches the configure failure and prints it cleanly."""
    project = tmp_path / "legacy"
    project.mkdir()
    (project / "agents.yaml").write_text(
        'project:\n  name: "Demo"\nboard:\n  columns:\n    - id: backlog\n'
        "      title: Backlog\n      cards: []\n",
        encoding="utf-8",
    )
    result = _invoke(project)
    assert result.exit_code == 1
    assert "inline `columns:` boards were removed" in result.output
    # No traceback — a clean error message.
    assert "Traceback" not in result.output
    assert "PluginHookError" not in result.output


def test_commit_flag_creates_conventional_commit(tmp_path: Path) -> None:
    project = _project(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=project, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=project, check=True)

    result = _invoke(project, "move", "alpha", "done", "--commit")
    assert result.exit_code == 0, result.output
    log = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=project,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert log == "board: alpha backlog -> done"


# --- Regressions from the adversarial review of the POC branch ---


def test_add_quotes_titles_and_colon_tags_safely(tmp_path: Path) -> None:
    """YAML metacharacters in add inputs must produce a valid card."""
    project = _project(tmp_path)
    result = _invoke(
        project, "add", 'Say "hello" to users', "--tags", "infra,needs: review"
    )
    assert result.exit_code == 0, result.output
    assert _invoke(project, "check").exit_code == 0
    import yaml as _yaml

    text = (project / "board" / "cards" / "say-hello-to-users.md").read_text(
        encoding="utf-8"
    )
    meta = _yaml.safe_load(text.split("---")[1])
    assert meta["title"] == 'Say "hello" to users'
    assert meta["tags"] == ["infra", "needs: review"]


def test_move_after_failures_leave_status_untouched(tmp_path: Path) -> None:
    project = _project(tmp_path)
    before = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")

    ghost = _invoke(project, "move", "alpha", "done", "--after", "ghost")
    assert ghost.exit_code == 1
    assert (project / "board" / "cards" / "alpha.md").read_text(
        encoding="utf-8"
    ) == before

    unranked = _invoke(project, "move", "alpha", "done", "--after", "gamma")
    assert unranked.exit_code == 1
    assert (project / "board" / "cards" / "alpha.md").read_text(
        encoding="utf-8"
    ) == before


def test_null_blocked_by_line_does_not_crash_move(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _card(project, "nully", "title: Nully\nstatus: backlog\nblocked_by:")
    assert _invoke(project, "check").exit_code == 0
    result = _invoke(project, "move", "nully", "done")
    assert result.exit_code == 0, result.output


def test_update_multi_set_is_atomic(tmp_path: Path) -> None:
    project = _project(tmp_path)
    before = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    # created=12:34 is YAML sexagesimal — the write verification rejects it.
    result = _invoke(
        project,
        "update",
        "alpha",
        "--set",
        "assignee=bob",
        "--set",
        "created=12:34",
    )
    assert result.exit_code == 1
    assert (project / "board" / "cards" / "alpha.md").read_text(
        encoding="utf-8"
    ) == before


def test_attach_invalid_targets_fail_cleanly(tmp_path: Path) -> None:
    project = _project(tmp_path)
    before = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    result = _invoke(project, "attach", "alpha", "--pr", "-3")
    assert result.exit_code == 1
    assert "must be a PR number" in result.output
    assert "Traceback" not in result.output
    assert (project / "board" / "cards" / "alpha.md").read_text(
        encoding="utf-8"
    ) == before


def test_attach_javascript_url_rolls_back(tmp_path: Path) -> None:
    project = _project(tmp_path)
    before = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    result = _invoke(project, "attach", "alpha", "--url", "javascript:alert(1)")
    assert result.exit_code == 1
    assert (project / "board" / "cards" / "alpha.md").read_text(
        encoding="utf-8"
    ) == before


def test_attach_file_copies_it_in_and_derivation_publishes_it(tmp_path: Path) -> None:
    """A file path turns the card into a bundle: the copy alone is the
    attach, and the loader derives the artifact — no frontmatter line."""
    project = _project(tmp_path)
    source = tmp_path / "elsewhere" / "notes.md"
    source.parent.mkdir()
    source.write_text("# Findings\n", encoding="utf-8")

    result = _invoke(project, "attach", "alpha", str(source))
    assert result.exit_code == 0, result.output
    assert "notes.md" in result.output

    dest = project / "board" / "cards" / "alpha" / "notes.md"
    assert dest.read_text(encoding="utf-8") == "# Findings\n"
    assert source.exists()  # a copy leaves the source alone

    card_text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "artifacts:" not in card_text

    artifacts = _board_card(project, "alpha")["artifacts"]
    assert artifacts == [
        {
            "kind": "doc",
            "target": "board/cards/alpha/notes.md",
            "label": "",
            "display": "notes.md",
        }
    ]


def test_attach_file_move_takes_the_source_with_it(tmp_path: Path) -> None:
    project = _project(tmp_path)
    source = tmp_path / "proto.html"
    source.write_text("<html></html>", encoding="utf-8")

    result = _invoke(project, "attach", "alpha", str(source), "--move")
    assert result.exit_code == 0, result.output
    assert not source.exists()
    dest = project / "board" / "cards" / "alpha" / "proto.html"
    assert dest.read_text(encoding="utf-8") == "<html></html>"

    artifacts = _board_card(project, "alpha")["artifacts"]
    assert [(a["kind"], a["display"]) for a in artifacts] == [("file", "proto.html")]


def test_attach_file_label_writes_one_bare_name_carrier(tmp_path: Path) -> None:
    """--label adds exactly one frontmatter line naming the sibling by its
    bare name; the loader merges the label onto the derived entry."""
    project = _project(tmp_path)
    (tmp_path / "notes.md").write_text("# n\n", encoding="utf-8")
    (tmp_path / "proto.html").write_text("<html></html>", encoding="utf-8")

    doc = _invoke(
        project, "attach", "alpha", str(tmp_path / "notes.md"), "--label", "Findings"
    )
    assert doc.exit_code == 0, doc.output
    raw = _invoke(
        project, "attach", "alpha", str(tmp_path / "proto.html"), "--label", "Tree"
    )
    assert raw.exit_code == 0, raw.output

    card_text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert card_text.count("- doc: notes.md") == 1
    assert card_text.count("- file: proto.html") == 1
    assert "board/cards" not in card_text  # bare names, never the full path

    artifacts = _board_card(project, "alpha")["artifacts"]
    assert [(a["display"], a["label"]) for a in artifacts] == [
        ("notes.md", "Findings"),
        ("proto.html", "Tree"),
    ]


def test_attach_file_refuses_missing_and_irregular_sources(tmp_path: Path) -> None:
    project = _project(tmp_path)

    missing = _invoke(project, "attach", "alpha", str(tmp_path / "gone.md"))
    assert missing.exit_code == 1
    assert "no file at" in missing.output

    directory = tmp_path / "adir"
    directory.mkdir()
    result = _invoke(project, "attach", "alpha", str(directory))
    assert result.exit_code == 1
    assert "not a regular file" in result.output

    (tmp_path / "real.md").write_text("x", encoding="utf-8")
    no_card = _invoke(project, "attach", "nope", str(tmp_path / "real.md"))
    assert no_card.exit_code == 1
    assert "no card 'nope'" in no_card.output
    assert not (project / "board" / "cards" / "nope").exists()


def test_attach_file_refuses_a_taken_name(tmp_path: Path) -> None:
    project = _project(tmp_path)
    card_dir = project / "board" / "cards" / "alpha"
    card_dir.mkdir()
    (card_dir / "notes.md").write_text("already here\n", encoding="utf-8")
    source = tmp_path / "notes.md"
    source.write_text("new\n", encoding="utf-8")

    result = _invoke(project, "attach", "alpha", str(source), "--move")
    assert result.exit_code == 1
    assert "already" in result.output
    assert "remove or rename" in " ".join(result.output.split())
    assert source.exists()  # nothing moved
    assert (card_dir / "notes.md").read_text(encoding="utf-8") == "already here\n"


def test_attach_file_refuses_names_derivation_would_skip(tmp_path: Path) -> None:
    """A dotfile or _-prefixed name would land and publish nothing —
    refused with the reason instead."""
    project = _project(tmp_path)
    for name in (".env-notes", "_draft.md"):
        source = tmp_path / name
        source.write_text("x", encoding="utf-8")
        result = _invoke(project, "attach", "alpha", str(source))
        assert result.exit_code == 1, name
        assert "derivation skips" in " ".join(result.output.split()), name
        assert not (project / "board" / "cards" / "alpha").exists()


def test_attach_file_and_typed_flags_are_exclusive(tmp_path: Path) -> None:
    project = _project(tmp_path)
    source = tmp_path / "notes.md"
    source.write_text("x", encoding="utf-8")

    both = _invoke(project, "attach", "alpha", str(source), "--url", "https://a.io")
    assert both.exit_code == 1
    assert "not both" in both.output

    move_alone = _invoke(project, "attach", "alpha", "--move", "--pr", "7")
    assert move_alone.exit_code == 1
    assert "--move needs a file path" in move_alone.output


def test_attach_file_commit_carries_the_file_and_the_card(tmp_path: Path) -> None:
    project = _project(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=project, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=project, check=True)
    source = tmp_path / "notes.md"
    source.write_text("# n\n", encoding="utf-8")

    result = _invoke(
        project, "attach", "alpha", str(source), "--label", "Findings", "--commit"
    )
    assert result.exit_code == 0, result.output

    log = subprocess.run(
        ["git", "log", "-1", "--format=%s", "--name-only"],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "board: attach alpha notes.md" in log
    assert "board/cards/alpha/notes.md" in log
    assert "board/cards/alpha.md" in log
    clean = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert clean.strip() == ""


def test_attach_move_of_a_tracked_source_commits_its_deletion(tmp_path: Path) -> None:
    """The deletion is the other half of the move: a tracked source rides
    the same commit, and the tree is clean after. An untracked source
    (the previous test's) keeps the board-only scope."""
    project = _project(tmp_path)
    source = project / "design" / "teardown.md"
    source.parent.mkdir()
    source.write_text("# teardown\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=project, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=project, check=True)

    result = _invoke(
        project,
        "attach",
        "alpha",
        str(source),
        "--move",
        "--label",
        "Teardown",
        "--commit",
    )
    assert result.exit_code == 0, result.output

    log = subprocess.run(
        # --no-renames: git shows the staged pair as R100 otherwise; the
        # claim under test is that both halves are in the one commit.
        ["git", "log", "-1", "--format=%s", "--name-status", "--no-renames"],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "board: attach alpha teardown.md" in log
    assert "A\tboard/cards/alpha/teardown.md" in log
    assert "M\tboard/cards/alpha.md" in log
    assert "D\tdesign/teardown.md" in log
    clean = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert clean.strip() == ""


def test_check_matches_build_policies(tmp_path: Path) -> None:
    """check must reject everything the build rejects (scheme policy)."""
    project = _project(tmp_path)
    _card(
        project,
        "evil-link",
        'title: Evil\nstatus: backlog\nlink: "javascript:alert(1)"',
    )
    result = _invoke(project, "check")
    assert result.exit_code == 1

    (project / "board" / "cards" / "evil-link.md").unlink()
    _card(
        project,
        "evil-url",
        'title: Evil2\nstatus: backlog\nartifacts:\n  - url: "javascript:alert(1)"',
    )
    assert _invoke(project, "check").exit_code == 1


def test_traversal_artifacts_are_rejected(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (tmp_path / "outside.md").write_text("x", encoding="utf-8")
    _card(
        project,
        "sneaky",
        "title: Sneaky\nstatus: backlog\nartifacts:\n  - file: ../outside.md",
    )
    result = _invoke(project, "check")
    assert result.exit_code == 1
    assert "escapes the project" in result.output


def test_editor_dotfiles_in_cards_are_ignored(tmp_path: Path) -> None:
    project = _project(tmp_path)
    (project / "board" / "cards" / ".goutputstream-X4").write_text(
        "garbage", encoding="utf-8"
    )
    (project / "board" / "cards" / ".hidden.md").write_text(
        "not yaml at all", encoding="utf-8"
    )
    assert _invoke(project, "check").exit_code == 0


def test_commit_noop_succeeds_with_notice(tmp_path: Path) -> None:
    project = _project(tmp_path)
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=project, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=project, check=True)
    subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=project, check=True)

    result = _invoke(project, "move", "alpha", "backlog", "--commit")
    assert result.exit_code == 0, result.output
    assert "nothing to commit" in result.output


def test_added_card_can_then_be_moved(tmp_path: Path) -> None:
    """`add` must write frontmatter the rest of the CLI can edit.

    `yaml.safe_dump(default_flow_style=None)` collapses a flat mapping onto
    one line — `{title: ..., status: ...}` — and every other command edits by
    line surgery. A card created that way could never be moved again: `move`
    looked for a `status:` line, found none, and refused the file as
    structurally unusual. That broke the second command a new user types.
    """
    project = _project(tmp_path)
    created = _invoke(project, "add", "Fix the kitchen light", "--priority", "high")
    assert created.exit_code == 0, created.output

    text = (project / "board" / "cards" / "fix-the-kitchen-light.md").read_text()
    assert "\nstatus: backlog\n" in text
    assert "{title:" not in text

    moved = _invoke(project, "move", "fix-the-kitchen-light", "doing")
    assert moved.exit_code == 0, moved.output
    assert "structurally unusual" not in moved.output
    assert (
        "\nstatus: doing\n"
        in (project / "board" / "cards" / "fix-the-kitchen-light.md").read_text()
    )


def test_init_scaffolds_a_board_and_wires_the_config(tmp_path: Path) -> None:
    """From a agents.yaml with no board to a board the other commands accept."""
    project = tmp_path / "fresh"
    project.mkdir()
    (project / "agents.yaml").write_text(
        'project:\n  name: "Fresh"\n\n# keep me\nsource:\n  docs:\n    - "docs/"\n',
        encoding="utf-8",
    )

    result = _invoke(project, "init", "--no-branch")
    assert result.exit_code == 0, result.output
    assert (project / "board" / "board.yaml").is_file()
    assert (project / "board" / "cards" / "read-me-first.md").is_file()
    # The protocol travels with the board, with a skill preamble so a runtime
    # that scans for skills can match it to a task rather than the agent
    # having to already know the file exists.
    skill = (project / "board" / "SKILL.md").read_text()
    assert skill.startswith("---\nname: folio-agents-board\n")
    assert "description: Use when reading or changing" in skill
    assert "folio board move <id> in-progress" in skill
    assert "condense artifacts <card-id>" in skill
    assert "It is not a shell command" in skill
    assert "rejects `all`, paths, globs, or multiple ids" in skill
    assert "Every artifact handoff includes a rendered URL" in skill
    assert "path alone is" in skill

    # The config is appended to, never round-tripped, so comments survive.
    config = (project / "agents.yaml").read_text()
    assert "# keep me" in config
    assert "board:" in config
    assert "source: board" in config

    # The generated board is usable by the commands that follow it.
    assert _invoke(project, "check").exit_code == 0
    added = _invoke(project, "add", "First task")
    assert added.exit_code == 0, added.output
    assert _invoke(project, "move", "first-task", "in-progress").exit_code == 0


def test_init_refuses_to_overwrite(tmp_path: Path) -> None:
    """An existing board or an existing kanban section is a loud refusal."""
    project = _project(tmp_path)
    result = _invoke(project, "init")
    assert result.exit_code == 1
    assert "already exists" in result.output or "already has" in result.output


def test_init_isolates_the_board_on_its_own_branch(tmp_path: Path) -> None:
    """Organization work gets its own branch so code history stays about code.

    A card moves several times a week; nobody wants "board: move x done"
    between two commits of a feature.
    """
    project = tmp_path / "repo"
    project.mkdir()
    (project / "agents.yaml").write_text('project:\n  name: "Repo"\n', encoding="utf-8")
    for args in (
        ["init", "-q"],
        ["config", "user.email", "t@t.t"],
        ["config", "user.name", "Tester"],
        ["add", "-A"],
        ["commit", "-qm", "first"],
    ):
        subprocess.run(["git", *args], cwd=project, check=True, capture_output=True)
    start = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=project,
        capture_output=True,
        text=True,
    ).stdout.strip()

    result = _invoke(project, "init", "--commit")
    assert result.exit_code == 0, result.output

    now = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=project,
        capture_output=True,
        text=True,
    ).stdout.strip()
    assert now == "board" and now != start

    # The starting branch never saw the board.
    on_start = subprocess.run(
        ["git", "ls-tree", "--name-only", start, "board/"],
        cwd=project,
        capture_output=True,
        text=True,
    ).stdout
    assert on_start.strip() == ""


def test_init_refuses_an_existing_branch(tmp_path: Path) -> None:
    project = tmp_path / "repo2"
    project.mkdir()
    (project / "agents.yaml").write_text('project:\n  name: "Repo"\n', encoding="utf-8")
    for args in (
        ["init", "-q"],
        ["config", "user.email", "t@t.t"],
        ["config", "user.name", "Tester"],
        ["add", "-A"],
        ["commit", "-qm", "first"],
        ["branch", "board"],
    ):
        subprocess.run(["git", *args], cwd=project, check=True, capture_output=True)

    result = _invoke(project, "init")
    assert result.exit_code == 1
    assert "already exists" in result.output
    # Refused before writing anything.
    assert not (project / "board").exists()


def test_init_without_git_says_so(tmp_path: Path) -> None:
    project = tmp_path / "nogit"
    project.mkdir()
    (project / "agents.yaml").write_text('project:\n  name: "Repo"\n', encoding="utf-8")
    result = _invoke(project, "init")
    assert result.exit_code == 1
    assert "not a git repository" in result.output
    assert not (project / "board").exists()


def test_show_table_prints_type(tmp_path: Path) -> None:
    project = _project(tmp_path)
    _card(project, "delta", "title: Delta\nstatus: backlog\ntype: bug")
    result = _invoke(project, "show")
    assert result.exit_code == 0, result.output
    assert "bug" in result.output


def test_update_sets_type(tmp_path: Path) -> None:
    project = _project(tmp_path)
    ok = _invoke(project, "update", "alpha", "--set", "type=bug")
    assert ok.exit_code == 0, ok.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "type: bug" in text


def test_update_sets_an_assignee_list_by_commas(tmp_path: Path) -> None:
    project = _project(tmp_path)
    result = _invoke(project, "update", "alpha", "--set", "assignee=ana, bo")
    assert result.exit_code == 0, result.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "assignee: [ana, bo]" in text


def test_update_rejects_a_size_off_the_scale_and_uppercases_on_it(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    bad = _invoke(project, "update", "alpha", "--set", "size=xxl")
    assert bad.exit_code != 0
    assert "use S, M, L, or XL" in bad.output
    good = _invoke(project, "update", "alpha", "--set", "size=m")
    assert good.exit_code == 0, good.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "size: M" in text


def test_update_sets_source_and_show_has_a_size_column(tmp_path: Path) -> None:
    project = _project(tmp_path)
    ok = _invoke(project, "update", "alpha", "--set", "source=folio#feat/x")
    assert ok.exit_code == 0, ok.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "source: folio#feat/x" in text
    shown = _invoke(project, "show")
    assert shown.exit_code == 0, shown.output
    assert "Size" in shown.output


def test_add_assignee_splits_on_commas(tmp_path: Path) -> None:
    project = _project(tmp_path)
    pair = _invoke(project, "add", "Pair task", "--assignee", "ana, bo")
    assert pair.exit_code == 0, pair.output
    text = (project / "board" / "cards" / "pair-task.md").read_text(encoding="utf-8")
    assert "assignee: [ana, bo]" in text

    solo = _invoke(project, "add", "Solo task", "--assignee", "claude")
    assert solo.exit_code == 0, solo.output
    assert "assignee: claude" in (
        project / "board" / "cards" / "solo-task.md"
    ).read_text(encoding="utf-8")


def test_add_all_comma_assignee_means_no_assignee(tmp_path: Path) -> None:
    """An --assignee of only commas/whitespace names nobody — same as omitting it."""
    project = _project(tmp_path)
    result = _invoke(project, "add", "Ghost task", "--assignee", " , ")
    assert result.exit_code == 0, result.output
    assert "Traceback" not in result.output
    text = (project / "board" / "cards" / "ghost-task.md").read_text(encoding="utf-8")
    assert "assignee" not in text


def test_comment_appends_canonical_entry_and_creates_the_section(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    result = _invoke(
        project,
        "comment",
        "alpha",
        "the retry masks the race — see the trail ref",
        "--by",
        "peter",
    )
    assert result.exit_code == 0, result.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "## Comments\n- " in text
    assert "@peter: the retry masks the race — see the trail ref" in text

    # A second comment lands at the section's tail, not its head.
    again = _invoke(project, "comment", "alpha", "second thought", "--by", "peter")
    assert again.exit_code == 0, again.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert text.index("the retry masks") < text.index("second thought")

    # Empty text is refused and the card is untouched.
    before = text
    bad = _invoke(project, "comment", "alpha", "   ")
    assert bad.exit_code == 1
    assert (project / "board" / "cards" / "alpha.md").read_text(
        encoding="utf-8"
    ) == before

    # The writer collapses whitespace like the trail's, the echoed entry
    # survives Rich markup (a bracketed path used to crash AFTER the
    # write), and the line lands in the strict grammar.
    ragged = _invoke(
        project, "comment", "alpha", "see  [/api/users]\n handler", "--by", "peter"
    )
    assert ragged.exit_code == 0, ragged.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert "@peter: see [/api/users] handler" in text
    import re as _re

    assert _re.search(
        r"^- \d{4}-\d{2}-\d{2} @peter: see \[/api/users\] handler$",
        text,
        _re.MULTILINE,
    )

    # A hand-authored section in another case is still THE section: the
    # writer must never create a duplicate the parse would last-wins over.
    shouty = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    shouty = shouty.replace("## Comments", "## COMMENTS")
    (project / "board" / "cards" / "alpha.md").write_text(shouty, encoding="utf-8")
    upper = _invoke(project, "comment", "alpha", "case blind", "--by", "peter")
    assert upper.exit_code == 0, upper.output
    text = (project / "board" / "cards" / "alpha.md").read_text(encoding="utf-8")
    assert text.count("## COMMENTS") == 1
    assert "## Comments" not in text
    assert "case blind" in text


def test_init_writes_card_template(tmp_path: Path) -> None:
    """init scaffolds cards/_TEMPLATE.md for the copy-a-template workflow."""
    from folio_agents.loader import load_board_dir

    project = tmp_path / "fresh"
    project.mkdir()
    (project / "agents.yaml").write_text(
        'project:\n  name: "Fresh"\n\n# keep me\nsource:\n  docs:\n    - "docs/"\n',
        encoding="utf-8",
    )

    result = _invoke(project, "init", "--no-branch")
    assert result.exit_code == 0, result.output
    template = project / "board" / "cards" / "_TEMPLATE.md"
    assert template.is_file()
    text = template.read_text()
    assert text.startswith("---")
    assert "status: backlog" in text
    # Underscore prefix means the loader must not count it as a card.
    board = load_board_dir(project / "board", project_dir=project)
    ids = {card["id"] for column in board["columns"] for card in column["cards"]}
    assert "_TEMPLATE" not in ids
