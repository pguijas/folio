//! The hidden `folio github-pages` group: the CI steps the two GitHub Pages
//! workflows call, the `folio-pages-state` branch lifecycle and the preview
//! data the `/previews/` page reads.

use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::thread;
use std::time::Duration;

use clap::Subcommand;
use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::error::CliError;
use crate::ui::Ui;

use super::resolve_path;

/// The branch that keeps the deployed Pages artifact between runs.
pub const STATE_BRANCH: &str = "folio-pages-state";
/// Author of the state commits and of the sticky PR comment.
pub const BOT_NAME: &str = "github-actions[bot]";
/// Committer email of the state commits.
pub const BOT_EMAIL: &str = "41898282+github-actions[bot]@users.noreply.github.com";
/// First line of the sticky PR comment; how it is found again.
pub const COMMENT_MARKER: &str = "<!-- folio-branch-preview -->";
/// Longest preview directory name.
pub const MAX_PREVIEW_ID_LENGTH: usize = 80;
/// Per-preview sidecar the `/previews/` cards read.
pub const PREVIEW_METADATA_FILE: &str = ".folio-preview.json";
/// The array of preview entries the `/previews/` page fetches.
pub const PREVIEWS_DATA_FILE: &str = "previews.json";
/// Files at the root of `previews/` the build owns; never clobbered by
/// previews restored from the state branch.
pub const RESERVED_PREVIEW_FILES: [&str; 2] = ["index.html", PREVIEWS_DATA_FILE];

type Result<T> = std::result::Result<T, String>;

/// Steps of the GitHub Pages workflows that folio init writes.
///
/// Each subcommand is one step the generated workflows run; they are not
/// meant to be called by hand.
#[derive(Subcommand, Debug)]
pub enum Cmd {
    /// Output the preview id, base path and URL of a pull request.
    ComputePreviewPath {
        #[arg(long, allow_hyphen_values = true)]
        head_ref: String,
        #[arg(long, allow_hyphen_values = true)]
        pr_number: String,
        #[arg(long, allow_hyphen_values = true)]
        pages_base_path: String,
        #[arg(long, allow_hyphen_values = true)]
        pages_base_url: String,
    },
    /// Restore the previews saved on the state branch into the production site.
    PreservePreviews {
        #[arg(long, allow_hyphen_values = true)]
        site_dir: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        git_repo: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        state_dir: PathBuf,
        #[arg(long, default_value = STATE_BRANCH, allow_hyphen_values = true)]
        state_branch: String,
    },
    /// Assemble the Pages artifact from the saved state or the production site.
    PrepareArtifact {
        #[arg(long, allow_hyphen_values = true)]
        production_site: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        artifact_dir: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        git_repo: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        state_dir: PathBuf,
        #[arg(long, default_value = STATE_BRANCH, allow_hyphen_values = true)]
        state_branch: String,
    },
    /// Copy a pull request's preview site into the artifact.
    CopyBranchPreview {
        #[arg(long, allow_hyphen_values = true)]
        preview_site: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        artifact_dir: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        preview_id: String,
    },
    /// Write the metadata file one preview card on /previews/ reads.
    WritePreviewMetadata {
        #[arg(long, allow_hyphen_values = true)]
        artifact_dir: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        preview_id: String,
        #[arg(long, allow_hyphen_values = true)]
        pr_number: String,
        #[arg(long, default_value = "", allow_hyphen_values = true)]
        title: String,
        #[arg(long, default_value = "", allow_hyphen_values = true)]
        branch: String,
        #[arg(long, default_value = "", allow_hyphen_values = true)]
        commit: String,
        #[arg(long, default_value = "", allow_hyphen_values = true)]
        pr_url: String,
        #[arg(long, allow_hyphen_values = true)]
        updated_at: String,
        #[arg(long, default_value = "", allow_hyphen_values = true)]
        repo: String,
        #[arg(long, default_value = "", allow_hyphen_values = true)]
        author: String,
        #[arg(long, default_value = "", allow_hyphen_values = true)]
        author_url: String,
        #[arg(long, default_value = "", allow_hyphen_values = true)]
        avatar_url: String,
    },
    /// Collect every preview into the previews.json the /previews/ page reads.
    WritePreviewsData {
        #[arg(long, allow_hyphen_values = true)]
        previews_dir: PathBuf,
    },
    /// Delete the previews of pull requests that are no longer open.
    PrunePreviews {
        #[arg(long, allow_hyphen_values = true)]
        previews_dir: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        open_prs_json: String,
    },
    /// Commit the artifact to the state branch and push it.
    SaveState {
        #[arg(long, allow_hyphen_values = true)]
        artifact_dir: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        git_repo: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        state_dir: PathBuf,
        #[arg(long, allow_hyphen_values = true)]
        commit_message: String,
        #[arg(long, default_value = STATE_BRANCH, allow_hyphen_values = true)]
        state_branch: String,
    },
    /// Wait until the page URL and the index URL both answer 200.
    VerifyUrl {
        #[arg(long, allow_hyphen_values = true)]
        url: String,
        #[arg(long, allow_hyphen_values = true)]
        index_url: String,
        #[arg(long, allow_hyphen_values = true)]
        summary_heading: String,
        #[arg(long, allow_hyphen_values = true)]
        primary_label: String,
        #[arg(long, allow_hyphen_values = true)]
        index_label: String,
        #[arg(long, allow_hyphen_values = true)]
        success_message: String,
        #[arg(long, allow_hyphen_values = true)]
        error_message: String,
        #[arg(long, default_value_t = 24)]
        attempts: u32,
        #[arg(long, default_value_t = 5.0)]
        sleep_seconds: f64,
    },
    /// Create or update the pull request comment that links the preview.
    CommentPreview {
        #[arg(long, allow_hyphen_values = true)]
        repo: String,
        #[arg(long, allow_hyphen_values = true)]
        pr_number: String,
        #[arg(long, allow_hyphen_values = true)]
        preview_url: String,
        #[arg(long, allow_hyphen_values = true)]
        index_url: String,
        #[arg(long, allow_hyphen_values = true)]
        branch: String,
        #[arg(long, allow_hyphen_values = true)]
        head_sha: String,
    },
}

