//! The real toolchain end to end on `docs/examples/generated-site`:
//! bundled template, pnpm install, next build, static export, rewriter, LLM
//! files. Ignored by default (network + minutes); run locally with
//! `cargo test -p folio-site --test e2e_export -- --ignored --nocapture`.

mod common;

use std::collections::BTreeSet;
use std::path::Path;
use std::time::Instant;

use folio_site::builder::SiteBuilder;
use folio_site::runtime::NextRuntime;
use folio_site::sidebar::{generate_meta_files, SidebarInput, SidebarPage};
use folio_site::template::resolve_template_dir;

#[test]
#[ignore = "runs pnpm install and next build on the generated-site example; run locally with --ignored"]
fn generated_site_example_exports_end_to_end() {
    let started = Instant::now();
    let dir = tempfile::tempdir().unwrap();
    let project = dir.path().join("generated-site");
    let source = Path::new(env!("CARGO_MANIFEST_DIR")).join("../../docs/examples/generated-site");
    folio_site::fs::copy_tree_all(&source, &project).unwrap();
    let loaded = folio_config::load_docs_config(&project.join("docs.yaml")).unwrap();
    let mut config = loaded.config;
    folio_plugins::Plugin::configure(
        &folio_plugins::LandingPlugin,
        &mut config,
        &loaded.raw,
        &mut Vec::new(),
    )
    .unwrap();
    let config = config.resolve_paths(&project).unwrap();
    let build_dir = project.join(".build");
    let template = resolve_template_dir(&config, &build_dir).unwrap();
    let mut builder = SiteBuilder::new(
        &config,
        &template.dir,
        &build_dir,
        Box::new(NextRuntime::default()),
    );
    let injection = builder.prepare(true).unwrap();
    assert!(injection.warnings.is_empty(), "{:?}", injection.warnings);

    let scan = folio_mdx::parse_markdown_directory(&project.join("docs"), "").unwrap();
    for page in &scan.pages {
        builder
            .write_page(&page.route, &folio_mdx::markdown_to_mdx(page))
            .unwrap();
    }
    let sidebar_pages: Vec<SidebarPage> = scan
        .pages
        .iter()
        .map(|p| SidebarPage {
            route: &p.route,
            title: p.frontmatter.get("title").and_then(|t| t.as_str()),
            unlisted: p.unlisted,
        })
        .collect();
    let meta = generate_meta_files(&SidebarInput {
        nav: &config.nav,
        modules: &[],
        pages: &sidebar_pages,
        default_collapsed: config.sidebar.default_collapsed,
    });
    for (path, text) in &meta {
        let directory = path.strip_suffix("/_meta.ts").unwrap_or("");
        builder.write_meta(directory, text).unwrap();
    }
    builder.write_search_index().unwrap();
    let keys: BTreeSet<String> = folio_plugins::contract_config_keys()
        .into_iter()
        .map(str::to_string)
        .collect();
    builder
        .write_authoring_contract(&keys, "2026-09-18T00:00:00Z")
        .unwrap();
    let prepared = started.elapsed();

    let installed = builder.install_deps(&mut |_| {}).unwrap().installed;
    let after_install = started.elapsed();
    let export = builder
        .export_static_site(
            Some("# Example Package\n"),
            Some("# Example Package full\n"),
        )
        .unwrap();
    let total = started.elapsed();
    eprintln!(
        "prepare {prepared:?}; install (ran: {installed}) {:?}; export {:?}; total {total:?}",
        after_install - prepared,
        total - after_install
    );
    eprintln!("warnings: {:?}", export.warnings);
    eprintln!(
        "last build lines: {:?}",
        export.output_lines.iter().rev().take(5).collect::<Vec<_>>()
    );

    let out = Path::new(&config.output_dir);
    for rel in [
        "index.html",
        "docs/index.html",
        "docs/cli/index.html",
        "docs/components/index.html",
        "_folio/markdown/index.md",
        "_folio/markdown/cli.md",
        "_folio/contract.json",
        "llms.txt",
        "llms-full.txt",
        "robots.txt",
        "sitemap.xml",
        "_pagefind/pagefind.js",
        "_folio-search.js",
    ] {
        assert!(out.join(rel).exists(), "missing {rel}");
    }
    let robots = common::read(&out.join("robots.txt"));
    assert!(
        robots.contains("# llms.txt: /llms.txt\n")
            && robots.contains("# llms-full.txt: /llms-full.txt\n"),
        "{robots}"
    );
    assert_eq!(export.llm_files, ["llms.txt", "llms-full.txt"]);
    let home = common::read(&out.join("docs/cli/index.html"));
    assert!(home.contains("Example Package") && !home.contains("__PROJECT_NAME__"));
    assert!(
        home.contains("src=\"../../_next/") || home.contains("src=\"./_next/"),
        "relative chunk srcs expected"
    );
    assert!(build_dir.join(".folio-build.log").is_file() && !export.output_lines.is_empty());
}
