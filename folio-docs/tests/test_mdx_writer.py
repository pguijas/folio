from folio_docs.docs import mdx_writer
from folio_docs.docs.mdx_writer import (
    _escape_mdx,
    _sanitize_for_mdx,
    markdown_to_mdx,
    module_to_mdx,
)
from folio_docs.ir import (
    ArgIR,
    ClassIR,
    DocstringIR,
    FunctionIR,
    ModuleIR,
    ReturnIR,
)
from folio_docs.parser.markdown_parser import MarkdownResult


def _make_function(name="greet", is_async=False):
    return FunctionIR(
        name=name,
        args=[
            ArgIR(
                name="name", type="str", default=None, description="The person's name."
            ),
            ArgIR(
                name="excited",
                type="bool",
                default="False",
                description="Add exclamation.",
            ),
        ],
        returns=ReturnIR(type="str", description="A greeting string."),
        raises=[],
        decorators=[],
        docstring=DocstringIR(short_description="Greet a person by name."),
        is_async=is_async,
        source_file="test.py",
        line_number=1,
    )


def _make_class():
    return ClassIR(
        name="Calculator",
        bases=["BaseCalc"],
        decorators=["dataclass"],
        docstring=DocstringIR(short_description="A simple calculator."),
        methods=[_make_function("add")],
        class_vars=[],
        source_file="test.py",
        line_number=10,
    )


def test_module_to_mdx_with_function():
    module = ModuleIR(
        name="mylib.utils",
        docstring=DocstringIR(short_description="Utility functions."),
        classes=[],
        functions=[_make_function()],
        constants=[],
        source_file="utils.py",
    )
    mdx = module_to_mdx(module)
    assert "title: mylib.utils" in mdx
    assert "ParamTable" in mdx
    assert "greet" in mdx
    assert "def greet(" in mdx


def test_source_links_default_to_main_ref():
    module = ModuleIR(
        name="mylib.utils",
        docstring=DocstringIR(short_description="Utility functions."),
        classes=[],
        functions=[_make_function()],
        constants=[],
        source_file="src/mylib/utils.py",
    )

    mdx = module_to_mdx(module, repo_url="https://github.com/acme/mylib")

    assert 'href="https://github.com/acme/mylib/blob/main/src/mylib/utils.py#L1"' in mdx
    assert 'href="https://github.com/acme/mylib/blob/main/test.py#L1"' in mdx


def test_source_links_use_configured_ref():
    module = ModuleIR(
        name="mylib.utils",
        docstring=DocstringIR(short_description="Utility functions."),
        classes=[],
        functions=[_make_function()],
        constants=[],
        source_file="src/mylib/utils.py",
    )

    mdx = module_to_mdx(
        module,
        repo_url="https://github.com/acme/mylib",
        source_ref="release/2.x",
    )

    assert (
        'href="https://github.com/acme/mylib/blob/release/2.x/src/mylib/utils.py#L1"'
        in mdx
    )
    assert 'href="https://github.com/acme/mylib/blob/release/2.x/test.py#L1"' in mdx
    assert "/blob/main/" not in mdx


def test_module_to_mdx_with_class():
    module = ModuleIR(
        name="mylib.calc",
        docstring=DocstringIR(short_description="Calculator module."),
        classes=[_make_class()],
        functions=[],
        constants=[],
        source_file="calc.py",
    )
    mdx = module_to_mdx(module)
    assert "ClassOverview" in mdx
    assert 'name="Calculator"' in mdx


def test_module_to_mdx_async_function():
    module = ModuleIR(
        name="mylib.async_utils",
        docstring=DocstringIR(short_description="Async utilities."),
        classes=[],
        functions=[_make_function("fetch_data", is_async=True)],
        constants=[],
        source_file="async_utils.py",
    )
    mdx = module_to_mdx(module)
    assert "async def" in mdx


def test_markdown_to_mdx():
    result = MarkdownResult(
        content="# Hello\n\nSome content here.",
        frontmatter={"title": "Hello", "description": "A greeting page."},
        route="hello",
    )
    mdx = markdown_to_mdx(result)
    assert "---" in mdx
    assert "title: Hello" in mdx
    assert "# Hello" in mdx
    assert "Some content here." in mdx


