"""Board operations as importable functions — the write path every surface shares.

The CLI's subcommands, the serve write API, and any future mount all call
these four operations; each one is a targeted file edit through the
verified surgery in ``kanban_edit``, a board revalidation with rollback,
and optionally one conventional commit whose pathspec is limited to the
touched card file. Refusals raise (``OpError``, or ``ExpectationError``
when the board moved under the caller); nothing here prints.
"""

from __future__ import annotations

import datetime as _dt
import subprocess
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml

from folio.generator.sidebar import _slugify
from folio.plugins.kanban_board import load_board_dir
from folio.plugins.kanban_edit import (
    append_comment,
    format_comment_entry,
    set_list,
    set_scalar,
)

UPDATE_FIELDS = (
    "assignee",
    "priority",
    "title",
    "order",
    "parent",
    "created",
    "milestone",
    "type",
    "size",
    "source",
)


class OpError(ValueError):
    """A refused operation: bad input, unknown ids, a failed commit."""


class ExpectationError(OpError):
    """The caller's picture of the board is stale; nothing was written."""


@dataclass
class OpResult:
    card_id: str
    path: Path
    committed: bool
    message: str  # the conventional commit message used or skipped
    warnings: list[str] = field(default_factory=list)
    old_status: str = ""  # move only: where the card came from
    # op-specific detail: the comment entry appended, or the column a new
    # card landed in.
    detail: str = ""


class _CardDumper(yaml.SafeDumper):
    """Block mappings, inline sequences — the format the rest of the CLI reads.

    The mapping has to be block style: every other command edits card
    frontmatter by line surgery, so a card dumped as
    ``{title: ..., status: ...}`` could never be moved again — ``move``
    looked for a ``status:`` line, found none, and refused the file as
    structurally unusual.

    The sequences have to stay inline: ``tags: [cli, core]`` is the one-line
    hand edit the format documents, and PyYAML's ``default_flow_style`` is
    all-or-nothing, so the two rules need a representer rather than a flag.
    """


def _represent_flow_sequence(dumper: yaml.SafeDumper, data: list) -> Any:
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


_CardDumper.add_representer(list, _represent_flow_sequence)


def resolve_actor() -> str:
    result = subprocess.run(
        ["git", "config", "user.name"], capture_output=True, text=True
    )
    name = _slugify(result.stdout.strip()) if result.returncode == 0 else ""
    return name or "local"


def _today() -> str:
    return _dt.date.today().isoformat()


def _project_dir(board_dir: Path, project_dir: Optional[Path]) -> Path:
    # The board directory conventionally sits at the project root; callers
    # with an unusual layout pass project_dir explicitly.
    return (project_dir or board_dir.parent).resolve()


def _load_board(board_dir: Path, project_dir: Path) -> dict[str, Any]:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return load_board_dir(board_dir, project_dir=project_dir)
    except ValueError as exc:
        raise OpError(str(exc)) from exc


def _card_path(board_dir: Path, card_id: str) -> Path:
    path = board_dir / "cards" / f"{card_id}.md"
    if not path.is_file():
        raise OpError(f"no card '{card_id}' on this board ({path} not found)")
    return path


def _find_card(board: dict[str, Any], card_id: str) -> tuple[dict, dict]:
    for column in board["columns"]:
        for card in column["cards"]:
            if card["id"] == card_id:
                return column, card
    raise OpError(f"no card '{card_id}' on this board")


def revalidate_or_rollback(
    board_dir: Path, project_dir: Path, path: Path, original: str
) -> None:
    """Board-level validation after an edit; a bad board never survives.

    The line-surgery editor verifies each file in isolation, but only a
    full reload catches board-topology damage (a dangling parent set via
    update, an artifact whose doc target is missing). On failure the card
    file gets its original bytes back before the error propagates.
    """
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            load_board_dir(board_dir, project_dir=project_dir)
    except ValueError as exc:
        path.write_text(original, encoding="utf-8")
        raise OpError(f"{exc} — the edit was rolled back") from exc