/// Where a pull request's preview lives: id, base path and public URL.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PreviewPath {
    pub safe_branch: String,
    pub base_path: String,
    pub url: String,
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

/// Lowercase, runs of anything but `[a-z0-9]` collapsed to `-`, trimmed.
///
/// Deliberately not `folio_config::slugify`: this slug names a directory in
/// the published Pages tree, so it stays ASCII where the content rule keeps
/// Unicode word characters.
fn slug(text: &str) -> String {
    let mut out = String::new();
    let mut dash = false;
    for c in text.to_lowercase().chars() {
        if c.is_ascii_lowercase() || c.is_ascii_digit() {
            out.push(c);
            dash = false;
        } else if !dash {
            out.push('-');
            dash = true;
        }
    }
    out.trim_matches('-').to_string()
}

/// The preview id for a pull request: `pr-<number>-<branch slug>`, at most
/// 80 characters; overflow keeps a digest so long names stay distinct.
pub fn safe_preview_branch(head_ref: &str, pr_number: &str) -> String {
    let digest = hex(&Sha256::digest(format!("{pr_number}:{head_ref}")))[..8].to_string();
    let mut safe_pr = slug(pr_number);
    if safe_pr.is_empty() {
        safe_pr = "unknown".to_string();
    }
    if safe_pr.len() > 24 {
        let head = safe_pr[..15].trim_matches('-');
        safe_pr = format!("{}-{digest}", if head.is_empty() { "id" } else { head });
    }
    let safe_branch = slug(head_ref);
    let mut preview_id = format!("pr-{safe_pr}");
    if !safe_branch.is_empty() {
        preview_id = format!("{preview_id}-{safe_branch}");
    }
    if preview_id.len() <= MAX_PREVIEW_ID_LENGTH {
        return preview_id;
    }
    let prefix = format!("pr-{safe_pr}-");
    let suffix = format!("-{digest}");
    let branch_length = MAX_PREVIEW_ID_LENGTH
        .saturating_sub(prefix.len() + suffix.len())
        .max(1);
    let cut = safe_branch[..branch_length.min(safe_branch.len())].trim_matches('-');
    format!(
        "{prefix}{}{suffix}",
        if cut.is_empty() { "branch" } else { cut }
    )
}

