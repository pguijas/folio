use super::*;
use crate::runtime::NoopRuntime;

#[test]
fn search_index_reuses_a_cached_document_for_an_unchanged_signature() {
    let dir = tempfile::tempdir().unwrap();
    let mapping: serde_yaml_ng::Mapping =
        serde_yaml_ng::from_str("project:\n  name: Search\noutput: out\n").unwrap();
    let config = folio_config::parse_docs_config_with(&mapping, dir.path(), "", &mut Vec::new())
        .unwrap()
        .resolve_paths(dir.path())
        .unwrap();
    let build = dir.path().join("build");
    let mut builder = SiteBuilder::new(
        &config,
        &dir.path().join("template"),
        &build,
        Box::new(NoopRuntime),
    );
    builder.write_page("guide", "# Guide\n\nBody.").unwrap();
    builder.write_search_index().unwrap();
    let page = build.join("content/guide.mdx");
    let (signature, _) = builder.search_documents.get(&page).cloned().unwrap();
    let fake = SearchDocument {
        url: "/docs/guide/".into(),
        title: "Cached title".into(),
        content: "cached".into(),
    };
    builder
        .search_documents
        .insert(page.clone(), (signature, fake));
    builder.write_search_index().unwrap();
    let index = std::fs::read_to_string(build.join("lib/search-index.ts")).unwrap();
    assert!(
        index.contains("Cached title"),
        "cached document not reused:\n{index}"
    );
    assert!(!index.contains("Body."));
    // Any signature change (here a rewrite) drops the cached document.
    std::fs::write(&page, "# Guide\n\nChanged.").unwrap();
    builder.write_search_index().unwrap();
    let index = std::fs::read_to_string(build.join("lib/search-index.ts")).unwrap();
    assert!(!index.contains("Cached title") && index.contains("Changed."));
}
