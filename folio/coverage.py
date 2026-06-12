"""Coverage analysis for Python documentation.

Analyzes parsed ModuleIR objects and reports which symbols have docstrings
vs which are undocumented.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from folio.ir import ClassIR, FunctionIR, ModuleIR


@dataclass
class CoverageResult:
    """Coverage statistics for a set of modules."""

    total: int
    documented: int
    undocumented: list[str] = field(default_factory=list)

    @property
    def percentage(self) -> float:
        """Return coverage as a percentage (0-100)."""
        return (self.documented / self.total * 100) if self.total > 0 else 100.0


def _is_private(name: str) -> bool:
    """Return True if the name is private (starts with _) but not __init__."""
    return name.startswith("_") and name != "__init__"


def _has_docstring(docstring_short: str) -> bool:
    """Return True if the short_description is non-empty."""
    return bool(docstring_short and docstring_short.strip())


def _analyze_function(
    func: FunctionIR,
    prefix: str,
    documented: list[str],
    undocumented: list[str],
) -> None:
    """Check a single function/method and classify it."""
    if _is_private(func.name):
        return
    fqn = f"{prefix}.{func.name}"
    if _has_docstring(func.docstring.short_description):
        documented.append(fqn)
    else:
        undocumented.append(fqn)


def _analyze_class(
    cls: ClassIR,
    prefix: str,
    documented: list[str],
    undocumented: list[str],
) -> None:
    """Check a class and all its public methods."""
    if _is_private(cls.name):
        return
    fqn = f"{prefix}.{cls.name}"
    if _has_docstring(cls.docstring.short_description):
        documented.append(fqn)
    else:
        undocumented.append(fqn)

    for method in cls.methods:
        _analyze_function(method, fqn, documented, undocumented)

    for inner in cls.inner_classes:
        _analyze_class(inner, fqn, documented, undocumented)


def analyze_module(module: ModuleIR) -> CoverageResult:
    """Analyze a single module and return coverage statistics."""
    documented: list[str] = []
    undocumented: list[str] = []

    # Module-level docstring
    if _has_docstring(module.docstring.short_description):
        documented.append(module.name)
    else:
        undocumented.append(module.name)

    # Top-level functions
    for func in module.functions:
        _analyze_function(func, module.name, documented, undocumented)

    # Classes
    for cls in module.classes:
        _analyze_class(cls, module.name, documented, undocumented)

    total = len(documented) + len(undocumented)
    return CoverageResult(
        total=total,
        documented=len(documented),
        undocumented=undocumented,
    )


def analyze_modules(modules: list[ModuleIR]) -> dict[str, CoverageResult]:
    """Analyze multiple modules. Returns a dict mapping module name to CoverageResult."""
    return {module.name: analyze_module(module) for module in modules}


def aggregate(results: dict[str, CoverageResult]) -> CoverageResult:
    """Aggregate multiple CoverageResults into a single total."""
    total = sum(r.total for r in results.values())
    documented = sum(r.documented for r in results.values())
    all_undocumented: list[str] = []
    for r in results.values():
        all_undocumented.extend(r.undocumented)
    return CoverageResult(
        total=total,
        documented=documented,
        undocumented=all_undocumented,
    )
