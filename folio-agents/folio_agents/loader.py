"""Cardfile board loader for ``board.source: <dir>/``.

One card, one Markdown file. ``board.yaml`` holds the column set (and only
the column set); every card lives in ``cards/<id>.md`` where the filename
stem is the card's immutable id, frontmatter carries machine state (status,
tags, relations, artifacts) and the Markdown body carries human/agent prose
(description, acceptance criteria, trail). Column membership is the
``status:`` field, so moving a card is a one-line diff and two concurrent
sessions editing different cards can never produce a merge conflict.

Validation contract (mirrors the plugin's fail-fast configure dispatch):
board topology errors — unparseable frontmatter, missing title/status,
unknown status, dangling parent/blocked_by, malformed artifacts, escaping
doc/file artifact targets — raise ``ValueError`` and stop the build loudly.
Prose-grammar problems (a trail bullet that doesn't parse, an unknown
priority, a doc/file target that resolves to no file, a card directory
whose card is gone) degrade with a warning: a typo in a note must never
break a build, a typo in board topology must never silently ship a wrong
board.
"""

from __future__ import annotations

import re
import warnings
from pathlib import Path
from typing import Any

import yaml

from folio_agents.text import safe_href, slugify

BOARD_FILE = "board.yaml"
CARDS_DIR = "cards"

ARTIFACT_KINDS = ("doc", "api", "file", "pr", "url")
PRIORITY_RANK = {"high": 0, "normal": 1, "low": 2}

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_CRITERION_RE = re.compile(r"^- \[( |x|X)\] (.+)$")
_TRAIL_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) @(\S+?)(?: \(([^)]+)\))?: (.+)$")
# The trail's grammar minus the ref: a comment argues, it does not point
# at a commit.
_COMMENT_RE = re.compile(r"^- (\d{4}-\d{2}-\d{2}) @(\S+?): (.+)$")
_ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_board_dir(path: Path) -> bool:
    """True when ``board.source`` points at a cardfile board directory."""
    return path.is_dir()


def load_board_dir(board_dir: Path, *, project_dir: Path) -> dict[str, Any]:
    """Load a cardfile board into ``{"title": ..., "columns": [...]}``.

    Columns come back in board.yaml order with their cards already grouped
    (by ``status:``) and sorted; card dicts are raw-but-validated and carry
    the extended fields that ``kanban._normalize_card`` normalizes into the
    emitted TS contract.
    """
    board_meta = _load_board_meta(board_dir / BOARD_FILE)
    columns = board_meta["columns"]
    column_ids = [column["id"] for column in columns]

    cards = _load_cards(board_dir / CARDS_DIR, column_ids=column_ids)
    _validate_relations(cards)
    _resolve_artifacts(cards, cards_dir=board_dir / CARDS_DIR, project_dir=project_dir)
    _warn_orphan_directories(
        board_dir / CARDS_DIR, card_ids={card["id"] for card in cards}
    )

    by_status: dict[str, list[dict[str, Any]]] = {cid: [] for cid in column_ids}
    for card in cards:
        by_status[card["status"]].append(card)

    for column in columns:
        column_cards = sorted(by_status[column["id"]], key=_sort_key)
        limit = column.get("limit")
        if limit is not None and len(column_cards) > limit:
            warnings.warn(
                f"kanban: column '{column['title']}' holds {len(column_cards)} "
                f"cards, over its WIP limit of {limit}",
                stacklevel=2,
            )
        column["cards"] = column_cards

    return {
        "title": board_meta["title"],
        "columns": columns,
        "icons": board_meta["icons"],
    }


