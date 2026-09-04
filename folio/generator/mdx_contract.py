from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from folio.builtins import BUILTIN_COMPONENTS
from folio.extensions import ComponentDefinition

FOLIO_MDX_CONTRACT_VERSION = "1.0"

# Path of the published authoring contract, relative to the build workspace's
# `public/` directory (and therefore to the exported site root).
FOLIO_AUTHORING_CONTRACT_PATH = "_folio/contract.json"

# The top-level docs.yaml keys Folio itself accepts. `folio.config` owns the
# set it validates against; this mirror lets the published contract name the
# core keys, and `tests/test_mdx_contract.py` fails when the two drift apart.
CORE_CONFIG_KEYS: frozenset[str] = frozenset(
    {
        "project",
        "source",
        "output",
        "theme",
        "nav",
        "sidebar",
        "llm",
        "plugins",
        "components",
        "i18n",
        "search",
        "versions",
        "deploy",
        "template",
    }
)

# The one instruction the contract carries for its readers. Fields are added
# in later Folio releases, so a reader that rejects unknown fields breaks on
# the next upgrade. Deliberately no promise about the envelope: nothing bumps
# when its shape changes, so telling a reader to pin to the version pair would
# hand it a signal that does not exist. `mdxContractVersion` versions the
# component list only.
AUTHORING_CONTRACT_INSTRUCTIONS = (
    "Ignore fields you do not recognise; later Folio releases add them. "
    "mdxContractVersion versions the components list only."
)

# Matches a whole import statement: `import ... from "module"` (including
# multi-line named-import lists) or a bare `import "module"` side-effect
# import. The import clause itself can never contain a quote, so scanning
# from a line-leading `import` up to the first quoted specifier is exact for
# well-formed files. Run on comment-stripped code.
_IMPORT_STATEMENT_RE = re.compile(
    r"^[ \t]*import\b[^'\"]*?(['\"])[^'\"\n]*\1", re.MULTILINE
)


def strip_js_comments(code: str) -> str:
    """Remove JS/TS line and block comments, leaving string literals intact.

    A small scanner instead of a regex so that ``//`` inside a string or
    template literal (e.g. ``"https://example.com"``) is not treated as the
    start of a line comment.
    """
    out: list[str] = []
    i = 0
    length = len(code)
    while i < length:
        ch = code[i]
        nxt = code[i + 1] if i + 1 < length else ""
        if ch == "/" and nxt == "/":
            end = code.find("\n", i)
            i = length if end == -1 else end
        elif ch == "/" and nxt == "*":
            end = code.find("*/", i + 2)
            i = length if end == -1 else end + 2
        elif ch in "'\"`":
            quote = ch
            out.append(ch)
            i += 1
            while i < length:
                current = code[i]
                out.append(current)
                if current == "\\" and i + 1 < length:
                    out.append(code[i + 1])
                    i += 2
                    continue
                i += 1
                if current == quote:
                    break
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def import_statements(code: str) -> list[str]:
    """Return every import statement found in comment-stripped ``code``."""
    return [match.group(0) for match in _IMPORT_STATEMENT_RE.finditer(code)]


def strip_import_statements(code: str) -> str:
    """Remove import statements from comment-stripped ``code``."""
    return _IMPORT_STATEMENT_RE.sub("", code)


def has_component_entry(code: str, name: str) -> bool:
    """Report whether ``name`` is wired as a components-mapping entry.

    Accepts the object-property forms (``Name,`` / ``Name:`` / ``Name }``, at
    any indentation) and ``as Name`` re-exports. ``code`` must already be
    comment- and import-stripped so a merely imported symbol never counts as
    a mapping entry.
    """
    n = re.escape(name)
    return re.search(rf"\bas\s+{n}\b|\b{n}\s*[:,}}]", code) is not None


