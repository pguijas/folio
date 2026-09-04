"""First-party landing plugin: owns the ``landing:`` docs.yaml key.

The landing feature ships as a **default plugin** (see ``DEFAULT_PLUGINS`` in
``folio/plugin.py``): it is loaded for every build and stays inert until a
``landing:`` key appears in docs.yaml. ``configure()`` is the single owner of
the key — core ``folio/config.py`` no longer parses it — and populates the
``Config.landing_*`` fields consumed downstream by the core template injector.

Ownership seam (why there is no ``register_extensions``/``emit_assets`` here):
the rendered page intentionally stays in the bundled template
(``template/app/page.tsx`` + ``template/components/landing*.tsx``), specialized
by marker replacement in ``TemplateConfigInjector._inject_landing_page`` during
``SiteBuilder.prepare()``. That injection runs *before* any plugin emission
hook, and the disabled-path fallback (docs index at ``/``) plus the coupled
``__DOCS_INDEX_CANONICAL_PATH__`` / ``__INCLUDE_DOCS_INDEX__`` markers must be
written even when this plugin is inert, so no public hook can take that
emission over without breaking the documented template contract
(``docs/guide/theming/custom-templates.md``). The plugin therefore owns the
config surface; the injector reads the fields this hook sets at
``load_config`` time, which happens before ``prepare()``.
"""

from __future__ import annotations

import warnings
from typing import Any

from folio.plugin import hookimpl

FOLIO_PLUGIN_API = "1.1"

HERO_VARIANTS = ("docs-map", "source-pipeline", "build-pipeline", "heartbeat")
DEFAULT_HERO_VARIANT = "docs-map"
DEFAULT_CTA_PRIMARY_TEXT = "Get Started"
DEFAULT_CTA_PRIMARY_LINK = "/docs"


@hookimpl
def config_keys() -> list[str]:
    return ["landing"]


# tryfirst: parse the `landing:` key before any project plugin's configure()
# runs, so project plugins can override the parsed landing_* fields. This
# mirrors the pre-plugin ordering, where core parsed the key before the
# configure dispatch; without it, folio's isolated dispatch (LIFO — last
# registered runs first, and default plugins register before `plugins:`
# entries) would run this hook last and silently clobber project overrides.
@hookimpl(tryfirst=True)
def configure(config: Any, raw_config: dict[str, Any]) -> None:
    # The plugin is loaded for every build as a first-party default; the
    # `landing:` config key is what activates it. Without the key the site
    # root keeps serving the docs index: landing_enabled is forced off here
    # because the Config dataclass default (True) exists for direct
    # construction (tests/embedders), not for the docs.yaml contract.
    if "landing" not in raw_config:
        config.landing_enabled = False
        return

    landing = normalize_landing(raw_config.get("landing"))
    config.landing_enabled = landing["enabled"]
    config.landing_hero_variant = landing["hero"]["variant"]
    config.landing_hero_tagline = landing["hero"]["tagline"]
    config.landing_hero_headline = landing["hero"]["headline"]
    config.landing_hero_description = landing["hero"]["description"]
    config.landing_notice_text = landing["hero"]["notice"]["text"]
    config.landing_notice_link = landing["hero"]["notice"]["link"]
    config.landing_cta_primary_text = landing["cta"]["primary"]["text"]
    config.landing_cta_primary_link = landing["cta"]["primary"]["link"]
    config.landing_cta_secondary_text = landing["cta"]["secondary"]["text"]
    config.landing_cta_secondary_link = landing["cta"]["secondary"]["link"]
    config.landing_install_commands = landing["install"]
    config.landing_features = landing["features"]
    config.landing_sections = landing["sections"]
    config.landing_comparison = landing["comparison"]
    config.extra["landing"] = landing


def landing_enabled(raw_landing: Any) -> bool:
    """`landing: <bool>` shorthand, `enabled:` subkey (default true), else true."""
    if isinstance(raw_landing, bool):
        return raw_landing
    if isinstance(raw_landing, dict):
        return raw_landing.get("enabled", True) is not False
    return True


