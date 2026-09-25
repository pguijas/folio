//! Materialising a `theme.package` that names a git reference: fetch it into
//! the theme cache keyed by its digest, verify the tree, and hand back a
//! directory the overlay treats like any other.
//!
//! The digest is the whole trust model, so the fetch is arranged to make the
//! tree a function of the commit alone: the ambient git environment is
//! dropped, the filters that rewrite bytes on checkout are pinned off, and a
//! revision that resolves to another tree fails with both digests named.

use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};

use folio_config::RemoteThemePackage;

use crate::fs::remove_dir_all_if_exists;
use crate::template::{package_tree_digest, user_cache_dir};
use crate::{Result, SiteError};

/// Points the theme cache somewhere else: what CI pre-seeds, what an
/// air-gapped machine fills by hand, and the seam the tests build on.
pub const THEME_CACHE_ENV: &str = "FOLIO_THEME_CACHE_DIR";

/// Where fetched packages live, one directory per digest.
fn themes_cache_dir() -> Result<PathBuf> {
    match std::env::var_os(THEME_CACHE_ENV).filter(|value| !value.is_empty()) {
        Some(dir) => Ok(PathBuf::from(dir)),
        None => Ok(user_cache_dir()?.join("themes")),
    }
}

/// The hex half of a `sha256:<hex>` digest.
fn hex_of(digest: &str) -> &str {
    digest.strip_prefix("sha256:").unwrap_or(digest)
}

/// The directory a package with this digest is cached at, under `cache`.
fn cache_entry(cache: &Path, remote: &RemoteThemePackage) -> PathBuf {
    cache.join(&hex_of(&remote.digest)[..16])
}

/// Staging directories are unique per fetch, not per process: one process can
/// materialise two packages at once, and a shared name would have them tread
/// on each other mid-clone.
static FETCH: AtomicU64 = AtomicU64::new(0);

/// The package directory for `remote`, in the theme cache.
pub fn materialise(remote: &RemoteThemePackage) -> Result<PathBuf> {
    materialise_in(&themes_cache_dir()?, remote)
}

/// The package directory for `remote`, fetching it once into `cache` and
/// reusing it after. A cache entry that no longer matches its digest is
/// discarded rather than trusted, so a half-written or hand-edited entry
/// cannot survive into a build.
fn materialise_in(cache: &Path, remote: &RemoteThemePackage) -> Result<PathBuf> {
    let expected = hex_of(&remote.digest).to_string();
    let dest = cache_entry(cache, remote);
    if dest.is_dir() {
        match package_tree_digest(&dest) {
            Ok(found) if found == expected => return Ok(dest),
            // An entry that no longer hashes to its pin is evidence of nothing
            // and is discarded; a read error is evidence, and is reported.
            Ok(_) => remove_dir_all_if_exists(&dest).map_err(io(&dest))?,
            Err(err) => return Err(err),
        }
    }

    std::fs::create_dir_all(cache).map_err(io(cache))?;
    let staging = cache.join(format!(
        ".fetch-{}-{}",
        std::process::id(),
        FETCH.fetch_add(1, Ordering::Relaxed)
    ));
    remove_dir_all_if_exists(&staging).map_err(io(&staging))?;
    let fetched = fetch(remote, &staging);
    let result = fetched.and_then(|root| verify_and_install(remote, &expected, &root, &dest));
    let _ = remove_dir_all_if_exists(&staging);
    result
}

/// The digest decides. Anything else is refused before it is installed, and
/// the cache is left as it was.
fn verify_and_install(
    remote: &RemoteThemePackage,
    expected: &str,
    root: &Path,
    dest: &Path,
) -> Result<PathBuf> {
    let found = package_tree_digest(root)?;
    if found != expected {
        return Err(SiteError::Value(format!(
            "theme.package {} at {} does not match its digest.\n  expected sha256:{expected}\n  found    sha256:{found}\nUpdate theme.package.digest if the change is one you reviewed.",
            remote.git, remote.rev
        )));
    }
    if let Err(err) = std::fs::rename(root, dest) {
        // Another build installed this digest while this one was fetching.
        // Same digest, same tree, so the entry that won is the one to use.
        if package_tree_digest(dest).is_ok_and(|found| found == expected) {
            return Ok(dest.to_path_buf());
        }
        return Err(io(dest)(err));
    }
    Ok(dest.to_path_buf())
}

