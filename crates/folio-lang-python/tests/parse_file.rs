//! Reading files: the error surface names the file, every checked-in `.py` parses, and
//! a synthetic package round-trips through discovery and parsing.

use std::fs;
use std::path::{Path, PathBuf};

use folio_ir::FunctionKind;
use folio_lang_python::{discover, parse_file, DocstringStyle, ErrorKind, ParseError};

fn write(path: &Path, content: &str) {
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(path, content).unwrap();
}

#[test]
fn failures_name_the_file() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path();

    let missing = root.join("missing.py");
    match parse_file(&missing, root, DocstringStyle::Google) {
        Err(ParseError::Io { path, source }) => {
            assert_eq!(path, missing);
            assert_eq!(source.kind(), std::io::ErrorKind::NotFound);
        }
        other => panic!("expected Io, got {other:?}"),
    }
    let err = parse_file(&missing, root, DocstringStyle::Google).unwrap_err();
    assert!(
        err.to_string()
            .ends_with(&format!(": {}", missing.display())),
        "{err}"
    );

    let latin1 = root.join("latin1.py");
    fs::write(&latin1, b"\"\"\"caf\xe9.\"\"\"\nX = 1\n").unwrap();
    match parse_file(&latin1, root, DocstringStyle::Google) {
        Err(ParseError::Decode { path, start, end }) => {
            assert_eq!(path, latin1);
            assert_eq!((start, end), (6, 7));
        }
        other => panic!("expected Decode, got {other:?}"),
    }

    let broken = root.join("broken.py");
    write(&broken, "def broken(:\n    pass\n");
    match parse_file(&broken, root, DocstringStyle::Google) {
        Err(ParseError::Syntax(err)) => {
            assert_eq!(err.path, broken);
            assert_eq!(err.line, 1);
            assert_eq!(err.kind, ErrorKind::Syntax);
            assert_eq!(
                err.to_string(),
                format!("{} ({}, line 1)", err.message, broken.display())
            );
        }
        other => panic!("expected Syntax, got {other:?}"),
    }

    let bad = root.join("bad.py");
    write(&bad, "é = 1 1\n");
    let Err(ParseError::Syntax(err)) = parse_file(&bad, root, DocstringStyle::Google) else {
        panic!("expected a syntax error");
    };
    assert_eq!((err.line, err.column), (1, 7));
    assert_eq!(err.path, bad);

    let deep = root.join("deep.py");
    write(&deep, &format!("X = {}1\n", "-".repeat(5000)));
    let Err(ParseError::Syntax(err)) = parse_file(&deep, root, DocstringStyle::Google) else {
        panic!("expected a recursion error");
    };
    assert_eq!(err.kind, ErrorKind::Recursion);
    assert_eq!(
        err.to_string(),
        format!(
            "maximum recursion depth exceeded ({}, line 1)",
            deep.display()
        )
    );

    let parens = root.join("parens.py");
    write(
        &parens,
        &format!("X = {}1{}\n", "(".repeat(5000), ")".repeat(5000)),
    );
    let Err(ParseError::Syntax(err)) = parse_file(&parens, root, DocstringStyle::Google) else {
        panic!("expected a syntax error");
    };
    assert_eq!(err.message, "too many nested parentheses");
    assert_eq!((err.line, err.column), (1, 205));
}

#[test]
fn parse_file_names_the_module_from_the_root() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().join("pkg");
    let file = root.join("sub/mod.py");
    write(&file, "\"\"\"Module docstring.\"\"\"\n\ndef greet(name: str) -> str:\n    return name\n\nasync def fetch(url: str) -> bytes:\n    ...\n");
    for style in [
        DocstringStyle::Google,
        DocstringStyle::Numpy,
        DocstringStyle::Auto,
    ] {
        let module = parse_file(&file, &root, style).unwrap();
        assert_eq!(module.name, "pkg.sub.mod");
        assert_eq!(module.source_file, file.display().to_string());
        assert_eq!(module.functions.len(), 2);
        assert_eq!(module.functions[0].source_file, module.source_file);
    }
}

fn collect_py(dir: &Path, out: &mut Vec<PathBuf>) {
    for entry in fs::read_dir(dir).unwrap().flatten() {
        let path = entry.path();
        if path.is_dir() {
            collect_py(&path, out);
        } else if path.extension().is_some_and(|e| e == "py") {
            out.push(path);
        }
    }
}

#[test]
fn every_checked_in_python_file_parses() {
    let crate_dir = Path::new(env!("CARGO_MANIFEST_DIR"));
    let mut files = Vec::new();
    collect_py(&crate_dir.join("../../docs/examples"), &mut files);
    collect_py(&crate_dir.join("tests/fixtures"), &mut files);
    assert!(files.len() >= 2, "corpus: {files:?}");
    for file in files {
        let root = file.parent().unwrap();
        let module = parse_file(&file, root, DocstringStyle::Auto)
            .unwrap_or_else(|e| panic!("{}: {e}", file.display()));
        assert_eq!(module.source_file, file.display().to_string());
    }
}

