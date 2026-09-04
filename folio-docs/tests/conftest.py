import os
from pathlib import Path

import pytest

# CLI-output tests assert on plain strings; a developer shell exporting
# FORCE_COLOR (Warp does) or a narrow COLUMNS would leak ANSI codes and
# line wraps into captured output. Pin a neutral terminal for the suite.
os.environ.pop("FORCE_COLOR", None)
os.environ.setdefault("NO_COLOR", "1")
os.environ.setdefault("COLUMNS", "200")


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    src = tmp_path / "mylib"
    src.mkdir()
    (src / "__init__.py").write_text('"""My library."""\n')
    return tmp_path


@pytest.fixture
def sample_python_source() -> str:
    return '''
"""Sample module for testing."""


def greet(name: str, excited: bool = False) -> str:
    """Greet a person by name.

    Args:
        name: The person's name.
        excited: Whether to add an exclamation mark.

    Returns:
        A greeting string.

    Raises:
        ValueError: If name is empty.

    Example:
        >>> greet("World")
        'Hello, World.'
    """
    if not name:
        raise ValueError("name cannot be empty")
    end = "!" if excited else "."
    return f"Hello, {name}{end}"


class Calculator:
    """A simple calculator.

    Args:
        precision: Number of decimal places.

    Example:
        >>> calc = Calculator(precision=2)
        >>> calc.add(1.1, 2.2)
        3.3
    """

    def __init__(self, precision: int = 2) -> None:
        self.precision = precision

    def add(self, a: float, b: float) -> float:
        """Add two numbers.

        Args:
            a: First number.
            b: Second number.

        Returns:
            The sum rounded to precision.
        """
        return round(a + b, self.precision)

    async def add_async(self, a: float, b: float) -> float:
        """Async version of add.

        Args:
            a: First number.
            b: Second number.

        Returns:
            The sum rounded to precision.
        """
        return round(a + b, self.precision)
'''


@pytest.fixture
def sample_docs_yaml() -> str:
    return """
project:
  name: "TestProject"
  version: "1.0.0"
  repo: "https://github.com/test/test"

source:
  python:
    - "src/"
  docs:
    - "docs/"

output: "_site"

theme:
  dark_mode: true

nav:
  - "Introduction"
  - "API Reference"

llm:
  generate_llms_txt: true
  generate_llms_full_txt: true
"""
