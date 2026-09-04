"""Resolve board milestones against each project's own release line."""

from __future__ import annotations

import warnings
from typing import Any


def resolve_roadmap_phases(board: dict[str, Any], *, raw_roadmap: Any) -> None:
    """Attach roadmap phase labels to matching cards and warn on drift."""
    if not isinstance(raw_roadmap, dict):
        return
    phases = raw_roadmap.get("phases")
    if not isinstance(phases, list):
        return

    by_key: dict[tuple[str, str], tuple[str, str]] = {}
    by_version: dict[str, list[tuple[str, str]]] = {}
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        version = (
            str(phase.get("milestone") or phase.get("version", "")).strip().lstrip("vV")
        )
        anchor = str(phase.get("id", "")).strip()
        project = str(phase.get("project", "")).strip()
        if version and anchor:
            found = (anchor, str(phase.get("title", "")).strip())
            by_key[(project, version)] = found
            by_version.setdefault(version, []).append(found)
    if not by_version:
        return

    unclaimed: dict[str, list[str]] = {}
    for column in board.get("columns", []):
        for card in column.get("cards", []):
            milestone = str(card.get("milestone", "")).strip()
            if not milestone:
                continue
            project = str(card.get("project", "")).strip()
            found = by_key.get((project, milestone)) or by_key.get(("", milestone))
            if found is None and not project:
                candidates = by_version.get(milestone, [])
                if len(candidates) == 1:
                    found = candidates[0]
            if found:
                card["phase"], card["phaseTitle"] = found
            else:
                unclaimed.setdefault(milestone, []).append(
                    str(card.get("id", "") or card.get("title", ""))
                )

    for milestone, cards in unclaimed.items():
        warnings.warn(
            f"kanban: milestone '{milestone}' matches no roadmap phase "
            f"(cards: {', '.join(cards)}; known: {', '.join(by_version)})",
            stacklevel=2,
        )