def landing_hero_variant(raw_variant: Any) -> str:
    if raw_variant in HERO_VARIANTS:
        return str(raw_variant)
    return DEFAULT_HERO_VARIANT


def landing_sections(raw_sections: Any) -> list[dict[str, Any]]:
    if not isinstance(raw_sections, list):
        return []
    sections: list[dict[str, Any]] = []
    for raw_section in raw_sections:
        if not isinstance(raw_section, dict):
            continue
        section = dict(raw_section)
        # Every section type may carry an optional stage label.
        _normalize_stage(section)
        normalizer = _SECTION_NORMALIZERS.get(section.get("type"))
        if normalizer is not None:
            section = normalizer(section)
        sections.append(section)
    return sections


def _string(value: Any, default: str = "") -> str:
    return value if isinstance(value, str) else default


def _safe_section_href(raw_value: Any, path: str, default: str) -> str:
    """A config href validated by the shared scheme policy, or ``default``.

    Landing sections are presentational, so unlike kanban card links an
    unsafe or malformed href degrades to the default with a warning instead
    of failing the build.
    """
    if not isinstance(raw_value, str) or not raw_value:
        return default
    from folio.config import _theme_href

    try:
        _theme_href(raw_value, path)
    except ValueError as error:
        warnings.warn(f"{error} — using {default!r} instead", UserWarning, stacklevel=2)
        return default
    return raw_value


def _normalize_heading_fields(section: dict[str, Any]) -> None:
    """Coerce shared heading fields in place: non-strings degrade to absent."""
    for key in ("eyebrow", "title", "description"):
        if key in section and not isinstance(section[key], str):
            del section[key]


def _normalize_stage(section: dict[str, Any]) -> None:
    """Coerce the optional ``stage`` label in place: blank degrades to absent.

    Any section (and the hero) may carry a short stage label ("The
    mechanism"); the template numbers staged blocks at render time, so the
    plugin only guarantees a non-empty stripped string. Non-string or
    whitespace-only values delete the key, and the section renders without a
    stage rail exactly as before.
    """
    if "stage" not in section:
        return
    raw_stage = section["stage"]
    stage = raw_stage.strip() if isinstance(raw_stage, str) else ""
    if stage:
        section["stage"] = stage
    else:
        del section["stage"]


def _normalize_hero_notice(raw_notice: Any) -> dict[str, str]:
    """The hero's announcement chip: one plain message plus a link.

    Kept deliberately simple — no lists, no rotation, no derived data. A
    notice without usable text degrades to absent; the link passes the same
    href scheme policy as every other configured link.
    """
    empty = {"text": "", "link": ""}
    if not isinstance(raw_notice, dict):
        return empty
    text = _string(raw_notice.get("text"))
    if not text:
        return empty
    link = _safe_section_href(
        raw_notice.get("link"),
        f"landing: hero notice '{text}' link",
        "",
    )
    return {"text": text, "link": link}


def _normalize_boards_section(section: dict[str, Any]) -> dict[str, Any]:
    _normalize_heading_fields(section)
    section["roadmap_url"] = _safe_section_href(
        section.get("roadmap_url"), "landing: boards section roadmap_url", "/roadmap"
    )
    section["kanban_url"] = _safe_section_href(
        section.get("kanban_url"), "landing: boards section kanban_url", "/kanban"
    )
    section["roadmap_link_text"] = _string(
        section.get("roadmap_link_text"), "Full roadmap"
    )
    section["kanban_link_text"] = _string(
        section.get("kanban_link_text"), "Open the board"
    )
    # kanban_embed: false keeps the kanban off the landing itself and shows
    # the kanban link under the roadmap miniature instead.
    section["kanban_embed"] = section.get("kanban_embed") is not False
    # narrow: true caps a single embedded board at a centered max-w-3xl.
    section["narrow"] = section.get("narrow") is True
    return section


