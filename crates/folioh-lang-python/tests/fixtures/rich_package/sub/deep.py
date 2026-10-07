"""A subpackage module: scope rules and a tuple ``__all__``."""

from typing import TYPE_CHECKING

__all__ = ("visible", "Shape")

if TYPE_CHECKING:
    def hidden() -> None: ...

try:
    def hidden_too() -> None: ...
except ImportError:
    pass


def visible(items: list[str] | None = None) -> dict[str, int]:
    """Only direct children of the module body are published.

    Args:
        items: Names to count.

    Returns:
        A mapping from name to count.
    """
    def inner() -> None: ...
    return {}


def filtered_out() -> None:
    """Not in ``__all__``."""


class Shape:
    """A shape."""

    if True:
        def hidden_method(self) -> None: ...

    sides = 3
    kind: str = "triangle"

    def perimeter(self, unit: str = "cm") -> str:
        """The perimeter.

        Args:
            unit: The unit. Defaults to cm.
        """
        return unit