#[test]
fn synthetic_package_round_trips() {
    let dir = tempfile::tempdir().unwrap();
    let pkg = dir.path().join("synth_pkg");
    write(
        &pkg.join("__init__.py"),
        "\"\"\"Synthetic package.\"\"\"\n\n__all__ = [\"greet\", \"Config\"]\n",
    );
    write(
        &pkg.join("core.py"),
        "\"\"\"Core module.\"\"\"\n\nfrom __future__ import annotations\n\nfrom typing import Optional\n\nMAX: int = 100\nDEFAULT_NAME = 'world'\n\ndef greet(name: str = DEFAULT_NAME, *, loud: bool = False) -> str:\n    \"\"\"Return a greeting.\"\"\"\n    msg = f'Hello, {name}!'\n    return msg.upper() if loud else msg\n\nasync def fetch(url: str, timeout: float = 30.0) -> bytes:\n    \"\"\"Fetch bytes from a URL.\"\"\"\n    ...\n\nclass Config:\n    \"\"\"Configuration holder.\"\"\"\n    debug: bool = False\n    retries: int = 3\n\n    def __init__(self, debug: bool = False) -> None:\n        self.debug = debug\n\n    @property\n    def is_debug(self) -> bool:\n        \"\"\"Whether debug mode is on.\"\"\"\n        return self.debug\n\n    @staticmethod\n    def default() -> 'Config':\n        \"\"\"Return default config.\"\"\"\n        return Config()\n\nclass _Internal:\n    \"\"\"Private class.\"\"\"\n    pass\n",
    );
    write(
        &pkg.join("models.py"),
        "\"\"\"Data models.\"\"\"\n\nfrom dataclasses import dataclass, field\nfrom typing import ClassVar, Final\n\n@dataclass\nclass Point:\n    \"\"\"A 2D point.\"\"\"\n    x: float\n    y: float\n    _count: ClassVar[int] = 0\n    TAG: Final = 'point'\n\n    def distance(self, other: 'Point') -> float:\n        \"\"\"Euclidean distance.\"\"\"\n        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5\n\n@dataclass\nclass Line:\n    \"\"\"A line segment.\"\"\"\n    start: Point\n    end: Point\n    tags: list[str] = field(default_factory=list)\n",
    );
    write(
        &pkg.join("utils.py"),
        "\"\"\"Utility helpers.\"\"\"\n\nimport os\n\nX, Y = 1, 2\n\ndef identity(x):\n    return x\n\nclass Mixin:\n    pass\n\nclass Child(Mixin):\n    \"\"\"A child class.\"\"\"\n    pass\n",
    );

    let files = discover(std::slice::from_ref(&pkg), &[]);
    let got: Vec<&str> = files.iter().map(|f| f.module_name.as_str()).collect();
    assert_eq!(
        got,
        [
            "synth_pkg",
            "synth_pkg.core",
            "synth_pkg.models",
            "synth_pkg.utils"
        ]
    );
    let modules: Vec<_> = files
        .iter()
        .map(|f| parse_file(&f.path, &f.root, DocstringStyle::Auto).unwrap())
        .collect();

    // `__all__` names imported symbols: nothing defined here is published.
    assert!(modules[0].functions.is_empty() && modules[0].classes.is_empty());
    let core = &modules[1];
    assert_eq!(
        core.constants
            .iter()
            .map(|c| c.name.as_str())
            .collect::<Vec<_>>(),
        ["MAX", "DEFAULT_NAME"]
    );
    assert_eq!(
        core.functions[0].args[0].default.as_deref(),
        Some("DEFAULT_NAME")
    );
    let config = &core.classes[0];
    let is_debug = config
        .methods
        .iter()
        .find(|m| m.name == "is_debug")
        .unwrap();
    assert_eq!(is_debug.kind, FunctionKind::Property);
    assert!(is_debug.args.is_empty());
    assert_eq!(
        config
            .methods
            .iter()
            .find(|m| m.name == "default")
            .unwrap()
            .kind,
        FunctionKind::Staticmethod
    );
    // No `__all__` here: the underscore keeps `_Internal` out.
    assert_eq!(core.classes.len(), 1);

    let point = &modules[2].classes[0];
    assert_eq!(point.decorators, ["dataclass"]);
    let names: Vec<&str> = point.class_vars.iter().map(|v| v.name.as_str()).collect();
    assert_eq!(names, ["x", "y", "TAG"], "`_count` is private");
    assert_eq!(point.class_vars[2].ty, "Final");
    assert_eq!(
        modules[2].classes[1].class_vars[2].value,
        "field(default_factory=list)"
    );

    let utils = &modules[3];
    assert!(
        utils.constants.is_empty(),
        "tuple targets are not constants"
    );
    assert_eq!(utils.classes[1].bases, ["Mixin"]);
}
