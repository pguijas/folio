//! `folio coverage` and `folio roadmap` as black-box runs: the tables, the
//! `--min` verdict, the missing-config and no-modules errors, the empty
//! roadmap note.

use std::fs;
use std::path::{Path, PathBuf};

mod common;

use common::Run;

fn folio(cwd: &Path, args: &[&str]) -> Run {
    common::folio(cwd, args, &[])
}

fn example_site() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../../docs/examples/generated-site")
        .canonicalize()
        .unwrap()
}

#[test]
fn coverage_table_verbose_list_and_min_threshold() {
    let project = example_site();
    let run = folio(&project, &["coverage"]);
    assert_eq!(run.code, 0, "{}", run.stdout);
    assert_eq!(
        run.stdout,
        "\n\
         \x20                   Documentation Coverage\n\
         ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┓\n\
         ┃ Module                     ┃ Total ┃ Documented ┃ Coverage ┃\n\
         ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━┩\n\
         │ example_package            │     1 │          0 │     0.0% │\n\
         │ example_package.arithmetic │     2 │          1 │    50.0% │\n\
         ├────────────────────────────┼───────┼────────────┼──────────┤\n\
         │ Total                      │     3 │          1 │    33.3% │\n\
         └────────────────────────────┴───────┴────────────┴──────────┘\n\
         \n"
    );

    let verbose = folio(&project, &["coverage", "--verbose"]);
    assert_eq!(verbose.code, 0);
    assert!(
        verbose
            .stdout
            .ends_with("└────────────────────────────┴───────┴────────────┴──────────┘\n\nUndocumented:\n  example_package\n  example_package.arithmetic\n\n"),
        "{}",
        verbose.stdout
    );

    let below = folio(&project, &["coverage", "--min", "80"]);
    assert_eq!(below.code, 1);
    assert!(
        below
            .diagnostics()
            .ends_with("Coverage 33.3% is below minimum 80.0%\n"),
        "{}",
        below.stdout
    );
    let above = folio(
        &project,
        &["coverage", "--min", "30.5", "--project-dir", "."],
    );
    assert_eq!(above.code, 0);
    assert!(!above.stdout.contains("below minimum"));

    // The positional directory works from elsewhere; --min 0 never fails.
    let elsewhere = tempfile::tempdir().unwrap();
    let positional = folio(
        elsewhere.path(),
        &["coverage", project.to_str().unwrap(), "--min", "0"],
    );
    assert_eq!(positional.code, 0, "{}", positional.stdout);
    assert!(positional.stdout.contains("│ Total"));
}

#[test]
fn coverage_errors_name_the_config_and_the_missing_modules() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    let missing = folio(&root, &["coverage"]);
    assert_eq!(missing.code, 1);
    assert_eq!(
        missing.diagnostics(),
        format!(
            "Error: Config file not found: {}/docs.yaml\n",
            root.display()
        )
    );

    fs::write(
        root.join("docs.yaml"),
        "project:\n  name: Empty\nsource:\n  python:\n    paths: [nowhere]\n",
    )
    .unwrap();
    let none = folio(&root, &["coverage"]);
    assert_eq!(none.code, 1);
    assert_eq!(
        none.diagnostics(),
        format!(
            "Warning: Python source path not found: {}/nowhere\nError: No Python modules found. Check source paths in docs.yaml.\n",
            root.display()
        )
    );

    // Only Python is counted in this release: other sources are refused.
    fs::write(
        root.join("docs.yaml"),
        "project:\n  name: Crate\nsource:\n  rust:\n    paths: [src/]\n",
    )
    .unwrap();
    let rust_only = folio(&root, &["coverage"]);
    assert_eq!(rust_only.code, 1);
    assert_eq!(
        rust_only.diagnostics(),
        "Error: folio coverage reads Python sources only in this release, and docs.yaml lists no source.python paths.\n"
    );
    assert!(rust_only.stdout.is_empty());
}

#[test]
fn roadmap_lists_phases_or_says_none_are_configured() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    fs::write(
        root.join("docs.yaml"),
        "project:\n  name: Demo\nroadmap:\n  phases:\n    - id: foundation\n      project: docs\n      title: Foundation\n      status: shipped\n      version: \"0.1\"\n      layer: Core\n      summary: The first release.\n      command: folio build\n    - id: next\n      title: Next\n      status: later\n      version: \"0.2\"\n      layer: Reach\n      summary: The one after.\n",
    )
    .unwrap();
    let run = folio(&root, &["roadmap"]);
    assert_eq!(run.code, 0, "{}", run.stdout);
    let lines: Vec<&str> = run.stdout.lines().collect();
    assert_eq!(lines[0], "");
    assert!(lines[1].trim() == "Demo Roadmap", "{}", lines[1]);
    assert_eq!(
        lines[3],
        "┃ Project ┃ Status  ┃ Version ┃ Title      ┃ Command     ┃"
    );
    assert_eq!(
        lines[5],
        "│ docs    │ shipped │ 0.1     │ Foundation │ folio build │"
    );
    assert_eq!(
        lines[6],
        "│         │ later   │ 0.2     │ Next       │             │"
    );
    assert_eq!(lines.last(), Some(&""), "a blank line closes the table");

    // The positional directory from elsewhere.
    let elsewhere = tempfile::tempdir().unwrap();
    let positional = folio(elsewhere.path(), &["roadmap", root.to_str().unwrap()]);
    assert_eq!(positional.code, 0);
    assert!(positional.stdout.contains("Demo Roadmap"));

    fs::write(
        root.join("docs.yaml"),
        "project:\n  name: Demo\nroadmap:\n  phases: []\n",
    )
    .unwrap();
    let empty = folio(&root, &["roadmap"]);
    assert_eq!(empty.code, 0);
    assert_eq!(empty.stdout, "No roadmap phases configured in docs.yaml.\n");

    let missing = folio(elsewhere.path(), &["roadmap"]);
    assert_eq!(missing.code, 1);
    assert!(missing
        .diagnostics()
        .starts_with("Error: Config file not found: "));
}
