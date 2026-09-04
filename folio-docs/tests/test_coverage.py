"""Tests for folio_docs.coverage module."""

from folio_docs.coverage import (
    CoverageResult,
    aggregate,
    analyze_module,
    analyze_modules,
)
from folio_docs.ir import ClassIR, DocstringIR, FunctionIR, ModuleIR


def _make_func(name: str, documented: bool = True, **kwargs) -> FunctionIR:
    """Helper to build a FunctionIR."""
    short = "Does something." if documented else ""
    return FunctionIR(
        name=name,
        args=[],
        returns=None,
        raises=[],
        decorators=[],
        docstring=DocstringIR(short_description=short),
        is_async=False,
        source_file="test.py",
        line_number=1,
        **kwargs,
    )


def _make_class(
    name: str,
    documented: bool = True,
    methods: list[FunctionIR] | None = None,
    inner_classes: list[ClassIR] | None = None,
) -> ClassIR:
    """Helper to build a ClassIR."""
    short = "A class." if documented else ""
    return ClassIR(
        name=name,
        bases=[],
        decorators=[],
        docstring=DocstringIR(short_description=short),
        methods=methods or [],
        class_vars=[],
        inner_classes=inner_classes or [],
        source_file="test.py",
        line_number=1,
    )


def _make_module(
    name: str = "mylib.core",
    documented: bool = True,
    functions: list[FunctionIR] | None = None,
    classes: list[ClassIR] | None = None,
) -> ModuleIR:
    """Helper to build a ModuleIR."""
    short = "A module." if documented else ""
    return ModuleIR(
        name=name,
        docstring=DocstringIR(short_description=short),
        classes=classes or [],
        functions=functions or [],
        constants=[],
        source_file="mylib/core.py",
    )


# --- CoverageResult tests ---


def test_coverage_result_percentage_basic():
    r = CoverageResult(total=10, documented=8, undocumented=["a", "b"])
    assert r.percentage == 80.0


def test_coverage_result_percentage_zero_total():
    r = CoverageResult(total=0, documented=0, undocumented=[])
    assert r.percentage == 100.0


def test_coverage_result_percentage_all_documented():
    r = CoverageResult(total=5, documented=5, undocumented=[])
    assert r.percentage == 100.0


def test_coverage_result_percentage_none_documented():
    r = CoverageResult(total=4, documented=0, undocumented=["a", "b", "c", "d"])
    assert r.percentage == 0.0


# --- analyze_module: module-level docstring ---


def test_module_with_docstring():
    mod = _make_module(documented=True)
    result = analyze_module(mod)
    assert result.total == 1
    assert result.documented == 1
    assert result.undocumented == []


def test_module_without_docstring():
    mod = _make_module(documented=False)
    result = analyze_module(mod)
    assert result.total == 1
    assert result.documented == 0
    assert "mylib.core" in result.undocumented


# --- analyze_module: functions ---


def test_documented_function():
    mod = _make_module(functions=[_make_func("greet", documented=True)])
    result = analyze_module(mod)
    # module + function
    assert result.total == 2
    assert result.documented == 2


def test_undocumented_function():
    mod = _make_module(functions=[_make_func("greet", documented=False)])
    result = analyze_module(mod)
    assert result.total == 2
    assert result.documented == 1  # module is documented
    assert "mylib.core.greet" in result.undocumented


def test_private_function_skipped():
    mod = _make_module(functions=[_make_func("_helper", documented=False)])
    result = analyze_module(mod)
    # only module itself counted, private function skipped
    assert result.total == 1
    assert result.documented == 1
    assert result.undocumented == []


def test_dunder_init_not_skipped():
    """__init__ is the exception to the private-name rule."""
    mod = _make_module(
        classes=[
            _make_class(
                "Foo",
                documented=True,
                methods=[
                    _make_func("__init__", documented=False),
                ],
            ),
        ],
    )
    result = analyze_module(mod)
    assert (
        "__init__" not in "".join(result.undocumented)
        or "mylib.core.Foo.__init__" in result.undocumented
    )
    # module(1) + class(1) + __init__(1) = 3 total
    assert result.total == 3
    # __init__ undocumented
    assert "mylib.core.Foo.__init__" in result.undocumented


