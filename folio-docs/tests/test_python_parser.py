from pathlib import Path

import pytest

from folio_docs.parser.python_parser import parse_python_file, parse_python_directory


def test_parse_function(sample_python_source, tmp_path):
    src_file = tmp_path / "sample.py"
    src_file.write_text(sample_python_source)
    module = parse_python_file(src_file, "sample")

    assert module.name == "sample"
    assert module.docstring.short_description == "Sample module for testing."

    funcs = module.functions
    assert len(funcs) == 1
    assert funcs[0].name == "greet"
    assert funcs[0].args[0].name == "name"
    assert funcs[0].args[0].type == "str"
    assert funcs[0].args[1].name == "excited"
    assert funcs[0].args[1].type == "bool"
    assert funcs[0].args[1].default == "False"
    assert funcs[0].returns.type == "str"
    assert len(funcs[0].raises) == 1
    assert funcs[0].raises[0].exception == "ValueError"
    assert funcs[0].is_async is False


def test_parse_class(sample_python_source, tmp_path):
    src_file = tmp_path / "sample.py"
    src_file.write_text(sample_python_source)
    module = parse_python_file(src_file, "sample")

    classes = module.classes
    assert len(classes) == 1

    cls = classes[0]
    assert cls.name == "Calculator"
    assert cls.docstring.short_description == "A simple calculator."
    assert len(cls.methods) == 3  # __init__, add, add_async

    init = next(m for m in cls.methods if m.name == "__init__")
    assert init.args[0].name == "precision"
    assert init.args[0].type == "int"

    add = next(m for m in cls.methods if m.name == "add")
    assert add.returns.type == "float"
    assert add.is_async is False

    add_async = next(m for m in cls.methods if m.name == "add_async")
    assert add_async.is_async is True


