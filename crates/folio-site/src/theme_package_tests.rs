use super::*;

use std::process::Command as Git;

/// A git repository on disk holding `files`, fetched over `file://`.
struct Origin {
    dir: tempfile::TempDir,
}

impl Origin {
    fn new(files: &[(&str, &str)]) -> Origin {
        let dir = tempfile::tempdir().unwrap();
        let root = dir.path();
        for (rel, body) in files {
            let path = root.join(rel);
            std::fs::create_dir_all(path.parent().unwrap()).unwrap();
            std::fs::write(&path, body).unwrap();
        }
        let origin = Origin { dir };
        for args in [
            vec!["init", "--quiet", "-b", "main"],
            vec!["add", "-A"],
            vec!["commit", "--quiet", "-m", "theme"],
        ] {
            origin.git(&args);
        }
        origin
    }

    /// One git command in the origin, with the developer's own git config and
    /// git environment kept out of it, so the fixture is the same everywhere.
    fn git(&self, args: &[&str]) -> String {
        let out = Git::new("git")
            .arg("-C")
            .arg(self.dir.path())
            .args([
                "-c",
                "user.email=theme@test",
                "-c",
                "user.name=Theme Test",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "core.hooksPath=",
                "-c",
                "core.autocrlf=false",
            ])
            .args(args)
            .env("GIT_CONFIG_GLOBAL", "/dev/null")
            .env("GIT_CONFIG_SYSTEM", "/dev/null")
            .env("GIT_CONFIG_NOSYSTEM", "1")
            .env_remove("GIT_DIR")
            .env_remove("GIT_WORK_TREE")
            .env_remove("GIT_INDEX_FILE")
            .output()
            .unwrap();
        assert!(
            out.status.success(),
            "git {args:?}: {}",
            String::from_utf8_lossy(&out.stderr)
        );
        String::from_utf8_lossy(&out.stdout).trim().to_string()
    }

    fn url(&self) -> String {
        format!("file://{}", self.dir.path().display())
    }

    /// The digest of a subdirectory of the origin, as the config would pin it.
    fn digest(&self, sub: &str) -> String {
        let root = if sub.is_empty() {
            self.dir.path().to_path_buf()
        } else {
            self.dir.path().join(sub)
        };
        // The working copy carries .git, which the fetch strips; hash a clean copy.
        let clean = tempfile::tempdir().unwrap();
        copy_without_git(&root, clean.path());
        format!("sha256:{}", package_tree_digest(clean.path()).unwrap())
    }
}

fn copy_without_git(from: &Path, to: &Path) {
    for entry in std::fs::read_dir(from).unwrap() {
        let entry = entry.unwrap();
        let name = entry.file_name();
        if name == ".git" {
            continue;
        }
        let target = to.join(&name);
        if entry.file_type().unwrap().is_dir() {
            std::fs::create_dir_all(&target).unwrap();
            copy_without_git(&entry.path(), &target);
        } else {
            std::fs::copy(entry.path(), &target).unwrap();
        }
    }
}

fn remote(origin: &Origin, rev: &str, digest: &str, path: &str) -> RemoteThemePackage {
    RemoteThemePackage {
        git: origin.url(),
        rev: rev.to_string(),
        digest: digest.to_string(),
        path: path.to_string(),
    }
}

const PACKAGE: [(&str, &str); 2] = [
    ("app/globals.css", ":root { --brand: hotpink; }\n"),
    (
        "theme/project-theme.ts",
        "export const projectThemePreset = 1\nexport const projectThemeDefaultConfig = {}\n",
    ),
];

