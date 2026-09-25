use super::*;

fn parse(source: &str) -> ModuleRaw {
    parse_source_raw(source, "test", "test.py").unwrap()
}

#[test]
fn test_bom_rejection() {
    let err = parse_source_raw("\u{feff}x = 1\n", "test", "test.py").unwrap_err();
    assert_eq!(err.message, "source code string cannot contain a UTF-8 BOM");
    assert_eq!((err.line, err.column), (1, 1));
    assert_eq!(err.path, PathBuf::from("test.py"));
}

#[test]
fn test_crlf_normalisation() {
    let module = parse("def f():\r\n    \"\"\"Doc.\"\"\"\r\n    pass\r\n");
    assert_eq!(module.functions.len(), 1);
    assert_eq!(module.functions[0].docstring_raw.as_deref(), Some("Doc."));
    let lone_cr = parse("def f():\r    \"\"\"Doc.\"\"\"\r    pass\r");
    assert_eq!(lone_cr.functions[0].docstring_raw.as_deref(), Some("Doc."));
}

#[test]
fn test_parse_simple_module() {
    let module = parse(
            "\n\"\"\"Module docstring.\"\"\"\n\ndef greet(name: str) -> str:\n    \"\"\"Greet someone.\"\"\"\n    return f\"Hello, {name}\"\n\nclass Calculator:\n    \"\"\"A calc.\"\"\"\n    x: int = 0\n",
        );
    assert_eq!(module.name, "test");
    assert_eq!(module.docstring_raw.as_deref(), Some("Module docstring."));
    assert_eq!(module.functions.len(), 1);
    assert_eq!(module.functions[0].name, "greet");
    assert_eq!(module.functions[0].args[0].name, "name");
    assert_eq!(module.functions[0].args[0].annotation, "str");
    assert_eq!(module.functions[0].returns_annotation, "str");
    assert_eq!(module.classes.len(), 1);
    assert_eq!(module.classes[0].name, "Calculator");
    assert_eq!(module.classes[0].class_vars[0].name, "x");
}

#[test]
fn test_empty_and_docstring_only_modules() {
    let empty = parse("");
    assert_eq!(empty.docstring_raw, None);
    assert!(empty.classes.is_empty() && empty.functions.is_empty() && empty.constants.is_empty());
    let doc_only = parse("\"\"\"Just a docstring.\"\"\"\n");
    assert_eq!(doc_only.docstring_raw.as_deref(), Some("Just a docstring."));
    assert!(doc_only.functions.is_empty());
}

#[test]
fn test_dunder_all_filtering() {
    let module = parse(
            "\n__all__ = [\"public_func\"]\n\ndef public_func():\n    pass\n\ndef private_func():\n    pass\n",
        );
    assert_eq!(module.functions.len(), 1);
    assert_eq!(module.functions[0].name, "public_func");
}

#[test]
fn test_self_cls_filtering() {
    let module = parse(
            "\nclass MyClass:\n    def method(self, x: int) -> None:\n        pass\n\n    @classmethod\n    def from_str(cls, s: str) -> None:\n        pass\n",
        );
    let method = &module.classes[0].methods[0];
    assert_eq!(method.args.len(), 1);
    assert_eq!(method.args[0].name, "x");
    let cm = &module.classes[0].methods[1];
    assert_eq!(cm.args.len(), 1);
    assert_eq!(cm.args[0].name, "s");
}

