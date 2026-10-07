use super::*;

fn page(dir: &Path, content: &str) -> MarkdownPage {
    MarkdownPage {
        content: content.to_string(),
        frontmatter: Default::default(),
        route: "guide".to_string(),
        source_file: dir.join("guide.md").to_string_lossy().into_owned(),
        unlisted: false,
    }
}

#[test]
fn images_are_found_outside_code_and_kept_inside_the_docs_dir() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    std::fs::create_dir_all(root.join("img")).unwrap();
    std::fs::write(root.join("img/shot.png"), b"png").unwrap();
    std::fs::write(root.join("logo.png"), b"logo").unwrap();
    let content = "# Guide\n\n![Shot](img/shot.png \"Title\")\n![Again](<img/shot.png>)\n\n![Logo](./logo.png#frag?x=1)\n![Missing](gone.png)\n![Up](../escape.png)\n![Abs](/static/a.png)\n![Remote](https://x/y.png)\n![Data](data:image/png;base64,AAAA)\n\n`![inline](inline.png)` and ``![two](two.png)``\n\n```md\n![fenced](fenced.png)\n```\n~~~\n![tilde](tilde.png)\n~~~\n";
    let found = doc_asset_sources(&page(&root, content));
    assert_eq!(
        found.assets,
        vec![
            ("img/shot.png".to_string(), root.join("img/shot.png")),
            ("./logo.png".to_string(), root.join("logo.png")),
        ]
    );
    assert_eq!(
        found.missing,
        ["gone.png", "../escape.png (escapes the docs directory)"]
    );
    let generated = MarkdownPage {
        source_file: String::new(),
        ..page(&root, "![x](x.png)")
    };
    assert_eq!(doc_asset_sources(&generated), DocAssets::default());
}

#[cfg(unix)]
#[test]
fn symlinked_images_are_never_published() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    std::fs::write(root.join("real.png"), b"x").unwrap();
    std::os::unix::fs::symlink(root.join("real.png"), root.join("link.png")).unwrap();
    let found = doc_asset_sources(&page(&root, "![L](link.png)"));
    assert_eq!(found.missing, ["link.png (symlinks are not published)"]);
    assert!(path_traverses_symlink(&root, &root.join("link.png")));
    assert!(!path_traverses_symlink(&root, &root.join("real.png")));
    assert!(path_traverses_symlink(&root, Path::new("/elsewhere")));
}

#[test]
fn code_spans_and_fences_are_blanked() {
    assert_eq!(blank_code_spans("a `b` c"), "a   c");
    assert_eq!(blank_code_spans("a ``b`c`` d"), "a   d");
    assert_eq!(blank_code_spans("open ` never"), "open ` never");
    assert_eq!(
        blank_fenced_code("a\n```md\n![x](x.png)\n```\nb\n"),
        "a\n b\n"
    );
    assert_eq!(blank_fenced_code("~~~\nx\n~~~~\ny"), " y");
    assert_eq!(blank_fenced_code("```\nopen\n"), "```\nopen\n");
    assert_eq!(blank_fenced_code("````\n```\nstill\n````\n"), " ");
}
