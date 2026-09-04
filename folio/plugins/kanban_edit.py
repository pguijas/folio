"""Line-surgery editor for cardfile board cards.

Card files are hand-authored Markdown; a writer that round-trips them
through ``yaml.safe_dump`` would destroy comments, key order, and quoting.
Every mutation here is therefore a targeted line edit — replace one scalar
line, insert one artifact line, append one trail line — followed by a
re-parse verification. When a file is structurally exotic (block scalars,
anchors, a key the surgery cannot find as a plain ``key: value`` line) the
edit refuses loudly and tells the actor to edit the file by hand; a wrong
write never survives, because verification failure restores the original
bytes before raising.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from folio.plugins.kanban_board import parse_artifact

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
# A value needs quoting when plain-YAML would misread it: an indicator as
# first char, ": "/" #" sequences, surrounding whitespace, or control chars.
# Bare URLs and paths (incl. #L12 anchors) stay plain for readable diffs.
_UNSAFE_PLAIN_RE = re.compile(
    r"(\A[\s\-?:,\[\]{}#&*!|>'\"%@`])|(: )|( #)|(\s\Z)|[\n\t]"
)
_YAML_SPECIAL_WORDS = {"true", "false", "null", "yes", "no", "on", "off", "~"}
# As tolerant as the loader, which lowercases headings: a writer that
# matched fewer spellings than the reader appended a DUPLICATE section,
# and the parse (last section wins) silently dropped the original thread.
_TRAIL_HEADING_RE = re.compile(r"^##\s+trail\s*$", re.IGNORECASE | re.MULTILINE)
_COMMENTS_HEADING_RE = re.compile(
    r"^##\s+comments\s*$", re.IGNORECASE | re.MULTILINE
)
_SECTION_HEADING_RE = re.compile(r"^##\s+", re.MULTILINE)


class CardEditError(ValueError):
    """A surgical edit could not be applied safely."""


def format_trail_entry(*, date: str, actor: str, note: str, ref: str = "") -> str:
    """The canonical trail line: strict writer, tolerant reader."""
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise CardEditError(f"trail date must be YYYY-MM-DD, got {date!r}")
    actor = actor.strip().lstrip("@")
    if not actor or re.search(r"\s", actor):
        raise CardEditError(f"trail actor must be a single token, got {actor!r}")
    note = " ".join(note.split())
    if not note:
        raise CardEditError("trail note must not be empty")
    ref = ref.strip()
    if ref and re.search(r"[()\n]", ref):
        raise CardEditError(
            f"trail ref must not contain parentheses or newlines (got {ref!r}) "
            "— use a bare sha or 'PR #n'"
        )
    ref_part = f" ({ref})" if ref else ""
    return f"- {date} @{actor}{ref_part}: {note}"


def format_comment_entry(*, date: str, actor: str, text: str) -> str:
    """The canonical comment line — the trail's grammar minus the ref.

    A comment argues; it does not point at a commit. Same strict-writer
    contract: the tolerant reader upstream renders anything, so the only
    place to keep the section parseable is here.
    """
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
        raise CardEditError(f"comment date must be YYYY-MM-DD, got {date!r}")
    actor = actor.strip().lstrip("@")
    if not actor or re.search(r"\s", actor):
        raise CardEditError(f"comment author must be a single token, got {actor!r}")
    text = " ".join(text.split())
    if not text:
        raise CardEditError("comment text must not be empty")
    return f"- {date} @{actor}: {text}"


def set_scalar(path: Path, key: str, value: Any) -> None:
    """Replace (or add) one plain ``key: value`` frontmatter line."""
    original = path.read_text(encoding="utf-8")
    front, body, front_span = _split(original, path)

    rendered = _render_scalar(value)
    line_re = re.compile(rf"^{re.escape(key)}:(.*)$", re.MULTILINE)
    match = line_re.search(front)
    if match:
        existing = match.group(1)
        if existing.rstrip().endswith(("|", ">")) or _continues(front, match.end()):
            raise CardEditError(
                f"'{path.name}': `{key}:` is not a plain single-line scalar — "
                "edit the file manually"
            )
        new_front = front[: match.start()] + f"{key}: {rendered}" + front[match.end() :]
    else:
        new_front = front.rstrip("\n") + f"\n{key}: {rendered}"

    _write_verified(
        path,
        original,
        _assemble(original, new_front, front_span),
        verify=lambda meta: str(meta.get(key)) == str(value),
        what=f"set {key}: {rendered}",
    )


def set_list(path: Path, key: str, values: list[str]) -> None:
    """Replace (or add) one inline ``key: [a, b]`` frontmatter line."""
    original = path.read_text(encoding="utf-8")
    front, _body, front_span = _split(original, path)

    rendered = "[" + ", ".join(_render_scalar(v) for v in values) + "]"
    line_re = re.compile(rf"^{re.escape(key)}:(.*)$", re.MULTILINE)
    match = line_re.search(front)
    if match:
        existing = match.group(1)
        if existing.rstrip().endswith(("|", ">")) or _continues(front, match.end()):
            raise CardEditError(
                f"'{path.name}': `{key}:` is not a plain single-line scalar — "
                "edit the file manually"
            )
        new_front = front[: match.start()] + f"{key}: {rendered}" + front[match.end() :]
    else:
        new_front = front.rstrip("\n") + f"\n{key}: {rendered}"

    _write_verified(
        path,
        original,
        _assemble(original, new_front, front_span),
        verify=lambda meta: meta.get(key) == values,
        what=f"set {key}: {rendered}",
    )


def _append_section_line(
    path: Path,
    entry: str,
    *,
    heading_re: re.Pattern[str],
    heading: str,
    what: str,
    before_re: re.Pattern[str] | None = None,
) -> None:
    """Append one bullet at the END of a ``## <heading>`` section.

    Appending at the tail keeps concurrent-session conflicts predictable:
    two appends collide at the same place and the resolution is
    mechanically "keep both lines". A missing section is created where
    ``before_re`` points (comments read before the trail, so they are
    created before it), or at the file's end.
    """
    if not entry.startswith("- "):
        raise CardEditError(f"a {what} must be a '- ' bullet line")
    original = path.read_text(encoding="utf-8")
    _split(original, path)  # validates frontmatter exists

    match = heading_re.search(original)
    if match is None:
        anchor = before_re.search(original) if before_re else None
        if anchor:
            new_text = (
                original[: anchor.start()].rstrip("\n")
                + f"\n\n## {heading}\n{entry}\n\n"
                + original[anchor.start() :]
            )
        else:
            new_text = original.rstrip("\n") + f"\n\n## {heading}\n{entry}\n"
    else:
        next_section = _SECTION_HEADING_RE.search(original, match.end())
        insert_at = next_section.start() if next_section else len(original)
        section = original[match.end() : insert_at].rstrip("\n")
        new_section = f"{section}\n{entry}\n" if section.strip() else f"\n{entry}\n"
        if next_section:
            new_section += "\n"
        new_text = original[: match.end()] + new_section + original[insert_at:]

    _write_verified(
        path,
        original,
        new_text,
        verify=lambda meta: True,
        what=f"append {what}",
    )


def append_trail(path: Path, entry: str) -> None:
    """Append one trail line at the END of the ``## Trail`` section."""
    _append_section_line(
        path,
        entry,
        heading_re=_TRAIL_HEADING_RE,
        heading="Trail",
        what="trail entry",
    )