#[test]
fn a_pinned_package_is_fetched_once_and_reused() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&PACKAGE);
    let pin = remote(&origin, "main", &origin.digest(""), "");

    let first = materialise_in(cache, &pin).unwrap();
    assert!(first.join("app/globals.css").is_file());
    assert!(
        !first.join(".git").exists(),
        "git's own directory is not the package"
    );
    assert_eq!(
        format!("sha256:{}", package_tree_digest(&first).unwrap()),
        pin.digest
    );

    // The origin moves; the cached entry is what a second build reads.
    std::fs::write(origin.dir.path().join("app/globals.css"), "moved\n").unwrap();
    let second = materialise_in(cache, &pin).unwrap();
    assert_eq!(second, first);
    assert_eq!(
        std::fs::read_to_string(second.join("app/globals.css")).unwrap(),
        ":root { --brand: hotpink; }\n"
    );
}

#[test]
fn a_tree_that_does_not_match_the_digest_is_refused() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&PACKAGE);
    let wrong = format!("sha256:{}", "b".repeat(64));
    let pin = remote(&origin, "main", &wrong, "");

    let error = materialise_in(cache, &pin).unwrap_err().to_string();
    assert!(error.contains("does not match its digest"), "{error}");
    assert!(error.contains(&wrong), "{error}");
    assert!(
        error.contains("Update theme.package.digest"),
        "the message says what to do: {error}"
    );
    let entry = cache_entry(cache, &pin);
    assert!(!entry.exists(), "a refused package is not installed");
    assert!(
        std::fs::read_dir(entry.parent().unwrap())
            .map(|dir| dir.count())
            .unwrap_or(0)
            == 0,
        "and leaves no staging directory behind"
    );
}

#[test]
fn a_subdirectory_of_the_repository_can_be_the_package() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&[
        ("README.md", "not the package\n"),
        (
            "themes/acme/app/globals.css",
            ":root { --brand: rebeccapurple; }\n",
        ),
    ]);
    let pin = remote(
        &origin,
        "main",
        &origin.digest("themes/acme"),
        "themes/acme",
    );

    let root = materialise_in(cache, &pin).unwrap();
    assert!(root.join("app/globals.css").is_file());
    assert!(
        !root.join("README.md").exists(),
        "only the subdirectory is the package"
    );

    // A different digest, so this asks for a fetch rather than the entry the
    // call above cached: the digest is the cache key, not the path.
    let missing = remote(&origin, "main", &origin.digest(""), "themes/nope");
    let error = materialise_in(cache, &missing).unwrap_err().to_string();
    assert!(error.contains("has no directory 'themes/nope'"), "{error}");
}

#[test]
fn a_revision_that_does_not_exist_names_itself() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&PACKAGE);
    let pin = remote(&origin, "v9.9.9", &origin.digest(""), "");

    let error = materialise_in(cache, &pin).unwrap_err().to_string();
    assert!(error.contains("v9.9.9"), "{error}");
    assert!(!cache_entry(cache, &pin).exists());
}

#[test]
fn a_cache_entry_that_no_longer_matches_is_discarded_and_refetched() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&PACKAGE);
    let pin = remote(&origin, "main", &origin.digest(""), "");
    let entry = materialise_in(cache, &pin).unwrap();

    // Someone edits the cache by hand: the digest no longer holds.
    std::fs::write(entry.join("app/globals.css"), "tampered\n").unwrap();
    let again = materialise_in(cache, &pin).unwrap();
    assert_eq!(again, entry);
    assert_eq!(
        std::fs::read_to_string(again.join("app/globals.css")).unwrap(),
        ":root { --brand: hotpink; }\n",
        "the tampered entry was refetched, not trusted"
    );
}

#[test]
fn a_moved_tag_is_caught_by_the_digest() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&PACKAGE);
    origin.git(&["tag", "v1"]);
    let pin = remote(&origin, "v1", &origin.digest(""), "");
    materialise_in(cache, &pin).unwrap();

    // The publisher moves the tag under a project that already pinned it.
    std::fs::write(
        origin.dir.path().join("theme/project-theme.ts"),
        "export const projectThemePreset = 2\nexport const projectThemeDefaultConfig = {}\n",
    )
    .unwrap();
    origin.git(&["add", "-A"]);
    origin.git(&["commit", "--quiet", "-m", "second"]);
    origin.git(&["tag", "-f", "v1"]);

    let fresh = tempfile::tempdir().unwrap();
    let error = materialise_in(fresh.path(), &pin).unwrap_err().to_string();
    assert!(error.contains("does not match its digest"), "{error}");
    assert!(error.contains(&pin.digest), "the pin is named: {error}");
    assert!(!cache_entry(fresh.path(), &pin).exists());
}

