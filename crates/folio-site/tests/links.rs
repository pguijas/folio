//! The link checker over real `.mdx` files in a temp content dir.

use std::collections::HashSet;
use std::path::Path;

use folio_site::links::{check_links, BrokenLink, LinkCheckInput};

fn write(dir: &Path, rel: &str, text: &str) {
    let path = dir.join(rel);
    std::fs::create_dir_all(path.parent().unwrap()).unwrap();
    std::fs::write(path, text).unwrap();
}

fn check(
    content: &Path,
    pages: &[&str],
    base: &str,
    site_routes: &[&str],
    static_root: Option<&Path>,
) -> Vec<BrokenLink> {
    let pages: Vec<String> = pages.iter().map(|p| p.to_string()).collect();
    let site_routes: HashSet<String> = site_routes.iter().map(|r| r.to_string()).collect();
    check_links(&LinkCheckInput {
        content_dir: content,
        pages: &pages,
        docs_route_base: base,
        site_routes: &site_routes,
        static_root,
    })
}

fn targets(broken: &[BrokenLink]) -> Vec<&str> {
    broken.iter().map(|b| b.target.as_str()).collect()
}

#[test]
fn page_links_resolve_against_known_routes() {
    let dir = tempfile::tempdir().unwrap();
    let content = dir.path().join("content");
    write(&content, "index.mdx", "# Home\n\nSee the [installation](./installation) guide.\n[GitHub](https://github.com/example/repo)\n[Jump](#details)\n");
    write(
        &content,
        "installation.mdx",
        "# Installation\n\nBack to [home](./index).\n",
    );
    assert!(check(&content, &["index", "installation"], "/docs", &[], None).is_empty());

    write(
        &content,
        "index.mdx",
        "# Home\n\nSee the [missing page](./nonexistent) here.\n",
    );
    let broken = check(&content, &["index", "installation"], "/docs", &[], None);
    assert_eq!(
        broken,
        vec![BrokenLink {
            source_page: "index".to_string(),
            target: "./nonexistent".to_string(),
            line_number: 3
        }]
    );
}

#[test]
fn absolute_docs_links_use_the_configured_base() {
    let dir = tempfile::tempdir().unwrap();
    let content = dir.path().join("content");
    write(
        &content,
        "index.mdx",
        "# Home\n\n[Guide](/docs/guide)\n[Missing](/docs/nope)\n",
    );
    write(&content, "guide.mdx", "# Guide\n");
    assert_eq!(
        targets(&check(&content, &["index", "guide"], "/docs", &[], None)),
        vec!["/docs/nope"]
    );

    write(
        &content,
        "index.mdx",
        "# Home\n\n[Guide](/reference/docs/guide)\n[Missing](/reference/docs/nope)\n",
    );
    assert_eq!(
        targets(&check(
            &content,
            &["index", "guide"],
            "/reference/docs",
            &[],
            None
        )),
        vec!["/reference/docs/nope"]
    );
}

#[test]
fn relative_links_resolve_from_the_page_directory() {
    let dir = tempfile::tempdir().unwrap();
    let content = dir.path().join("content");
    write(
        &content,
        "index.mdx",
        "# Home\n\n[Config](/docs/api-reference/folio/config)\n",
    );
    write(
        &content,
        "api-reference/folio/config.mdx",
        "# Config\n\n[Home](/docs/index)\n[Build](./build)\n",
    );
    let broken = check(
        &content,
        &["index", "api-reference/folio/config"],
        "/docs",
        &[],
        None,
    );
    assert_eq!(
        broken,
        vec![BrokenLink {
            source_page: "api-reference/folio/config".to_string(),
            target: "./build".to_string(),
            line_number: 4
        }]
    );

    let content = dir.path().join("content2");
    write(&content, "index.mdx", "# Home\n");
    write(
        &content,
        "guide/setup.mdx",
        "# Setup\n[Home](../index)\n[Bad](../nonexistent)\n",
    );
    let broken = check(&content, &["index", "guide/setup"], "/docs", &[], None);
    assert_eq!(
        broken,
        vec![BrokenLink {
            source_page: "guide/setup".to_string(),
            target: "../nonexistent".to_string(),
            line_number: 3
        }]
    );
}

#[test]
fn several_links_per_line_and_per_tree_are_reported_in_order() {
    let dir = tempfile::tempdir().unwrap();
    let content = dir.path().join("content");
    write(
        &content,
        "index.mdx",
        "See [a](./a) and [b](./b) for details.\n",
    );
    assert_eq!(
        targets(&check(&content, &["index", "a"], "/docs", &[], None)),
        vec!["./b"]
    );

    write(&content, "index.mdx", "# Home\n[Missing1](./gone1)\n");
    write(&content, "page.mdx", "# Page\n[Missing2](./gone2)\n");
    assert_eq!(
        targets(&check(&content, &["index", "page"], "/docs", &[], None)),
        vec!["./gone1", "./gone2"]
    );
}

