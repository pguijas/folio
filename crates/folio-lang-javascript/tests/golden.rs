//! The fixture sources parse to `tests/fixtures/golden_ir.json`, field for
//! field, and the broken one names where it broke.
//! `FOLIO_UPDATE_GOLDEN=1 cargo test -p folio-lang-javascript --test golden` rewrites it.

use std::path::{Path, PathBuf};

use folio_lang_javascript::{discover, parse_file, ParseError};
use serde_json::Value;

fn fixture() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures")
}

/// Every `source_file` becomes relative to the fixture root so the golden is
/// stable wherever the checkout lives; the reader reports the path as discovered.
fn relativise(value: &mut Value, base: &str) {
    match value {
        Value::Object(map) => {
            for (key, v) in map.iter_mut() {
                if key == "source_file" {
                    if let Value::String(s) = v {
                        if let Some(rel) = s.strip_prefix(base) {
                            *s = rel.trim_start_matches('/').to_string();
                        }
                    }
                } else {
                    relativise(v, base);
                }
            }
        }
        Value::Array(items) => items.iter_mut().for_each(|v| relativise(v, base)),
        _ => {}
    }
}

/// The parsed IR against the checked-in golden; `FOLIO_UPDATE_GOLDEN=1`
/// rewrites it first, and the diff is read before it is committed.
fn check_golden(root: &Path, mut actual: Value) {
    relativise(&mut actual, &root.display().to_string());
    let golden_path = root.join("golden_ir.json");
    if std::env::var_os("FOLIO_UPDATE_GOLDEN").is_some() {
        let mut text = serde_json::to_string_pretty(&actual).expect("serialises");
        text.push('\n');
        std::fs::write(&golden_path, text).expect("golden written");
    }
    let golden: Value =
        serde_json::from_str(&std::fs::read_to_string(&golden_path).expect("golden"))
            .expect("the golden is JSON");
    assert_eq!(actual, golden);
}

#[test]
fn the_fixture_sources_parse_to_the_golden_ir() {
    let root = fixture();
    // The broken fixture is the subject of its own test.
    let excludes = vec![root.join("syntax_error.js").display().to_string()];
    let found = discover(std::slice::from_ref(&root), &excludes);

    let names: Vec<&str> = found
        .files
        .iter()
        .map(|file| file.module_name.as_str())
        .collect();
    assert_eq!(
        names,
        [
            "classes",
            "commonjs",
            "constants",
            "exports",
            "functions",
            "nested"
        ]
    );
    assert_eq!(found.warnings.len(), 1, "the JSX file is reported");
    assert!(found.warnings[0].ends_with("component.jsx"));

    let modules: Vec<_> = found
        .files
        .iter()
        .map(|file| parse_file(&file.path, &file.root).expect("the fixture parses"))
        .collect();
    check_golden(&root, serde_json::to_value(&modules).expect("serialises"));
}

#[test]
fn a_module_names_the_file_it_was_read_from() {
    let root = fixture();
    let path = root.join("nested/index.js");
    let module = parse_file(&path, &root).expect("the fixture parses");
    let expected = path.display().to_string();
    assert_eq!(module.source_file, expected);
    assert!(module.functions.iter().all(|f| f.source_file == expected));
}

#[test]
fn the_broken_fixture_names_its_file_and_line() {
    let root = fixture();
    let path = root.join("syntax_error.js");
    match parse_file(&path, &root).expect_err("it does not parse") {
        ParseError::Syntax(err) => {
            assert_eq!(err.path, path);
            assert_eq!(err.line, 2);
            assert!(err.to_string().contains("syntax_error.js"));
        }
        other => panic!("expected a syntax error, got {other}"),
    }
}
