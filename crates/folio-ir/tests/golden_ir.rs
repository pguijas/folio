//! The serde contract: the Rust reader's golden loads as `Vec<ModuleIR>` and
//! serialises back to the same JSON. The file belongs to the crate that
//! produces it, `folio-lang-rust`; this suite reads it as the IR's own shape.

use std::path::Path;

use folio_ir::{Language, ModuleIR};
use serde_json::Value;

#[test]
fn golden_ir_round_trips_through_the_ir_types() {
    let path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../folio-lang-rust/tests/fixtures/golden_ir.json");
    let text = std::fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    let modules: Vec<ModuleIR> = serde_json::from_str(&text).expect("golden_ir.json");
    assert_eq!(modules.len(), 4);
    assert!(modules.iter().all(|m| m.language == Language::Rust));
    let round_trip: Value = serde_json::to_value(&modules).unwrap();
    let original: Value = serde_json::from_str(&text).unwrap();
    assert_eq!(round_trip, original);
}
