//! `docs/examples/generated-site` through the whole crate: the pages a build
//! must write, byte for byte against the checked-in example output, the symbol
//! index, the mirror, the llms files and the coverage numbers.

use std::fs;
use std::path::{Path, PathBuf};

use folio_config::load_docs_config;
use folio_docs::{
    aggregate, analyze_modules, api_reference_index_to_mdx, below_minimum, build_symbol_index,
    coverage_level, generate_llms_full_txt, generate_llms_txt, module_route, module_to_mdx,
    parse_doc_sources, parse_language_sources, CoverageLevel, LlmsContext, RenderOptions,
};
use folio_mdx::mdx_to_markdown;

fn docs_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

/// The pages this crate must write, checked in beside the test that compares
/// them; `folio-cli` compares the built site against the same files.
fn golden_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/generated_site")
}

/// Compare `actual` against the golden file `name`, or rewrite it when
/// `FOLIO_UPDATE_GOLDEN` is set: the one refresh switch for every golden.
fn golden(name: &str, actual: &str) {
    let path = golden_root().join(name);
    if std::env::var_os("FOLIO_UPDATE_GOLDEN").is_some() {
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(&path, actual).unwrap();
    }
    let expected = fs::read_to_string(&path).unwrap_or_else(|e| panic!("{}: {e}", path.display()));
    assert_eq!(actual, expected, "{name}");
}

#[test]
fn generated_site_matches_the_golden_files() {
    let project = docs_root()
        .join("docs/examples/generated-site")
        .canonicalize()
        .unwrap();
    let config = load_docs_config(&project.join("docs.yaml"))
        .unwrap()
        .config
        .resolve_paths(&project)
        .unwrap();

    let parsed = parse_language_sources(&config).unwrap();
    assert!(parsed.warnings.is_empty(), "{:?}", parsed.warnings);
    assert!(parsed.missing_paths.is_empty());
    assert_eq!(parsed.scanned_paths, [project.join("src/example_package")]);
    let names: Vec<&str> = parsed.modules.iter().map(|m| m.name.as_str()).collect();
    assert_eq!(names, ["example_package", "example_package.arithmetic"]);
    for module in &parsed.modules {
        assert!(module
            .source_file
            .starts_with(&format!("{}/", project.display())));
    }

    let index = build_symbol_index(&parsed.modules, &config.template.docs_route_base);
    assert_eq!(
        serde_json::to_string(&index).unwrap(),
        r#"{"example_package":"/docs/api-reference/example_package","example_package.arithmetic":"/docs/api-reference/example_package/arithmetic","example_package.arithmetic.add":"/docs/api-reference/example_package/arithmetic#add"}"#
    );

    let source_root = format!("{}/", project.display());
    let opts = RenderOptions {
        repo_url: &config.project.repo,
        source_root: &source_root,
        source_ref: Some(&config.project.repo_ref),
        symbol_index: Some(&index),
    };
    for module in &parsed.modules {
        let route = module_route(module);
        golden(&format!("{route}.mdx"), &module_to_mdx(module, &opts));
    }
    golden(
        "api-reference/index.mdx",
        &api_reference_index_to_mdx(&parsed.modules),
    );
    // The mirror reads as the page: headings without their source link or
    // id, the parameter table as a Markdown table.
    assert_eq!(
        mdx_to_markdown(&module_to_mdx(&parsed.modules[1], &opts)),
        "# example_package.arithmetic\n\n## Functions\n\n### `add`\n\n```python\ndef add(left: int, right: int) -> int\n```\n\nAdd two integers.\n\n| Parameter | Type | Default | Description |\n| --- | --- | --- | --- |\n| `left` | `int` |  | First number. |\n| `right` | `int` |  | Second number. |\n\n**Returns:** `int` - The sum of both numbers.\n"
    );

    let docs = parse_doc_sources(&config).unwrap();
    assert!(docs.warnings.is_empty());
    let routes: Vec<&str> = docs.docs.iter().map(|d| d.route.as_str()).collect();
    assert_eq!(routes, ["cli", "components", "index"]);
    let project_dir = project.to_string_lossy();
    let ctx = LlmsContext {
        project_name: &config.project.name,
        landing_hero_description: "",
        site_url: &config.project.url,
        docs_route_base: &config.template.docs_route_base,
        project_dir: &project_dir,
        ..LlmsContext::default()
    };
    golden(
        "llms.txt",
        &generate_llms_txt(&ctx, &parsed.modules, &docs.docs),
    );
    golden(
        "llms-full.txt",
        &generate_llms_full_txt(&parsed.modules, &docs.docs, Some(&ctx)),
    );

    // `arithmetic.py` has no module docstring, so its row is 2/1: a module
    // without a docstring counts as one undocumented item.
    let results = analyze_modules(&parsed.modules);
    let rows: Vec<(&str, usize, usize, String)> = results
        .iter()
        .map(|(name, r)| {
            (
                name.as_str(),
                r.total,
                r.documented,
                format!("{:.1}%", r.percentage()),
            )
        })
        .collect();
    assert_eq!(
        rows,
        [
            ("example_package", 1, 0, "0.0%".to_string()),
            ("example_package.arithmetic", 2, 1, "50.0%".to_string()),
        ]
    );
    assert_eq!(
        coverage_level(results["example_package"].percentage()),
        CoverageLevel::Low
    );
    assert_eq!(
        coverage_level(results["example_package.arithmetic"].percentage()),
        CoverageLevel::Medium
    );
    let total = aggregate(&results);
    assert_eq!(
        (
            total.total,
            total.documented,
            format!("{:.1}%", total.percentage())
        ),
        (3, 1, "33.3%".to_string())
    );
    assert_eq!(coverage_level(total.percentage()), CoverageLevel::Low);
    assert_eq!(
        total.undocumented,
        ["example_package", "example_package.arithmetic"]
    );
    assert_eq!(
        below_minimum(total.percentage(), 80.0).as_deref(),
        Some("Coverage 33.3% is below minimum 80.0%")
    );
}