def test_api_reference_index_lists_all_modules():
    modules = [
        ModuleIR(
            name="mylib",
            docstring=DocstringIR(short_description="Core package"),
            classes=[],
            functions=[],
            constants=[],
            source_file="mylib/__init__.py",
        ),
        ModuleIR(
            name="mylib.core",
            docstring=DocstringIR(short_description="Core helpers"),
            classes=[_make_class()],
            functions=[_make_function("normalize")],
            constants=[],
            source_file="mylib/core.py",
        ),
    ]

    mdx = mdx_writer.api_reference_index_to_mdx(modules)

    assert "title: Source Code" in mdx
    assert "Generated source code documentation" in mdx
    assert "<ApiReferenceIndex modules={" in mdx
    assert '"name": "mylib"' in mdx
    assert '"href": "./mylib/"' in mdx
    assert "Core package" in mdx
    assert '"name": "mylib.core"' in mdx
    assert '"href": "./mylib/core/"' in mdx
    assert "Core helpers" in mdx
    assert '"classCount": 1' in mdx
    assert '"functionCount": 1' in mdx


def test_function_with_args_kwargs():
    func = FunctionIR(
        name="process",
        args=[
            ArgIR(
                name="x", type="int", default=None, description="First.", kind="regular"
            ),
            ArgIR(
                name="args",
                type="Any",
                default=None,
                description="Positional.",
                kind="var_positional",
            ),
            ArgIR(
                name="kwargs",
                type="Any",
                default=None,
                description="Keyword.",
                kind="var_keyword",
            ),
        ],
        returns=None,
        raises=[],
        decorators=[],
        docstring=DocstringIR(short_description="Process things."),
        is_async=False,
        source_file="test.py",
        line_number=1,
    )
    module = ModuleIR(
        name="test",
        docstring=DocstringIR(short_description=""),
        classes=[],
        functions=[func],
        constants=[],
        source_file="test.py",
    )
    mdx = module_to_mdx(module)
    assert "def process(x: int, *args: Any, **kwargs: Any)" in mdx
    assert '"name": "*args"' in mdx
    assert '"name": "**kwargs"' in mdx


def test_keyword_only_separator():
    func = FunctionIR(
        name="kw_func",
        args=[
            ArgIR(name="a", type="int", default=None, description="", kind="regular"),
            ArgIR(
                name="b", type="str", default=None, description="", kind="keyword_only"
            ),
        ],
        returns=None,
        raises=[],
        decorators=[],
        docstring=DocstringIR(short_description=""),
        is_async=False,
        source_file="test.py",
        line_number=1,
    )
    module = ModuleIR(
        name="test",
        docstring=DocstringIR(short_description=""),
        classes=[],
        functions=[func],
        constants=[],
        source_file="test.py",
    )
    mdx = module_to_mdx(module)
    assert "def kw_func(a: int, *, b: str)" in mdx


def test_positional_only_separator():
    func = FunctionIR(
        name="pos_func",
        args=[
            ArgIR(
                name="x",
                type="int",
                default=None,
                description="",
                kind="positional_only",
            ),
            ArgIR(name="y", type="str", default=None, description="", kind="regular"),
        ],
        returns=None,
        raises=[],
        decorators=[],
        docstring=DocstringIR(short_description=""),
        is_async=False,
        source_file="test.py",
        line_number=1,
    )
    module = ModuleIR(
        name="test",
        docstring=DocstringIR(short_description=""),
        classes=[],
        functions=[func],
        constants=[],
        source_file="test.py",
    )
    mdx = module_to_mdx(module)
    assert "def pos_func(x: int, /, y: str)" in mdx