def _load_board_meta(board_file: Path) -> dict[str, Any]:
    if not board_file.is_file():
        raise ValueError(
            f"kanban: cardfile board is missing its column set: '{board_file}' "
            "not found (a board directory must contain board.yaml)"
        )
    try:
        document = yaml.safe_load(board_file.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"kanban: '{board_file}' is not valid YAML: {exc}") from exc
    if not isinstance(document, dict) or not isinstance(document.get("columns"), list):
        raise ValueError(
            f"kanban: '{board_file}' must contain a top-level `columns:` list"
        )

    title = document.get("title")
    title = title.strip() if isinstance(title, str) and title.strip() else ""

    # Optional `icons:` map, tag -> icon. Prose-tier: a malformed map warns
    # and renders nothing, it never breaks the board.
    icons: dict[str, str] = {}
    raw_icons = document.get("icons")
    if raw_icons is not None:
        if not isinstance(raw_icons, dict):
            warnings.warn(
                f"kanban: '{board_file}' `icons:` must be a mapping of "
                "tag to icon; ignoring it",
                stacklevel=2,
            )
        else:
            for key, value in raw_icons.items():
                if isinstance(key, str) and isinstance(value, str) and value.strip():
                    icons[key.strip()] = value.strip()
                else:
                    warnings.warn(
                        f"kanban: '{board_file}' `icons:` entry {key!r} is not "
                        "a tag-to-icon string pair; skipping it",
                        stacklevel=2,
                    )

    columns: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, raw in enumerate(document["columns"]):
        if not isinstance(raw, dict):
            raise ValueError(
                f"kanban: '{board_file}' column #{index + 1} must be a mapping"
            )
        column_title = raw.get("title")
        if not isinstance(column_title, str) or not column_title.strip():
            raise ValueError(
                f"kanban: '{board_file}' column #{index + 1} needs a title"
            )
        column_title = column_title.strip()
        raw_id = raw.get("id")
        column_id = (
            slugify(raw_id)
            if isinstance(raw_id, str) and raw_id.strip()
            else slugify(column_title)
        ) or f"column-{index + 1}"
        if column_id in seen:
            raise ValueError(
                f"kanban: '{board_file}' declares column id '{column_id}' twice"
            )
        seen.add(column_id)

        raw_limit = raw.get("limit")
        limit: int | None = None
        if raw_limit is not None:
            if (
                isinstance(raw_limit, int)
                and not isinstance(raw_limit, bool)
                and raw_limit > 0
            ):
                limit = raw_limit
            else:
                warnings.warn(
                    f"kanban: column '{column_title}': ignoring invalid WIP "
                    f"limit {raw_limit!r} (expected a positive integer)",
                    stacklevel=2,
                )
        columns.append(
            {"id": column_id, "title": column_title, "limit": limit, "cards": []}
        )
    return {"title": title, "columns": columns, "icons": icons}


def _load_cards(cards_dir: Path, *, column_ids: list[str]) -> list[dict[str, Any]]:
    if not cards_dir.is_dir():
        raise ValueError(f"kanban: cardfile board has no '{cards_dir}' directory")
    cards = []
    for path in sorted(cards_dir.glob("*.md")):
        if path.name.startswith(("_", ".")):
            # _TEMPLATE.md and friends are not cards; dotfiles are editor
            # droppings (.#lock symlinks, .goutputstream-*) that must never
            # brick a build.
            continue
        cards.append(_load_card(path, column_ids=column_ids))
    return cards


