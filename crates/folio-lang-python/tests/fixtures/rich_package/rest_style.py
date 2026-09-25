"""ReST fields, epydoc fields, a malformed docstring and docstring-only returns.

:note: A module-level rest note.
"""


def read(path, encoding="utf-8"):
    """Read a file.

    :param path: Location to read.
    :type path: str
    :param str encoding: The encoding, defaults to 'utf-8'.
    :returns: The file contents.
    :rtype: str
    :raises IOError: when the file cannot be read.
    :note: Reads the whole file into memory.
    """
    return path


def epydoc_fields(x):
    """Epydoc markers decide ``auto``.

    @param x: the x
    @type x: int
    @return: the result
    @rtype: str
    @raise ValueError: when x is bad
    @note: an epydoc note
    """


def broken_google(x):
    """Summary line.

    More prose.

    Args:
        x no colon here
    """


def docstring_only_returns():
    """Returns without a type or annotation.

    Returns:
        the thing
    """


def returns_then_yields():
    """Only the first returns-like section counts.

    Returns:
        int: first
    Yields:
        str: ignored
    """
    return 1


def empty_docstring():
    """"""


def whitespace_docstring():
    """   """


def not_a_docstring():
    x = 1
    """Not first, not a docstring."""
    return x