/// Preview id, base path and URL for a pull request under the Pages base.
pub fn compute_preview_path(
    head_ref: &str,
    pr_number: &str,
    pages_base_path: &str,
    pages_base_url: &str,
) -> PreviewPath {
    let safe_branch = safe_preview_branch(head_ref, pr_number);
    let mut base_path = format!(
        "{}/previews/{safe_branch}",
        pages_base_path.trim_end_matches('/')
    );
    if !base_path.starts_with('/') {
        base_path = format!("/{base_path}");
    }
    let url = format!(
        "{}/previews/{safe_branch}/",
        pages_base_url.trim_end_matches('/')
    );
    PreviewPath {
        safe_branch,
        base_path,
        url,
    }
}

fn at(path: &Path) -> impl Fn(io::Error) -> String + '_ {
    move |err| format!("{}: {err}", path.display())
}

/// A real directory is removed recursively; a file or symlink is unlinked.
fn remove_path(path: &Path) -> Result<()> {
    match fs::symlink_metadata(path) {
        Ok(meta) if meta.is_dir() => fs::remove_dir_all(path),
        Ok(_) => fs::remove_file(path),
        Err(err) if err.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(err) => Err(err),
    }
    .map_err(at(path))
}

/// `copytree(symlinks=True)` / `copy2(follow_symlinks=False)` for one entry.
fn copy_entry(src: &Path, dst: &Path) -> io::Result<()> {
    let meta = fs::symlink_metadata(src)?;
    if meta.file_type().is_symlink() {
        let link = fs::read_link(src)?;
        #[cfg(unix)]
        return std::os::unix::fs::symlink(link, dst);
        #[cfg(not(unix))]
        {
            let _ = link;
            return fs::copy(src, dst).map(|_| ());
        }
    }
    if meta.is_dir() {
        fs::create_dir_all(dst)?;
        for entry in fs::read_dir(src)? {
            let entry = entry?;
            copy_entry(&entry.path(), &dst.join(entry.file_name()))?;
        }
        return fs::set_permissions(dst, meta.permissions());
    }
    fs::copy(src, dst).map(|_| ())
}

/// Copy the children of `source` into `destination` (created as needed),
/// replacing same-named targets and keeping the others.
fn copy_contents(source: &Path, destination: &Path, exclude_names: &[&str]) -> Result<()> {
    if !source.is_dir() {
        return Err(format!("Source directory not found: {}", source.display()));
    }
    fs::create_dir_all(destination).map_err(at(destination))?;
    for entry in fs::read_dir(source).map_err(at(source))? {
        let entry = entry.map_err(at(source))?;
        let name = entry.file_name();
        if exclude_names.contains(&name.to_string_lossy().as_ref()) {
            continue;
        }
        let target = destination.join(&name);
        remove_path(&target)?;
        copy_entry(&entry.path(), &target).map_err(at(&target))?;
    }
    Ok(())
}

fn clear_directory(path: &Path, keep_names: &[&str]) -> Result<()> {
    fs::create_dir_all(path).map_err(at(path))?;
    for entry in fs::read_dir(path).map_err(at(path))? {
        let entry = entry.map_err(at(path))?;
        if keep_names.contains(&entry.file_name().to_string_lossy().as_ref()) {
            continue;
        }
        remove_path(&entry.path())?;
    }
    Ok(())
}

fn touch(path: &Path) -> Result<()> {
    fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(path)
        .map(|_| ())
        .map_err(at(path))
}

/// Run a program, fail on a non-zero exit, return its stdout.
fn run_checked(program: &str, args: &[String]) -> Result<String> {
    let output = Command::new(program)
        .args(args)
        .output()
        .map_err(|err| format!("{program}: {err}"))?;
    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).into_owned())
    } else {
        Err(format!(
            "{program} {} failed ({}): {}",
            args.join(" "),
            output.status,
            String::from_utf8_lossy(&output.stderr).trim()
        ))
    }
}

fn git(repo: &Path, args: &[&str]) -> Result<String> {
    let mut argv = vec!["-C".to_string(), repo.display().to_string()];
    argv.extend(args.iter().map(|a| a.to_string()));
    run_checked("git", &argv)
}

fn remote_branch_exists(git_repo: &Path, state_branch: &str) -> Result<bool> {
    let status = Command::new("git")
        .args([
            "-C",
            &git_repo.display().to_string(),
            "ls-remote",
            "--exit-code",
            "--heads",
            "origin",
            state_branch,
        ])
        .stdout(std::process::Stdio::null())
        .stderr(std::process::Stdio::null())
        .status()
        .map_err(|err| format!("git: {err}"))?;
    match status.code() {
        Some(0) => Ok(true),
        Some(2) => Ok(false),
        _ => Err(format!(
            "git ls-remote origin {state_branch} failed ({status})"
        )),
    }
}

