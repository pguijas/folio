"""A package that exercises every Python construct Folio documents.

The package docstring keeps a longer description, an example and a note.

Examples:
    >>> from rich_package import compute
    >>> compute(2, 3)
    5

Notes:
    Only the names in ``__all__`` are published from this module.
"""

from .core import Widget

__all__ = ["Widget", "VERSION", "compute"]

VERSION = "1.0"
HIDDEN_CONSTANT = 42


def compute(left: int, right: int = 3) -> int:
    """Add two integers.

    Args:
        left: First number.
        right: Second number. Defaults to 3.

    Returns:
        The sum of both numbers.
    """
    return left + right


def _hidden() -> None:
    """Filtered out by ``__all__``."""