def _load_card(path: Path, *, column_ids: list[str]) -> dict[str, Any]:
    card_id = path.stem
    if card_id != slugify(card_id):
        raise ValueError(
            f"kanban: card filename '{path.name}' is not a slug — the stem is "
            f"the card id and must look like '{slugify(card_id) or 'my-card'}'"
        )

    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise ValueError(
            f"kanban: card '{path}' has no frontmatter block "
            "(the file must start with '---')"
        )
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise ValueError(
            f"kanban: card '{path}' frontmatter is not valid YAML: {exc}"
        ) from exc
    if not isinstance(meta, dict):
        raise ValueError(f"kanban: card '{path}' frontmatter must be a mapping")

    title = meta.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(f"kanban: card '{path}' needs a `title:`")

    status = meta.get("status")
    if not isinstance(status, str) or not status.strip():
        raise ValueError(f"kanban: card '{path}' needs a `status:`")
    status = status.strip()
    if status not in column_ids:
        raise ValueError(
            f"kanban: card '{path}' has status '{status}' but board.yaml "
            f"defines columns {column_ids} — fix the status or add the column"
        )

    size = meta.get("size")
    if size is not None and (
        not isinstance(size, str) or size.strip().upper() not in ("S", "M", "L", "XL")
    ):
        raise ValueError(
            f"kanban: card '{path}' has size {size!r} — use S, M, L, or XL"
        )

    body = text[match.end() :]
    description, criteria, trail, comments = _parse_body(body, path=path)

    card: dict[str, Any] = {
        "id": card_id,
        "title": title.strip(),
        "status": status,
        "description": description,
        "criteria": criteria,
        "trail": trail,
        "comments": comments,
    }
    for key in (
        "tags",
        "assignee",
        "track",
        "type",
        "priority",
        "order",
        "created",
        "parent",
        "blocked_by",
        "milestone",
        "artifacts",
        "size",
        "source",
    ):
        # A bare `blocked_by:` line is YAML null; treat it as absent so no
        # downstream consumer trips over None where a list is expected.
        if meta.get(key) is not None:
            card[key] = meta[key]
    if meta.get("link") is not None:
        card["link"] = safe_href(meta["link"], f"kanban: card '{card_id}' link")
    # `created: 2026-8-1` is not a YAML date — the implicit resolver wants
    # zero padding — so it arrives as the string "2026-8-1" and is carried
    # through untouched. Everything that orders by date compares text, and
    # text says "2026-8-1" comes after "2026-08-01" and before nothing at
    # all. Both the intra-column sort and the board's `created:<…` filter
    # then answer wrongly about that card, silently. Say so once, here,
    # where the file that caused it can be named.
    created = card.get("created")
    if created is not None and not _ISO_DATE_RE.match(str(created)):
        warnings.warn(
            f"kanban: card '{path.name}': created {str(created)!r} is not a "
            "YYYY-MM-DD date — it will not order or filter by date",
            stacklevel=2,
        )
    return card