/// Check the remote state branch out as a detached worktree at `state_dir`;
/// nothing happens when the branch does not exist yet.
fn fetch_state_worktree(git_repo: &Path, state_dir: &Path, state_branch: &str) -> Result<bool> {
    if !remote_branch_exists(git_repo, state_branch)? {
        return Ok(false);
    }
    git(git_repo, &["fetch", "origin", state_branch])?;
    git(
        git_repo,
        &[
            "worktree",
            "add",
            "--detach",
            &state_dir.display().to_string(),
            "FETCH_HEAD",
        ],
    )?;
    Ok(true)
}

/// Restore the previews saved on the state branch into a fresh production site.
pub fn preserve_branch_previews(
    site_dir: &Path,
    git_repo: &Path,
    state_dir: &Path,
    state_branch: &str,
    fetch_state: bool,
) -> Result<()> {
    let site_dir = resolve_path(site_dir);
    let git_repo = resolve_path(git_repo);
    let state_dir = resolve_path(state_dir);
    if fetch_state {
        remove_path(&state_dir)?;
        fetch_state_worktree(&git_repo, &state_dir, state_branch)?;
    }
    let previews = state_dir.join("previews");
    if previews.is_dir() {
        copy_contents(
            &previews,
            &site_dir.join("previews"),
            &RESERVED_PREVIEW_FILES,
        )?;
    }
    fs::create_dir_all(&site_dir).map_err(at(&site_dir))?;
    touch(&site_dir.join(".nojekyll"))
}

/// Assemble the Pages artifact: the saved root when the state branch has one, else the production site plus the saved previews.
pub fn prepare_pages_artifact(
    production_site: &Path,
    artifact_dir: &Path,
    git_repo: &Path,
    state_dir: &Path,
    state_branch: &str,
    fetch_state: bool,
) -> Result<()> {
    let production_site = resolve_path(production_site);
    let artifact_dir = resolve_path(artifact_dir);
    let git_repo = resolve_path(git_repo);
    let state_dir = resolve_path(state_dir);
    if fetch_state {
        remove_path(&state_dir)?;
        fetch_state_worktree(&git_repo, &state_dir, state_branch)?;
    }
    remove_path(&artifact_dir)?;
    fs::create_dir_all(&artifact_dir).map_err(at(&artifact_dir))?;
    if state_dir.join("index.html").is_file() {
        copy_contents(&state_dir, &artifact_dir, &[".git"])?;
    } else {
        copy_contents(&production_site, &artifact_dir, &[])?;
        let previews = state_dir.join("previews");
        if previews.is_dir() {
            copy_contents(
                &previews,
                &artifact_dir.join("previews"),
                &RESERVED_PREVIEW_FILES,
            )?;
        }
    }
    touch(&artifact_dir.join(".nojekyll"))
}

fn validate_preview_id(preview_id: &str) -> Result<()> {
    let mut chars = preview_id.chars();
    let valid = preview_id.len() <= MAX_PREVIEW_ID_LENGTH
        && chars
            .next()
            .is_some_and(|c| c.is_ascii_lowercase() || c.is_ascii_digit())
        && chars.all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-');
    if valid {
        Ok(())
    } else {
        Err(format!("Invalid preview id: {preview_id}"))
    }
}

fn resolve_preview_dir(artifact_dir: &Path, preview_id: &str) -> Result<PathBuf> {
    validate_preview_id(preview_id)?;
    let previews_dir = resolve_path(&artifact_dir.join("previews"));
    let preview_dir = resolve_path(&previews_dir.join(preview_id));
    if preview_dir.parent() != Some(previews_dir.as_path()) {
        return Err(format!("Invalid preview id: {preview_id}"));
    }
    Ok(preview_dir)
}

/// Replace `artifact_dir/previews/<id>` with the preview site's contents.
pub fn copy_branch_preview(
    preview_site: &Path,
    artifact_dir: &Path,
    preview_id: &str,
) -> Result<()> {
    let preview_dir = resolve_preview_dir(artifact_dir, preview_id)?;
    remove_path(&preview_dir)?;
    fs::create_dir_all(&preview_dir).map_err(at(&preview_dir))?;
    copy_contents(preview_site, &preview_dir, &[])
}

