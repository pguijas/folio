from __future__ import annotations

import ast
from pathlib import Path

import docstring_parser

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


_STYLE_MAP = {
    "google": docstring_parser.Style.GOOGLE,
    "numpy": docstring_parser.Style.NUMPYDOC,
    "auto": docstring_parser.Style.AUTO,
}


def _resolve_style(style: str) -> docstring_parser.Style:
    return _STYLE_MAP.get(style, docstring_parser.Style.GOOGLE)


def _parse_docstring(
    raw: str | None, style: docstring_parser.Style = docstring_parser.Style.GOOGLE
) -> DocstringIR:
    if not raw:
        return DocstringIR(short_description="")
    try:
        parsed = docstring_parser.parse(raw, style=style)
    except Exception:
        lines = raw.strip().split("\n")
        short = lines[0] if lines else ""
        long = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
        return DocstringIR(short_description=short, long_description=long)
    examples = [ex.description or "" for ex in parsed.examples if ex.description]
    notes = []
    for meta in parsed.meta:
        if hasattr(meta, "args") and meta.args and meta.args[0] == "note":
            notes.append(meta.description or "")
    return DocstringIR(
        short_description=parsed.short_description or "",
        long_description=parsed.long_description or "",
        examples=examples,
        notes=notes,
    )


def _get_annotation(node: ast.expr | None) -> str:
    if node is None:
        return ""
    return ast.unparse(node)


def _parse_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    source_file: str,
    is_in_class: bool = False,
    style: docstring_parser.Style = docstring_parser.Style.GOOGLE,
) -> FunctionIR:
    raw_doc = ast.get_docstring(node)
    docstring = _parse_docstring(raw_doc, style=style)
    try:
        parsed_doc = docstring_parser.parse(raw_doc or "", style=style)
    except Exception:
        parsed_doc = docstring_parser.parse("")
    doc_args = {p.arg_name: p for p in parsed_doc.params}

    def _make_arg(arg: ast.arg, default_val: str | None, kind: str) -> ArgIR | None:
        if arg.arg in ("self", "cls"):
            return None
        type_str = _get_annotation(arg.annotation)
        doc_param = doc_args.get(arg.arg)
        description = doc_param.description if doc_param else ""
        if doc_param and doc_param.type_name and not type_str:
            type_str = doc_param.type_name
        return ArgIR(
            name=arg.arg,
            type=type_str,
            default=default_val,
            description=description or "",
            kind=kind,
        )

    args: list[ArgIR] = []

    n_posonlyargs = len(node.args.posonlyargs)
    for i, arg in enumerate(node.args.posonlyargs):
        default_val = None
        defaults_offset = (
            len(node.args.posonlyargs) + len(node.args.args) - len(node.args.defaults)
        )
        idx = i
        if idx >= defaults_offset:
            default_val = ast.unparse(node.args.defaults[idx - defaults_offset])
        a = _make_arg(arg, default_val, "positional_only")
        if a:
            args.append(a)

    for i, arg in enumerate(node.args.args):
        default_val = None
        defaults_offset = (
            len(node.args.posonlyargs) + len(node.args.args) - len(node.args.defaults)
        )
        idx = n_posonlyargs + i
        if idx >= defaults_offset:
            default_val = ast.unparse(node.args.defaults[idx - defaults_offset])
        a = _make_arg(arg, default_val, "regular")
        if a:
            args.append(a)

    if node.args.vararg:
        a = _make_arg(node.args.vararg, None, "var_positional")
        if a:
            args.append(a)

    for i, arg in enumerate(node.args.kwonlyargs):
        default_val = None
        kw_default = node.args.kw_defaults[i]
        if kw_default is not None:
            default_val = ast.unparse(kw_default)
        a = _make_arg(arg, default_val, "keyword_only")
        if a:
            args.append(a)

    if node.args.kwarg:
        a = _make_arg(node.args.kwarg, None, "var_keyword")
        if a:
            args.append(a)

    returns = None
    ret_annotation = _get_annotation(node.returns)
    doc_returns = parsed_doc.returns
    if ret_annotation or doc_returns:
        returns = ReturnIR(
            type=ret_annotation or (doc_returns.type_name if doc_returns else "") or "",
            description=(doc_returns.description if doc_returns else "") or "",
        )

    raises = [
        RaiseIR(exception=r.type_name or "", description=r.description or "")
        for r in parsed_doc.raises
    ]
    decorators = [ast.unparse(d) for d in node.decorator_list]

    decorator_names = {d.split("(")[0].split(".")[-1] for d in decorators}
    if "property" in decorator_names:
        kind = "property"
    elif "staticmethod" in decorator_names:
        kind = "staticmethod"
    elif "classmethod" in decorator_names:
        kind = "classmethod"
    elif is_in_class:
        kind = "method"
    else:
        kind = "function"

    return FunctionIR(
        name=node.name,
        args=args,
        returns=returns,
        raises=raises,
        decorators=decorators,
        docstring=docstring,
        is_async=isinstance(node, ast.AsyncFunctionDef),
        source_file=source_file,
        line_number=node.lineno,
        kind=kind,
    )


