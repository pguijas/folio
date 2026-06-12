from folio.ir import (
    ArgIR,
    ClassIR,
    DocstringIR,
    FunctionIR,
    ModuleIR,
    RaiseIR,
    ReturnIR,
    VarIR,
)


def test_function_ir_basic():
    doc = DocstringIR(short_description="Greet a person.", long_description="")
    func = FunctionIR(
        name="greet",
        args=[ArgIR(name="name", type="str", default=None, description="The name.")],
        returns=ReturnIR(type="str", description="A greeting."),
        raises=[RaiseIR(exception="ValueError", description="If empty.")],
        decorators=[],
        docstring=doc,
        is_async=False,
        source_file="mod.py",
        line_number=10,
    )
    assert func.name == "greet"
    assert len(func.args) == 1
    assert func.args[0].type == "str"
    assert func.returns.type == "str"
    assert func.is_async is False


def test_class_ir_with_methods():
    doc = DocstringIR(short_description="A calculator.")
    method_doc = DocstringIR(short_description="Add two numbers.")
    method = FunctionIR(
        name="add",
        args=[
            ArgIR(name="a", type="float", default=None, description="First."),
            ArgIR(name="b", type="float", default=None, description="Second."),
        ],
        returns=ReturnIR(type="float", description="The sum."),
        raises=[],
        decorators=[],
        docstring=method_doc,
        is_async=False,
        source_file="calc.py",
        line_number=20,
    )
    cls = ClassIR(
        name="Calculator",
        bases=["object"],
        decorators=[],
        docstring=doc,
        methods=[method],
        class_vars=[],
        source_file="calc.py",
        line_number=5,
    )
    assert cls.name == "Calculator"
    assert len(cls.methods) == 1
    assert cls.methods[0].name == "add"


def test_module_ir():
    doc = DocstringIR(short_description="A test module.")
    mod = ModuleIR(
        name="mylib.core",
        docstring=doc,
        classes=[],
        functions=[],
        constants=[],
        source_file="mylib/core.py",
    )
    assert mod.name == "mylib.core"
    assert mod.source_file == "mylib/core.py"


def test_docstring_ir_defaults():
    doc = DocstringIR(short_description="Hello.")
    assert doc.long_description == ""
    assert doc.examples == []
    assert doc.notes == []


def test_arg_ir_with_default():
    arg = ArgIR(
        name="verbose", type="bool", default="False", description="Verbose mode."
    )
    assert arg.default == "False"


def test_var_ir():
    var = VarIR(name="MAX_RETRIES", type="int", value="3", description="Max retries.")
    assert var.name == "MAX_RETRIES"
    assert var.type == "int"


def test_arg_ir_kind_default():
    arg = ArgIR(name="x", type="int", default=None, description="")
    assert arg.kind == "regular"


def test_arg_ir_kind_values():
    for kind in (
        "regular",
        "positional_only",
        "keyword_only",
        "var_positional",
        "var_keyword",
    ):
        arg = ArgIR(name="x", type="", default=None, description="", kind=kind)
        assert arg.kind == kind


def test_function_ir_kind_default():
    doc = DocstringIR(short_description="")
    func = FunctionIR(
        name="f",
        args=[],
        returns=None,
        raises=[],
        decorators=[],
        docstring=doc,
        is_async=False,
        source_file="f.py",
        line_number=1,
    )
    assert func.kind == "function"


def test_function_ir_kind_values():
    doc = DocstringIR(short_description="")
    for kind in ("function", "method", "property", "staticmethod", "classmethod"):
        func = FunctionIR(
            name="f",
            args=[],
            returns=None,
            raises=[],
            decorators=[],
            docstring=doc,
            is_async=False,
            source_file="f.py",
            line_number=1,
            kind=kind,
        )
        assert func.kind == kind


def test_class_ir_inner_classes():
    doc = DocstringIR(short_description="Outer.")
    inner_doc = DocstringIR(short_description="Inner.")
    inner = ClassIR(
        name="Inner",
        bases=[],
        decorators=[],
        docstring=inner_doc,
        methods=[],
        class_vars=[],
        inner_classes=[],
        source_file="c.py",
        line_number=10,
    )
    outer = ClassIR(
        name="Outer",
        bases=[],
        decorators=[],
        docstring=doc,
        methods=[],
        class_vars=[],
        inner_classes=[inner],
        source_file="c.py",
        line_number=1,
    )
    assert len(outer.inner_classes) == 1
    assert outer.inner_classes[0].name == "Inner"


def test_class_ir_inner_classes_default():
    doc = DocstringIR(short_description="")
    cls = ClassIR(
        name="C",
        bases=[],
        decorators=[],
        docstring=doc,
        methods=[],
        class_vars=[],
        source_file="c.py",
        line_number=1,
    )
    assert cls.inner_classes == []