def append_comment(path: Path, entry: str) -> None:
    """Append one comment line at the END of the ``## Comments`` section."""
    _append_section_line(
        path,
        entry,
        heading_re=_COMMENTS_HEADING_RE,
        heading="Comments",
        what="comment",
        # The documented order: the conversation reads before the record.
        before_re=_TRAIL_HEADING_RE,
    )


def insert_artifact(path: Path, kind: str, target: Any, label: str = "") -> None:
    """Insert one artifact item at the end of the ``artifacts:`` block."""
    raw: dict[str, Any] = {kind: target}
    if label:
        raw["label"] = label
    parse_artifact(raw, card_id=path.stem)  # validates kind/target shape

    original = path.read_text(encoding="utf-8")
    front, _body, front_span = _split(original, path)

    rendered_target = str(target) if isinstance(target, int) else _render_scalar(target)
    item_lines = [f"  - {kind}: {rendered_target}"]
    if label:
        item_lines.append(f"    label: {_render_scalar(label)}")

    lines = front.split("\n")
    key_index = next(
        (i for i, line in enumerate(lines) if re.match(r"artifacts:\s*$", line)),
        None,
    )
    if key_index is None:
        if any(re.match(r"artifacts:", line) for line in lines):
            raise CardEditError(
                f"'{path.name}': `artifacts:` uses flow style — edit the file manually"
            )
        new_lines = [*lines, "artifacts:", *item_lines]
    else:
        end = key_index + 1
        while end < len(lines) and (
            not lines[end].strip()
            or lines[end].startswith((" ", "\t"))
            or lines[end].lstrip().startswith("#")  # comments stay in-block
        ):
            end += 1
        while end > key_index + 1 and not lines[end - 1].strip():
            end -= 1  # keep the new item inside the block, before blank lines
        new_lines = [*lines[:end], *item_lines, *lines[end:]]

    expected = _artifact_count(front) + 1
    _write_verified(
        path,
        original,
        _assemble(original, "\n".join(new_lines), front_span),
        verify=lambda meta: (
            isinstance(meta.get("artifacts"), list)
            and len(meta["artifacts"]) == expected
            and parse_artifact(meta["artifacts"][-1], card_id=path.stem)[0] == kind
        ),
        what=f"attach {kind}: {target}",
    )