/// What `write-preview-metadata` receives from the workflow.
pub struct PreviewMetadata<'a> {
    pub pr_number: &'a str,
    pub title: &'a str,
    pub branch: &'a str,
    pub commit: &'a str,
    pub pr_url: &'a str,
    pub updated_at: &'a str,
    pub repo: &'a str,
    pub author: &'a str,
    pub author_url: &'a str,
    pub avatar_url: &'a str,
}

/// Write the `.folio-preview.json` sidecar the `/previews/` cards read.
pub fn write_preview_metadata(
    artifact_dir: &Path,
    preview_id: &str,
    m: &PreviewMetadata,
) -> Result<()> {
    let preview_dir = resolve_preview_dir(artifact_dir, preview_id)?;
    if !preview_dir.is_dir() {
        return Err(format!(
            "Preview directory not found: {}",
            preview_dir.display()
        ));
    }
    let repo_url = if m.repo.is_empty() {
        String::new()
    } else {
        format!("https://github.com/{}", m.repo)
    };
    let commit_url = if repo_url.is_empty() || m.commit.is_empty() {
        String::new()
    } else {
        format!("{repo_url}/commit/{}", m.commit)
    };
    let short_commit: String = m.commit.chars().take(12).collect();
    let metadata: BTreeMap<&str, &str> = BTreeMap::from([
        ("pr_number", m.pr_number),
        ("title", m.title),
        ("branch", m.branch),
        ("commit", short_commit.as_str()),
        ("commit_url", commit_url.as_str()),
        ("pr_url", m.pr_url),
        ("repo", m.repo),
        ("repo_url", repo_url.as_str()),
        ("author", m.author),
        ("author_url", m.author_url),
        ("avatar_url", m.avatar_url),
        ("updated_at", m.updated_at),
    ]);
    let payload = serde_json::to_string_pretty(&metadata).map_err(|err| err.to_string())?;
    let path = preview_dir.join(PREVIEW_METADATA_FILE);
    fs::write(&path, format!("{payload}\n")).map_err(at(&path))
}

/// One `previews.json` entry; the field order is the JSON key order.
#[derive(Serialize, Debug, Clone, PartialEq, Eq, Default)]
pub struct PreviewEntry {
    pub name: String,
    pub href: String,
    pub title: String,
    pub pr_number: String,
    pub branch: String,
    pub commit: String,
    pub commit_url: String,
    pub pr_url: String,
    pub repo: String,
    pub repo_url: String,
    pub author: String,
    pub author_url: String,
    pub avatar_url: String,
    pub updated_at: String,
}

fn read_preview_entry(path: &Path) -> PreviewEntry {
    let name = path
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default();
    let mut entry = PreviewEntry {
        href: format!("./{name}/"),
        title: name.clone(),
        name,
        ..PreviewEntry::default()
    };
    let metadata = fs::read_to_string(path.join(PREVIEW_METADATA_FILE))
        .ok()
        .and_then(|text| serde_json::from_str::<serde_json::Value>(&text).ok());
    let Some(serde_json::Value::Object(metadata)) = metadata else {
        return entry;
    };
    for (field, slot) in [
        ("pr_number", &mut entry.pr_number),
        ("branch", &mut entry.branch),
        ("commit", &mut entry.commit),
        ("commit_url", &mut entry.commit_url),
        ("pr_url", &mut entry.pr_url),
        ("repo", &mut entry.repo),
        ("repo_url", &mut entry.repo_url),
        ("author", &mut entry.author),
        ("author_url", &mut entry.author_url),
        ("avatar_url", &mut entry.avatar_url),
        ("updated_at", &mut entry.updated_at),
    ] {
        if let Some(serde_json::Value::String(value)) = metadata.get(field) {
            *slot = value.clone();
        }
    }
    if let Some(serde_json::Value::String(title)) = metadata.get("title") {
        if !title.trim().is_empty() {
            entry.title = title.clone();
        }
    }
    entry
}