def _parse_class(
    node: ast.ClassDef,
    source_file: str,
    style: docstring_parser.Style = docstring_parser.Style.GOOGLE,
) -> ClassIR:
    raw_doc = ast.get_docstring(node)
    docstring = _parse_docstring(raw_doc, style=style)
    methods: list[FunctionIR] = []
    class_vars: list[VarIR] = []
    inner_classes: list[ClassIR] = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(
                _parse_function(item, source_file, is_in_class=True, style=style)
            )
        elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            class_vars.append(
                VarIR(
                    name=item.target.id,
                    type=_get_annotation(item.annotation),
                    value=ast.unparse(item.value) if item.value else "",
                    description="",
                )
            )
        elif isinstance(item, ast.ClassDef):
            inner_classes.append(_parse_class(item, source_file, style=style))
    return ClassIR(
        name=node.name,
        bases=[ast.unparse(b) for b in node.bases],
        decorators=[ast.unparse(d) for d in node.decorator_list],
        docstring=docstring,
        methods=methods,
        class_vars=class_vars,
        inner_classes=inner_classes,
        source_file=source_file,
        line_number=node.lineno,
    )


def parse_python_file(
    path: Path,
    module_name: str,
    style: docstring_parser.Style = docstring_parser.Style.GOOGLE,
) -> ModuleIR:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ModuleIR(
            name=module_name,
            docstring=DocstringIR(short_description=""),
            classes=[],
            functions=[],
            constants=[],
            source_file=str(path),
        )

    dunder_all: list[str] | None = None
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "__all__":
                    if isinstance(node.value, (ast.List, ast.Tuple)):
                        dunder_all = [
                            elt.value
                            for elt in node.value.elts
                            if isinstance(elt, ast.Constant)
                            and isinstance(elt.value, str)
                        ]

    raw_doc = ast.get_docstring(tree)
    classes: list[ClassIR] = []
    functions: list[FunctionIR] = []
    constants: list[VarIR] = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            if dunder_all is None or node.name in dunder_all:
                classes.append(_parse_class(node, str(path), style=style))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if dunder_all is None or node.name in dunder_all:
                functions.append(_parse_function(node, str(path), style=style))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if dunder_all is None or node.target.id in dunder_all:
                constants.append(
                    VarIR(
                        name=node.target.id,
                        type=_get_annotation(node.annotation),
                        value=ast.unparse(node.value) if node.value else "",
                        description="",
                    )
                )
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id.isupper()
                    and not target.id.startswith("_")
                ):
                    if dunder_all is None or target.id in dunder_all:
                        constants.append(
                            VarIR(
                                name=target.id,
                                type="",
                                value=ast.unparse(node.value),
                                description="",
                            )
                        )
    return ModuleIR(
        name=module_name,
        docstring=_parse_docstring(raw_doc, style=style),
        classes=classes,
        functions=functions,
        constants=constants,
        source_file=str(path),
    )


def parse_python_directory(
    directory: str,
    package_name: str,
    excludes: list[str],
    docstring_style: str = "google",
) -> list[ModuleIR]:
    style = _resolve_style(docstring_style)
    root = Path(directory)
    modules: list[ModuleIR] = []
    for py_file in sorted(root.rglob("*.py")):
        if any(str(py_file).startswith(ex) for ex in excludes):
            continue
        rel = py_file.relative_to(root)
        parts = list(rel.parts)
        if parts[-1] == "__init__.py":
            parts = parts[:-1]
        else:
            parts[-1] = parts[-1].removesuffix(".py")
        module_name = f"{package_name}.{'.'.join(parts)}" if parts else package_name
        modules.append(parse_python_file(py_file, module_name, style=style))
    return modules
