//! `parse_markdown_directory` on a temporary docs tree: routes, README to
//! index, the `.rst` warning, the route prefix.

use std::fs;
use std::path::Path;

use folio_mdx::{parse_markdown_directory, parse_markdown_file, RST_WARNING};

fn write(dir: &Path, name: &str, text: &str) {
    let path = dir.join(name);
    fs::create_dir_all(path.parent().unwrap()).unwrap();
    fs::write(path, text).unwrap();
}

#[test]
fn scans_recursively_in_sorted_order_and_routes_readmes_as_index() {
    let tmp = tempfile::tempdir().unwrap();
    let docs = tmp.path().join("docs");
    write(&docs, "README.md", "# Home\n\nWelcome.\n");
    write(&docs, "install.md", "# Installation\n\nSteps here.\n");
    write(&docs, "guides/README.md", "# Guides\n\nGuide index.\n");
    write(
        &docs,
        "guides/quickstart.md",
        "# Quickstart\n\nFast start.\n",
    );
    write(&docs, "notes.txt", "ignored\n");

    let scan = parse_markdown_directory(&docs, "").unwrap();
    let routes: Vec<&str> = scan.pages.iter().map(|p| p.route.as_str()).collect();
    assert_eq!(
        routes,
        ["index", "guides/index", "guides/quickstart", "install"]
    );
    assert!(scan.warnings.is_empty());
    let quickstart = &scan.pages[2];
    assert_eq!(
        quickstart.source_file,
        docs.join("guides/quickstart.md").to_string_lossy()
    );
    assert_eq!(quickstart.frontmatter["title"], "Quickstart");
    assert_eq!(quickstart.content, "# Quickstart\n\nFast start.");

    let prefixed = parse_markdown_directory(&docs, "agents").unwrap();
    let routes: Vec<&str> = prefixed.pages.iter().map(|p| p.route.as_str()).collect();
    assert_eq!(
        routes,
        [
            "agents/index",
            "agents/guides/index",
            "agents/guides/quickstart",
            "agents/install"
        ]
    );
}

#[test]
fn warns_once_that_rst_is_migration_only_and_ignores_the_files() {
    let tmp = tempfile::tempdir().unwrap();
    let docs = tmp.path().join("docs");
    write(&docs, "index.md", "# Home\n\nWelcome.\n");
    write(&docs, "legacy.rst", "Legacy\n======\n");
    write(&docs, "old/more.rst", "More\n====\n");

    let scan = parse_markdown_directory(&docs, "").unwrap();
    let routes: Vec<&str> = scan.pages.iter().map(|p| p.route.as_str()).collect();
    assert_eq!(routes, ["index"]);
    assert_eq!(scan.warnings, [RST_WARNING]);
    assert!(RST_WARNING.contains("convert .rst files to Markdown"));
}

#[test]
fn file_reader_uses_the_stem_as_route_and_reports_errors_with_the_path() {
    let tmp = tempfile::tempdir().unwrap();
    write(
        tmp.path(),
        "intro.md",
        "# Introduction\n\nWelcome to the project.\n",
    );
    let page = parse_markdown_file(&tmp.path().join("intro.md")).unwrap();
    assert_eq!(page.route, "intro");
    assert_eq!(page.frontmatter["title"], "Introduction");
    assert!(page.content.contains("# Introduction"));

    write(
        tmp.path(),
        "crlf.md",
        "---\r\ntitle: Authored\r\n---\r\n\r\n# Heading\r\n\r\nBody {x}.\r\n",
    );
    let crlf = parse_markdown_file(&tmp.path().join("crlf.md")).unwrap();
    assert_eq!(crlf.frontmatter["title"], "Authored");
    assert_eq!(crlf.content, "# Heading\n\nBody {x}.");

    let missing = parse_markdown_file(&tmp.path().join("missing.md")).unwrap_err();
    assert!(missing
        .to_string()
        .starts_with(&tmp.path().join("missing.md").to_string_lossy().to_string()));

    write(tmp.path(), "bad.md", "---\n- not\n- a map\n---\n# X\n");
    let bad = parse_markdown_file(&tmp.path().join("bad.md")).unwrap_err();
    assert!(
        bad.to_string().contains("bad.md: invalid frontmatter"),
        "{bad}"
    );
    let bad_dir = parse_markdown_directory(tmp.path(), "").unwrap_err();
    assert!(bad_dir.to_string().contains("invalid frontmatter"));
}