/// Clone `remote` into `staging` and return the directory holding the package.
/// A shallow fetch of the revision is tried first; servers that refuse to
/// serve an arbitrary commit that way get a full fetch.
fn fetch(remote: &RemoteThemePackage, staging: &Path) -> Result<PathBuf> {
    let checkout = staging.join("checkout");
    std::fs::create_dir_all(&checkout).map_err(io(&checkout))?;
    git(&checkout, &["init", "--quiet"])?;
    git(&checkout, &["remote", "add", "origin", "--", &remote.git])?;
    if git(
        &checkout,
        &[
            "fetch",
            "--quiet",
            "--depth",
            "1",
            "origin",
            "--",
            &remote.rev,
        ],
    )
    .is_err()
    {
        git(&checkout, &["fetch", "--quiet", "--tags", "origin"]).map_err(|err| {
            SiteError::Value(format!(
                "theme.package could not fetch {} from {}: {err}",
                remote.rev, remote.git
            ))
        })?;
        // A revision fetched into FETCH_HEAD is not a local ref, so it is
        // resolved rather than checked out by name; a branch only exists here
        // as `origin/<name>`.
        let commit = resolve(&checkout, &remote.rev).ok_or_else(|| {
            SiteError::NotFound(format!(
                "theme.package: {} has no revision {}",
                remote.git, remote.rev
            ))
        })?;
        git(&checkout, &["checkout", "--quiet", "--detach", &commit])?;
    } else {
        git(
            &checkout,
            &["checkout", "--quiet", "--detach", "FETCH_HEAD"],
        )?;
    }
    // Git's own directory is not part of the package and would change the digest.
    remove_dir_all_if_exists(&checkout.join(".git")).map_err(io(&checkout))?;

    let root = if remote.path.is_empty() {
        checkout
    } else {
        checkout.join(&remote.path)
    };
    if !root.is_dir() {
        return Err(SiteError::NotFound(format!(
            "theme.package: {} at {} has no directory '{}'",
            remote.git, remote.rev, remote.path
        )));
    }
    Ok(root)
}

/// The commit `rev` names, as a tag, a branch or a commit; `None` when the
/// repository has no such revision.
fn resolve(repo: &Path, rev: &str) -> Option<String> {
    for candidate in [
        format!("{rev}^{{commit}}"),
        format!("refs/remotes/origin/{rev}^{{commit}}"),
    ] {
        let output = command(repo)
            .args(["rev-parse", "--verify", "--quiet", &candidate])
            .output()
            .ok()?;
        let sha = String::from_utf8_lossy(&output.stdout).trim().to_string();
        if output.status.success() && !sha.is_empty() {
            return Some(sha);
        }
    }
    None
}

/// A git invocation in `repo`, with the caller's git environment dropped.
/// `-C` only changes the working directory: `GIT_DIR` and its relatives would
/// still point git at whatever repository invoked Folio, and the fetch would
/// land in it. The checkout filters are pinned off in the same breath, so the
/// tree the digest covers is a function of the commit and not of the machine.
fn command(repo: &Path) -> Command {
    let mut git = Command::new("git");
    git.arg("-C").arg(repo);
    for var in [
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES",
        "GIT_NAMESPACE",
    ] {
        git.env_remove(var);
    }
    // A fetch that wants a password fails instead of blocking the build on a
    // prompt nobody is watching.
    git.env("GIT_TERMINAL_PROMPT", "0");
    git.env("GIT_ASKPASS", "");
    git.env("SSH_ASKPASS", "");
    git.args([
        "-c",
        "core.autocrlf=false",
        "-c",
        "core.eol=lf",
        "-c",
        "core.symlinks=true",
        "-c",
        "core.hooksPath=",
        "-c",
        "core.attributesFile=",
        "-c",
        "filter.lfs.smudge=cat",
        "-c",
        "filter.lfs.process=",
        "-c",
        "filter.lfs.required=false",
    ]);
    git
}

/// One git command in `repo`. A missing git is the one failure worth naming
/// on its own: the binary needs no toolchain, but fetching a package does.
fn git(repo: &Path, args: &[&str]) -> Result<()> {
    let output = command(repo)
        .args(args)
        .output()
        .map_err(|err| match err.kind() {
            std::io::ErrorKind::NotFound => SiteError::Value(
                "git is not installed, and a remote theme.package is fetched with it".to_string(),
            ),
            _ => SiteError::Value(format!("git: {err}")),
        })?;
    if output.status.success() {
        return Ok(());
    }
    Err(SiteError::Value(format!(
        "git {} failed: {}",
        args.join(" "),
        String::from_utf8_lossy(&output.stderr).trim()
    )))
}

fn io(path: &Path) -> impl Fn(std::io::Error) -> SiteError + '_ {
    move |err| SiteError::Value(format!("{}: {err}", path.display()))
}

#[cfg(test)]
#[path = "theme_package_tests.rs"]
mod tests;