def _parse_body(
    body: str, *, path: Path
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    sections: dict[str, str] = {}
    matches = list(_SECTION_RE.finditer(body))
    description = body[: matches[0].start()].strip() if matches else body.strip()
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[match.group(1).strip().lower()] = body[match.end() : end]

    criteria = []
    for line in sections.get("acceptance criteria", "").splitlines():
        line = line.strip()
        if not line:
            continue
        criterion = _CRITERION_RE.match(line)
        if criterion:
            criteria.append(
                {
                    "text": criterion.group(2).strip(),
                    "done": criterion.group(1) in ("x", "X"),
                }
            )

    trail = []
    for line in sections.get("trail", "").splitlines():
        line = line.rstrip()
        if not line.strip():
            continue
        entry = _TRAIL_RE.match(line.strip())
        if entry:
            trail.append(
                {
                    "date": entry.group(1),
                    "actor": entry.group(2),
                    "ref": entry.group(3) or "",
                    "note": entry.group(4).strip(),
                }
            )
        else:
            # Strict writer, tolerant reader: a hand-written bullet that
            # misses the grammar still shows up in the timeline as-is.
            warnings.warn(
                f"kanban: card '{path.name}': trail line does not match "
                f"'- YYYY-MM-DD @actor (ref): note': {line.strip()!r}",
                stacklevel=2,
            )
            trail.append({"date": "", "actor": "", "ref": "", "note": line.strip()})

    comments = []
    for line in sections.get("comments", "").splitlines():
        line = line.strip()
        if not line:
            continue
        comment = _COMMENT_RE.match(line)
        if comment:
            comments.append(
                {
                    "date": comment.group(1),
                    "actor": comment.group(2),
                    "text": comment.group(3).strip(),
                }
            )
        else:
            # Same tolerance as the trail: a bullet that misses the grammar
            # warns and still joins the thread as prose.
            warnings.warn(
                f"kanban: card '{path.name}': comment line does not match "
                f"'- YYYY-MM-DD @actor: text': {line!r}",
                stacklevel=2,
            )
            comments.append({"date": "", "actor": "", "text": line})
    return description, criteria, trail, comments


def _validate_relations(cards: list[dict[str, Any]]) -> None:
    ids = {card["id"] for card in cards}
    for card in cards:
        parent = card.get("parent")
        if parent is not None:
            if not isinstance(parent, str) or parent not in ids:
                raise ValueError(
                    f"kanban: card '{card['id']}' has parent {parent!r} "
                    "which is not a card id on this board"
                )
            if parent == card["id"]:
                raise ValueError(
                    f"kanban: card '{card['id']}' cannot be its own parent"
                )
        blocked_by = card.get("blocked_by")
        if blocked_by is None:
            continue
        if not isinstance(blocked_by, list):
            raise ValueError(
                f"kanban: card '{card['id']}': `blocked_by:` must be a list of card ids"
            )
        for blocker in blocked_by:
            if not isinstance(blocker, str) or blocker not in ids:
                raise ValueError(
                    f"kanban: card '{card['id']}' is blocked_by {blocker!r} "
                    "which is not a card id on this board"
                )
            if blocker == card["id"]:
                raise ValueError(f"kanban: card '{card['id']}' cannot block itself")


def _resolve_artifacts(
    cards: list[dict[str, Any]], *, cards_dir: Path, project_dir: Path
) -> None:
    """Derive each card's artifacts from its directory, then merge the block.

    The directory is the record: one artifact per regular file at its top
    level, name-sorted — ``doc`` for Markdown and MDX, ``file`` for the rest.
    Dotfiles, ``_``-prefixed names, subdirectories, and symlinks stay behind,
    the same lines publishing already draws. The frontmatter block survives
    for what is not a file — ``pr:``, ``url:``, ``api:`` — and for labelling
    a sibling: a ``doc:``/``file:`` entry naming one (bare name, ``./`` form,
    or the full project-relative path) lands its label on the derived entry
    instead of appearing twice.

    Every entry carries ``display``, the target as the author wrote it (the
    bare name for a derived sibling nothing labels), and ``target``, always a
    project-relative path. A ``doc:``/``file:`` target resolves against the
    card's directory first, then the project root — the order a relative
    markdown link already implies. One that resolves to no file warns and
    stays: a stale path in one card's frontmatter is not board topology.
    Only an absolute path or one escaping the project still raises.
    """
    project_root = project_dir.resolve()
    try:
        cards_prefix = cards_dir.resolve().relative_to(project_root).as_posix()
    except ValueError:
        # A board outside the project publishes nothing, so there is nothing
        # to derive; frontmatter targets still resolve from the project root.
        cards_prefix = None
    for card in cards:
        card_id = card["id"]
        raw_artifacts = card.get("artifacts")
        if raw_artifacts is not None and not isinstance(raw_artifacts, list):
            raise ValueError(f"kanban: card '{card_id}': `artifacts:` must be a list")
        derived: list[dict[str, Any]] = []
        by_name: dict[str, dict[str, Any]] = {}
        if cards_prefix is not None:
            derived = _derived_sibling_artifacts(
                cards_dir / card_id, cards_prefix=cards_prefix, card_id=card_id
            )
            by_name = {entry["display"]: entry for entry in derived}
        listed: list[dict[str, Any]] = []
        for raw in raw_artifacts or []:
            kind, target, label = parse_artifact(raw, card_id=card_id)
            if kind == "url":
                # Enforced at load time so `folio board check`, every
                # CLI write path, and optional renderers reject unsafe schemes
                # identically.
                safe_href(target, f"kanban: card '{card_id}' url artifact")
            if kind not in ("doc", "file"):
                listed.append(
                    {"kind": kind, "target": target, "label": label, "display": target}
                )
                continue
            path_part, _, raw_fragment = target.partition("#")
            fragment = f"#{raw_fragment}" if raw_fragment else ""
            if Path(path_part).is_absolute():
                raise ValueError(
                    f"kanban: card '{card_id}': {kind} artifact '{target}' "
                    "escapes the project directory (artifact paths resolve "
                    "against the card's directory, then the project root)"
                )
            sibling = _sibling_name(
                path_part, cards_prefix=cards_prefix, card_id=card_id
            )
            if sibling is not None and sibling in by_name:
                entry = by_name[sibling]
                if label:
                    entry["label"] = label
                entry["display"] = target
                if fragment:
                    entry["target"] += fragment
                continue
            listed.append(
                {
                    "kind": kind,
                    "target": _resolve_file_target(
                        path_part,
                        kind=kind,
                        written=target,
                        fragment=fragment,
                        card_id=card_id,
                        card_dir=cards_dir / card_id
                        if cards_prefix is not None
                        else None,
                        project_dir=project_dir,
                        project_root=project_root,
                    ),
                    "label": label,
                    "display": target,
                }
            )
        merged = derived + listed
        if merged or raw_artifacts is not None:
            card["artifacts"] = merged


def _derived_sibling_artifacts(
    sibling_dir: Path, *, cards_prefix: str, card_id: str
) -> list[dict[str, Any]]:
    """One artifact per visible regular file at the directory's top level."""
    if sibling_dir.is_symlink() or not sibling_dir.is_dir():
        return []
    entries: list[dict[str, Any]] = []
    for path in sorted(sibling_dir.iterdir()):
        if path.name.startswith((".", "_")) or path.is_symlink() or not path.is_file():
            continue
        kind = "doc" if path.suffix.lower() in (".md", ".mdx") else "file"
        entries.append(
            {
                "kind": kind,
                "target": f"{cards_prefix}/{card_id}/{path.name}",
                "label": "",
                "display": path.name,
            }
        )
    return entries


def _sibling_name(
    path_part: str, *, cards_prefix: str | None, card_id: str
) -> str | None:
    """The top-level sibling a written target names, or ``None``.

    Three spellings reach a sibling: the bare name, the ``./`` form a
    markdown link would use, and the legacy full project-relative path
    existing boards carry.
    """
    name = path_part
    if cards_prefix is not None and name.startswith(f"{cards_prefix}/{card_id}/"):
        name = name[len(f"{cards_prefix}/{card_id}/") :]
    elif name.startswith("./"):
        name = name[2:]
    if not name or "/" in name:
        return None
    return name


def _resolve_file_target(
    path_part: str,
    *,
    kind: str,
    written: str,
    fragment: str,
    card_id: str,
    card_dir: Path | None,
    project_dir: Path,
    project_root: Path,
) -> str:
    """A ``doc:``/``file:`` target as a project-relative path, or a warning.

    The card's directory is tried first, then the project root. A target the
    card resolves is recorded at its project-relative address, so everything
    downstream keeps one path grammar; one the project resolves is already
    written in it and stays as written.
    """
    if card_dir is not None:
        candidate = (card_dir / path_part).resolve()
        if candidate.is_file() and candidate.is_relative_to(project_root):
            return candidate.relative_to(project_root).as_posix() + fragment
    resolved = (project_dir / path_part).resolve()
    if not resolved.is_relative_to(project_root):
        raise ValueError(
            f"kanban: card '{card_id}': {kind} artifact '{written}' escapes "
            "the project directory (artifact paths resolve against the "
            "card's directory, then the project root)"
        )
    if not resolved.is_file():
        warnings.warn(
            f"kanban: card '{card_id}': {kind} artifact '{written}' resolves "
            "to no file (tried the card's directory, then the project root); "
            "the tile renders unlinked",
            stacklevel=2,
        )
    return written


def _warn_orphan_directories(cards_dir: Path, *, card_ids: set[str]) -> None:
    """Name every directory whose card is gone — shape B's one drift risk.

    The filename stem names the directory, so a card renamed or deleted
    leaves its directory behind and nothing publishes an unclaimed one. Dot
    and ``_`` prefixes keep their existing meanings — editor scratch and
    "not the board's business" — and stay quiet.
    """
    for path in sorted(cards_dir.iterdir()):
        if not path.is_dir() or path.name.startswith((".", "_")):
            continue
        if path.name not in card_ids:
            warnings.warn(
                f"kanban: card directory '{path}' has no card "
                f"'{path.name}.md' beside it — the filename stem names the "
                "directory, so nothing publishes its contents",
                stacklevel=2,
            )


def parse_artifact(raw: Any, *, card_id: str) -> tuple[str, str, str]:
    """One artifact entry -> ``(kind, target, label)``.

    The committed form is a one-line single-key map — ``- doc: research/x.md``
    — with an optional ``label:`` sibling key.
    """
    if not isinstance(raw, dict):
        raise ValueError(
            f"kanban: card '{card_id}': each artifact must be a mapping like "
            f"'- doc: path' (one of {ARTIFACT_KINDS}), got {raw!r}"
        )
    label = raw.get("label", "")
    label = label.strip() if isinstance(label, str) else ""
    kinds = [key for key in raw if key != "label"]
    if len(kinds) != 1 or kinds[0] not in ARTIFACT_KINDS:
        raise ValueError(
            f"kanban: card '{card_id}': artifact {raw!r} must have exactly "
            f"one kind key out of {ARTIFACT_KINDS} (plus an optional label)"
        )
    kind = kinds[0]
    target = raw[kind]
    if kind == "pr":
        if not isinstance(target, int) or isinstance(target, bool) or target <= 0:
            raise ValueError(
                f"kanban: card '{card_id}': `pr:` artifact must be a PR "
                f"number, got {target!r}"
            )
        return kind, str(target), label
    if not isinstance(target, str) or not target.strip():
        raise ValueError(
            f"kanban: card '{card_id}': `{kind}:` artifact needs a "
            f"non-empty string target, got {target!r}"
        )
    return kind, target.strip(), label


def _sort_key(card: dict[str, Any]) -> tuple:
    """Deterministic intra-column order: rank, then priority, created, id.

    ``order:`` is the rare escape hatch — ranked cards sort first among
    themselves; everything else falls back to computed order so reordering
    never has to touch another card's file.
    """
    order = card.get("order")
    has_rank = 0
    rank = 0.0
    if order is not None:
        try:
            rank = float(order)
        except (TypeError, ValueError):
            warnings.warn(
                f"kanban: card '{card['id']}': ignoring non-numeric order {order!r}",
                stacklevel=2,
            )
            has_rank, rank = 1, 0.0
        else:
            has_rank = 0
    else:
        has_rank = 1

    priority = card.get("priority")
    if isinstance(priority, str) and priority.strip().lower() in PRIORITY_RANK:
        priority_rank = PRIORITY_RANK[priority.strip().lower()]
    else:
        if priority is not None:
            warnings.warn(
                f"kanban: card '{card['id']}': unknown priority {priority!r} "
                "(expected low | normal | high); treating as normal",
                stacklevel=2,
            )
        priority_rank = PRIORITY_RANK["normal"]

    created = card.get("created")
    created_key = (
        str(created)
        if created is not None and _ISO_DATE_RE.match(str(created))
        else "9999-12-31"
    )
    return (has_rank, rank, priority_rank, created_key, card["id"])
