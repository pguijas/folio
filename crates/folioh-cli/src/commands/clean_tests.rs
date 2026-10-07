use super::*;

#[test]
fn output_dir_must_stay_inside_the_project() {
    let dir = tempfile::tempdir().unwrap();
    let target = dir.path().canonicalize().unwrap();
    assert_eq!(
        resolve_output_dir(&target, "public", &[]).unwrap(),
        target.join("public")
    );
    assert_eq!(
        resolve_output_dir(&target, "", &[]).unwrap_err(),
        "Output directory must be a non-empty relative path"
    );
    assert_eq!(
        resolve_output_dir(&target, "/tmp/x", &[]).unwrap_err(),
        "Output directory must be relative to the project directory"
    );
    for outside in [".", "../x", "a/../.."] {
        assert_eq!(
            resolve_output_dir(&target, outside, &[]).unwrap_err(),
            "Output directory must stay within the project directory",
            "{outside}"
        );
    }
    assert_eq!(
        resolve_output_dir(&target, ".git", &[]).unwrap_err(),
        "Output directory '.git' must not contain the repository's .git directory; the build removes the output directory before writing to it"
    );
}

#[test]
fn output_dir_never_contains_a_source_root() {
    let dir = tempfile::tempdir().unwrap();
    let target = dir.path().canonicalize().unwrap();
    let sources = vec!["docs/".to_string(), "src/pkg".to_string()];
    for output in ["docs", "src", "src/pkg"] {
        let err = resolve_output_dir(&target, output, &sources).unwrap_err();
        assert!(
            err.contains("would delete the source directory"),
            "{output}: {err}"
        );
    }
    assert!(resolve_output_dir(&target, "_site", &sources).is_ok());
}

#[test]
fn raw_source_roots_reads_every_language_and_the_docs() {
    let raw: Value = serde_yaml_ng::from_str(
        "source:\n  docs: [guides/]\n  python: [src/]\n  javascript:\n    paths: [web/]\n  rust:\n    paths: [crates/]\n",
    )
    .unwrap();
    assert_eq!(
        raw_source_roots(&raw),
        ["guides/", "src/", "web/", "crates/"]
    );
    let raw: Value =
        serde_yaml_ng::from_str("source:\n  python:\n    paths: [lib/]\n    exclude: [lib/x]\n")
            .unwrap();
    assert_eq!(raw_source_roots(&raw), ["lib/"]);
    // Shapes the parser would reject still yield what they can.
    let raw: Value = serde_yaml_ng::from_str("source:\n  docs: 3\n  rust: [a]\n").unwrap();
    assert_eq!(raw_source_roots(&raw), ["a"]);
    assert!(raw_source_roots(&Value::Null).is_empty());
}
