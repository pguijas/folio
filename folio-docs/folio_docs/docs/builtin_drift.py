"""Guard the builtin manifest against the bundled MDX components.

Two guards, because the manifest can drift from the template in two ways.

:func:`check_template_drift` is bidirectional over component *names*: it
reports both builtins missing from ``mdx-components.tsx`` (manifest ⊆
template) and template entries missing from the manifest (template ⊆
manifest), so the template cannot become a second source of truth.

:func:`check_component_prop_drift` does the same for *props*, against the
component sources themselves. Names agreeing is not enough: the manifest and
each ``template/components/*.tsx`` declare props independently, so a manifest
prop the component never reads - or a component prop the manifest never
declares - is published as contract while being fiction.

Both are safe to call at build time and return human-readable descriptions
instead of raising.
"""

from __future__ import annotations

from pathlib import Path
import re
from folio_docs.builtins import BUILTIN_COMPONENTS
from folio_docs.agent_output.contract import strip_import_statements, strip_js_comments

# A shorthand components-mapping entry occupying a whole line (`    Name,`).
# Import statements are stripped before matching so names inside multi-line
# import lists never count as entries.
_SHORTHAND_ENTRY_RE = re.compile(
    r"^[ \t]*([A-Za-z_$][A-Za-z0-9_$]*),[ \t]*$", re.MULTILINE
)


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


# --- prop drift -----------------------------------------------------------

_MEMBER_RE = re.compile(r'^\s*(?:"(?P<quoted>[^"]+)"|(?P<bare>[A-Za-z_$][\w$]*))\s*(?P<optional>\?)?\s*:')
_ALIAS_RE = r"(?:interface\s+{name}\s*|type\s+{name}\s*=\s*)"


def _matching_brace(text: str, start: int) -> int:
    """Index just past the brace group opening at ``text[start]``."""
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char in "{([<":
            depth += 1
        elif char in "})]>":
            depth -= 1
            if depth == 0:
                return index + 1
    return len(text)


def _split_members(body: str) -> list[str]:
    """Split an object type body into members, ignoring nested punctuation."""
    members: list[str] = []
    depth = 0
    current: list[str] = []
    for char in body:
        if char in "{([<":
            depth += 1
        elif char in "})]>":
            depth -= 1
        if depth == 0 and char in ";,\n":
            members.append("".join(current))
            current = []
            continue
        current.append(char)
    members.append("".join(current))
    return [member for member in members if member.strip()]


def _object_fields(body: str) -> dict[str, bool]:
    """Map member name -> required, for one object type body."""
    fields: dict[str, bool] = {}
    for member in _split_members(body):
        match = _MEMBER_RE.match(member)
        if not match:
            continue
        name = match.group("quoted") or match.group("bare")
        fields[name] = match.group("optional") is None
    return fields


def _resolve_alias(source: str, name: str) -> str | None:
    """The object body of a same-file ``interface``/``type`` declaration."""
    match = re.search(_ALIAS_RE.format(name=re.escape(name)) + r"\{", source)
    if not match:
        return None
    open_brace = source.index("{", match.end() - 1)
    return source[open_brace + 1 : _matching_brace(source, open_brace) - 1]


def _props_type_text(source: str, component: str) -> str | None:
    """The type expression annotating ``component``'s destructured props."""
    signature = re.search(
        rf"(?:export\s+)?(?:default\s+)?function\s+{re.escape(component)}\s*\(",
        source,
    )
    if not signature:
        return None
    params_open = signature.end() - 1
    params = source[params_open + 1 : _matching_brace(source, params_open) - 1]
    stripped = params.lstrip()
    if not stripped.startswith("{"):
        return None
    pattern_start = params.index("{")
    after_pattern = params[_matching_brace(params, pattern_start) :].lstrip()
    if not after_pattern.startswith(":"):
        return None
    return after_pattern[1:].strip()


def component_prop_names(source: str, component: str) -> dict[str, bool] | None:
    """Map ``component``'s prop names to whether they are required.

    Handles both an inline destructured annotation and a named ``Props``
    interface or type alias declared in the same file. Returns ``None`` when
    the component is not declared in ``source``.
    """
    code = strip_js_comments(source)
    type_text = _props_type_text(code, component)
    if type_text is None:
        return None
    if type_text.startswith("{"):
        return _object_fields(type_text[1 : _matching_brace(type_text, 0) - 1])
    alias = re.match(r"[A-Za-z_$][\w$]*", type_text)
    if not alias:
        return None
    body = _resolve_alias(code, alias.group(0))
    return _object_fields(body) if body is not None else None


