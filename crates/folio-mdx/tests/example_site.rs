//! The `docs/examples/generated-site` guides through the whole crate: inferred
//! frontmatter, the emitted MDX and the Markdown mirror.

use std::path::PathBuf;

use folio_mdx::{markdown_to_mdx, mdx_to_markdown, parse_markdown_directory};

fn example_docs() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../../docs/examples/generated-site/docs")
}

#[test]
fn generated_site_docs_get_titles_descriptions_mdx_and_mirrors() {
    let scan = parse_markdown_directory(&example_docs(), "").unwrap();
    let routes: Vec<&str> = scan.pages.iter().map(|p| p.route.as_str()).collect();
    assert_eq!(routes, ["cli", "components", "index"]);
    let [cli, components, index] = scan.pages.as_slice() else {
        unreachable!()
    };

    assert_eq!(index.frontmatter["title"], "Example docs");
    assert_eq!(
        index.frontmatter["description"],
        "This sample project shows the kind of static documentation site Folio generates from a small Python package."
    );
    let index_mdx = markdown_to_mdx(index);
    assert!(index_mdx.starts_with(
        "---\ndescription: This sample project shows the kind of static documentation site Folio generates from a small Python package.\ntitle: Example docs\n---\n\n# Example docs\n\n"
    ));
    assert!(index_mdx.ends_with("compare the generated API reference with the Python source.\n"));
    assert_eq!(
        &index_mdx[index_mdx.find("\n\n# ").unwrap() + 2..],
        format!("{}\n", index.content)
    );

    assert_eq!(cli.frontmatter["title"], "CLI reference");
    let cli_mdx = markdown_to_mdx(cli);
    assert!(cli_mdx.starts_with(
        "---\ndescription: 'Run the local preview server while editing:'\ntitle: CLI reference\n---\n\n# CLI reference\n"
    ));
    assert_eq!(cli_mdx.matches("```bash\n").count(), 2);
    assert!(cli_mdx.contains("```bash\nfolio serve --port 4321\n```"));

    assert_eq!(components.frontmatter["title"], "Components");
    assert_eq!(
        components.frontmatter["description"],
        "Use small MDX components when prose needs a clearer shape."
    );
    let components_mdx = markdown_to_mdx(components);
    assert!(components_mdx.contains("\n<Callout title=\"Tip\">\n  Keep examples short. The preview should support the explanation, not replace the documentation.\n</Callout>\n"));
    assert!(
        components_mdx.contains("```python\nfrom example_package import add\n\nadd(2, 3)\n```\n")
    );
    assert_eq!(
        mdx_to_markdown(&components_mdx),
        "# Components\n\nUse small MDX components when prose needs a clearer shape.\n\n**Tip**\n\n  Keep examples short. The preview should support the explanation, not replace the documentation.\n\n```python\nfrom example_package import add\n\nadd(2, 3)\n```\n"
    );
}
