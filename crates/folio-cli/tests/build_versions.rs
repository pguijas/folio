//! `folio build-versions` as black-box runs with the frontend runtime
//! stubbed: the feature gate, the empty-versions note, a working-tree plus a
//! tagged version through `git worktree`, reuse of a cached version, the
//! root redirect, `--clean`, an unknown ref and an escaping output path.

use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use serde_json::Value;

mod common;

use common::Run;

fn folio(cwd: &Path, args: &[&str], experimental: bool) -> Run {
    let env: &[(&str, &str)] = if experimental {
        &[("FOLIO_EXPERIMENTAL", "versions")]
    } else {
        &[]
    };
    common::folio(cwd, args, env)
}

fn git(cwd: &Path, args: &[&str]) -> String {
    let output = Command::new("git")
        .args(args)
        .current_dir(cwd)
        .env("GIT_AUTHOR_NAME", "t")
        .env("GIT_AUTHOR_EMAIL", "t@example.com")
        .env("GIT_COMMITTER_NAME", "t")
        .env("GIT_COMMITTER_EMAIL", "t@example.com")
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "git {args:?}: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    String::from_utf8(output.stdout).unwrap().trim().to_string()
}

fn docs_yaml(versions: &str) -> String {
    format!(
        "project:\n  name: Demo\n  repo: https://github.com/acme/demo\nsource:\n  docs: [docs]\nllm:\n  generate_llms_txt: true\n  generate_llms_full_txt: false\nroadmap:\n  phases: []\n{versions}"
    )
}

/// A git repository with a tagged first commit and a docs-only project.
fn repo() -> (tempfile::TempDir, PathBuf) {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    fs::create_dir_all(root.join("docs")).unwrap();
    fs::write(root.join("docs/index.md"), "# Demo\n\nOld body.\n").unwrap();
    fs::write(root.join("docs.yaml"), docs_yaml("")).unwrap();
    git(&root, &["init", "-q", "-b", "main"]);
    git(&root, &["add", "."]);
    git(
        &root,
        &["-c", "commit.gpgsign=false", "commit", "-q", "-m", "v0.1.0"],
    );
    git(&root, &["tag", "v0.1.0"]);
    fs::write(root.join("docs/index.md"), "# Demo\n\nNew body.\n").unwrap();
    fs::write(
        root.join("docs.yaml"),
        docs_yaml("versions:\n  - label: latest\n    path: latest\n  - label: v0.1.0\n    path: v0.1\n    ref: v0.1.0\n"),
    )
    .unwrap();
    (dir, root)
}

#[test]
fn gate_and_empty_versions() {
    let dir = tempfile::tempdir().unwrap();
    let root = dir.path().canonicalize().unwrap();
    fs::write(root.join("docs.yaml"), docs_yaml("")).unwrap();
    let gated = folio(&root, &["build-versions"], false);
    assert_eq!(gated.code, 1);
    assert_eq!(
        gated.stdout,
        "The 'versions' feature is not available in this release.\n"
    );
    let none = folio(&root, &["build-versions"], true);
    assert_eq!(none.code, 1);
    assert_eq!(
        none.stdout,
        "No versions configured in docs.yaml. Use 'folio build' instead.\nAdd a 'versions' section to docs.yaml to use multi-version builds.\n"
    );
    fs::write(
        root.join("docs.yaml"),
        docs_yaml("versions:\n  - label: out\n    path: ../x\n"),
    )
    .unwrap();
    let escape = folio(&root, &["build-versions"], true);
    assert_eq!(escape.code, 1);
    assert_eq!(
        escape.diagnostics(),
        "Build failed: Version output path must stay within the output directory\n"
    );
    assert!(!root.parent().unwrap().join("x").exists());
}