/// Collect every preview (a child directory with an `index.html`) into
/// `previews.json`, newest first.
pub fn write_previews_data(previews_dir: &Path) -> Result<Vec<PreviewEntry>> {
    fs::create_dir_all(previews_dir).map_err(at(previews_dir))?;
    let mut entries: Vec<PreviewEntry> = fs::read_dir(previews_dir)
        .map_err(at(previews_dir))?
        .filter_map(|entry| entry.ok().map(|e| e.path()))
        .filter(|path| path.is_dir() && path.join("index.html").is_file())
        .map(|path| read_preview_entry(&path))
        .collect();
    entries.sort_by(|a, b| a.name.cmp(&b.name));
    entries.sort_by(|a, b| b.updated_at.cmp(&a.updated_at));
    let payload = serde_json::to_string_pretty(&entries).map_err(|err| err.to_string())?;
    let path = previews_dir.join(PREVIEWS_DATA_FILE);
    fs::write(&path, format!("{payload}\n")).map_err(at(&path))?;
    Ok(entries)
}

/// Delete every child directory whose name is not in `keep_ids`; files at
/// the root (`previews.json`, `index.html`) are untouched.
pub fn prune_previews(previews_dir: &Path, keep_ids: &BTreeSet<String>) -> Result<Vec<String>> {
    if !previews_dir.is_dir() {
        return Ok(Vec::new());
    }
    let mut dirs: Vec<PathBuf> = fs::read_dir(previews_dir)
        .map_err(at(previews_dir))?
        .filter_map(|entry| entry.ok().map(|e| e.path()))
        .filter(|path| path.is_dir())
        .collect();
    dirs.sort();
    let mut removed = Vec::new();
    for path in dirs {
        let name = path
            .file_name()
            .map(|n| n.to_string_lossy().into_owned())
            .unwrap_or_default();
        if !keep_ids.contains(&name) {
            remove_path(&path)?;
            removed.push(name);
        }
    }
    Ok(removed)
}

/// Commit the artifact to the state branch worktree and push it.
pub fn save_pages_state(
    ui: &Ui,
    artifact_dir: &Path,
    git_repo: &Path,
    state_dir: &Path,
    commit_message: &str,
    state_branch: &str,
) -> Result<()> {
    let artifact_dir = resolve_path(artifact_dir);
    let git_repo = resolve_path(git_repo);
    let state_dir = resolve_path(state_dir);
    if !state_dir.is_dir() {
        git(
            &git_repo,
            &[
                "worktree",
                "add",
                "--detach",
                &state_dir.display().to_string(),
            ],
        )?;
        git(&state_dir, &["switch", "--orphan", state_branch])?;
    }
    clear_directory(&state_dir, &[".git"])?;
    copy_contents(&artifact_dir, &state_dir, &[])?;
    git(&state_dir, &["config", "user.name", BOT_NAME])?;
    git(&state_dir, &["config", "user.email", BOT_EMAIL])?;
    git(&state_dir, &["add", "-A"])?;
    let diff = Command::new("git")
        .args([
            "-C",
            &state_dir.display().to_string(),
            "diff",
            "--cached",
            "--quiet",
        ])
        .status()
        .map_err(|err| format!("git: {err}"))?;
    match diff.code() {
        Some(0) => {
            ui.print("Pages state is already current.");
            return Ok(());
        }
        Some(1) => {}
        _ => return Err(format!("git diff --cached --quiet failed ({diff})")),
    }
    git(&state_dir, &["commit", "-m", commit_message])?;
    git(
        &state_dir,
        &["push", "origin", &format!("HEAD:{state_branch}")],
    )?;
    Ok(())
}

fn http_ok(url: &str) -> bool {
    let sink = if cfg!(windows) { "NUL" } else { "/dev/null" };
    Command::new("curl")
        .args([
            "-sS",
            "-L",
            "-o",
            sink,
            "-m",
            "10",
            "-w",
            "%{http_code}",
            url,
        ])
        .output()
        .map(|output| {
            output.status.success() && String::from_utf8_lossy(&output.stdout).trim() == "200"
        })
        .unwrap_or(false)
}

/// Both URLs answer 200 in the same attempt, retrying `attempts` times.
pub fn verify_urls(url: &str, index_url: &str, attempts: u32, sleep: Duration) -> bool {
    for _ in 0..attempts {
        if http_ok(url) && http_ok(index_url) {
            return true;
        }
        thread::sleep(sleep);
    }
    false
}

