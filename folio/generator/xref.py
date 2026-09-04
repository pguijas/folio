from __future__ import annotations

import re

from folio.ir import ClassIR, ModuleIR

# Python builtins that should never be linked
_BUILTINS = frozenset(
    {
        "str",
        "int",
        "float",
        "bool",
        "bytes",
        "bytearray",
        "list",
        "dict",
        "set",
        "frozenset",
        "tuple",
        "None",
        "type",
        "object",
        "complex",
        "range",
        "memoryview",
        "slice",
        "property",
        "classmethod",
        "staticmethod",
        "super",
        "Exception",
        "BaseException",
        "Any",
        "Callable",
        "Iterator",
        "Generator",
        "Coroutine",
        "Awaitable",
        "AsyncIterator",
        "AsyncGenerator",
        "Iterable",
        "Sequence",
        "Mapping",
        "MutableMapping",
        "MutableSequence",
        "MutableSet",
        "Optional",
        "Union",
        "Type",
        "ClassVar",
        "Final",
        "Literal",
        "Protocol",
        "TypeVar",
        "TypeAlias",
        "Self",
        "Never",
        "NoReturn",
        "Concatenate",
        "ParamSpec",
        "TypeVarTuple",
        "Unpack",
    }
)

# Regex to strip generic wrappers and union types, extracting inner type names
_GENERIC_RE = re.compile(r"^(\w+)\[(.+)\]$")
_UNION_PIPE_RE = re.compile(r"\s*\|\s*")


def build_symbol_index(
    modules: list[ModuleIR],
    docs_route_base: str = "/docs",
) -> dict[str, str]:
    """Build a mapping of fully-qualified symbol names to documentation URLs.

    Returns a dict like:
        {
            "folio.config": "/docs/api-reference/folio/config",
            "folio.config.Config": "/docs/api-reference/folio/config#config",
            "folio.config.load_config": "/docs/api-reference/folio/config#load_config",
        }
    """
    index: dict[str, str] = {}
    docs_route_base = docs_route_base.rstrip("/") or "/docs"

    for mod in modules:
        mod_route = f"{docs_route_base}/api-reference/{mod.name.replace('.', '/')}"
        index[mod.name] = mod_route

        for cls in mod.classes:
            _index_class(index, cls, mod.name, mod_route)

        for func in mod.functions:
            fqn = f"{mod.name}.{func.name}"
            index[fqn] = f"{mod_route}#{func.name.lower()}"

    return index


def _index_class(
    index: dict[str, str],
    cls: ClassIR,
    parent_fqn: str,
    mod_route: str,
) -> None:
    """Index a class and its inner classes recursively."""
    fqn = f"{parent_fqn}.{cls.name}"
    index[fqn] = f"{mod_route}#{cls.name.lower()}"

    for inner in cls.inner_classes:
        _index_class(index, inner, fqn, mod_route)


def _extract_bare_names(type_str: str) -> list[str]:
    """Extract all potential symbol names from a type string.

    Handles generics like ``list[Config]``, unions like ``Config | None``,
    and comma-separated types like ``dict[str, Config]``.
    """
    # Split union types (X | Y)
    parts = _UNION_PIPE_RE.split(type_str)

    names: list[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = _GENERIC_RE.match(part)
        if m:
            # Recurse into the generic's inner types
            inner = m.group(2)
            # Split on commas but respect nested brackets
            inner_parts = _split_respecting_brackets(inner)
            for ip in inner_parts:
                names.extend(_extract_bare_names(ip.strip()))
        else:
            names.append(part)
    return names


def _split_respecting_brackets(s: str) -> list[str]:
    """Split a string on commas, but not inside brackets."""
    parts: list[str] = []
    depth = 0
    current: list[str] = []
    for ch in s:
        if ch in "([":
            depth += 1
            current.append(ch)
        elif ch in ")]":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current))
    return parts


def resolve_type_link(
    type_str: str,
    index: dict[str, str],
    current_module: str,
) -> str | None:
    """Try to resolve a type string to a documentation URL.

    Handles:
    - Simple names: ``Config`` -> look up ``{current_module}.Config``, then all modules
    - Qualified names: ``folio.config.Config`` -> direct lookup
    - Generic types: ``list[Config]`` -> resolve the inner type ``Config``
    - Union types: ``Config | None`` -> resolve ``Config``

    Returns the URL if a single resolvable symbol is found, None otherwise.
    """
    type_str = type_str.strip()
    if not type_str:
        return None

    # Try direct lookup first (fully-qualified name)
    if type_str in index:
        return index[type_str]

    # Extract all bare names from the type expression
    bare_names = _extract_bare_names(type_str)

    # Filter out builtins and empty strings
    candidates = [
        n for n in bare_names if n and n not in _BUILTINS and not n.startswith("_")
    ]

    if len(candidates) != 1:
        # Ambiguous or no candidates -- don't link
        return None

    name = candidates[0]

    # Direct lookup (fully qualified)
    if name in index:
        return index[name]

    # Try current_module.name
    local_fqn = f"{current_module}.{name}"
    if local_fqn in index:
        return index[local_fqn]

    # Try parent package.name (e.g., current_module=folio.config, try folio.name)
    if "." in current_module:
        parent = current_module.rsplit(".", 1)[0]
        parent_fqn = f"{parent}.{name}"
        if parent_fqn in index:
            return index[parent_fqn]

    # Search all entries for a matching suffix
    suffix = f".{name}"
    matches = [url for fqn, url in index.items() if fqn.endswith(suffix)]
    if len(matches) == 1:
        return matches[0]

    return None
