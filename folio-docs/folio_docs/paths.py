"""Shared path-resolution helpers with project containment guards."""

from __future__ import annotations

from pathlib import Path


def resolve_contained_dir(
    raw_path: str | Path,
    project_root: Path,
    output_dir: str | Path,
    label: str,
    must_exist: bool = True,
) -> Path:
    """Resolve ``raw_path`` against the project root with containment guards.

    This is the single implementation of the guard applied to every
    user-configurable directory that Folio reads from or copies into the
    build workspace (``theme.package``, ``template.path``,
    ``template.overlay_path``).

    Contract:

    - A relative ``raw_path`` is resolved against ``project_root``; an
      absolute path is resolved as-is.
    - The resolved path must stay within ``project_root`` (the root itself is
      allowed); otherwise ``ValueError`` with
      ``"{label} must stay within the project directory"``.
    - The resolved path must not be ``<project_root>/.build`` or anything
      inside it; otherwise ``ValueError`` with
      ``"{label} cannot point inside the .build directory"``.
    - The resolved path must not be ``output_dir`` or anything inside it;
      otherwise ``ValueError`` with
      ``"{label} cannot point inside the output directory"``.
    - With ``must_exist=True`` the resolved path must be an existing
      directory; otherwise ``FileNotFoundError`` with
      ``"{label} does not exist: {resolved}"``.

    Returns the fully resolved absolute :class:`~pathlib.Path`.
    """
    root = project_root.resolve()
    path = Path(raw_path)
    if not path.is_absolute():
        path = root / path
    resolved = path.resolve()

    if not resolved.is_relative_to(root):
        raise ValueError(f"{label} must stay within the project directory")

    build_dir = root / ".build"
    if resolved == build_dir or resolved.is_relative_to(build_dir):
        raise ValueError(f"{label} cannot point inside the .build directory")

    output_root = Path(output_dir).resolve()
    if resolved == output_root or resolved.is_relative_to(output_root):
        raise ValueError(f"{label} cannot point inside the output directory")

    if must_exist and not resolved.is_dir():
        raise FileNotFoundError(f"{label} does not exist: {resolved}")

    return resolved
