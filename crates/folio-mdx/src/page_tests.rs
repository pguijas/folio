use super::*;

fn text<'a>(page: &'a MarkdownPage, key: &str) -> Option<&'a str> {
    page.frontmatter.get(key).and_then(Value::as_str)
}

#[test]
fn title_comes_from_the_h1_and_the_body_is_trimmed() {
    let page = parse_markdown("# Introduction\n\nWelcome to the project.\n").unwrap();
    assert_eq!(text(&page, "title"), Some("Introduction"));
    assert_eq!(page.content, "# Introduction\n\nWelcome to the project.");
    assert_eq!(page.route, "");
    assert!(!page.unlisted);
}

#[test]
fn authored_frontmatter_wins_over_inference() {
    let page = parse_markdown(
        "---\ntitle: My Guide\ndescription: A guide.\n---\n\n# Guide\n\nContent here.\n",
    )
    .unwrap();
    assert_eq!(text(&page, "title"), Some("My Guide"));
    assert_eq!(text(&page, "description"), Some("A guide."));
    assert_eq!(page.content, "# Guide\n\nContent here.");
}

#[test]
fn description_is_the_first_paragraph_without_images_or_link_targets() {
    let cases = [
            ("# Title\n\nFirst paragraph is the description.\n\nMore content.\n", Some("First paragraph is the description.")),
            ("# Title\n\nSee ![logo](./logo.png) here.\n", Some("See  here.")),
            ("# Title\n\nBack [home](../index.md) and [on](./nope.md).\n", Some("Back home and on.")),
            ("# Title\nline one\nline two\n\nlater\n", Some("line one line two")),
            ("No heading first.\n\n# Later\n\nBody.\n", Some("No heading first.")),
            ("---\ntitle: Gallery\n---\n\n{/* The gallery renders from gallery/items/*.md at build time.\n    Write above or below it. */}\n\n<GalleryGrid />\n", None),
            ("---\ntitle: Gallery\n---\n\n<GalleryGrid />\n\nWhat the team is doing.\n", Some("What the team is doing.")),
            ("# Only a title\n", None),
        ];
    for (raw, expected) in cases {
        let page = parse_markdown(raw).unwrap();
        assert_eq!(text(&page, "description"), expected, "{raw:?}");
    }
}

#[test]
fn title_inference_reads_any_h1_line_even_in_a_fence_or_after_a_lone_hash() {
    // `^#\s+(.+)$` searches the whole body and its `\s+` spans newlines.
    let cases = [
        ("```md\n# In fence\n```\n", "In fence"),
        ("#\nNext line\n", "Next line"),
    ];
    for (raw, title) in cases {
        let page = parse_markdown(raw).unwrap();
        assert_eq!(text(&page, "title"), Some(title), "{raw:?}");
    }
}

#[test]
fn no_h1_means_no_title() {
    let page = parse_markdown("## Sub\n\nBody.\n").unwrap();
    assert!(!page.frontmatter.contains_key("title"));
    assert_eq!(text(&page, "description"), Some("Body."));
}

#[test]
fn source_route_drops_md_and_maps_readme_to_index() {
    let cases = [
        ("README.md", "index"),
        ("guides/README.md", "guides/index"),
        ("guides/quickstart.md", "guides/quickstart"),
        ("readme.MD", "readme.MD"),
        ("a/b/Readme.md", "a/b/index"),
    ];
    for (input, expected) in cases {
        assert_eq!(source_route(Path::new(input)), expected, "{input}");
    }
}