def test_parse_directory(sample_python_source, tmp_path):
    pkg = tmp_path / "mylib"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""My library."""\n')
    (pkg / "core.py").write_text(sample_python_source)

    modules = parse_python_directory(str(pkg), "mylib", excludes=[])
    assert len(modules) == 2

    names = {m.name for m in modules}
    assert "mylib" in names
    assert "mylib.core" in names


def test_parse_directory_with_excludes(sample_python_source, tmp_path):
    pkg = tmp_path / "mylib"
    pkg.mkdir()
    (pkg / "__init__.py").write_text('"""My library."""\n')
    (pkg / "core.py").write_text(sample_python_source)

    tests_dir = pkg / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_core.py").write_text("def test_it(): pass\n")

    modules = parse_python_directory(str(pkg), "mylib", excludes=[str(tests_dir)])
    names = {m.name for m in modules}
    assert "mylib.tests" not in names
    assert "mylib.tests.test_core" not in names


def test_parse_empty_module(tmp_path):
    src_file = tmp_path / "empty.py"
    src_file.write_text("")
    module = parse_python_file(src_file, "empty")
    assert module.name == "empty"
    assert module.functions == []
    assert module.classes == []


def test_parse_invalid_python_raises_with_source_path(tmp_path: Path) -> None:
    src_file = tmp_path / "broken.py"
    src_file.write_text("def broken(:\n    pass\n", encoding="utf-8")

    with pytest.raises(SyntaxError) as exc_info:
        parse_python_file(src_file, "broken")

    assert exc_info.value.filename == str(src_file)


def test_parse_directory_supports_documented_exclude_globs(tmp_path: Path) -> None:
    pkg = tmp_path / "src" / "demo"
    tests_dir = pkg / "tests"
    tests_dir.mkdir(parents=True)
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    (pkg / "core.py").write_text("PUBLIC = True\n", encoding="utf-8")
    (pkg / "test_unit.py").write_text("HIDDEN = True\n", encoding="utf-8")
    (tests_dir / "test_hidden.py").write_text("HIDDEN = True\n", encoding="utf-8")
    (pkg / "conftest.py").write_text("FIXTURE = True\n", encoding="utf-8")

    modules = parse_python_directory(
        str(pkg),
        "demo",
        excludes=[
            str(tmp_path / "**/test_*.py"),
            str(tmp_path / "**/tests/"),
            str(tmp_path / "**/conftest.py"),
        ],
    )

    assert [module.name for module in modules] == ["demo", "demo.core"]


def test_directory_exclude_does_not_match_a_shared_prefix(tmp_path: Path) -> None:
    pkg = tmp_path / "demo"
    internal = pkg / "internal"
    internal_tools = pkg / "internal_tools"
    internal.mkdir(parents=True)
    internal_tools.mkdir()
    (internal / "hidden.py").write_text("HIDDEN = True\n", encoding="utf-8")
    (internal_tools / "public.py").write_text("PUBLIC = True\n", encoding="utf-8")

    modules = parse_python_directory(
        str(pkg), "demo", excludes=[str(internal)]
    )

    assert [module.name for module in modules] == ["demo.internal_tools.public"]


def test_parse_args_and_kwargs(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
def func(a: int, *args: str, **kwargs: float) -> None:
    """A function with *args and **kwargs."""
    pass
''')
    module = parse_python_file(src, "mod")
    func = module.functions[0]
    assert func.name == "func"
    assert len(func.args) == 3

    assert func.args[0].name == "a"
    assert func.args[0].kind == "regular"
    assert func.args[0].type == "int"

    assert func.args[1].name == "args"
    assert func.args[1].kind == "var_positional"
    assert func.args[1].type == "str"

    assert func.args[2].name == "kwargs"
    assert func.args[2].kind == "var_keyword"
    assert func.args[2].type == "float"


def test_parse_keyword_only_args(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
def func(a: int, *, key: str = "default", flag: bool = True) -> None:
    """Function with keyword-only args."""
    pass
''')
    module = parse_python_file(src, "mod")
    func = module.functions[0]
    assert len(func.args) == 3

    assert func.args[0].name == "a"
    assert func.args[0].kind == "regular"

    assert func.args[1].name == "key"
    assert func.args[1].kind == "keyword_only"
    assert func.args[1].default == "'default'"

    assert func.args[2].name == "flag"
    assert func.args[2].kind == "keyword_only"
    assert func.args[2].default == "True"


def test_parse_positional_only_args(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
def func(x: int, y: int, /, z: int = 0) -> None:
    """Function with positional-only args."""
    pass
''')
    module = parse_python_file(src, "mod")
    func = module.functions[0]
    assert len(func.args) == 3

    assert func.args[0].name == "x"
    assert func.args[0].kind == "positional_only"

    assert func.args[1].name == "y"
    assert func.args[1].kind == "positional_only"

    assert func.args[2].name == "z"
    assert func.args[2].kind == "regular"
    assert func.args[2].default == "0"


def test_parse_complex_signature(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
def func(a: int, b: str, /, c: float = 1.0, *args, key: bool = False, **kwargs) -> None:
    """Complex signature with all arg types."""
    pass
''')
    module = parse_python_file(src, "mod")
    func = module.functions[0]
    assert len(func.args) == 6

    assert func.args[0].name == "a"
    assert func.args[0].kind == "positional_only"

    assert func.args[1].name == "b"
    assert func.args[1].kind == "positional_only"

    assert func.args[2].name == "c"
    assert func.args[2].kind == "regular"
    assert func.args[2].default == "1.0"

    assert func.args[3].name == "args"
    assert func.args[3].kind == "var_positional"

    assert func.args[4].name == "key"
    assert func.args[4].kind == "keyword_only"
    assert func.args[4].default == "False"

    assert func.args[5].name == "kwargs"
    assert func.args[5].kind == "var_keyword"


def test_parse_property_method(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
class MyClass:
    """A class."""

    @property
    def value(self) -> int:
        """The value."""
        return self._value

    @value.setter
    def value(self, val: int) -> None:
        self._value = val
''')
    module = parse_python_file(src, "mod")
    cls = module.classes[0]
    getter = next(m for m in cls.methods if m.name == "value" and m.kind == "property")
    assert getter.kind == "property"
    assert getter.returns.type == "int"


def test_parse_staticmethod(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
class MyClass:
    """A class."""

    @staticmethod
    def create(name: str) -> "MyClass":
        """Create an instance."""
        return MyClass()
''')
    module = parse_python_file(src, "mod")
    cls = module.classes[0]
    method = cls.methods[0]
    assert method.name == "create"
    assert method.kind == "staticmethod"
    assert len(method.args) == 1
    assert method.args[0].name == "name"


def test_parse_classmethod(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
class MyClass:
    """A class."""

    @classmethod
    def from_string(cls, data: str) -> "MyClass":
        """Create from string."""
        return cls()
''')
    module = parse_python_file(src, "mod")
    cls = module.classes[0]
    method = cls.methods[0]
    assert method.name == "from_string"
    assert method.kind == "classmethod"
    assert len(method.args) == 1
    assert method.args[0].name == "data"


def test_parse_regular_method_kind(sample_python_source, tmp_path):
    src_file = tmp_path / "sample.py"
    src_file.write_text(sample_python_source)
    module = parse_python_file(src_file, "sample")
    cls = module.classes[0]
    add = next(m for m in cls.methods if m.name == "add")
    assert add.kind == "method"


def test_parse_function_kind(sample_python_source, tmp_path):
    src_file = tmp_path / "sample.py"
    src_file.write_text(sample_python_source)
    module = parse_python_file(src_file, "sample")
    func = module.functions[0]
    assert func.kind == "function"


def test_parse_dunder_all_filtering(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
"""Module with __all__."""

__all__ = ["public_func", "PublicClass", "MAX_SIZE"]

def public_func() -> None:
    """Public function."""
    pass

def _private_func() -> None:
    """Private function (not in __all__)."""
    pass

def excluded_func() -> None:
    """Excluded function (not in __all__)."""
    pass

class PublicClass:
    """Public class."""
    pass

class ExcludedClass:
    """Excluded class (not in __all__)."""
    pass

MAX_SIZE: int = 100
EXCLUDED_CONST: int = 50
''')
    module = parse_python_file(src, "mod")
    func_names = [f.name for f in module.functions]
    class_names = [c.name for c in module.classes]
    const_names = [c.name for c in module.constants]

    assert func_names == ["public_func"]
    assert class_names == ["PublicClass"]
    assert const_names == ["MAX_SIZE"]


def test_parse_dunder_all_tuple(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text("""
__all__ = ("func_a",)