# --- analyze_module: classes ---


def test_documented_class():
    cls = _make_class("Calculator", documented=True)
    mod = _make_module(classes=[cls])
    result = analyze_module(mod)
    # module + class
    assert result.total == 2
    assert result.documented == 2


def test_undocumented_class():
    cls = _make_class("Calculator", documented=False)
    mod = _make_module(classes=[cls])
    result = analyze_module(mod)
    assert "mylib.core.Calculator" in result.undocumented


def test_class_with_methods():
    cls = _make_class(
        "Calculator",
        documented=True,
        methods=[
            _make_func("add", documented=True),
            _make_func("subtract", documented=False),
        ],
    )
    mod = _make_module(classes=[cls])
    result = analyze_module(mod)
    # module + class + add + subtract = 4
    assert result.total == 4
    assert result.documented == 3
    assert "mylib.core.Calculator.subtract" in result.undocumented


def test_private_class_skipped():
    cls = _make_class("_Internal", documented=False)
    mod = _make_module(classes=[cls])
    result = analyze_module(mod)
    assert result.total == 1  # only module
    assert "_Internal" not in "".join(result.undocumented)


def test_private_method_skipped():
    cls = _make_class(
        "Foo",
        documented=True,
        methods=[
            _make_func("public_method", documented=True),
            _make_func("_private_method", documented=False),
        ],
    )
    mod = _make_module(classes=[cls])
    result = analyze_module(mod)
    # module + class + public_method = 3 (private skipped)
    assert result.total == 3
    assert result.documented == 3


def test_inner_class():
    inner = _make_class("Inner", documented=False)
    outer = _make_class("Outer", documented=True, inner_classes=[inner])
    mod = _make_module(classes=[outer])
    result = analyze_module(mod)
    # module + Outer + Inner = 3
    assert result.total == 3
    assert "mylib.core.Outer.Inner" in result.undocumented


# --- analyze_modules / aggregate ---


def test_analyze_modules():
    mod1 = _make_module(
        name="mylib.core",
        documented=True,
        functions=[
            _make_func("foo", documented=True),
        ],
    )
    mod2 = _make_module(
        name="mylib.utils",
        documented=False,
        functions=[
            _make_func("bar", documented=False),
        ],
    )
    results = analyze_modules([mod1, mod2])
    assert "mylib.core" in results
    assert "mylib.utils" in results
    assert results["mylib.core"].documented == 2
    assert results["mylib.utils"].documented == 0


def test_aggregate():
    results = {
        "a": CoverageResult(total=5, documented=4, undocumented=["a.x"]),
        "b": CoverageResult(total=3, documented=2, undocumented=["b.y"]),
    }
    total = aggregate(results)
    assert total.total == 8
    assert total.documented == 6
    assert total.percentage == 75.0
    assert sorted(total.undocumented) == ["a.x", "b.y"]


def test_aggregate_empty():
    total = aggregate({})
    assert total.total == 0
    assert total.documented == 0
    assert total.percentage == 100.0


# --- Mixed scenario ---


def test_full_module_scenario():
    """Realistic module with mix of documented and undocumented symbols."""
    mod = _make_module(
        name="mylib.api",
        documented=True,
        functions=[
            _make_func("public_func", documented=True),
            _make_func("another_func", documented=False),
            _make_func("_private_func", documented=False),  # skipped
        ],
        classes=[
            _make_class(
                "Service",
                documented=True,
                methods=[
                    _make_func("__init__", documented=True),
                    _make_func("run", documented=True),
                    _make_func("stop", documented=False),
                    _make_func("_cleanup", documented=False),  # skipped
                ],
            ),
            _make_class("_InternalHelper", documented=False),  # skipped
        ],
    )
    result = analyze_module(mod)
    # Counted: module, public_func, another_func, Service, __init__, run, stop = 7
    # Skipped: _private_func, _cleanup, _InternalHelper
    assert result.total == 7
    # Documented: module, public_func, Service, __init__, run = 5
    assert result.documented == 5
    assert sorted(result.undocumented) == [
        "mylib.api.Service.stop",
        "mylib.api.another_func",
    ]
