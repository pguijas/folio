use super::*;
use serde_json::json;

#[test]
fn quoted_value_spells_scalars_as_the_config_does() {
    assert_eq!(quoted_value(&json!("a")), "'a'");
    assert_eq!(quoted_value(&json!("it's")), "'it\\'s'");
    assert_eq!(quoted_value(&json!("say \"hi\"")), "'say \"hi\"'");
    assert_eq!(quoted_value(&json!("a\nb\\c")), "'a\\nb\\\\c'");
    assert_eq!(quoted_value(&json!(42)), "42");
    assert_eq!(quoted_value(&json!(1.5)), "1.5");
    assert_eq!(quoted_value(&json!(true)), "true");
    assert_eq!(quoted_value(&json!(null)), "null");
    assert_eq!(quoted_value(&json!([1, "x"])), "[1, 'x']");
    assert_eq!(
        quoted_value(&json!({"k": "v", "n": null})),
        "{'k': 'v', 'n': null}"
    );
}

#[test]
fn truthy_reads_emptiness() {
    for (value, expected) in [
        (json!(null), false),
        (json!(false), false),
        (json!(0), false),
        (json!(0.0), false),
        (json!(""), false),
        (json!([]), false),
        (json!({}), false),
        (json!(true), true),
        (json!(2), true),
        (json!("no"), true),
        (json!([0]), true),
        (json!({"a": 1}), true),
    ] {
        assert_eq!(truthy(&value), expected, "{value}");
    }
}

#[test]
fn as_text_keeps_strings_bare() {
    assert_eq!(as_text(&json!("plain")), "plain");
    assert_eq!(as_text(&json!(0.1)), "0.1");
    assert_eq!(as_text(&json!(3)), "3");
    assert_eq!(as_text(&json!(false)), "false");
    assert_eq!(as_text(&json!(null)), "null");
    assert_eq!(as_text(&json!(["a"])), "['a']");
}
