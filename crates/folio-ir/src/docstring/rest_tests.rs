use super::*;

#[test]
fn multi_line_field_descriptions_are_cleaned() {
    // The continuation goes through cleandoc: its first line is lstripped, the
    // margin comes from the lines after it.
    let doc = parse("S.\n\n:param x: first\n    second\n      third\n:returns: r").unwrap();
    assert_eq!(doc.meta.len(), 2);
    assert!(matches!(
        &doc.meta[0],
        Meta::Param { description, .. } if description == "first\nsecond\nthird"
    ));
}
