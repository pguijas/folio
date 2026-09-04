"""Helpers that project the builtin manifest onto the lines the bundled
``template/mdx-components.tsx`` is expected to contain.

These exist to guard against drift between :mod:`folio.builtins` and the
hand-written bundled template. The guard is bidirectional:
:func:`check_template_drift` reports both builtins missing from the template
(manifest ⊆ template) and template component entries missing from the
manifest (template ⊆ manifest), so the template cannot become a second
source of truth in either direction. It is safe to call at build time and
returns human-readable descriptions instead of raising.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from folio.builtins import BUILTIN_COMPONENTS
from folio.extensions import ComponentDefinition
from folio.generator.mdx_contract import strip_import_statements, strip_js_comments

# A shorthand components-mapping entry occupying a whole line (`    Name,`).
# Import statements are stripped before matching so names inside multi-line
# import lists never count as entries.
_SHORTHAND_ENTRY_RE = re.compile(
    r"^[ \t]*([A-Za-z_$][A-Za-z0-9_$]*),[ \t]*$", re.MULTILINE
)


def expected_import_lines(
    components: Iterable[ComponentDefinition],
) -> list[str]:
    """Return one ``import { ... } from "<path>"`` line per source module.

    Components sharing an ``import_path`` (multi-export modules such as
    ``Tabs``/``TabItem``) are grouped into a single import statement, with names
    in manifest order and modules in first-seen order.
    """
    names_by_module: dict[str, list[str]] = {}
    for component in components:
        names_by_module.setdefault(component.import_path, []).append(
            component.imported_name
        )
    return [
        f'import {{ {", ".join(names)} }} from "{import_path}"'
        for import_path, names in names_by_module.items()
    ]


def expected_entry_lines(
    components: Iterable[ComponentDefinition],
) -> list[str]:
    """Return the ``useMDXComponents`` map entry line for each component.

    Includes the 4-space indentation used in the template so the entry is
    unambiguous (a bare ``Tabs,`` also occurs inside ``import { Tabs, TabItem }``).
    """
    return [f"    {component.name}," for component in components]


def template_component_entry_names(template_text: str) -> list[str]:
    """Extract shorthand component entry names from ``mdx-components.tsx``.

    Comments and import statements are ignored; only whole-line shorthand
    mapping entries (``Name,`` at any indentation) count.
    """
    code = strip_import_statements(strip_js_comments(template_text))
    return [match.group(1) for match in _SHORTHAND_ENTRY_RE.finditer(code)]


def check_template_drift(template_text: str) -> list[str]:
    """Compare the builtin manifest and a template's component entries.

    Bidirectional: reports builtins declared in :data:`BUILTIN_COMPONENTS`
    that have no entry in ``template_text``, and component entries present in
    ``template_text`` that the manifest does not declare. Returns
    human-readable drift descriptions; empty when the two agree.
    """
    manifest_names = [component.name for component in BUILTIN_COMPONENTS]
    template_names = template_component_entry_names(template_text)
    manifest_set = set(manifest_names)
    template_set = set(template_names)
    drift = [
        f"builtin component '{name}' is declared in the manifest "
        "(folio/builtins.py) but has no entry in mdx-components.tsx"
        for name in manifest_names
        if name not in template_set
    ]
    drift.extend(
        f"component entry '{name}' in mdx-components.tsx is not declared "
        "in the builtin manifest (folio/builtins.py)"
        for name in template_names
        if name not in manifest_set
    )
    return drift