#[test]
fn test_kind_detection() {
    let module = parse(
            "\nclass C:\n    @property\n    def prop(self) -> int:\n        return 0\n\n    @staticmethod\n    def static_m() -> None:\n        pass\n\n    @classmethod\n    def class_m(cls) -> None:\n        pass\n\n    def regular(self) -> None:\n        pass\n\ndef func() -> None:\n    pass\n\n@staticmethod\ndef static_fn():\n    pass\n\n@functools.lru_cache(maxsize=128)\ndef cached(x: int) -> int:\n    return x\n",
        );
    let methods = &module.classes[0].methods;
    assert_eq!(methods[0].kind, FunctionKind::Property);
    assert_eq!(methods[1].kind, FunctionKind::Staticmethod);
    assert_eq!(methods[2].kind, FunctionKind::Classmethod);
    assert_eq!(methods[3].kind, FunctionKind::Method);
    assert_eq!(module.functions[0].kind, FunctionKind::Function);
    // A module-level `@staticmethod` is a staticmethod.
    assert_eq!(module.functions[1].kind, FunctionKind::Staticmethod);
    assert_eq!(
        module.functions[2].decorators,
        ["functools.lru_cache(maxsize=128)"]
    );
    assert_eq!(module.functions[2].kind, FunctionKind::Function);
}

#[test]
fn test_uppercase_constants() {
    let module = parse(
            "\nMAX_RETRIES = 3\nDEFAULT_TIMEOUT = 30.0\nlowercase_var = \"not a constant\"\n_PRIVATE = \"private\"\nANNOTATED: int = 42\n",
        );
    let names: Vec<&str> = module.constants.iter().map(|c| c.name.as_str()).collect();
    assert_eq!(names, ["MAX_RETRIES", "DEFAULT_TIMEOUT", "ANNOTATED"]);
    assert!(
        is_upper_name("A1") && is_upper_name("À") && is_upper_name("Σ") && is_upper_name("__ALL__")
    );
    assert!(!is_upper_name("Mixed") && !is_upper_name("lowercase_var") && !is_upper_name("_1"));
}

#[test]
fn test_fullwidth_identifiers_are_nfkc_normalised() {
    // CPython NFKC-normalises identifiers: `Ａ` (U+FF21) is `A`.
    let module = parse("Ａ = 1\n");
    assert_eq!(module.constants[0].name, "A");
}

#[test]
fn test_syntax_error() {
    let err = parse_source_raw("def broken(:\n    pass\n", "test", "/p/broken.py").unwrap_err();
    assert_eq!(err.line, 1);
    assert_eq!(err.kind, ErrorKind::Syntax);
    assert_eq!(err.path, PathBuf::from("/p/broken.py"));
    // ruff's own message, without its ` at byte range N..M` suffix.
    assert_eq!(
        err.message,
        "Expected a parameter or the end of the parameter list"
    );
    assert_eq!(
        err.to_string(),
        "Expected a parameter or the end of the parameter list (/p/broken.py, line 1)"
    );
}

#[test]
fn test_async_function() {
    let module =
        parse("\nasync def fetch(url: str) -> bytes:\n    \"\"\"Fetch data.\"\"\"\n    pass\n");
    assert!(module.functions[0].is_async);
}

#[test]
fn test_inner_classes() {
    let module = parse("\nclass Outer:\n    class Inner:\n        pass\n");
    assert_eq!(module.classes[0].inner_classes.len(), 1);
    assert_eq!(module.classes[0].inner_classes[0].name, "Inner");
}

#[test]
fn test_defaults_alignment() {
    let module = parse("\ndef f(a, b=1, c=2):\n    pass\n");
    let args = &module.functions[0].args;
    assert_eq!(args[0].default, None);
    assert_eq!(args[1].default.as_deref(), Some("1"));
    assert_eq!(args[2].default.as_deref(), Some("2"));
}

#[test]
fn test_positional_only() {
    let module = parse("\ndef f(x: int, y: int, /, z: int = 0):\n    pass\n\ndef foo(a, b, /, c, *, d):\n    pass\n");
    let args = &module.functions[0].args;
    assert_eq!(args[0].kind, ArgKind::PositionalOnly);
    assert_eq!(args[1].kind, ArgKind::PositionalOnly);
    assert_eq!(args[2].kind, ArgKind::Regular);
    assert_eq!(args[2].default.as_deref(), Some("0"));
    let kinds: Vec<(&str, ArgKind)> = module.functions[1]
        .args
        .iter()
        .map(|a| (a.name.as_str(), a.kind))
        .collect();
    assert_eq!(
        kinds,
        [
            ("a", ArgKind::PositionalOnly),
            ("b", ArgKind::PositionalOnly),
            ("c", ArgKind::Regular),
            ("d", ArgKind::KeywordOnly),
        ]
    );
}