/// The sticky PR comment: marker, preview and index links, branch and short sha.
pub fn preview_comment_body(
    preview_url: &str,
    index_url: &str,
    branch: &str,
    head_sha: &str,
) -> String {
    let short_sha: String = head_sha.chars().take(7).collect();
    [
        COMMENT_MARKER.to_string(),
        "### Branch preview".to_string(),
        String::new(),
        format!("Preview: [Preview]({preview_url})"),
        String::new(),
        format!("Preview index: [Preview index]({index_url})"),
        String::new(),
        format!("Branch: `{branch}`"),
        format!("Commit: `{short_sha}`"),
    ]
    .join("\n")
}

/// Update the bot's sticky comment or create it. `gh` runs the GitHub CLI
/// with the given arguments and returns its stdout; tests pass a recorder.
pub fn upsert_preview_comment(
    gh: &mut dyn FnMut(&[String]) -> Result<String>,
    repo: &str,
    pr_number: &str,
    body: &str,
) -> Result<&'static str> {
    let jq = format!(".[] | select(.user.login == \"{BOT_NAME}\" and (.body | startswith(\"{COMMENT_MARKER}\"))) | .id");
    let listing = gh(&[
        "api".to_string(),
        format!("repos/{repo}/issues/{pr_number}/comments"),
        "--paginate".to_string(),
        "--jq".to_string(),
        jq,
    ])?;
    let comment_id = listing.lines().map(str::trim).find(|line| !line.is_empty());
    match comment_id {
        Some(id) => {
            gh(&[
                "api".to_string(),
                "--method".to_string(),
                "PATCH".to_string(),
                format!("repos/{repo}/issues/comments/{id}"),
                "-f".to_string(),
                format!("body={body}"),
            ])?;
            Ok("updated")
        }
        None => {
            gh(&[
                "api".to_string(),
                "--method".to_string(),
                "POST".to_string(),
                format!("repos/{repo}/issues/{pr_number}/comments"),
                "-f".to_string(),
                format!("body={body}"),
            ])?;
            Ok("created")
        }
    }
}

fn append_env_file(env_name: &str, lines: &[String]) -> Result<bool> {
    let Some(path) = std::env::var_os(env_name).filter(|p| !p.is_empty()) else {
        return Ok(false);
    };
    let path = PathBuf::from(path);
    let mut file = fs::OpenOptions::new()
        .create(true)
        .append(true)
        .open(&path)
        .map_err(at(&path))?;
    for line in lines {
        io::Write::write_all(&mut file, format!("{line}\n").as_bytes()).map_err(at(&path))?;
    }
    Ok(true)
}

/// `key=value` lines into `$GITHUB_OUTPUT`, or on stdout when it is unset.
pub fn write_outputs(ui: &Ui, values: &[(&str, &str)]) -> Result<()> {
    let lines: Vec<String> = values
        .iter()
        .map(|(key, value)| format!("{key}={value}"))
        .collect();
    if !append_env_file("GITHUB_OUTPUT", &lines)? {
        for line in &lines {
            ui.print(line);
        }
    }
    Ok(())
}

/// Lines appended to `$GITHUB_STEP_SUMMARY`; nothing happens when unset.
pub fn write_summary(lines: &[String]) -> Result<()> {
    append_env_file("GITHUB_STEP_SUMMARY", lines).map(|_| ())
}

fn prune_command(
    ui: &Ui,
    previews_dir: &Path,
    open_prs_json: &str,
) -> std::result::Result<(), CliError> {
    let open_prs: serde_json::Value = serde_json::from_str(open_prs_json)
        .map_err(|err| CliError::Message(format!("--open-prs-json: {err}")))?;
    let mut keep_ids = BTreeSet::new();
    for pr in open_prs.as_array().into_iter().flatten() {
        let number = match pr.get("number") {
            Some(serde_json::Value::String(s)) => s.trim().to_string(),
            Some(serde_json::Value::Number(n)) => n.to_string(),
            _ => String::new(),
        };
        let head_ref = pr
            .get("headRefName")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .trim();
        if !number.is_empty() {
            keep_ids.insert(safe_preview_branch(head_ref, &number));
        }
    }
    let removed = prune_previews(previews_dir, &keep_ids).map_err(CliError::Message)?;
    for name in &removed {
        ui.print(&format!("Removed stale preview: {name}"));
    }
    write_outputs(ui, &[("removed", &removed.len().to_string())]).map_err(CliError::Message)
}