def _artifact_count(front: str) -> int:
    meta = yaml.safe_load(front)
    artifacts = meta.get("artifacts") if isinstance(meta, dict) else None
    return len(artifacts) if isinstance(artifacts, list) else 0


def _split(text: str, path: Path) -> tuple[str, str, tuple[int, int]]:
    match = _FRONTMATTER_RE.match(text)
    if match is None:
        raise CardEditError(f"'{path.name}' has no frontmatter block — not a card file")
    try:
        meta = yaml.safe_load(match.group(1))
    except yaml.YAMLError as exc:
        raise CardEditError(
            f"'{path.name}' frontmatter is not valid YAML: {exc}"
        ) from exc
    if not isinstance(meta, dict):
        raise CardEditError(f"'{path.name}' frontmatter must be a mapping")
    return match.group(1), text[match.end() :], (match.start(1), match.end(1))


def _assemble(original: str, new_front: str, span: tuple[int, int]) -> str:
    start, end = span
    return original[:start] + new_front + original[end:]


def _continues(front: str, line_end: int) -> bool:
    """True when the next frontmatter line continues this scalar (multiline)."""
    rest = front[line_end:].lstrip("\n")
    return bool(rest) and rest.startswith((" ", "\t"))


def _render_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    needs_quotes = (
        not text
        or _UNSAFE_PLAIN_RE.search(text)
        or text.lower() in _YAML_SPECIAL_WORDS
        or _parses_as_number(text)
    )
    if not needs_quotes:
        return text
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _parses_as_number(text: str) -> bool:
    """A string that YAML would read as a number must be quoted to stay one."""
    try:
        float(text)
    except ValueError:
        return False
    return True


def _write_verified(
    path: Path,
    original: str,
    new_text: str,
    *,
    verify,
    what: str,
) -> None:
    path.write_text(new_text, encoding="utf-8")
    try:
        written = path.read_text(encoding="utf-8")
        match = _FRONTMATTER_RE.match(written)
        meta = yaml.safe_load(match.group(1)) if match else None
        ok = isinstance(meta, dict) and verify(meta)
    except Exception:
        ok = False
    if not ok:
        path.write_text(original, encoding="utf-8")
        raise CardEditError(
            f"'{path.name}': could not {what} safely (the file is structurally "
            "unusual); the file was left untouched — edit it manually"
        )
