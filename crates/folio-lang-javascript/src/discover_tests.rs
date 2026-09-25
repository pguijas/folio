use super::*;

#[test]
fn a_root_publishes_its_sources_and_names_index_after_its_directory() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    let write = |rel: &str| {
        let path = root.join(rel);
        std::fs::create_dir_all(path.parent().expect("a parent")).unwrap();
        std::fs::write(path, "export function f() {}\n").unwrap();
    };
    write("index.js");
    write("util.mjs");
    write("compat.cjs");
    write("lib/helpers.js");
    write("lib/nested/index.js");
    write("widget.jsx");
    write("node_modules/pkg/index.js");

    let found = discover(std::slice::from_ref(&root), &[]);
    let names: Vec<&str> = found
        .files
        .iter()
        .map(|file| file.module_name.as_str())
        .collect();
    let root_name = root.file_name().unwrap().to_string_lossy().to_string();
    assert_eq!(
        names,
        ["compat", &root_name, "lib.helpers", "lib.nested", "util"]
    );
    assert_eq!(found.warnings.len(), 1);
    assert!(found.warnings[0].ends_with("widget.jsx"));
}

#[test]
fn an_excluded_directory_publishes_nothing() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    std::fs::create_dir_all(root.join("vendor")).unwrap();
    std::fs::write(root.join("app.js"), "export function app() {}\n").unwrap();
    std::fs::write(root.join("vendor/dep.js"), "export function dep() {}\n").unwrap();

    let excludes = vec![root.join("vendor").display().to_string()];
    let found = discover(&[root], &excludes);
    let names: Vec<&str> = found
        .files
        .iter()
        .map(|file| file.module_name.as_str())
        .collect();
    assert_eq!(names, ["app"]);
}

#[test]
fn built_output_is_not_source_and_typescript_is_reported_once() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    let write = |rel: &str| {
        let path = root.join(rel);
        std::fs::create_dir_all(path.parent().expect("a parent")).unwrap();
        std::fs::write(path, "export function f() {}\n").unwrap();
    };
    write("app.js");
    write("dist/app.min.js");
    write("build/chunk.js");
    write(".build/content/x.js");
    write("types/app.d.ts");
    write("types/extra.ts");

    let found = discover(std::slice::from_ref(&root), &[]);
    let names: Vec<&str> = found
        .files
        .iter()
        .map(|file| file.module_name.as_str())
        .collect();
    assert_eq!(names, ["app"]);
    assert_eq!(found.warnings.len(), 1, "{:?}", found.warnings);
    assert!(found.warnings[0]
        .starts_with("TypeScript is not read in this release; skipping 2 files under "));
    assert!(found.warnings[0].ends_with("app.d.ts)"));

    // A root that is itself a skipped name is read: it was asked for.
    let dist = discover(&[root.join("dist")], &[]);
    assert_eq!(dist.files.len(), 1);
}

#[test]
fn two_files_that_publish_one_module_keep_the_first_and_warn() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    let write = |rel: &str| {
        let path = root.join(rel);
        std::fs::create_dir_all(path.parent().expect("a parent")).unwrap();
        std::fs::write(path, "export function f() {}\n").unwrap();
    };
    write("pkg/index.cjs");
    write("pkg/index.mjs");
    write("util.js");
    write("util/index.js");

    let found = discover(std::slice::from_ref(&root), &[]);
    let files: Vec<(&str, String)> = found
        .files
        .iter()
        .map(|file| {
            let relative = file.path.strip_prefix(&root).unwrap();
            (file.module_name.as_str(), relative.display().to_string())
        })
        .collect();
    assert_eq!(
        files,
        [
            ("pkg", "pkg/index.cjs".to_string()),
            ("util", "util/index.js".to_string())
        ]
    );
    assert_eq!(found.warnings.len(), 2, "{:?}", found.warnings);
    assert!(found.warnings[0].contains("index.mjs publishes the module `pkg` that "));
    assert!(found.warnings[1].contains("util.js publishes the module `util` that "));
}