def test_property_renders_without_parens():
    func = FunctionIR(
        name="value",
        args=[],
        returns=ReturnIR(type="int", description="The value."),
        raises=[],
        decorators=["property"],
        docstring=DocstringIR(short_description="Get the value."),
        is_async=False,
        source_file="test.py",
        line_number=1,
        kind="property",
    )
    module = ModuleIR(
        name="test",
        docstring=DocstringIR(short_description=""),
        classes=[],
        functions=[func],
        constants=[],
        source_file="test.py",
    )
    mdx = module_to_mdx(module)
    assert "`@property`" in mdx
    assert "value" in mdx
    assert "def value(" not in mdx
    assert "**Type:**" in mdx
    assert "**Returns:**" not in mdx


def test_staticmethod_badge():
    func = FunctionIR(
        name="create",
        args=[],
        returns=None,
        raises=[],
        decorators=["staticmethod"],
        docstring=DocstringIR(short_description="Factory."),
        is_async=False,
        source_file="test.py",
        line_number=1,
        kind="staticmethod",
    )
    module = ModuleIR(
        name="test",
        docstring=DocstringIR(short_description=""),
        classes=[],
        functions=[func],
        constants=[],
        source_file="test.py",
    )
    mdx = module_to_mdx(module)
    assert "`@staticmethod`" in mdx


def test_classmethod_badge():
    func = FunctionIR(
        name="from_dict",
        args=[ArgIR(name="cls", type="", default=None, description="", kind="regular")],
        returns=None,
        raises=[],
        decorators=["classmethod"],
        docstring=DocstringIR(short_description="Create from dict."),
        is_async=False,
        source_file="test.py",
        line_number=1,
        kind="classmethod",
    )
    module = ModuleIR(
        name="test",
        docstring=DocstringIR(short_description=""),
        classes=[],
        functions=[func],
        constants=[],
        source_file="test.py",
    )
    mdx = module_to_mdx(module)
    assert "`@classmethod`" in mdx


def test_inner_classes_rendered():
    inner = ClassIR(
        name="InnerHelper",
        bases=[],
        decorators=[],
        docstring=DocstringIR(short_description="An inner class."),
        methods=[],
        class_vars=[],
        source_file="test.py",
        line_number=20,
    )
    outer = ClassIR(
        name="Outer",
        bases=[],
        decorators=[],
        docstring=DocstringIR(short_description="An outer class."),
        methods=[],
        class_vars=[],
        inner_classes=[inner],
        source_file="test.py",
        line_number=10,
    )
    module = ModuleIR(
        name="test",
        docstring=DocstringIR(short_description=""),
        classes=[outer],
        functions=[],
        constants=[],
        source_file="test.py",
    )
    mdx = module_to_mdx(module)
    assert "Outer" in mdx
    assert "InnerHelper" in mdx


def test_mdx_injection_in_class_name():
    cls = ClassIR(
        name='Foo" onclick="alert(1)',
        bases=[],
        decorators=[],
        docstring=DocstringIR(short_description=""),
        methods=[],
        class_vars=[],
        source_file="test.py",
        line_number=1,
    )
    module = ModuleIR(
        name="test",
        docstring=DocstringIR(short_description=""),
        classes=[cls],
        functions=[],
        constants=[],
        source_file="test.py",
    )
    mdx = module_to_mdx(module)
    assert 'name="Foo" onclick="alert(1)"' not in mdx
    assert "&quot;" in mdx


class TestDocstringInlineCodeSpans:
    """MDX escapes must not leak into inline code spans.

    CommonMark treats a backtick span's content as literal text: it decodes
    neither HTML entities nor backslash escapes there. Escaping inside a span
    therefore renders the escape itself, so readers see `/\\{repo\\}` and
    `&lt;a href&gt;` instead of the code the docstring documented.
    """

    def test_braces_in_inline_code_are_preserved(self):
        assert _escape_mdx("Route is `/{repo}` here.") == "Route is `/{repo}` here."

    def test_angle_brackets_in_inline_code_are_preserved(self):
        assert _escape_mdx("Use `<a href>` tags.") == "Use `<a href>` tags."

    def test_braces_outside_inline_code_are_still_escaped(self):
        assert _escape_mdx("A {brace} here.") == "A \\{brace\\} here."

    def test_angle_brackets_outside_inline_code_are_still_escaped(self):
        assert _escape_mdx("A <Tag> here.") == "A &lt;Tag&gt; here."

    def test_escaping_resumes_after_a_code_span_closes(self):
        assert (
            _escape_mdx("`{kept}` then {escaped}")
            == "`{kept}` then \\{escaped\\}"
        )

    def test_double_backtick_span_is_preserved(self):
        assert _escape_mdx("``a `{b}` c``") == "``a `{b}` c``"

    def test_unterminated_backtick_is_treated_as_literal_text(self):
        assert _escape_mdx("An ` unclosed {brace}") == "An ` unclosed \\{brace\\}"

    def test_fenced_block_inside_a_docstring_is_preserved(self):
        content = 'Example:\n\n```python\nd = {"k": 1}\n```\n\nAfter {brace}.'
        result = _escape_mdx(content)
        assert 'd = {"k": 1}' in result
        assert "After \\{brace\\}." in result


