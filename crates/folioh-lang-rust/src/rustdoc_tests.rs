use super::*;

#[test]
fn an_untagged_block_is_rust_and_its_hidden_lines_are_dropped() {
    let doc = "Adds.\n\n```\n# use demo::add;\n#\nlet x = add(1, 2);\n## not hidden\n```\n\n```no_run,edition2021\nrun();\n```\n\n```text\n# kept\n```\n";
    assert_eq!(
        plain_markdown(doc),
        "Adds.\n\n```rust\nlet x = add(1, 2);\n# not hidden\n```\n\n```rust\nrun();\n```\n\n```text\n# kept\n```\n"
    );
}

#[test]
fn intra_doc_links_keep_their_text() {
    let doc = "See [`Widget`], [`Widget::new()`], [the builder][Builder] and [docs](crate::guide).\n\n[Builder]: crate::build::Builder\n";
    assert_eq!(
        plain_markdown(doc),
        "See `Widget`, `Widget::new()`, the builder and docs.\n"
    );
}

#[test]
fn urls_prose_brackets_and_code_stay_as_written() {
    let doc = "Read [the book](https://doc.rust-lang.org/book/) or [Vec].\nIndex `a[i]` or a[i]; see [note] and [x].\n\n[Vec]: https://doc.rust-lang.org/std/vec/struct.Vec.html\n";
    assert_eq!(plain_markdown(doc), doc);
}

#[test]
fn a_disambiguated_or_macro_link_is_an_item() {
    assert_eq!(
        plain_markdown("Use [`fn@parse`] or [vec!] or [struct@Config]."),
        "Use `parse` or vec! or Config."
    );
}