/// Run one `github-pages` step; a failure is an `Error:` line, exit 1.
pub fn run(ui: &Ui, cmd: Cmd) -> std::result::Result<(), CliError> {
    match cmd {
        Cmd::ComputePreviewPath {
            head_ref,
            pr_number,
            pages_base_path,
            pages_base_url,
        } => {
            let preview =
                compute_preview_path(&head_ref, &pr_number, &pages_base_path, &pages_base_url);
            write_outputs(
                ui,
                &[
                    ("safe_branch", &preview.safe_branch),
                    ("base_path", &preview.base_path),
                    ("url", &preview.url),
                ],
            )
            .map_err(CliError::Message)
        }
        Cmd::PreservePreviews {
            site_dir,
            git_repo,
            state_dir,
            state_branch,
        } => preserve_branch_previews(&site_dir, &git_repo, &state_dir, &state_branch, true)
            .map_err(CliError::Message),
        Cmd::PrepareArtifact {
            production_site,
            artifact_dir,
            git_repo,
            state_dir,
            state_branch,
        } => prepare_pages_artifact(
            &production_site,
            &artifact_dir,
            &git_repo,
            &state_dir,
            &state_branch,
            true,
        )
        .map_err(CliError::Message),
        Cmd::CopyBranchPreview {
            preview_site,
            artifact_dir,
            preview_id,
        } => copy_branch_preview(&preview_site, &artifact_dir, &preview_id)
            .map_err(CliError::Message),
        Cmd::WritePreviewMetadata {
            artifact_dir,
            preview_id,
            pr_number,
            title,
            branch,
            commit,
            pr_url,
            updated_at,
            repo,
            author,
            author_url,
            avatar_url,
        } => write_preview_metadata(
            &artifact_dir,
            &preview_id,
            &PreviewMetadata {
                pr_number: &pr_number,
                title: &title,
                branch: &branch,
                commit: &commit,
                pr_url: &pr_url,
                updated_at: &updated_at,
                repo: &repo,
                author: &author,
                author_url: &author_url,
                avatar_url: &avatar_url,
            },
        )
        .map_err(CliError::Message),
        Cmd::WritePreviewsData { previews_dir } => {
            let entries = write_previews_data(&previews_dir).map_err(CliError::Message)?;
            ui.print(&format!("Wrote metadata for {} preview(s).", entries.len()));
            Ok(())
        }
        Cmd::PrunePreviews {
            previews_dir,
            open_prs_json,
        } => prune_command(ui, &previews_dir, &open_prs_json),
        Cmd::SaveState {
            artifact_dir,
            git_repo,
            state_dir,
            commit_message,
            state_branch,
        } => save_pages_state(
            ui,
            &artifact_dir,
            &git_repo,
            &state_dir,
            &commit_message,
            &state_branch,
        )
        .map_err(CliError::Message),
        Cmd::VerifyUrl {
            url,
            index_url,
            summary_heading,
            primary_label,
            index_label,
            success_message,
            error_message,
            attempts,
            sleep_seconds,
        } => {
            ui.print(&format!("{primary_label}: {url}"));
            ui.print(&format!("{index_label}: {index_url}"));
            write_summary(&[
                format!("### {summary_heading}"),
                String::new(),
                format!("{primary_label}: {url}"),
                format!("{index_label}: {index_url}"),
            ])
            .map_err(CliError::Message)?;
            if verify_urls(
                &url,
                &index_url,
                attempts,
                Duration::from_secs_f64(sleep_seconds.max(0.0)),
            ) {
                ui.print(&success_message);
                write_summary(&[String::new(), success_message]).map_err(CliError::Message)
            } else {
                ui.print(&format!("::error::{error_message}: {url} {index_url}"));
                Err(CliError::Exit(1))
            }
        }
        Cmd::CommentPreview {
            repo,
            pr_number,
            preview_url,
            index_url,
            branch,
            head_sha,
        } => {
            let body = preview_comment_body(&preview_url, &index_url, &branch, &head_sha);
            let mut gh = |args: &[String]| run_checked("gh", args);
            let result = upsert_preview_comment(&mut gh, &repo, &pr_number, &body)
                .map_err(CliError::Message)?;
            ui.print(&format!("Preview PR comment {result}."));
            Ok(())
        }
    }
}

#[cfg(test)]
#[path = "github_pages_tests.rs"]
mod tests;
