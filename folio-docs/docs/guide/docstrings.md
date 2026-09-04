---
title: Writing Docstrings
description: Write Google-style and NumPy-style Python docstrings that Folio can turn into clear API reference pages.
---

# Writing Docstrings

*How to write docstrings that produce clear, complete API documentation.*

folio supports **Google-style** and **NumPy-style** docstrings. By default, Folio
auto-detects the style for each docstring. You can force a parser with
`source.python.docstring_style` in `docs.yaml` (see
[Configuration](./configuration#sourcepython)).

## Google-style format

Google-style parsing is powered by the `docstring_parser` library with
`Style.GOOGLE`. Set `source.python.docstring_style` to `"google"` when you want to
force this parser for every docstring:

```yaml
source:
  python:
    docstring_style: "google"
```

A basic Google-style docstring looks like this:

```python
def connect(host: str, port: int = 8080, timeout: float = 30.0) -> Connection:
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
```

## NumPy-style format

To use NumPy-style docstrings, set `source.python.docstring_style` to `"numpy"` in your `docs.yaml`:

```yaml
source:
  python:
    docstring_style: "numpy"
```

A NumPy-style docstring uses section headers with underlines instead of trailing colons:

```python
def connect(host: str, port: int = 8080) -> Connection:
    """Establish a connection to the remote server.

    Parameters
    ----------
    host : str
        The hostname or IP address.
    port : int, optional
        The port number, by default 8080.

    Returns
    -------
    Connection
        The active connection object.

    Raises
    ------
    ConnectionError
        If the server is unreachable.
    """
```

The default `source.python.docstring_style` value is `"auto"`, which detects the
style on a per-docstring basis. This is useful for projects that mix both
conventions or are migrating from one style to the other.

## Docstring sections

folio recognizes the following sections in a docstring. Each section must use the
exact heading shown below, followed by a colon (for Google-style) or an underline
(for NumPy-style).

### Args

Document function parameters under the `Args:` section. Each parameter is listed on its
own line with an indented description:

```python
def train(data: Dataset, epochs: int = 10, lr: float = 0.001) -> Model:
    """Train a model on the given dataset.

    Args:
        data: The training dataset.
        epochs: Number of training epochs.
        lr: Learning rate for the optimizer.
    """
```

### Returns

Describe the return value under `Returns:`:

```python
def load(path: str) -> dict:
    """Load configuration from a YAML file.

    Returns:
        A dictionary containing the parsed configuration.
    """
```

### Raises

List exceptions the function may raise under `Raises:`:

```python
def parse(text: str) -> AST:
    """Parse source code into an AST.

    Raises:
        SyntaxError: If the source code is invalid.
        FileNotFoundError: If the source file does not exist.
    """
```

### Examples

Provide usage examples under `Examples:`. These are rendered as code blocks in the
generated docs:

```python
def add(a: int, b: int) -> int:
    """Add two numbers.

    Examples:
        >>> add(2, 3)
        5
        >>> add(-1, 1)
        0
    """
```

### Notes

Add extra context under `Notes:`. This section is useful for implementation details,
caveats, or related information:

```python
def encrypt(data: bytes, key: bytes) -> bytes:
    """Encrypt data using AES-256-GCM.

    Notes:
        The nonce is generated randomly and prepended to the ciphertext.
        This function is not suitable for encrypting data larger than 2 GiB.
    """
```

## Type annotations

folio extracts type information from two places, in order of priority:

1. **Function signatures** (preferred) — type annotations on parameters and return types
2. **Docstring type fields** — the `(type)` syntax in Google-style docstrings

If a parameter has a type annotation in the function signature, that takes precedence.
If there is no signature annotation, folio falls back to the type specified in the
docstring.

```python
# Type from signature (preferred)
def greet(name: str) -> str:
    """Greet a user.

    Args:
        name: The user's name.
    """

# Type from docstring (fallback)
def greet(name):
    """Greet a user.

    Args:
        name (str): The user's name.

    Returns:
        str: A greeting message.
    """
```

Both styles produce the same output. When both are present, the signature annotation wins.

## Decorators and method kinds

folio detects decorators on functions and methods and renders them differently
based on their kind.

### @property

Properties are rendered with a "property" badge. The getter docstring is used as the
description. Parameters (like `self`) are automatically excluded:

```python
class User:
    @property
    def full_name(self) -> str:
        """The user's full name, computed from first and last name."""
        return f"{self.first} {self.last}"
```

### @staticmethod

Static methods are marked with a "staticmethod" badge. Since they don't receive `self`
or `cls`, all parameters are documented:

```python
class MathUtils:
    @staticmethod
    def clamp(value: float, low: float, high: float) -> float:
        """Clamp a value to a range.

        Args:
            value: The value to clamp.
            low: Minimum bound.
            high: Maximum bound.
        """
```

### @classmethod

Class methods are marked with a "classmethod" badge. The `cls` parameter is
automatically excluded from the documentation, just like `self`:

```python
class Config:
    @classmethod
    def from_file(cls, path: str) -> "Config":
        """Load configuration from a file.

        Args:
            path: Path to the configuration file.
        """
```

### Custom decorators

All decorators are recorded and displayed in the generated documentation. Custom
decorators appear as-is:

```python
class EventHandler:
    @retry(max_attempts=3)
    def handle(self, event: Event) -> None:
        """Handle an incoming event with automatic retry."""
```

## *args and **kwargs

Variable positional and keyword arguments are fully supported. They appear in the
documentation with their `*` or `**` prefix implied by their argument kind:

```python
def log(message: str, *args: Any, **kwargs: Any) -> None:
    """Log a message with optional formatting arguments.

    Args:
        message: The log message template.
        *args: Positional arguments for string formatting.
        **kwargs: Additional keyword arguments passed to the logger.
    """
```

The parser tracks argument kinds internally: `var_positional` for `*args` and
`var_keyword` for `**kwargs`. Keyword-only arguments (those after `*` in the
signature) are tracked as `keyword_only`.

## Controlling what gets documented with \_\_all\_\_

By default, folio documents **every** public class, function, and constant in a
module. You can restrict what appears in the documentation by defining `__all__`:

```python
__all__ = ["PublicClass", "public_function"]

class PublicClass:
    """This will be documented."""

class _InternalHelper:
    """This is private by convention but would be documented without __all__."""

def public_function():
    """This will be documented."""

def helper():
    """This will NOT be documented because it's not in __all__."""
```

When `__all__` is defined, only the names listed in it are included in the generated
documentation. When `__all__` is not defined, all top-level definitions are documented
(including those without a leading underscore).

**`__all__` must be a simple list or tuple of string literals.** folio parses it
statically from the AST, so dynamic constructions like `__all__ = get_exports()` are not
supported.

## Nested classes

folio fully supports nested (inner) classes. They are parsed recursively and
appear as sub-sections within their parent class documentation:

```python
class Model:
    """A machine learning model.

    The Model class supports nested configuration via inner classes.
    """

    class Config:
        """Model configuration.

        Args are defined as class variables with type annotations.
        """
        learning_rate: float = 0.001
        batch_size: int = 32

    class Callbacks:
        """Lifecycle callbacks for training."""

        def on_epoch_end(self, epoch: int, metrics: dict) -> None:
            """Called at the end of each training epoch.

            Args:
                epoch: The epoch number that just completed.
                metrics: Dictionary of metric names to values.
            """
```

Inner classes have their own methods, class variables, and can even contain further
nested classes.

## Module-level constants

folio documents module-level constants in two ways:

**With type annotations** — any top-level annotated assignment is captured:

```python
DEFAULT_TIMEOUT: float = 30.0
MAX_RETRIES: int = 3
API_BASE_URL: str = "https://api.example.com"
```

**Without type annotations** — only UPPER_CASE names (without a leading underscore) are
captured:

```python
VERSION = "1.0.0"          # documented (UPPER_CASE)
DEFAULT_PORT = 8080        # documented (UPPER_CASE)
_internal_cache = {}       # NOT documented (leading underscore)
some_config = "value"      # NOT documented (not UPPER_CASE)
```

The constant's name, type (if annotated), and assigned value are all shown in the
generated documentation.

## Class variables

Annotated assignments inside a class body are documented as class variables:

```python
class Server:
    """An HTTP server.

    Attributes are documented from annotated class-level assignments.
    """
    host: str = "localhost"
    port: int = 8080
    max_connections: int = 100
```

These appear in a dedicated "Attributes" section in the class documentation, showing
the variable name, type, and default value.

## Async functions

Async functions and methods are fully supported. They are rendered with an `async`
badge to distinguish them from synchronous functions:

```python
async def fetch(url: str, timeout: float = 10.0) -> Response:
    """Fetch a resource from the given URL.

    Args:
        url: The URL to fetch.
        timeout: Maximum time to wait in seconds.

    Returns:
        The HTTP response.

    Raises:
        TimeoutError: If the request exceeds the timeout.
    """
```

## Tips for writing good docstrings

**Start with a one-line summary.** The first line of your docstring becomes the short
description shown in module overviews and search results. Keep it concise and
action-oriented (e.g., "Connect to the database" not "This function connects to the
database").

**Separate the summary from the body.** Leave a blank line between the summary and the
longer description. The parser treats the first line as `short_description` and
everything after the blank line as `long_description`.

**Document all public parameters.** Every parameter that appears in the function
signature should have a corresponding entry in the `Args:` (Google) or `Parameters`
(NumPy) section. Missing descriptions will render as empty in the docs.

**Use type annotations in signatures.** Prefer `def foo(x: int)` over documenting types
in the docstring. Signature annotations are more reliable and are checked by type
checkers like mypy.

**Keep examples runnable.** Examples in the `Examples:` section should be valid Python
that a reader could copy-paste. Use `>>>` prefix for interactive-style examples.

**Document exceptions explicitly.** If your function raises exceptions, list them in the
`Raises:` section. This helps users write proper error handling code.

## Complete example

Here is a well-documented class that demonstrates all the features described in this
guide:

```python
"""Connection management for the RPC framework.

This module provides connection pooling and lifecycle management
for RPC clients.
"""

__all__ = ["ConnectionPool", "DEFAULT_POOL_SIZE"]

DEFAULT_POOL_SIZE: int = 10

class ConnectionPool:
    """A thread-safe pool of reusable connections.

    The pool maintains a set of open connections and distributes them
    to callers on demand. Connections are returned to the pool when
    released.

    Examples:
        >>> pool = ConnectionPool("localhost", max_size=5)
        >>> async with pool.acquire() as conn:
        ...     await conn.execute("SELECT 1")

    Notes:
        The pool does not currently support connection health checks.
    """

    max_size: int = DEFAULT_POOL_SIZE
    timeout: float = 30.0

    class Stats:
        """Pool usage statistics."""
        active: int = 0
        idle: int = 0

    def __init__(self, host: str, port: int = 5432, max_size: int = 10) -> None:
        """Initialize the connection pool.

        Args:
            host: Database hostname.
            port: Database port.
            max_size: Maximum number of connections in the pool.
        """

    async def acquire(self, timeout: float | None = None) -> Connection:
        """Acquire a connection from the pool.

        Args:
            timeout: Maximum time to wait for a connection.
                If None, uses the pool's default timeout.

        Returns:
            An open database connection.

        Raises:
            PoolExhaustedError: If no connection is available within the timeout.
        """

    @property
    def size(self) -> int:
        """The current number of connections in the pool."""

    @classmethod
    def from_url(cls, url: str) -> "ConnectionPool":
        """Create a pool from a database URL.

        Args:
            url: A connection string like ``postgresql://host:port/db``.
        """

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check whether a connection string is valid.

        Args:
            url: The connection string to validate.
        """
```