def _normalize_mechanism_section(section: dict[str, Any]) -> dict[str, Any]:
    _normalize_heading_fields(section)
    section["code_title"] = _string(section.get("code_title"), "docs.yaml")
    section["code"] = _string(section.get("code"))
    section["caption"] = _string(section.get("caption"))
    section["board_label"] = _string(section.get("board_label"), "● LIVE")
    section["board_url"] = _safe_section_href(
        section.get("board_url"), "landing: mechanism section board_url", "/kanban"
    )

    raw_pills = section.get("pills")
    pills = (
        [pill for pill in raw_pills if isinstance(pill, str) and pill]
        if isinstance(raw_pills, list)
        else []
    )
    section["pills"] = pills or ["git push", "folio build", "deploy"]

    raw_commits = section.get("commits")
    commits: list[dict[str, str]] = []
    if isinstance(raw_commits, list):
        for raw_commit in raw_commits:
            if not isinstance(raw_commit, dict):
                continue
            commit = {
                "hash": _string(raw_commit.get("hash")),
                "message": _string(raw_commit.get("message")),
            }
            if commit["hash"] or commit["message"]:
                commits.append(commit)
    section["commits"] = commits
    return section


def _normalize_statement_section(section: dict[str, Any]) -> dict[str, Any]:
    _normalize_heading_fields(section)
    section["text"] = _string(section.get("text"))
    section["accent"] = _string(section.get("accent"))
    # size: "md" steps the headline down for a mid-page thesis block; the
    # default ("lg") keeps the full-scale closer. Anything else degrades to
    # the default.
    if "size" in section and section["size"] not in ("md", "lg"):
        del section["size"]

    raw_actions = section.get("actions")
    actions: list[dict[str, Any]] = []
    if isinstance(raw_actions, list):
        for raw_action in raw_actions:
            if not isinstance(raw_action, dict):
                continue
            title = _string(raw_action.get("title"))
            href = _safe_section_href(
                raw_action.get("href"),
                f"landing: statement section action '{title}' href",
                "",
            )
            if not title or not href:
                continue
            action: dict[str, Any] = {"title": title, "href": href}
            if isinstance(raw_action.get("primary"), bool):
                action["primary"] = raw_action["primary"]
            elif not actions:
                # The first kept action defaults to the primary style.
                action["primary"] = True
            actions.append(action)
    section["actions"] = actions
    return section


# Node marks the bundled template can draw on a funnel input/output card.
# An unknown value is dropped and the card renders without a mark.
_FUNNEL_ICONS = (
    "config",
    "python",
    "markdown",
    "language",
    "folder",
    "search",
    "agents",
    "hash",
    "board",
)


def _labeled_entries(
    raw_entries: Any, key: str, *, allow_icon: bool = False
) -> list[dict[str, str]]:
    """Clean a list of ``{key, detail}`` mappings; entries without ``key`` drop."""
    entries: list[dict[str, str]] = []
    if isinstance(raw_entries, list):
        for raw_entry in raw_entries:
            if not isinstance(raw_entry, dict):
                continue
            name = _string(raw_entry.get(key))
            if not name:
                continue
            entry = {key: name, "detail": _string(raw_entry.get("detail"))}
            if allow_icon:
                icon = _string(raw_entry.get("icon"))
                if icon in _FUNNEL_ICONS:
                    entry["icon"] = icon
            entries.append(entry)
    return entries


def _normalize_harness_section(section: dict[str, Any]) -> dict[str, Any]:
    """The two product surfaces plus the meta-harness relationship.

    The bundled template owns useful defaults, so omitted lists stay empty and
    trigger that copy there. Config can replace every label without introducing
    a new vocabulary or implying that Folio controls the harnesses it wraps.
    """
    _normalize_heading_fields(section)
    for key in (
        "thesis",
        "docs_label",
        "docs_detail",
        "agents_label",
        "agents_detail",
    ):
        if key in section and not isinstance(section[key], str):
            del section[key]
    section["harnesses"] = _labeled_entries(section.get("harnesses"), "label")
    section["unifies"] = _labeled_entries(section.get("unifies"), "label")
    return section