#[test]
fn test_complex_annotations() {
    let module = parse(
            "from typing import Optional, Union\n\ndef bar(\n    x: list[int],\n    y: dict[str, Optional[int]] = None,\n    *args: tuple[str, ...],\n    **kwargs: Any,\n) -> Union[str, None]:\n    pass\n",
        );
    let f = &module.functions[0];
    assert_eq!(f.args[1].annotation, "dict[str, Optional[int]]");
    assert_eq!(f.args[1].default.as_deref(), Some("None"));
    assert_eq!(f.args[2].annotation, "tuple[str, ...]");
    assert_eq!(f.args[2].kind, ArgKind::VarPositional);
    assert_eq!(f.args[3].annotation, "Any");
    assert_eq!(f.returns_annotation, "Union[str, None]");
}

#[test]
fn test_line_number_is_the_keyword_line() {
    let source = "def \\\n    f(): ...\n\nclass \\\n    C:\n    def \\\n        m(self): ...\n\nasync \\\ndef g(): ...\n\n@dec\ndef h(): ...\n\n@dec  # trailing comment\n\n# a comment line\nclass D: ...\n";
    let module = parse(source);
    let lines: Vec<(&str, u32)> = module
        .functions
        .iter()
        .map(|f| (f.name.as_str(), f.line_number))
        .collect();
    assert_eq!(lines, vec![("f", 1), ("g", 9), ("h", 13)]);
    let classes: Vec<(&str, u32)> = module
        .classes
        .iter()
        .map(|c| (c.name.as_str(), c.line_number))
        .collect();
    assert_eq!(classes, vec![("C", 4), ("D", 18)]);
    assert_eq!(module.classes[0].methods[0].line_number, 6);
}

#[test]
fn test_syntax_error_column_is_in_chars() {
    // CPython: SyntaxError("invalid syntax", lineno=1, offset=7); 'é' is two bytes.
    let err = parse_source_raw("é = 1 1\n", "test", "test.py").unwrap_err();
    assert_eq!((err.line, err.column), (1, 7), "{err}");
    assert_eq!(err.kind, ErrorKind::Syntax);
}

#[test]
fn test_too_many_nested_parentheses_matches_cpython_limit() {
    let ok = format!("x = {}1{}\n", "(".repeat(200), ")".repeat(200));
    assert!(parse_source_raw(&ok, "test", "test.py").is_ok());

    let too_deep = format!("x = {}1{}\n", "(".repeat(201), ")".repeat(201));
    let err = parse_source_raw(&too_deep, "test", "test.py").unwrap_err();
    assert_eq!(err.message, "too many nested parentheses");
    assert_eq!(err.kind, ErrorKind::Syntax);
    assert_eq!((err.line, err.column), (1, 205));

    let brackets = format!("x = {}1{}\n", "[".repeat(5000), "]".repeat(5000));
    assert!(parse_source_raw(&brackets, "test", "test.py").is_err());
}

#[test]
fn test_deep_expression_is_a_recursion_error_not_a_stack_overflow() {
    // Parentheses are not AST nodes; unary chains are, one level each.
    let fine = format!("X = {}1\n", "-".repeat(unparse::MAX_DEPTH - 1));
    assert!(parse_source_raw(&fine, "test", "test.py").is_ok());

    let deep = format!("X = {}1\n", "-".repeat(5000));
    let err = parse_source_raw(&deep, "test", "test.py").unwrap_err();
    assert_eq!(err.kind, ErrorKind::Recursion);
    assert_eq!(err.message, "maximum recursion depth exceeded");
    assert_eq!((err.line, err.column), (1, 5));

    let in_default = format!("def f(a={}1): ...\n", "-".repeat(5000));
    assert_eq!(
        parse_source_raw(&in_default, "test", "test.py")
            .unwrap_err()
            .kind,
        ErrorKind::Recursion
    );
}