#[test]
fn inline_code_extensions_anchors_and_attributes() {
    let dir = tempfile::tempdir().unwrap();
    let content = dir.path().join("content");
    write(&content, "index.mdx", "# Home\n\nExample image syntax: `![path](path)`\n[Guide](./guide.md)\n[Guide install](./guide#installation)\n");
    write(&content, "guide.mdx", "# Guide\n");
    assert!(check(&content, &["index", "guide"], "/docs", &[], None).is_empty());

    write(&content, "index.mdx", "# Home\n\n<FeatureCard title=\"Plugins\" href=\"/docs/plugins\" />\n<FeatureCard title=\"GitHub\" href=\"https://github.com\" />\n");
    let broken = check(&content, &["index"], "/docs", &[], None);
    assert_eq!(
        broken,
        vec![BrokenLink {
            source_page: "index".to_string(),
            target: "/docs/plugins".to_string(),
            line_number: 3
        }]
    );
}

#[test]
fn empty_content_dir_has_no_broken_links() {
    let dir = tempfile::tempdir().unwrap();
    let content = dir.path().join("content");
    std::fs::create_dir(&content).unwrap();
    assert!(check(&content, &[], "/docs", &[], None).is_empty());
}

#[test]
fn site_absolute_links_validate_against_site_routes_and_static_files() {
    let dir = tempfile::tempdir().unwrap();
    let content = dir.path().join("content");
    write(
        &content,
        "index.mdx",
        "[Roadmap](/roadmap) [Gallery](/gallery/) [Home](/) [Nope](/missing)",
    );
    assert_eq!(
        targets(&check(
            &content,
            &["index"],
            "/docs",
            &["/roadmap", "/gallery"],
            None
        )),
        vec!["/missing"]
    );

    write(&content, "index.mdx", "[Prototype](/_folio/gallery/demo/prototype.html) [Brief](/_folio/gallery/demo/brief.md#decision) [Missing](/_folio/gallery/demo/missing.html)");
    let public = dir.path().join("public");
    write(
        &public,
        "_folio/gallery/demo/prototype.html",
        "<!doctype html>",
    );
    write(&public, "_folio/gallery/demo/brief.md", "# Decision");
    assert_eq!(
        targets(&check(&content, &["index"], "/docs", &[], Some(&public))),
        vec!["/_folio/gallery/demo/missing.html"]
    );

    write(&content, "index.mdx", "[Secret](/../secret.txt)");
    std::fs::write(dir.path().join("secret.txt"), "private").unwrap();
    assert_eq!(
        targets(&check(&content, &["index"], "/docs", &[], Some(&public))),
        vec!["/../secret.txt"]
    );

    write(&content, "index.mdx", "[Home](/)");
    assert!(check(&content, &["index"], "/docs", &[], None).is_empty());
}

#[test]
fn images_are_not_links_and_directories_resolve_to_their_index() {
    let dir = tempfile::tempdir().unwrap();
    let content = dir.path().join("content");
    write(
        &content,
        "guide.mdx",
        "![The diagram](./diagram.png)\n\n![Remote](https://x.test/a.png)\n",
    );
    assert!(check(&content, &["guide"], "/docs", &[], None).is_empty());

    write(
        &content,
        "cli.mdx",
        "See [Gallery](./plugins/gallery) and [gone](./plugins/nope).\n",
    );
    assert_eq!(
        targets(&check(
            &content,
            &["cli", "plugins/gallery/index"],
            "/docs",
            &[],
            None
        )),
        vec!["./plugins/nope"]
    );
}

#[test]
fn href_props_are_checked_outside_fenced_code() {
    let dir = tempfile::tempdir().unwrap();
    let content = dir.path().join("content");
    write(
        &content,
        "index.mdx",
        "# Home\n\n<ClassOverview bases={[{ name: \"A\", href: \"/docs/guide\" }, { name: \"B\", href: '/docs/nope' }]} />\n\n```yaml\nhref: \"/docs/fenced-nope\"\n```\n",
    );
    write(&content, "guide.mdx", "# Guide\n");
    let broken = check(&content, &["index", "guide"], "/docs", &[], None);
    assert_eq!(
        broken,
        vec![BrokenLink {
            source_page: "index".to_string(),
            target: "/docs/nope".to_string(),
            line_number: 3
        }]
    );
}