def commit_paths(project_dir: Path, paths: list[Path], message: str) -> bool:
    """Stage and commit exactly ``paths``; True when a commit was made.

    False means the working tree already held this state — not an error,
    the caller decides whether that is worth a word.
    """
    specs = [str(p) for p in paths]
    try:
        subprocess.run(
            ["git", "add", "--", *specs],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        status = subprocess.run(
            ["git", "status", "--porcelain", "--", *specs],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        if not status.stdout.strip():
            return False
        subprocess.run(
            ["git", "commit", "-m", message, "--", *specs],
            cwd=project_dir,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise OpError(f"git commit failed: {exc.stderr or exc.stdout}") from exc
    return True


def compute_after_rank(column: dict[str, Any], after: str):
    """The midpoint rank for an after-anchor, computed from the pre-edit board."""
    anchors = {card["id"]: card for card in column["cards"]}
    if after not in anchors:
        raise OpError(f"--after card '{after}' is not in column '{column['id']}'")
    anchor_rank = _rank(anchors[after])
    if anchor_rank is None:
        raise OpError(
            f"--after needs '{after}' to carry an `order:` rank; ranks are "
            "the explicit-ordering escape hatch — set one first or omit "
            "--after to use computed ordering"
        )
    ranked = sorted(
        rank
        for card in column["cards"]
        if (rank := _rank(card)) is not None and rank > anchor_rank
    )
    new_rank = (anchor_rank + ranked[0]) / 2 if ranked else anchor_rank + 100
    return int(new_rank) if float(new_rank).is_integer() else new_rank


def _rank(card: dict[str, Any]) -> float | None:
    try:
        return float(card["order"]) if "order" in card else None
    except (TypeError, ValueError):
        return None


def move_card(
    board_dir: Path,
    card_id: str,
    status: str,
    *,
    expect_status: str | None = None,
    after: str | None = None,
    actor: str = "",
    commit: bool = True,
    project_dir: Optional[Path] = None,
) -> OpResult:
    """Move a card to another column — a one-line ``status:`` edit."""
    target = _project_dir(board_dir, project_dir)
    board = _load_board(board_dir, target)
    columns = {column["id"]: column for column in board["columns"]}
    if status not in columns:
        raise OpError(f"unknown status '{status}' (columns: {', '.join(columns)})")
    column, card = _find_card(board, card_id)
    old_status = card["status"] if "status" in card else column["id"]
    if expect_status is not None and old_status != expect_status:
        raise ExpectationError(
            f"'{card_id}' is in '{old_status}', not '{expect_status}' — "
            "the board moved; reload and retry"
        )

    notes: list[str] = []
    destination = columns[status]
    limit = destination.get("limit")
    occupancy = len(destination["cards"])
    if limit is not None and occupancy >= limit and old_status != status:
        notes.append(
            f"'{destination['title']}' is at its WIP limit ({occupancy}/{limit})"
        )
    terminal = board["columns"][-1]["id"]
    open_blockers = [
        blocker
        for blocker in card.get("blocked_by") or []
        if _find_card(board, blocker)[0]["id"] != terminal
    ]
    if open_blockers and status != old_status:
        notes.append(f"'{card_id}' is blocked by {', '.join(open_blockers)}")

    # All anchor validation and rank math happens BEFORE any write, so a
    # bad anchor can never leave a half-applied move behind.
    new_rank = compute_after_rank(destination, after) if after else None
    path = _card_path(board_dir, card_id)
    original = path.read_text(encoding="utf-8")
    try:
        set_scalar(path, "status", status)
        if new_rank is not None:
            set_scalar(path, "order", new_rank)
    except ValueError:
        path.write_text(original, encoding="utf-8")
        raise
    revalidate_or_rollback(board_dir, target, path, original)
    message = f"board: {card_id} {old_status} -> {status}"
    committed = commit_paths(target, [path], message) if commit else False
    return OpResult(
        card_id=card_id,
        path=path,
        committed=committed,
        message=message,
        warnings=notes,
        old_status=old_status,
    )


def update_card(
    board_dir: Path,
    card_id: str,
    field_name: str,
    value: str,
    *,
    actor: str = "",
    commit: bool = True,
    project_dir: Optional[Path] = None,
) -> OpResult:
    """Set one allowlisted frontmatter field (assignee takes a comma list)."""
    target = _project_dir(board_dir, project_dir)
    if field_name not in UPDATE_FIELDS:
        raise OpError(
            f"cannot set '{field_name}' (allowed: {', '.join(UPDATE_FIELDS)}; "
            "status changes go through `move`, tags and blocked_by are "
            "one-line hand edits)"
        )
    if field_name == "size":
        value = value.strip().upper()
        if value not in ("S", "M", "L", "XL"):
            raise OpError(
                f"size must be one of the scale — use S, M, L, or XL (got {value!r})"
            )
    _find_card(_load_board(board_dir, target), card_id)
    path = _card_path(board_dir, card_id)
    original = path.read_text(encoding="utf-8")
    try:
        if field_name == "assignee" and "," in value:
            names = [name.strip() for name in value.split(",") if name.strip()]
            set_list(path, field_name, names)
        else:
            set_scalar(path, field_name, value)
    except ValueError:
        path.write_text(original, encoding="utf-8")
        raise
    revalidate_or_rollback(board_dir, target, path, original)
    message = f"board: update {card_id}"
    committed = commit_paths(target, [path], message) if commit else False
    return OpResult(card_id=card_id, path=path, committed=committed, message=message)


def comment_card(
    board_dir: Path,
    card_id: str,
    text: str,
    *,
    actor: str = "",
    commit: bool = True,
    project_dir: Optional[Path] = None,
) -> OpResult:
    """Append one comment to the card's thread (always at the end)."""
    target = _project_dir(board_dir, project_dir)
    _find_card(_load_board(board_dir, target), card_id)
    path = _card_path(board_dir, card_id)
    entry = format_comment_entry(
        date=_today(), actor=actor or resolve_actor(), text=text
    )
    append_comment(path, entry)
    message = f"board: comment on {card_id}"
    committed = commit_paths(target, [path], message) if commit else False
    return OpResult(
        card_id=card_id,
        path=path,
        committed=committed,
        message=message,
        detail=entry,
    )


def add_card(
    board_dir: Path,
    title: str,
    *,
    status: str = "",
    description: str = "",
    tags: list[str] | None = None,
    priority: str = "",
    parent: str = "",
    assignee: list[str] | None = None,
    actor: str = "",
    commit: bool = True,
    project_dir: Optional[Path] = None,
) -> OpResult:
    """Create a new card file; an empty status lands in the first column."""
    target = _project_dir(board_dir, project_dir)
    board = _load_board(board_dir, target)
    column_ids = [column["id"] for column in board["columns"]]
    status = status or column_ids[0]
    if status not in column_ids:
        raise OpError(f"unknown status '{status}' (columns: {', '.join(column_ids)})")
    if parent and not any(
        card["id"] == parent for column in board["columns"] for card in column["cards"]
    ):
        raise OpError(f"parent '{parent}' is not a card id on this board")

    card_id = _slugify(title)
    if not card_id:
        raise OpError(f"cannot derive a card id from title {title!r}")
    path = board_dir / "cards" / f"{card_id}.md"
    if path.exists():
        raise OpError(f"card '{card_id}' already exists ({path})")

    if priority and priority not in ("low", "normal", "high"):
        raise OpError("priority must be low, normal, or high")
    meta: dict[str, Any] = {"title": title, "status": status}
    if priority:
        meta["priority"] = priority
    if parent:
        meta["parent"] = parent
    if tags:
        meta["tags"] = list(tags)
    names = [name for name in (assignee or []) if name.strip()]
    if names:
        meta["assignee"] = names if len(names) > 1 else names[0]
    meta["created"] = _today()
    # A brand-new file has no hand formatting to preserve, so this is the
    # one safe place for a YAML dumper: it quotes titles and tags that
    # would otherwise inject keys or break parsing.
    #
    # `default_flow_style` must be False, not None. None lets PyYAML
    # collapse a flat mapping onto one line — `{title: ..., status: ...}`
    # — and every command here edits by line surgery, so a card written in
    # flow style could never be moved again.
    front = yaml.dump(
        meta,
        Dumper=_CardDumper,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=79,
    )
    body = f"\n{description.strip()}\n" if description.strip() else ""
    path.write_text(f"---\n{front}---\n{body}", encoding="utf-8")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            load_board_dir(board_dir, project_dir=target)
    except ValueError as exc:
        # A rejected card must never survive to brick the next build.
        path.unlink(missing_ok=True)
        raise OpError(f"{exc} — the new card was removed") from exc
    message = f"board: add {card_id}"
    committed = commit_paths(target, [path], message) if commit else False
    return OpResult(
        card_id=card_id,
        path=path,
        committed=committed,
        message=message,
        detail=status,
    )