class TestCodeBlockMetaPreservation:
    """Ensure _sanitize_for_mdx preserves code block meta strings like {2,4-6}."""

    def test_line_highlight_meta_preserved(self):
        content = "```python {2,4-6}\nimport os\nimport sys\n```"
        result = _sanitize_for_mdx(content)
        assert "```python {2,4-6}" in result

    def test_line_highlight_single_line(self):
        content = "```python {3}\nline1\nline2\nline3\n```"
        result = _sanitize_for_mdx(content)
        assert "```python {3}" in result

    def test_line_highlight_range(self):
        content = "```python {1-5}\nline1\nline2\nline3\nline4\nline5\n```"
        result = _sanitize_for_mdx(content)
        assert "```python {1-5}" in result

    def test_line_highlight_mixed(self):
        content = "```js {1,3-5,7}\ncode\n```"
        result = _sanitize_for_mdx(content)
        assert "```js {1,3-5,7}" in result

    def test_curly_braces_outside_code_block_still_escaped(self):
        content = "Text with {braces} here.\n\n```python {2}\nimport os\nimport sys\n```\n\nMore {braces}."
        result = _sanitize_for_mdx(content)
        assert "\\{braces\\}" in result
        assert "```python {2}" in result

    def test_curly_braces_inside_code_block_not_escaped(self):
        content = '```python\nmy_dict = {"key": "value"}\n```'
        result = _sanitize_for_mdx(content)
        assert '{"key": "value"}' in result

    def test_three_tick_fence_nested_in_four_ticks_stays_code(self):
        """A nested fence must not flip the tracker back to 'outside code'."""
        content = '````markdown\n```python\nd = {"k": 1}\n```\n````'
        result = _sanitize_for_mdx(content)
        assert 'd = {"k": 1}' in result

    def test_tilde_fence_contents_not_escaped(self):
        content = '~~~python\nd = {"k": 1}\n~~~'
        result = _sanitize_for_mdx(content)
        assert 'd = {"k": 1}' in result

    def test_indented_fence_under_a_list_item_stays_code(self):
        content = '1. Step:\n\n   ```python\n   d = {"k": 1}\n   ```\n'
        result = _sanitize_for_mdx(content)
        assert 'd = {"k": 1}' in result

    def test_braces_in_an_inline_code_span_are_not_escaped(self):
        """Authored Markdown hits the same CommonMark rule as docstrings.

        `docs/guide/configuration.md` documents the `/{repo}` route shape in
        backticks, and the escape rendered literally as `/\\{repo\\}`.
        """
        result = _sanitize_for_mdx("Route is `/{repo}` here.")
        assert result == "Route is `/{repo}` here."

    def test_braces_outside_an_inline_code_span_are_still_escaped(self):
        result = _sanitize_for_mdx("A `{kept}` and a {escaped} one.")
        assert result == "A `{kept}` and a \\{escaped\\} one."

    def test_inline_math_is_still_preserved_alongside_code_spans(self):
        result = _sanitize_for_mdx("Math $x_{i}$ and code `{y}` and {z}.")
        assert "$x_{i}$" in result
        assert "`{y}`" in result
        assert "\\{z\\}" in result

    def test_escaping_resumes_after_a_four_tick_fence_closes(self):
        content = '````markdown\n```python\nx = {1}\n```\n````\n\nProse {brace}.'
        result = _sanitize_for_mdx(content)
        assert "x = {1}" in result
        assert "Prose \\{brace\\}." in result

    def test_filename_meta_preserved(self):
        content = '```python filename="main.py"\nimport os\n```'
        result = _sanitize_for_mdx(content)
        assert '```python filename="main.py"' in result

    def test_line_numbers_meta_preserved(self):
        content = "```python showLineNumbers {2,4}\nimport os\nimport sys\nfrom pathlib import Path\ndef main(): pass\n```"
        result = _sanitize_for_mdx(content)
        assert "```python showLineNumbers {2,4}" in result

    def test_markdown_to_mdx_preserves_line_highlight(self):
        md_result = MarkdownResult(
            content='# Example\n\n```python {2,4-6}\nimport os\nimport sys\nfrom pathlib import Path\ndef main():\n    print("hello")\n    return 0\n```',
            frontmatter={"title": "Example"},
            route="example",
        )
        mdx = markdown_to_mdx(md_result)
        assert "```python {2,4-6}" in mdx


