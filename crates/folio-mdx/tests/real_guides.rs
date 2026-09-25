//! Folio's own guides through mermaid conversion and the mirror: the real
//! pages the site publishes must stay useful to agents.

use std::fs;
use std::path::PathBuf;

use folio_mdx::{convert_mermaid_blocks, mdx_to_markdown};

fn guide(name: &str) -> String {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../../docs/guide")
        .join(name);
    fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {e}", path.display()))
}

#[test]
fn guide_index_mirror_keeps_mermaid_and_feature_cards() {
    let markdown = mdx_to_markdown(&convert_mermaid_blocks(&guide("index.md")));

    assert!(markdown.contains("```mermaid\nflowchart LR"));
    assert!(markdown.contains("Parse --> IRNode[\"◇ IR objects\"]"));
    assert!(!markdown.contains("`} />"));
    assert!(!markdown.contains("<Mermaid"));
    assert!(markdown.contains("- **[Automatic API reference](/docs/docstrings)**:"));
    assert!(markdown.contains("Point Folio at your source directories"));
    assert!(!markdown.contains("<FeatureCard"));
}

#[test]
fn why_folio_mirror_keeps_children_and_code_but_drops_prop_data() {
    let markdown = mdx_to_markdown(&guide("why-folio.md"));

    assert!(markdown.contains("Documentation rots because it lives apart from the code."));
    assert!(markdown.contains("### Why Folio instead of Sphinx or MkDocs Material?"));
    assert!(markdown.contains("Same job — parse Python source into reference docs"));
    assert!(markdown.contains("`<Callout>`"));
    assert!(markdown.contains("`<Swot>`"));
    assert!(!markdown.contains("stats={["));
    assert!(!markdown.contains("strengths={["));
}
