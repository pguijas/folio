"""Core module: constants, functions, decorators and a class with everything."""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from logging import Logger, getLogger
from typing import Any, ClassVar, Generic, TypeVar

T = TypeVar("T")

MAX_RETRIES = 3
DEFAULT_TIMEOUT: float = 30.0
A = B = 1
X, Y = 1, 2
_PRIVATE = "hidden"
Mixed = "not a constant"
logger: Logger = getLogger(__name__)
NAMES = ["a", 'b', 0xFF, 1_000, 1e3]
FORWARD: "list[str]" = []


def connect(host: str, port: int = 8080, *, timeout: float | None = None) -> "Connection":
    """Establish a connection to the remote server.

    Opens a TCP connection using the specified host and port. The connection
    will be kept alive until explicitly closed or the timeout is reached.

    Args:
        host: The hostname or IP address to connect to.
        port: The port number. Defaults to 8080.
        timeout: Maximum time in seconds to wait for the connection.

    Returns:
        A Connection object representing the active connection.

    Raises:
        ConnectionError: If the server is unreachable.
        ValueError: If the host string is empty.

    Examples:
        >>> conn = connect("localhost")
        >>> conn.is_alive()
        True

    Notes:
        This function does not support Unix domain sockets.
    """


async def fetch(url, retries=3, *, verify=True):
    """Fetch a resource.

    Args:
        url (str): The URL to fetch.
        retries (int, optional): How many attempts. Defaults to 3.
        verify (bool): Whether to verify certificates.

    Yields:
        bytes: Chunks of the body.
    """
    yield b""


def log(message: str, *args: Any, **kwargs: Any) -> None:
    """Log a message with optional formatting arguments.

    Args:
        message: The log message template.
        *args: Positional arguments for string formatting.
        **kwargs: Additional keyword arguments passed to the logger.
    """


def positional(a, b, /, c=1, d="x" "y", e=(1,), f=lambda: None):
    """Positional-only parameters and assorted defaults."""


@functools.lru_cache(maxsize=None)
def cached(x: int) -> int:
    """A cached function keeps its decorator text."""
    return x


def _private_helper(value: dict[str, list[int]]) -> tuple[int, ...]:
    """Private without ``__all__``: a leading underscore keeps it out."""
    return ()


class Base:
    """A base class."""


@dataclass(frozen=True)
class Widget(Base, Generic[T], metaclass=type):
    """A widget with fields, properties and nested classes.

    Attributes:
        name: The widget name (merged into the class vars).
        size: The size.
    """

    name: str
    size: int = 0
    tags: list[str] = field(default_factory=list)
    _count: ClassVar[int] = 0
    plain = 1
    label_text: "str" = 'a' 'b'

    def __init__(self, name: str, size: int = 0) -> None:
        """Build a widget.

        Args:
            name: The name.
            size: The size.
        """

    @property
    def area(self) -> float:
        """The area.

        Returns:
            float: Width times height.
        """
        return 0.0

    @area.setter
    def area(self, value: float) -> None:
        pass

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Widget":
        """Build from a mapping.

        Args:
            data: The mapping.
        """
        return cls(**data)

    @staticmethod
    def validate(value: object) -> bool:
        """Validate a value."""
        return True

    async def refresh(self, *, force: bool = False) -> None:
        """Refresh asynchronously."""

    @functools.cached_property
    def label(self) -> str:
        """Cached properties are plain methods."""
        return self.name

    class Config:
        """Nested configuration."""

        learning_rate: float = 0.001
        batch_size: int = 32

        class Deep:
            """Deeply nested."""

            level: int = 3
