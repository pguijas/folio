use super::*;

#[test]
fn a_one_line_comment_is_all_description() {
    assert_eq!(parse("/** Hello world. */").description, "Hello world.");
}

#[test]
fn the_tags_carry_the_types_the_language_does_not() {
    let doc = parse(
        "/**\n\
         * Do something.\n\
         * @param {string} name - The name.\n\
         * @param {boolean} [flag=false] - A flag.\n\
         * @returns {number} The count.\n\
         * @throws {Error} If bad.\n\
         * @deprecated Use the new one.\n\
         * @example\n\
         * foo(\"bar\")\n\
         */",
    );
    assert_eq!(doc.description, "Do something.");
    assert_eq!(
        doc.params,
        vec![
            Param {
                name: "name".into(),
                ty: "string".into(),
                default: String::new(),
                description: "The name.".into(),
            },
            Param {
                name: "flag".into(),
                ty: "boolean".into(),
                default: "false".into(),
                description: "A flag.".into(),
            },
        ]
    );
    assert_eq!(doc.returns_type, "number");
    assert_eq!(doc.returns_description, "The count.");
    assert_eq!(doc.throws, vec![("Error".into(), "If bad.".into())]);
    assert_eq!(doc.examples, vec!["foo(\"bar\")".to_string()]);
    assert_eq!(doc.docstring().short_description, "Do something.");
    assert_eq!(
        doc.docstring().long_description,
        "**Deprecated:** Use the new one."
    );
}

#[test]
fn prose_keeps_its_paragraphs_and_the_first_line_is_the_summary() {
    let doc = parse("/**\n * A short line.\n *\n * A longer one.\n */");
    let docstring = doc.docstring();
    assert_eq!(docstring.short_description, "A short line.");
    assert_eq!(docstring.long_description, "A longer one.");
}

#[test]
fn inline_links_read_as_their_text_and_types_keep_nested_braces() {
    let doc = parse(
        "/**\n\
         * See {@link Widget}, {@link Widget#render|the renderer} and {@link https://x.dev docs}.\n\
         * @param {{a: number, b: {c: string}}} opts - Built by {@linkcode make}.\n\
         * @returns {Array<{id: number}>} The rows.\n\
         */",
    );
    assert_eq!(
        doc.description,
        "See `Widget`, the renderer and [docs](https://x.dev)."
    );
    assert_eq!(doc.params[0].ty, "{a: number, b: {c: string}}");
    assert_eq!(doc.params[0].name, "opts");
    assert_eq!(doc.params[0].description, "Built by `make`.");
    assert_eq!(doc.returns_type, "Array<{id: number}>");
    assert_eq!(doc.returns_description, "The rows.");
}