class TestMathEscaping:
    """Ensure _sanitize_for_mdx preserves curly braces inside math delimiters."""

    def test_inline_math_braces_not_escaped(self):
        content = r"The formula $\frac{a}{b}$ is useful"
        result = _sanitize_for_mdx(content)
        assert r"$\frac{a}{b}$" in result

    def test_block_math_braces_not_escaped(self):
        content = "$$\nx = \\frac{-b}{2a}\n$$"
        result = _sanitize_for_mdx(content)
        assert "\\frac{-b}{2a}" in result

    def test_regular_braces_still_escaped(self):
        content = "Use dict {key: value} syntax"
        result = _sanitize_for_mdx(content)
        assert "\\{key: value\\}" in result

    def test_mixed_math_and_regular_braces(self):
        content = r"Set $\frac{a}{b}$ and use {config}"
        result = _sanitize_for_mdx(content)
        assert r"$\frac{a}{b}$" in result
        assert "\\{config\\}" in result

    def test_multiple_inline_math_on_one_line(self):
        content = r"Both $\frac{x}{y}$ and $\sum_{i=1}^{n}$ work"
        result = _sanitize_for_mdx(content)
        assert r"$\frac{x}{y}$" in result
        assert r"$\sum_{i=1}^{n}$" in result

    def test_single_line_display_math(self):
        content = r"$$\frac{a}{b}$$"
        result = _sanitize_for_mdx(content)
        assert r"$$\frac{a}{b}$$" in result

    def test_block_math_multiline_complex(self):
        content = "$$\n\\int_{-\\infty}^{\\infty} e^{-x^2} \\, dx = \\sqrt{\\pi}\n$$"
        result = _sanitize_for_mdx(content)
        assert "e^{-x^2}" in result
        assert "\\sqrt{\\pi}" in result


def test_mdx_comment_survives_curly_escaping():
    """`{/*` is spared by the opening rule, so `*/}` must be spared too.

    Escaping only the closing brace leaves `{/* ... */\\}`, which fails the
    build with "Expecting Unicode escape sequence \\uXXXX" — an error that
    names neither the comment nor the brace.
    """
    from folio_docs.docs.mdx_writer import _sanitize_for_mdx

    result = _sanitize_for_mdx("{/* a note */}\n\n<Component />\n")
    assert "{/* a note */}" in result
    assert "*/\\}" not in result


def test_multiline_mdx_comment_survives_curly_escaping():
    from folio_docs.docs.mdx_writer import _sanitize_for_mdx

    result = _sanitize_for_mdx("{/* first line\n    second line */}\n")
    assert "second line */}" in result
    assert "\\}" not in result


def test_bare_closing_brace_is_still_escaped():
    from folio_docs.docs.mdx_writer import _sanitize_for_mdx

    result = _sanitize_for_mdx("Use {config} in the template.\n")
    assert "\\{config\\}" in result