#[test]
fn a_commit_sha_pins_a_revision_that_is_not_the_tip() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&PACKAGE);
    let first = origin.git(&["rev-parse", "HEAD"]);
    let digest = origin.digest("");

    std::fs::write(origin.dir.path().join("app/globals.css"), "later\n").unwrap();
    origin.git(&["add", "-A"]);
    origin.git(&["commit", "--quiet", "-m", "later"]);

    let pin = remote(&origin, &first, &digest, "");
    let root = materialise_in(cache, &pin).unwrap();
    assert_eq!(
        std::fs::read_to_string(root.join("app/globals.css")).unwrap(),
        ":root { --brand: hotpink; }\n",
        "the sha, not the branch tip"
    );
}

#[test]
fn a_branch_name_resolves_through_the_full_fetch_fallback() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&PACKAGE);
    origin.git(&["branch", "release"]);
    // file:// origins refuse a shallow fetch of a bare branch name often enough
    // that the fallback is the path this exercises; either way it must resolve.
    let pin = remote(&origin, "release", &origin.digest(""), "");
    let root = materialise_in(cache, &pin).unwrap();
    assert!(root.join("app/globals.css").is_file());
}

#[test]
fn a_symlink_inside_a_package_is_refused() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&PACKAGE);
    std::os::unix::fs::symlink("/etc/passwd", origin.dir.path().join("app/link.css")).unwrap();
    origin.git(&["add", "-A"]);
    origin.git(&["commit", "--quiet", "-m", "link"]);
    let pin = remote(&origin, "main", &format!("sha256:{}", "c".repeat(64)), "");

    let error = materialise_in(cache, &pin).unwrap_err().to_string();
    assert!(
        error.contains("symlink") || error.contains("link.css"),
        "{error}"
    );
    assert!(!cache_entry(cache, &pin).exists());
}

#[test]
fn the_ambient_git_environment_does_not_reach_the_fetch() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path();
    let origin = Origin::new(&PACKAGE);
    let pin = remote(&origin, "main", &origin.digest(""), "");

    // A repository the caller is inside. If GIT_DIR reached git, the fetch
    // would land here and this checkout would be rewritten.
    let victim = tempfile::tempdir().unwrap();
    let victim_repo = Origin::new(&[("readme.md", "mine\n")]);
    let marker = victim_repo.dir.path().join("readme.md");

    let previous = std::env::var_os("GIT_DIR");
    std::env::set_var("GIT_DIR", victim_repo.dir.path().join(".git"));
    let fetched = materialise_in(cache, &pin);
    match previous {
        Some(value) => std::env::set_var("GIT_DIR", value),
        None => std::env::remove_var("GIT_DIR"),
    }
    drop(victim);

    let root = fetched.expect("the fetch ignores the caller's GIT_DIR");
    assert!(root.join("app/globals.css").is_file());
    assert_eq!(
        std::fs::read_to_string(&marker).unwrap(),
        "mine\n",
        "the caller's working tree is untouched"
    );
}

#[test]
fn two_builds_sharing_a_cache_both_get_the_package() {
    let cache = tempfile::tempdir().unwrap();
    let cache = cache.path().to_path_buf();
    let origin = Origin::new(&PACKAGE);
    let pin = remote(&origin, "main", &origin.digest(""), "");

    let (a, b) = std::thread::scope(|scope| {
        let one = scope.spawn(|| materialise_in(&cache, &pin));
        let two = scope.spawn(|| materialise_in(&cache, &pin));
        (one.join().unwrap(), two.join().unwrap())
    });
    assert_eq!(a.unwrap(), b.unwrap(), "both installs agree on the entry");
}