#[test]
fn builds_the_matrix_reuses_cached_versions_and_reports_failures() {
    let (_dir, root) = repo();
    let commit = git(&root, &["rev-parse", "v0.1.0^{commit}"]);
    let site = root.join("_site");
    fs::create_dir_all(&site).unwrap();
    fs::write(site.join("stale.html"), "stale").unwrap();

    let run = folio(&root, &["build-versions", "--clean"], true);
    assert_eq!(run.code, 0, "{}", run.stdout);
    assert!(
        !site.join("stale.html").exists(),
        "--clean removes stale output"
    );
    assert!(run.stdout.contains(&format!(
        "  Building version: latest → {}/latest\n",
        site.display()
    )));
    assert!(run.stdout.contains(&format!(
        "  Building version: v0.1.0 → {}/v0.1\n",
        site.display()
    )));
    assert!(
        run.stdout.ends_with("\n  All versions built to _site/\n\n"),
        "{}",
        run.stdout
    );
    assert_eq!(run.stdout.matches("✓ Site ready").count(), 2);
    let redirect = fs::read_to_string(site.join("index.html")).unwrap();
    assert!(redirect.contains("url=latest/"));
    // The historical build saw the old body; the working tree the new one.
    assert!(fs::read_to_string(site.join("v0.1/llms.txt")).is_ok());
    let historical_mirror = root.join(".build/worktrees");
    assert!(
        !historical_mirror.join("v0.1").exists(),
        "the worktree is removed after the build"
    );
    let manifest: Value =
        serde_json::from_str(&fs::read_to_string(site.join("v0.1/.folio-version.json")).unwrap())
            .unwrap();
    assert_eq!(manifest["commit"], commit);
    assert_eq!(manifest["label"], "v0.1.0");
    assert_eq!(manifest["path"], "v0.1");
    assert_eq!(manifest["ref"], "v0.1.0");
    assert_eq!(manifest["schema"], 1);
    assert_eq!(manifest["folio_version"], env!("CARGO_PKG_VERSION"));
    assert_eq!(manifest["versions_hash"].as_str().unwrap().len(), 64);
    let latest: Value =
        serde_json::from_str(&fs::read_to_string(site.join("latest/.folio-version.json")).unwrap())
            .unwrap();
    assert_eq!(latest["commit"], "");
    assert_eq!(latest["ref"], "");

    // A second run reuses the tagged version and rebuilds the working tree.
    fs::write(site.join("v0.1/version.txt"), "cached").unwrap();
    let again = folio(&root, &["build-versions"], true);
    assert_eq!(again.code, 0, "{}", again.stdout);
    assert!(again.stdout.contains(&format!(
        "  Reusing version: v0.1.0 → {}/v0.1\n",
        site.display()
    )));
    assert_eq!(again.stdout.matches("Building version:").count(), 1);
    assert_eq!(
        fs::read_to_string(site.join("v0.1/version.txt")).unwrap(),
        "cached"
    );

    // Without --clean other version folders survive.
    fs::create_dir_all(site.join("v9")).unwrap();
    fs::write(site.join("v9/index.html"), "keep").unwrap();
    folio(&root, &["build-versions"], true);
    assert!(site.join("v9/index.html").exists());

    // An unknown ref fails that version, the summary and the exit code; no redirect rewrite.
    fs::remove_file(site.join("index.html")).unwrap();
    fs::write(
        root.join("docs.yaml"),
        docs_yaml("versions:\n  - label: latest\n    path: latest\n  - label: ghost\n    path: ghost\n    ref: missing-tag\n"),
    )
    .unwrap();
    let failed = folio(&root, &["build-versions"], true);
    assert_eq!(failed.code, 1);
    assert!(
        failed.stdout.contains(&format!(
            "  Failed to checkout ref 'missing-tag' for ghost → {}/ghost: ",
            site.display()
        )),
        "{}",
        failed.stdout
    );
    assert!(failed
        .stdout
        .contains(&format!("  Version output: {}/ghost\n", site.display())));
    assert!(failed.stderr.contains(
        "  Version build failed:\n  - ghost: failed to checkout ref 'missing-tag' for output '"
    ));
    assert!(!failed.stdout.contains("All versions built"));
    assert!(!site.join("index.html").exists());
}