def func_a() -> None:
    pass

def func_b() -> None:
    pass
""")
    module = parse_python_file(src, "mod")
    assert len(module.functions) == 1
    assert module.functions[0].name == "func_a"


def test_parse_no_dunder_all_includes_everything(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text("""
def func_a() -> None:
    pass

def func_b() -> None:
    pass
""")
    module = parse_python_file(src, "mod")
    assert len(module.functions) == 2


def test_parse_nested_class(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
class Outer:
    """Outer class."""

    class Inner:
        """Inner class."""

        def inner_method(self) -> None:
            """An inner method."""
            pass

    class AnotherInner:
        """Another inner class."""
        pass

    def outer_method(self) -> None:
        """An outer method."""
        pass
''')
    module = parse_python_file(src, "mod")
    cls = module.classes[0]
    assert cls.name == "Outer"
    assert len(cls.inner_classes) == 2

    inner = cls.inner_classes[0]
    assert inner.name == "Inner"
    assert len(inner.methods) == 1
    assert inner.methods[0].name == "inner_method"

    another = cls.inner_classes[1]
    assert another.name == "AnotherInner"


def test_parse_unannotated_uppercase_constants(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text("""
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30.0
API_URL = "https://api.example.com"
lowercase_var = "not a constant"
_PRIVATE = "private"
ANNOTATED: int = 42
""")
    module = parse_python_file(src, "mod")
    const_names = [c.name for c in module.constants]
    assert "MAX_RETRIES" in const_names
    assert "DEFAULT_TIMEOUT" in const_names
    assert "API_URL" in const_names
    assert "lowercase_var" not in const_names
    assert "_PRIVATE" not in const_names
    assert "ANNOTATED" in const_names

    max_retries = next(c for c in module.constants if c.name == "MAX_RETRIES")
    assert max_retries.type == ""
    assert max_retries.value == "3"

    annotated = next(c for c in module.constants if c.name == "ANNOTATED")
    assert annotated.type == "int"
    assert annotated.value == "42"


def test_parse_method_self_cls_filtered(tmp_path):
    src = tmp_path / "mod.py"
    src.write_text('''
class MyClass:
    """A class."""

    def method(self, x: int) -> None:
        pass

    @classmethod
    def class_method(cls, y: str) -> None:
        pass
''')
    module = parse_python_file(src, "mod")
    cls = module.classes[0]

    method = next(m for m in cls.methods if m.name == "method")
    assert len(method.args) == 1
    assert method.args[0].name == "x"

    cm = next(m for m in cls.methods if m.name == "class_method")
    assert len(cm.args) == 1
    assert cm.args[0].name == "y"
