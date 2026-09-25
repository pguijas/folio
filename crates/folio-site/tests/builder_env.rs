//! Builder behaviours that read `FOLIO_BASE_PATH`; isolated in their own process.

mod common;

use folio_site::builder::PreviewBuildRequest;

#[test]
fn base_path_env_feeds_robots_pointers_nested_example_builds_and_their_digest() {
    let dir = tempfile::tempdir().unwrap();
    std::env::set_var("FOLIO_BASE_PATH", "/mylib");
    let config = common::config(dir.path(), "project:\n  name: MyLib\n");
    let output = std::path::Path::new(&config.output_dir).to_path_buf();
    common::write(&output, "robots.txt", "User-Agent: *\nAllow: /\n");
    let build = dir.path().join("build");
    let builder = common::builder(&config, &dir.path().join("template"), &build);
    assert_eq!(builder.base_path(), "/mylib");
    builder
        .write_llm_files(Some("# MyLib\n"), None, false)
        .unwrap();
    let robots = common::read(&output.join("robots.txt"));
    assert!(robots.contains("# llms.txt: /mylib/llms.txt\n") && !robots.contains("llms-full.txt"));

    std::env::set_var("FOLIO_BASE_PATH", "/folio");
    let builder = common::builder(&config, &dir.path().join("template"), &build);
    let example = dir.path().join("docs/examples/sample-preview");
    std::fs::create_dir_all(&example).unwrap();
    let target = build.join("public/_folio/examples/sample-preview");
    let mut seen = Vec::new();
    builder
        .build_preview_example_project(&example, &target, &mut |request: PreviewBuildRequest| {
            seen.push((request, std::env::var("FOLIO_BASE_PATH").unwrap()));
            Ok(())
        })
        .unwrap();
    assert_eq!(
        seen,
        vec![(
            PreviewBuildRequest {
                project_dir: example.clone(),
                output_dir: target,
                build_dir: build.join(".preview-examples/sample-preview"),
                base_path: "/folio/_folio/examples/sample-preview".to_string(),
            },
            "/folio/_folio/examples/sample-preview".to_string()
        )]
    );
    assert_eq!(std::env::var("FOLIO_BASE_PATH").unwrap(), "/folio");

    // The nested build bakes the base path in, so a new one rebuilds it.
    let examples = dir.path().join("docs/examples");
    std::fs::write(example.join("docs.yaml"), "project:\n  name: Sample\n").unwrap();
    let mut run = |request: PreviewBuildRequest| {
        std::fs::create_dir_all(&request.output_dir).unwrap();
        std::fs::write(request.output_dir.join("index.html"), "<html></html>").unwrap();
        Ok(())
    };
    let mut counts = Vec::new();
    for base in ["/one", "/one", "/two"] {
        std::env::set_var("FOLIO_BASE_PATH", base);
        let builder = common::builder(&config, &dir.path().join("template"), &build);
        let summary = builder.write_preview_examples(&examples, &mut run).unwrap();
        counts.push((summary.built, summary.reused));
    }
    assert_eq!(counts, [(1, 0), (0, 1), (1, 0)]);
}
