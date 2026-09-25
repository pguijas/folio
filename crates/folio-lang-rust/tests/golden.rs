//! The fixture crate parses to `tests/fixtures/golden_ir.json`, field for field.
//! `FOLIO_UPDATE_GOLDEN=1 cargo test -p folio-lang-rust --test golden` rewrites it.

use std::path::{Path, PathBuf};

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
fn the_fixture_crate_parses_to_the_golden_ir() {
    let root = fixture();
    let files = folio_lang_rust::discover(std::slice::from_ref(&root), &[]);
    let modules: Vec<_> = files
        .iter()
        .map(|file| {
            folio_lang_rust::parse_file(&file.path, &file.root).expect("the fixture parses")
        })
        .collect();

    let names: Vec<&str> = files.iter().map(|f| f.module_name.as_str()).collect();
    assert_eq!(
        names,
        [
            "demo_crate",
            "demo_crate::models",
            "demo_crate::utils",
            "demo_crate::utils::helpers"
        ]
    );

    check_golden(&root, serde_json::to_value(&modules).expect("serialises"));
}

#[test]
fn every_item_names_the_file_it_was_read_from() {
    let root = fixture();
    let path = root.join("src/models.rs");
    let module = folio_lang_rust::parse_file(&path, &root).expect("the fixture parses");
    let expected = path.display().to_string();
    assert_eq!(module.source_file, expected);
    for item in &module.types {
        assert_eq!(item.source_file, expected, "{}", item.name);
        for method in &item.methods {
            assert_eq!(
                method.source_file, expected,
                "{}::{}",
                item.name, method.name
            );
        }
    }
}
