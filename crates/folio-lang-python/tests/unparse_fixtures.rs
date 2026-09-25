//! Every `expr` case in tests/fixtures/unparse_fixtures.json renders like CPython 3.12's
//! `ast.unparse`; the `module` cases are checked by `module_fixtures.rs`.

use folio_lang_python::unparse::try_unparse_expr;
use ruff_python_ast::Stmt;
use ruff_python_parser::parse_module;
use serde::Deserialize;

#[derive(Deserialize)]
struct Fixtures {
    meta: Meta,
    fixtures: Vec<Fixture>,
}

#[derive(Deserialize)]
struct Meta {
    count: usize,
}

#[derive(Deserialize)]
struct Fixture {
    id: usize,
    category: String,
    kind: String,
    input: String,
    output: Option<serde_json::Value>,
    error: Option<String>,
}

fn parse_and_unparse_expr(input: &str) -> Result<String, String> {
    let source = format!("__x__ = {input}\n");
    let parsed = parse_module(&source).map_err(|e| e.to_string())?;
    match parsed.suite().first() {
        Some(Stmt::Assign(assign)) => {
            try_unparse_expr(&assign.value, &source).map_err(|e| format!("{e:?}"))
        }
        _ => Err("no assignment in the parsed module".to_string()),
    }
}

#[test]
fn every_expr_fixture_unparses_like_cpython() {
    let fixtures: Fixtures = serde_json::from_str(include_str!("fixtures/unparse_fixtures.json"))
        .expect("fixtures JSON");
    assert_eq!(fixtures.fixtures.len(), fixtures.meta.count);
    assert_eq!(fixtures.meta.count, 546);

    // 29: a lone surrogate cannot exist in a Rust String; 425 and 449: ruff accepts
    // syntax CPython 3.12 rejects and the build does not need to reject it.
    let allowlist: &[usize] = &[29, 425, 449];
    let mut checked = 0;
    let mut failures: Vec<String> = Vec::new();
    for fixture in fixtures.fixtures.iter().filter(|f| f.kind == "expr") {
        if allowlist.contains(&fixture.id) {
            continue;
        }
        checked += 1;
        let result = parse_and_unparse_expr(&fixture.input);
        match (&fixture.error, &fixture.output) {
            (Some(_), _) => {
                if let Ok(rendered) = result {
                    failures.push(format!(
                        "{} ({}): expected a parse error, got {rendered:?}",
                        fixture.id, fixture.category
                    ));
                }
            }
            (None, Some(expected)) => {
                let expected = expected.as_str().expect("expr output is a string");
                match result {
                    Ok(rendered) if rendered == expected => {}
                    Ok(rendered) => failures.push(format!(
                        "{} ({}): input={:?} expected={expected:?} got={rendered:?}",
                        fixture.id, fixture.category, fixture.input
                    )),
                    Err(err) => failures.push(format!(
                        "{} ({}): parse error on {:?}: {err}",
                        fixture.id, fixture.category, fixture.input
                    )),
                }
            }
            (None, None) => failures.push(format!("{}: neither output nor error", fixture.id)),
        }
    }
    assert_eq!(checked, 495 - allowlist.len());
    assert!(
        failures.is_empty(),
        "{} failures:\n{}",
        failures.len(),
        failures.join("\n")
    );
}
