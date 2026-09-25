use super::*;

fn strings(pairs: &[(&str, &str)]) -> IndexMap<String, String> {
    pairs
        .iter()
        .map(|(k, v)| (k.to_string(), v.to_string()))
        .collect()
}

#[test]
fn split_takes_the_block_at_byte_zero_only() {
    assert_eq!(
        split_frontmatter("---\ntitle: A\n---\n# H\n"),
        Some(("title: A", "# H\n"))
    );
    assert_eq!(split_frontmatter("---\n\n---\nbody"), Some(("", "body")));
    for raw in [
        "# H\n---\ntitle: A\n---\n",
        "---\n---\n",
        "---\ntitle: A\n",
        "--- \ntitle: A\n---\n",
    ] {
        assert_eq!(split_frontmatter(raw), None, "{raw:?}");
    }
}

#[test]
fn parse_accepts_empty_and_typed_values_and_rejects_non_mappings() {
    assert!(parse_frontmatter("").unwrap().is_empty());
    assert!(parse_frontmatter("  \n").unwrap().is_empty());
    let typed = parse_frontmatter("title: x\nsidebar_position: 3\ntheme:\n  toc: false\n").unwrap();
    assert_eq!(
        typed.keys().collect::<Vec<_>>(),
        ["title", "sidebar_position", "theme"]
    );
    assert_eq!(typed["sidebar_position"], Value::Number(3.into()));
    for bad in ["just a string", "- a\n- b", "a: 1\na: 2"] {
        assert!(parse_frontmatter(bad).is_err(), "{bad:?}");
    }
}

#[test]
fn render_sorts_keys_quotes_ambiguous_scalars_and_never_folds() {
    let long = "This sample project shows the kind of static documentation site Folio generates from a small Python package.";
    let out = render_frontmatter(&strings(&[
        ("title", "Source Code"),
        ("description", "Run the local preview server while editing:"),
        ("flag", "True"),
        ("number", "123"),
        ("hash", "# hash"),
        ("colon", "Utility functions: with colon"),
        ("long", long),
        ("unicode", "Parse --> IRNode ◇ café"),
    ]));
    assert_eq!(
            out,
            format!(
                "---\ncolon: 'Utility functions: with colon'\ndescription: 'Run the local preview server while editing:'\nflag: 'True'\nhash: '# hash'\nlong: {long}\nnumber: '123'\ntitle: Source Code\nunicode: Parse --> IRNode ◇ café\n---\n"
            )
        );
}

#[test]
fn render_reemits_author_scalars_as_written() {
    let fm = parse_frontmatter("title: Gallery\nsidebar_position: 3\ndraft: true\n").unwrap();
    assert_eq!(
        render_frontmatter(&fm),
        "---\ndraft: true\nsidebar_position: 3\ntitle: Gallery\n---\n"
    );
}
