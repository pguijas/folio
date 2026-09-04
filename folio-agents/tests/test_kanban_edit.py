"""Line-surgery card edits: targeted, verified, never a YAML round-trip."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from folio_agents.edit import (
    CardEditError,
    append_trail,
    format_trail_entry,
    insert_artifact,
    set_scalar,
)

CARD = """\
---
# hand-written comment that must survive every edit
title: "Write CLI"
status: backlog
tags: [cli]
artifacts:
  - url: https://example.com/spec
---

Deterministic mutation commands.

## Acceptance criteria
- [ ] move command

## Trail
- 2026-07-10 @pguijas: card created
"""


@pytest.fixture()
def card(tmp_path: Path) -> Path:
    path = tmp_path / "write-cli.md"
    path.write_text(CARD, encoding="utf-8")
    return path


def test_set_scalar_is_a_one_line_diff(card: Path) -> None:
    set_scalar(card, "status", "in-progress")
    text = card.read_text(encoding="utf-8")
    assert "status: in-progress\n" in text
    # Everything else — comments, quoting, order, body — is byte-identical.
    assert text == CARD.replace("status: backlog", "status: in-progress")


def test_set_scalar_adds_missing_key_at_end_of_frontmatter(card: Path) -> None:
    set_scalar(card, "assignee", "claude")
    text = card.read_text(encoding="utf-8")
    assert "\nassignee: claude\n---\n" in text


def test_set_scalar_quotes_unsafe_values(card: Path) -> None:
    set_scalar(card, "title", 'a "quoted": title')
    assert 'title: "a \\"quoted\\": title"' in card.read_text(encoding="utf-8")


def test_set_scalar_refuses_block_scalars(tmp_path: Path) -> None:
    path = tmp_path / "exotic.md"
    path.write_text(
        "---\ntitle: >\n  folded\n  scalar\nstatus: backlog\n---\n",
        encoding="utf-8",
    )
    before = path.read_text(encoding="utf-8")
    with pytest.raises(CardEditError, match="edit the file manually"):
        set_scalar(path, "title", "plain")
    assert path.read_text(encoding="utf-8") == before


def test_append_trail_lands_at_section_end(card: Path) -> None:
    entry = format_trail_entry(
        date="2026-07-12", actor="claude", ref="abc1234", note="did the thing"
    )
    append_trail(card, entry)
    text = card.read_text(encoding="utf-8")
    assert text.endswith(
        "## Trail\n"
        "- 2026-07-10 @pguijas: card created\n"
        "- 2026-07-12 @claude (abc1234): did the thing\n"
    )


def test_append_trail_keeps_following_sections_intact(tmp_path: Path) -> None:
    path = tmp_path / "ordered.md"
    path.write_text(
        textwrap.dedent(
            """\
            ---
            title: X
            status: backlog
            ---

            ## Trail
            - 2026-07-10 @a: first

            ## Notes
            keep me last
            """
        ),
        encoding="utf-8",
    )
    append_trail(path, "- 2026-07-12 @b: second")
    text = path.read_text(encoding="utf-8")
    assert text.index("@a: first") < text.index("@b: second") < text.index("## Notes")


def test_append_trail_creates_missing_section(tmp_path: Path) -> None:
    path = tmp_path / "fresh.md"
    path.write_text("---\ntitle: X\nstatus: backlog\n---\n\nBody.\n", encoding="utf-8")
    append_trail(path, "- 2026-07-12 @claude: first entry")
    assert path.read_text(encoding="utf-8").endswith(
        "Body.\n\n## Trail\n- 2026-07-12 @claude: first entry\n"
    )


def test_insert_artifact_appends_to_existing_block(card: Path) -> None:
    insert_artifact(card, "pr", 42)
    insert_artifact(card, "doc", "research/notes.md", label="Notes")
    text = card.read_text(encoding="utf-8")
    assert (
        "artifacts:\n"
        "  - url: https://example.com/spec\n"
        "  - pr: 42\n"
        "  - doc: research/notes.md\n"
        "    label: Notes\n"
        "---" in text
    )


def test_insert_artifact_creates_missing_block(tmp_path: Path) -> None:
    path = tmp_path / "bare.md"
    path.write_text("---\ntitle: X\nstatus: backlog\n---\n", encoding="utf-8")
    insert_artifact(path, "url", "https://example.com")
    assert "artifacts:\n  - url: https://example.com\n---" in path.read_text(
        encoding="utf-8"
    )


def test_insert_artifact_rejects_bad_kind(card: Path) -> None:
    before = card.read_text(encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one kind key"):
        insert_artifact(card, "nope", "x")
    assert card.read_text(encoding="utf-8") == before


def test_format_trail_entry_grammar() -> None:
    assert (
        format_trail_entry(date="2026-07-12", actor="@claude", note="a  b\nc")
        == "- 2026-07-12 @claude: a b c"
    )
    with pytest.raises(CardEditError, match="YYYY-MM-DD"):
        format_trail_entry(date="yesterday", actor="a", note="n")
    with pytest.raises(CardEditError, match="single token"):
        format_trail_entry(date="2026-07-12", actor="two words", note="n")


def test_failed_verification_restores_original(card: Path) -> None:
    from folio_agents.edit import _write_verified

    before = card.read_text(encoding="utf-8")
    with pytest.raises(CardEditError, match="left untouched"):
        _write_verified(
            card, before, "garbage, not a card", verify=lambda meta: True, what="test"
        )
    assert card.read_text(encoding="utf-8") == before


def test_format_trail_entry_rejects_parens_in_ref() -> None:
    with pytest.raises(CardEditError, match="parentheses"):
        format_trail_entry(date="2026-07-13", actor="a", ref="feat(cli): x", note="n")


def test_insert_artifact_survives_comment_inside_block(tmp_path: Path) -> None:
    path = tmp_path / "commented.md"
    path.write_text(
        "---\ntitle: X\nstatus: backlog\nartifacts:\n"
        "  - url: https://a.example\n"
        "# a hand-written note\n"
        "  - url: https://b.example\n---\n",
        encoding="utf-8",
    )
    insert_artifact(path, "pr", 9)
    text = path.read_text(encoding="utf-8")
    assert text.index("b.example") < text.index("- pr: 9")
