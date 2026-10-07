use super::*;
use serde_json::json;

#[test]
fn compact_matches_python_default_separators_and_keeps_utf8() {
    let value = json!({"a": [1, {"b": "é → x"}], "c": null, "d": true, "e": []});
    assert_eq!(
        compact(&value),
        "{\"a\": [1, {\"b\": \"é → x\"}], \"c\": null, \"d\": true, \"e\": []}"
    );
    assert_eq!(
        pretty(&json!({"a": {}, "b": [1]})),
        "{\n  \"a\": {},\n  \"b\": [\n    1\n  ]\n}"
    );
    assert_eq!(string("quote\"s\n"), "\"quote\\\"s\\n\"");
}
