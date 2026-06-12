from pathlib import Path

from folio.parser.rst_parser import rst_to_mdx


def test_heading_equals():
    rst = "My Title\n========"
    result = rst_to_mdx(rst)
    assert "# My Title" in result


def test_heading_dash():
    rst = "Section\n-------"
    result = rst_to_mdx(rst)
    assert "## Section" in result


def test_heading_tilde():
    rst = "Subsection\n~~~~~~~~~~"
    result = rst_to_mdx(rst)
    assert "### Subsection" in result


def test_heading_caret():
    rst = "Detail\n^^^^^^"
    result = rst_to_mdx(rst)
    assert "#### Detail" in result


def test_code_block():
    rst = ".. code-block:: python\n\n   x = 1\n   y = 2\n"
    result = rst_to_mdx(rst)
    assert "```python" in result
    assert "x = 1" in result
    assert "y = 2" in result


def test_note():
    rst = ".. note::\n\n   This is a note.\n"
    result = rst_to_mdx(rst)
    assert '<Callout type="info">' in result
    assert "This is a note." in result
    assert "</Callout>" in result


def test_warning():
    rst = ".. warning::\n\n   This is a warning.\n"
    result = rst_to_mdx(rst)
    assert '<Callout type="warning">' in result
    assert "This is a warning." in result
    assert "</Callout>" in result


def test_rst_directive_body_dedent_is_shared():
    source = (
        Path(__file__).parents[1] / "folio" / "parser" / "rst_parser.py"
    ).read_text()

    assert "def _dedent_directive_body" in source
    assert source.count("_dedent_directive_body(body)") >= 3
    assert source.count('body.split("\\n")') == 1


def test_image():
    rst = ".. image:: images/logo.png"
    result = rst_to_mdx(rst)
    assert "![images/logo.png](images/logo.png)" in result


def test_inline_code():
    rst = "Use ``my_function()`` to call it."
    result = rst_to_mdx(rst)
    assert "`my_function()`" in result
    assert "``" not in result


def test_rst_role_class():
    rst = "See :class:`Node` for details."
    result = rst_to_mdx(rst)
    assert "`Node`" in result
    assert ":class:" not in result


def test_rst_role_func():
    rst = "Call :func:`run` now."
    result = rst_to_mdx(rst)
    assert "`run`" in result
    assert ":func:" not in result