def _normalize_funnel_section(section: dict[str, Any]) -> dict[str, Any]:
    _normalize_heading_fields(section)
    section["command"] = _string(section.get("command"), "folio build")
    section["caption"] = _string(section.get("caption"))

    raw_notes = section.get("command_notes")
    if isinstance(raw_notes, list):
        # An explicit list wins, empty included: a plate whose node needs no
        # gloss sets `command_notes: []` and the card renders the flow alone.
        section["command_notes"] = [
            note for note in raw_notes if isinstance(note, str) and note
        ]
    else:
        section["command_notes"] = [
            "reads source · never runs it",
            "one build → every surface",
        ]

    raw_inputs = section.get("inputs")
    inputs: list[dict[str, Any]] = []
    if isinstance(raw_inputs, list):
        for raw_input in raw_inputs:
            if not isinstance(raw_input, dict):
                continue
            label = _string(raw_input.get("label"))
            if not label:
                continue
            item: dict[str, Any] = {
                "label": label,
                "detail": _string(raw_input.get("detail")),
                # Strict coercion: only a boolean true dims the row; truthy
                # strings like "yes" degrade to false.
                "ghost": raw_input.get("ghost") is True,
            }
            chip = _string(raw_input.get("chip"))
            if chip:
                item["chip"] = chip
            icon = _string(raw_input.get("icon"))
            if icon in _FUNNEL_ICONS:
                item["icon"] = icon
            inputs.append(item)
    # Empty stays empty: the template renders its built-in folio defaults
    # when inputs/outputs are missing; the plugin never injects them.
    section["inputs"] = inputs
    section["outputs"] = _labeled_entries(
        section.get("outputs"), "label", allow_icon=True
    )
    # Guarantees render as the plate's apparatus strip; no node marks.
    section["guarantees"] = _labeled_entries(section.get("guarantees"), "title")
    return section


# Vignette kinds the bundled template can draw at the top of a "features"
# bento card. A feature without (or with an unknown) visual renders copy-only.
_FEATURE_VISUALS = ("components", "llms", "receipt", "deploy", "plugins", "theming")


def _normalize_features_section(section: dict[str, Any]) -> dict[str, Any]:
    _normalize_heading_fields(section)
    # variant: "bento" opts into the card grid; anything else degrades to
    # absent, which keeps the legacy rows layout.
    if "variant" in section and section["variant"] != "bento":
        del section["variant"]

    # title_muted: the display header's second beat; non-strings degrade.
    if "title_muted" in section and not isinstance(section["title_muted"], str):
        del section["title_muted"]

    # actions: the bento header renders the first one as a quiet button.
    raw_actions = section.get("actions")
    if raw_actions is not None:
        actions: list[dict[str, Any]] = []
        if isinstance(raw_actions, list):
            for raw_action in raw_actions:
                if not isinstance(raw_action, dict):
                    continue
                title = _string(raw_action.get("title"))
                href = _safe_section_href(
                    raw_action.get("href"),
                    f"landing: features section action '{title}' href",
                    "",
                )
                if title and href:
                    actions.append({"title": title, "href": href})
        section["actions"] = actions

    raw_features = section.get("features")
    if isinstance(raw_features, list):
        features: list[Any] = []
        for raw_feature in raw_features:
            if not isinstance(raw_feature, dict):
                features.append(raw_feature)
                continue
            feature = dict(raw_feature)
            if "visual" in feature and feature["visual"] not in _FEATURE_VISUALS:
                # Unknown vignette kinds drop; the card renders copy-only.
                del feature["visual"]
            features.append(feature)
        section["features"] = features
    return section


# Vignette kinds the bundled template can draw at the top of a "cells" item.
_CELL_VISUALS = ("components", "llms", "export", "plugins")


