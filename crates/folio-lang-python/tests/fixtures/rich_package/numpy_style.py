"""NumPy-style docstrings.

Notes
-----
The module note is a NumPy section too.
"""


def add(a, b, copy: bool = True):
    """Add two numbers.

    Parameters
    ----------
    a : int
        First operand.
    b : int, optional
        Second operand, by default 0.
    copy : bool, default True
        Whether to copy.

    Returns
    -------
    int
        The sum.

    Raises
    ------
    ValueError
        If the operands do not add.

    Warns
    -----
    UserWarning
        When the result overflows.

    Examples
    --------
    >>> add(2, 3)
    5
    Prose after the snippet.

    See Also
    --------
    Matrix : the class below.

    Notes
    -----
    Addition is commutative.
    """
    return a + b


class Matrix:
    """A matrix.

    Attributes
    ----------
    rows : int
        Row count.
    """

    rows: int = 0

    def walk(self, step=1):
        """Walk the cells.

        Parameters
        ----------
        step : int
            Stride.

        Other Parameters
        ----------------
        extra : str
            Ignored.

        Yields
        ------
        cell : Cell
            Each cell in turn.
        """
        yield from ()

    def scale(self, factor):
        """Scale in place.

        Parameters
        ----------
        factor
            The factor, default=2.
        """
