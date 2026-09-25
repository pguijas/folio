//! `resolve_output_dir`, `resolve_contained_dir` and lenient canonicalisation
//! against a real temporary project.

use std::fs;
use std::path::{Path, PathBuf};

use folio_config::paths::{canonicalize_lenient, resolve_contained_dir, resolve_output_dir};

fn project() -> (tempfile::TempDir, PathBuf) {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    (dir, root)
}

#[test]
fn canonicalize_lenient_resolves_the_existing_prefix_and_collapses_the_rest() {
    let (_dir, root) = project();
    fs::create_dir_all(root.join("a/b")).unwrap();
    let raw = _dir.path().join("a/b/../c/./d/../e");
    assert_eq!(canonicalize_lenient(&raw), root.join("a/c/e"));
    // An existing symlinked prefix is resolved through the OS.
    #[cfg(unix)]
    {
        std::os::unix::fs::symlink(root.join("a"), root.join("link")).unwrap();
        assert_eq!(
            canonicalize_lenient(&root.join("link/b/missing")),
            root.join("a/b/missing")
        );
    }
    // A relative path is anchored on the current directory.
    let cwd = std::env::current_dir().unwrap().canonicalize().unwrap();
    assert_eq!(canonicalize_lenient(Path::new("nope/../x")), cwd.join("x"));
}

#[test]
fn resolve_output_dir_accepts_a_sibling_of_the_sources() {
    let (_dir, root) = project();
    fs::create_dir_all(root.join("_site")).unwrap();
    let out = resolve_output_dir(&root, "_site", &["src/", "docs/"]).unwrap();
    assert_eq!(out, root.join("_site"));
    // Nested output and no sources also pass; the raw text is joined lexically.
    assert_eq!(
        resolve_output_dir(&root, "build/out/", &[]).unwrap(),
        root.join("build/out")
    );
}

#[test]
fn resolve_output_dir_refuses_what_the_build_would_destroy() {
    let (_dir, root) = project();
    let abs = root.join("outside").to_string_lossy().into_owned();
    let sources = ["src/", "docs/", "crates/core"];
    for (output, message) in [
        ("", "Output directory must be a non-empty relative path"),
        ("   ", "Output directory must be a non-empty relative path"),
        (abs.as_str(), "Output directory must be relative to the project directory"),
        (".", "Output directory must stay within the project directory"),
        ("./", "Output directory must stay within the project directory"),
        ("../outside", "Output directory must stay within the project directory"),
        ("a/..", "Output directory must stay within the project directory"),
        (
            ".git",
            "Output directory '.git' must not contain the repository's .git directory; the build removes the output directory before writing to it",
        ),
        (
            ".git/objects",
            "Output directory '.git/objects' must not be inside the repository's .git directory; the build removes the output directory before writing to it",
        ),
        (
            "docs",
            "Output directory 'docs' would delete the source directory 'docs/'; the build removes the output directory before writing to it. Choose an output path that is not a source directory and does not contain one",
        ),
        (
            "src",
            "Output directory 'src' would delete the source directory 'src/'; the build removes the output directory before writing to it. Choose an output path that is not a source directory and does not contain one",
        ),
        (
            "crates",
            "Output directory 'crates' would delete the source directory 'crates/core'; the build removes the output directory before writing to it. Choose an output path that is not a source directory and does not contain one",
        ),
    ] {
        let err = resolve_output_dir(&root, output, &sources).unwrap_err();
        assert_eq!(err.to_string(), message, "output {output:?}");
    }
    // Blank source entries are skipped.
    assert!(resolve_output_dir(&root, "_site", &["", "  "]).is_ok());
}

#[test]
fn resolve_contained_dir_happy_path_and_must_exist() {
    let (_dir, root) = project();
    let target = root.join("docs/theme");
    fs::create_dir_all(&target).unwrap();
    let out = root.join("_site");

    assert_eq!(
        resolve_contained_dir(Path::new("docs/theme"), &root, &out, "theme.package", true).unwrap(),
        target
    );
    // Absolute paths inside the project are accepted as-is.
    assert_eq!(
        resolve_contained_dir(&target, &root, &out, "theme.package", true).unwrap(),
        target
    );
    let err = resolve_contained_dir(Path::new("missing"), &root, &out, "theme.package", true)
        .unwrap_err();
    assert_eq!(
        err.to_string(),
        format!(
            "theme.package does not exist: {}",
            root.join("missing").display()
        )
    );
    assert_eq!(
        resolve_contained_dir(Path::new("missing"), &root, &out, "theme.package", false).unwrap(),
        root.join("missing")
    );
    // The project root itself is allowed.
    assert_eq!(
        resolve_contained_dir(Path::new("."), &root, &out, "template.path", false).unwrap(),
        root
    );
}

#[test]
fn resolve_contained_dir_rejects_escapes() {
    let (_dir, root) = project();
    let out = root.join("_site");
    let outside = root
        .parent()
        .unwrap()
        .join("evil-theme")
        .to_string_lossy()
        .into_owned();
    for (raw, message) in [
        (
            "../outside",
            "template.path must stay within the project directory",
        ),
        (
            outside.as_str(),
            "template.path must stay within the project directory",
        ),
        (
            ".build",
            "template.path cannot point inside the .build directory",
        ),
        (
            ".build/theme",
            "template.path cannot point inside the .build directory",
        ),
        (
            "_site",
            "template.path cannot point inside the output directory",
        ),
        (
            "_site/theme",
            "template.path cannot point inside the output directory",
        ),
    ] {
        let err =
            resolve_contained_dir(Path::new(raw), &root, &out, "template.path", false).unwrap_err();
        assert_eq!(err.to_string(), message, "raw {raw:?}");
        assert!(
            matches!(err, folio_config::ConfigError::Field { ref field, .. } if field == "template.path")
        );
    }
}