def _normalize_cells_section(section: dict[str, Any]) -> dict[str, Any]:
    _normalize_heading_fields(section)

    raw_items = section.get("items")
    items: list[dict[str, Any]] = []
    if isinstance(raw_items, list):
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
            title = _string(raw_item.get("title"))
            if not title:
                continue
            item: dict[str, Any] = {
                "title": title,
                "label": _string(raw_item.get("label")),
                "description": _string(raw_item.get("description")),
                "link_text": _string(raw_item.get("link_text")),
            }
            visual = _string(raw_item.get("visual"))
            if visual in _CELL_VISUALS:
                item["visual"] = visual
            href = _safe_section_href(
                raw_item.get("href"),
                f"landing: cells item '{title}' href",
                "",
            )
            if href:
                item["href"] = href
            items.append(item)
    section["items"] = items
    return section


# The bundled matrix components draw three cell states: yes (``True``), no
# (``False``) and partial (``"~"``, the spelling ``CompareMatrix`` already
# uses in docs pages).
_COMPARISON_PARTIAL = "~"

_COMPARISON_REPLACEMENT = (
    "The built-in table is deprecated and will be removed; fill in your own "
    "instead: `comparison: {caption, tools: [...], rows: [{feature, "
    "values: [...], note}]}` "
    "(see https://pguijas.github.io/folio/docs/plugins/landing)"
)


def _warn_builtin_comparison(source: str) -> None:
    warnings.warn(
        f"landing: {source} renders Folio's own table of documentation tools "
        f"on your landing page. {_COMPARISON_REPLACEMENT}",
        UserWarning,
        stacklevel=3,
    )


def _comparison_value(raw_value: Any) -> bool | str:
    """One matrix cell: yes (``True``), no (``False``) or partial (``"~"``).

    An unrecognized value reads as partial rather than as a yes or a no, so a
    malformed cell never invents a claim about a named tool. YAML parses a
    bare ``~`` as null, so ``values: [true, ~]`` arrives here as ``None`` and
    lands on partial, which is what the tilde means in the table anyway.
    """
    if isinstance(raw_value, bool):
        return raw_value
    if isinstance(raw_value, str):
        text = raw_value.strip().lower()
        if text in ("yes", "true"):
            return True
        if text in ("no", "false"):
            return False
    return _COMPARISON_PARTIAL


def _comparison_tools(raw_tools: Any) -> list[str]:
    """The column names; blanks and non-strings drop."""
    if not isinstance(raw_tools, list):
        return []
    return [
        tool.strip() for tool in raw_tools if isinstance(tool, str) and tool.strip()
    ]


def _comparison_rows(raw_rows: Any, tool_count: int) -> list[dict[str, Any]]:
    """Rows carrying exactly one value per tool; anything else drops.

    A row whose value count disagrees with ``tools`` would slide every cell
    under the wrong column, so it is dropped with a warning instead of being
    padded into a claim nobody wrote.
    """
    if not isinstance(raw_rows, list):
        return []
    rows: list[dict[str, Any]] = []
    for raw_row in raw_rows:
        if not isinstance(raw_row, dict):
            continue
        feature = _string(raw_row.get("feature")).strip()
        raw_values = raw_row.get("values")
        if not feature or not isinstance(raw_values, list):
            continue
        if len(raw_values) != tool_count:
            warnings.warn(
                f"landing: comparison row '{feature}' has {len(raw_values)} "
                f"values for {tool_count} tools; dropping the row",
                UserWarning,
                stacklevel=4,
            )
            continue
        row: dict[str, Any] = {
            "feature": feature,
            "values": [_comparison_value(value) for value in raw_values],
        }
        note = _string(raw_row.get("note")).strip()
        if note:
            row["note"] = note
        rows.append(row)
    return rows


def _comparison_table(raw_table: Any) -> dict[str, Any]:
    """``{caption, tools, rows}`` from a config mapping, or ``{}`` if unusable."""
    table = _mapping(raw_table)
    tools = _comparison_tools(table.get("tools"))
    rows = _comparison_rows(table.get("rows"), len(tools)) if tools else []
    if not tools or not rows:
        return {}
    return {
        "caption": _string(table.get("caption")).strip(),
        "tools": tools,
        "rows": rows,
    }


