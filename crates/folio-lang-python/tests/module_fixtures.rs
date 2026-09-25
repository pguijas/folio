//! The 51 `module` cases in tests/fixtures/unparse_fixtures.json: each category's
//! projection of `finalize_module(parse_source_raw(input))` against the recorded IR.

use std::collections::BTreeSet;

use folio_ir::{ArgIR, ClassIR, DocstringIR, ModuleIR, ReturnIR, VarIR};
use folio_lang_python::extract::decorator_name;
use folio_lang_python::{finalize_module, parse_source_raw, DocstringStyle, ModuleRaw};
use serde::Deserialize;
use serde_json::{json, Value};

#[derive(Deserialize)]
struct Fixtures {
    fixtures: Vec<Fixture>,
}

#[derive(Deserialize)]
struct Fixture {
    id: usize,
    category: String,
    kind: String,
    input: String,
    /// Absent on the `expr` error cases, which this test skips.
    #[serde(default)]
    output: Value,
}

fn raw(input: &str) -> ModuleRaw {
    parse_source_raw(input, "fx", "fx.py").expect("module fixture parses")
}

fn ir(input: &str, style: DocstringStyle) -> ModuleIR {
    finalize_module(raw(input), style)
}

fn names<'a>(items: impl Iterator<Item = &'a String>) -> Value {
    json!(items.collect::<Vec<_>>())
}

fn from<T: serde::de::DeserializeOwned>(value: &Value) -> T {
    serde_json::from_value(value.clone()).expect("fixture shape")
}

fn check(fixture: &Fixture) -> Result<(), String> {
    let out = &fixture.output;
    let module = ir(&fixture.input, DocstringStyle::Google);
    let single_function = || module.functions.first().expect("one function");
    let mut mismatches = Vec::new();
    let mut expect = |label: &str, actual: Value, expected: Value| {
        if actual != expected {
            mismatches.push(format!("{label}: expected {expected}, got {actual}"));
        }
    };
    match fixture.category.as_str() {
        "decorators" => {
            let decorators = &single_function().decorators;
            expect("decorators", json!(decorators), out["decorators"].clone());
            let derived: BTreeSet<&str> = decorators.iter().map(|d| decorator_name(d)).collect();
            expect(
                "decorator_names",
                json!(derived),
                out["decorator_names"].clone(),
            );
        }
        "bases" => {
            expect(
                "bases",
                json!(module.classes[0].bases),
                out["bases"].clone(),
            );
        }
        "classvars" | "kind" | "body_scope" => {
            let expected: Vec<ClassIR> = from(&out["classes"]);
            expect(
                "classes",
                serde_json::to_value(&module.classes).unwrap(),
                serde_json::to_value(&expected).unwrap(),
            );
            expect(
                "functions",
                names(module.functions.iter().map(|f| &f.name)),
                out["functions"].clone(),
            );
        }
        "defaults" | "defaults_alignment" | "returns" => {
            let expected_args: Vec<ArgIR> = from(&out["args"]);
            let expected_returns: Option<ReturnIR> = from(&out["returns"]);
            let f = single_function();
            expect("args", json!(f.args), json!(expected_args));
            expect("returns", json!(f.returns), json!(expected_returns));
        }
        "constants" | "dunder_all" => {
            let expected: Vec<VarIR> = from(&out["constants"]);
            expect("constants", json!(module.constants), json!(expected));
            expect(
                "functions",
                names(module.functions.iter().map(|f| &f.name)),
                out["functions"].clone(),
            );
            expect(
                "classes",
                names(module.classes.iter().map(|c| &c.name)),
                out["classes"].clone(),
            );
        }
        "docstring" => {
            let raw = raw(&fixture.input);
            let raw_doc = match raw.functions.first() {
                Some(f) => f.docstring_raw.clone(),
                None => raw.docstring_raw.clone(),
            };
            expect(
                "get_docstring",
                json!(raw_doc),
                out["get_docstring"].clone(),
            );
            for (key, style) in [
                ("folio_ir_google", DocstringStyle::Google),
                ("folio_ir_auto", DocstringStyle::Auto),
            ] {
                let module = ir(&fixture.input, style);
                let doc: &DocstringIR = match module.functions.first() {
                    Some(f) => &f.docstring,
                    None => &module.docstring,
                };
                expect(key, json!(doc), out[key].clone());
            }
        }
        "lineno" => {
            let f = single_function();
            let c = &module.classes[0];
            expect(
                "linenos",
                json!({f.name.clone(): f.line_number, c.name.clone(): c.line_number}),
                out["linenos"].clone(),
            );
        }
        other => return Err(format!("unknown category {other}")),
    }
    if mismatches.is_empty() {
        Ok(())
    } else {
        Err(mismatches.join("\n  "))
    }
}

#[test]
fn every_module_fixture_matches_the_recorded_ir() {
    let fixtures: Fixtures = serde_json::from_str(include_str!("fixtures/unparse_fixtures.json"))
        .expect("fixtures JSON");
    let modules: Vec<&Fixture> = fixtures
        .fixtures
        .iter()
        .filter(|f| f.kind == "module")
        .collect();
    assert_eq!(modules.len(), 51);
    let failures: Vec<String> = modules
        .iter()
        .filter_map(|f| {
            check(f)
                .err()
                .map(|e| format!("fixture {} ({}):\n  {e}", f.id, f.category))
        })
        .collect();
    assert!(
        failures.is_empty(),
        "{} failures:\n{}",
        failures.len(),
        failures.join("\n")
    );
}