def component_object_field_names(source: str, component: str) -> dict[str, set[str]]:
    """For each object-shaped prop, the field names it carries.

    A prop typed ``Array<{ ... }>`` or ``SomeAlias[]`` declares a shape the
    manifest also spells out, so the two shapes have to agree too - that is
    how ``ApiReferenceIndex`` came to name four fields its component never
    reads.
    """
    code = strip_js_comments(source)
    type_text = _props_type_text(code, component)
    if type_text is None:
        return {}
    if type_text.startswith("{"):
        members = _split_members(type_text[1 : _matching_brace(type_text, 0) - 1])
    else:
        alias = re.match(r"[A-Za-z_$][\w$]*", type_text)
        body = _resolve_alias(code, alias.group(0)) if alias else None
        members = _split_members(body) if body is not None else []

    shapes: dict[str, set[str]] = {}
    for member in members:
        match = _MEMBER_RE.match(member)
        if not match:
            continue
        name = match.group("quoted") or match.group("bare")
        fields = _type_expression_fields(code, member[match.end() :])
        if fields:
            shapes[name] = fields
    return shapes


def _type_expression_fields(source: str, type_text: str) -> set[str]:
    """Field names of the first object shape a type expression resolves to."""
    brace = type_text.find("{")
    if brace != -1:
        body = type_text[brace + 1 : _matching_brace(type_text, brace) - 1]
        return set(_object_fields(body))
    for identifier in re.findall(r"[A-Za-z_$][\w$]*", type_text):
        if identifier in {"Array", "ReadonlyArray", "React", "ReactNode"}:
            continue
        body = _resolve_alias(source, identifier)
        if body is not None:
            return set(_object_fields(body))
    return set()


def _manifest_field_names(type_text: str) -> set[str]:
    brace = type_text.find("{")
    if brace == -1:
        return set()
    body = type_text[brace + 1 : _matching_brace(type_text, brace) - 1]
    return set(_object_fields(body))


def check_component_prop_drift(components_dir: Path) -> list[str]:
    """Compare each builtin's declared props against its component source.

    Reports manifest props the component does not accept, component props the
    manifest omits, optionality mismatches, and object-shape field mismatches.
    Components whose source cannot be found or parsed are skipped rather than
    reported, so a refactor to a new declaration style degrades to no guard
    instead of a false alarm.
    """
    drift: list[str] = []
    for component in BUILTIN_COMPONENTS:
        # Only contract entries publish their props. The rest deliberately
        # declare none, so comparing them would report the design as drift.
        if not component.contract:
            continue
        module = component.import_path.removeprefix("@/components/")
        source_path = components_dir / f"{module}.tsx"
        if not source_path.exists():
            continue
        source = source_path.read_text(encoding="utf-8")
        actual = component_prop_names(source, component.name)
        if actual is None:
            continue

        declared = component.props
        where = f"{component.name} ({source_path.name})"
        for name in sorted(set(declared) - set(actual)):
            drift.append(
                f"{where}: manifest declares prop '{name}', which the "
                "component does not accept"
            )
        for name in sorted(set(actual) - set(declared)):
            drift.append(
                f"{where}: component accepts prop '{name}', which the "
                "manifest does not declare"
            )
        for name in sorted(set(declared) & set(actual)):
            manifest_optional = "undefined" in declared[name]
            if actual[name] is manifest_optional:
                drift.append(
                    f"{where}: prop '{name}' is "
                    f"{'required' if actual[name] else 'optional'} in the "
                    "component but the manifest says otherwise"
                )

        shapes = component_object_field_names(source, component.name)
        for name, fields in shapes.items():
            if name not in declared:
                continue
            manifest_fields = _manifest_field_names(declared[name])
            if not manifest_fields:
                continue
            for field in sorted(manifest_fields - fields):
                drift.append(
                    f"{where}: manifest prop '{name}' declares field "
                    f"'{field}', which the component never reads"
                )
            for field in sorted(fields - manifest_fields):
                drift.append(
                    f"{where}: component prop '{name}' carries field "
                    f"'{field}', which the manifest does not declare"
                )
    return drift