def landing_comparison(raw_comparison: Any) -> bool | dict[str, Any]:
    """Normalize ``landing.comparison``: the project's own table, or the bool.

    Returns ``{caption, tools, rows}`` for a configured table, ``True`` for
    the deprecated bool that renders Folio's bundled matrix, and ``False``
    when the key is off, absent, or leaves nothing to render.
    """
    if raw_comparison is True:
        _warn_builtin_comparison("`comparison: true`")
        return True
    if not isinstance(raw_comparison, dict):
        return False
    table = _comparison_table(raw_comparison)
    if not table:
        warnings.warn(
            "landing: comparison needs a `tools:` list and at least one "
            "usable `rows:` entry; ignoring it",
            UserWarning,
            stacklevel=3,
        )
        return False
    return table


def _normalize_comparison_section(section: dict[str, Any]) -> dict[str, Any]:
    """A comparison section carrying the project's own table.

    The table sits on the section under the same keys as ``landing.comparison``
    (``caption``, ``tools``, ``rows``). A section without a usable table keeps
    rendering the deprecated built-in matrix, so the keys are dropped rather
    than handed to the template as an empty shell.
    """
    _normalize_heading_fields(section)
    table = _comparison_table(section)
    if not table:
        for key in ("caption", "tools", "rows"):
            section.pop(key, None)
        _warn_builtin_comparison("a `comparison` section without `tools:` and `rows:`")
        return section
    section.update(table)
    return section


_SECTION_NORMALIZERS = {
    "boards": _normalize_boards_section,
    "cells": _normalize_cells_section,
    "comparison": _normalize_comparison_section,
    "features": _normalize_features_section,
    "funnel": _normalize_funnel_section,
    "harness": _normalize_harness_section,
    "mechanism": _normalize_mechanism_section,
    "statement": _normalize_statement_section,
}


def _mapping(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def normalize_landing(raw_landing: Any) -> dict[str, Any]:
    """Normalize a raw ``landing:`` section into its canonical mapping.

    Accepts the bool shorthand (``landing: false``) and tolerates non-mapping
    values anywhere in the tree (they degrade to defaults). Defaults mirror
    the pre-plugin core parser exactly: hero variant ``docs-map``, primary CTA
    ``Get Started``/``/docs``, empty secondary CTA, empty install/feature/
    section lists, and the comparison section off unless the project fills in
    its own table.
    """
    landing = _mapping(raw_landing)
    hero = _mapping(landing.get("hero"))
    cta = _mapping(landing.get("cta"))
    primary = _mapping(cta.get("primary"))
    secondary = _mapping(cta.get("secondary"))
    normalized_hero: dict[str, Any] = {
        "variant": landing_hero_variant(hero.get("variant")),
        "tagline": hero.get("tagline", ""),
        "headline": hero.get("headline", ""),
        "description": hero.get("description", ""),
        "notice": _normalize_hero_notice(hero.get("notice")),
    }
    # The hero participates in stage numbering like any section.
    if "stage" in hero:
        normalized_hero["stage"] = hero["stage"]
        _normalize_stage(normalized_hero)
    return {
        "enabled": landing_enabled(raw_landing),
        "hero": normalized_hero,
        "cta": {
            "primary": {
                "text": primary.get("text", DEFAULT_CTA_PRIMARY_TEXT),
                "link": primary.get("link", DEFAULT_CTA_PRIMARY_LINK),
            },
            "secondary": {
                "text": secondary.get("text", ""),
                "link": secondary.get("link", ""),
            },
        },
        "install": landing.get("install", []),
        "features": landing.get("features", []),
        "sections": landing_sections(landing.get("sections")),
        # Opt-in: the comparison section names other tools, so a project
        # supplies its own table (`{caption, tools, rows}`). The bool that
        # renders Folio's bundled matrix still works and warns.
        "comparison": landing_comparison(landing.get("comparison")),
    }