def build_contract(
    components: Iterable[ComponentDefinition] | None = None,
) -> list[dict[str, Any]]:
    """Derive the MDX component contract from component definitions.

    Membership is the explicit ``contract`` flag on the definition and the
    contract ``source`` field comes from ``source_label`` (never from
    ``category``, which is pure taxonomy). Passing the components of a live
    registry lets plugin components carrying ``contract=True`` join the
    emitted contract; the default is the builtin manifest, keeping
    :mod:`folio.builtins` the single source of truth for the published
    TypeScript contract.
    """
    if components is None:
        components = BUILTIN_COMPONENTS
    contract: list[dict[str, Any]] = []
    for component in components:
        if not component.contract:
            continue
        contract.append(
            {
                "name": component.name,
                "required": component.required,
                "source": component.source_label,
                "props": dict(component.props),
            }
        )
    return contract


FOLIO_MDX_COMPONENTS: list[dict[str, Any]] = build_contract()


def required_component_names() -> list[str]:
    return [
        str(component["name"])
        for component in FOLIO_MDX_COMPONENTS
        if component.get("required") is True
    ]


def render_mdx_contract_module(
    components: Iterable[ComponentDefinition] | None = None,
) -> str:
    contract = (
        FOLIO_MDX_COMPONENTS if components is None else build_contract(components)
    )
    components_json = json.dumps(contract, indent=2, ensure_ascii=True)
    return (
        f"export const folioMdxContractVersion = "
        f"{json.dumps(FOLIO_MDX_CONTRACT_VERSION)} as const\n\n"
        f"export const folioMdxComponents = {components_json} as const\n\n"
        "export type FolioMdxComponentName = "
        '(typeof folioMdxComponents)[number]["name"]\n'
    )


def build_authoring_contract(
    *,
    folio_version: str,
    generated_at: str,
    components: Iterable[ComponentDefinition] | None = None,
    config_keys: Iterable[str] = (),
    routes: Iterable[str] = (),
) -> dict[str, Any]:
    """Assemble what a page in this project may contain, as one JSON payload.

    Three answers, one envelope: which components MDX pages can use, which
    top-level ``docs.yaml`` keys this project accepts, and which pages the
    build emitted. ``components`` takes the live registry so plugin and config
    components flagged ``contract=True`` are described too; ``None`` falls back
    to the builtin manifest.
    """
    return {
        "folioVersion": folio_version,
        "mdxContractVersion": FOLIO_MDX_CONTRACT_VERSION,
        "generatedAt": generated_at,
        "instructions": AUTHORING_CONTRACT_INSTRUCTIONS,
        "components": build_contract(components),
        "configKeys": sorted(set(config_keys)),
        "routes": sorted(set(routes)),
    }


def render_authoring_contract(
    *,
    folio_version: str,
    generated_at: str,
    components: Iterable[ComponentDefinition] | None = None,
    config_keys: Iterable[str] = (),
    routes: Iterable[str] = (),
) -> str:
    """Serialize :func:`build_authoring_contract` as the published file text."""
    contract = build_authoring_contract(
        folio_version=folio_version,
        generated_at=generated_at,
        components=components,
        config_keys=config_keys,
        routes=routes,
    )
    return json.dumps(contract, indent=2, ensure_ascii=True) + "\n"


def validate_template_mdx_contract(template_dir: str | Path) -> list[str]:
    mdx_components_path = Path(template_dir) / "mdx-components.tsx"
    if not mdx_components_path.exists():
        return required_component_names()

    content = mdx_components_path.read_text(encoding="utf-8")
    # Strip comments (string-literal aware) so a name mentioned only in a
    # comment does not count, and strip import statements so a name that is
    # merely imported — but never exposed as a mapping entry — does not count
    # either. This stays a heuristic: it cannot see components injected via
    # `{...spread}` and does not inspect theme overlays.
    code = strip_import_statements(strip_js_comments(content))
    return [
        name
        for name in required_component_names()
        if not has_component_entry(code, name)
    ]
