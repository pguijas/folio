//! Golden IR: the example package under `docs/examples` and the rich package
//! under `tests/fixtures` parse to the checked-in JSON, compared as `serde_json::Value`.
//! `FOLIO_UPDATE_GOLDEN=1 cargo test -p folio-lang-python --test golden` rewrites them.

use std::path::{Path, PathBuf};

use folio_lang_python::{discover, parse_file, DocstringStyle};
use serde_json::Value;

fn repo() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root")
}

/// Every `source_file` becomes relative to the repository root so the golden is stable.
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

fn parse_root(root: &Path) -> Value {
    let repo = repo();
    let modules: Vec<Value> = discover(&[root.to_path_buf()], &[])
        .iter()
        .map(|f| {
            let module = parse_file(&f.path, &f.root, DocstringStyle::Auto)
                .unwrap_or_else(|e| panic!("{e}"));
            serde_json::to_value(module).expect("serialisable")
        })
        .collect();
    let mut value = Value::Array(modules);
    relativise(&mut value, &repo.display().to_string());
    value
}

/// The crate's own fixtures: the rich package and both goldens.
fn fixtures() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("tests/fixtures")
        .canonicalize()
        .expect("the crate fixtures")
}

fn check_golden(source: &Path, golden: &str) {
    let actual = parse_root(source);
    let golden_path = fixtures().join(golden);
    if std::env::var_os("FOLIO_UPDATE_GOLDEN").is_some() {
        let mut text = serde_json::to_string_pretty(&actual).unwrap();
        text.push('\n');
        std::fs::write(&golden_path, text).unwrap();
    }
    let expected: Value = serde_json::from_str(
        &std::fs::read_to_string(&golden_path).unwrap_or_else(|e| panic!("{golden}: {e}")),
    )
    .expect("golden JSON");
    assert_eq!(
        actual,
        expected,
        "{golden} differs from the parsed IR:\n{}",
        serde_json::to_string_pretty(&actual).unwrap()
    );
}

#[test]
fn example_package_matches_its_golden_ir() {
    check_golden(
        &repo().join("docs/examples/generated-site/src/example_package"),
        "example_package_ir.json",
    );
}

#[test]
fn rich_package_matches_its_golden_ir() {
    check_golden(&fixtures().join("rich_package"), "rich_package_ir.json");
}
