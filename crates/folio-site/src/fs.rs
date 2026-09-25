//! Atomic write-if-changed, the template copy rules, symlink rejection and the
//! content hashes.

use std::collections::BTreeSet;
use std::io::{self, Write};
use std::path::{Path, PathBuf};

use sha2::{Digest, Sha256};

use crate::SiteError;

/// Directory names never copied from a template, theme package or overlay.
pub const COPY_IGNORED_DIRS: [&str; 5] =
    ["node_modules", ".next", "__pycache__", ".git", "content"];
/// Marker file written into staging directories Folio may delete again.
pub const FOLIO_STAGING_MARKER: &str = ".folio-staging";
/// Root-level files the injector writes itself from pristine source.
pub const INJECTED_ROOT_FILES: [&str; 1] = ["next.config.mjs"];

/// Atomic write, only when the bytes differ; keeps the existing mode or 0o644.
/// Returns whether a write happened.
pub fn write_text_if_changed(path: &Path, content: &str) -> io::Result<bool> {
    write_bytes_if_changed(path, content.as_bytes())
}

/// `write_text_if_changed` for raw bytes.
pub fn write_bytes_if_changed(path: &Path, data: &[u8]) -> io::Result<bool> {
    if let Ok(existing) = std::fs::read(path) {
        if existing == data {
            return Ok(false);
        }
    }
    let parent = path
        .parent()
        .filter(|p| !p.as_os_str().is_empty())
        .unwrap_or(Path::new("."));
    std::fs::create_dir_all(parent)?;
    let name = path
        .file_name()
        .map(|n| n.to_string_lossy().into_owned())
        .unwrap_or_default();
    let mut temp = tempfile::Builder::new()
        .prefix(&format!(".{name}."))
        .tempfile_in(parent)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mode = std::fs::metadata(path)
            .map(|m| m.permissions().mode() & 0o777)
            .unwrap_or(0o644);
        std::fs::set_permissions(temp.path(), std::fs::Permissions::from_mode(mode))?;
    }
    temp.write_all(data)?;
    temp.flush()?;
    temp.persist(path).map_err(|e| e.error)?;
    Ok(true)
}

fn is_ignored_name(name: &std::ffi::OsStr) -> bool {
    let name = name.to_string_lossy();
    COPY_IGNORED_DIRS.contains(&name.as_ref()) || name == FOLIO_STAGING_MARKER
}

fn sorted_entries(dir: &Path) -> io::Result<Vec<PathBuf>> {
    let mut entries: Vec<PathBuf> = std::fs::read_dir(dir)?
        .map(|e| e.map(|e| e.path()))
        .collect::<io::Result<_>>()?;
    entries.sort();
    Ok(entries)
}

/// Recursive copy with `dirs_exist_ok` semantics: skips `COPY_IGNORED_DIRS`
/// and the staging marker at every level and `extra_root_ignores` at the
/// root of `src`. Callers reject symlinks first.
pub fn copy_tree(src: &Path, dst: &Path, extra_root_ignores: &[&str]) -> io::Result<()> {
    fn walk(src: &Path, dst: &Path, root_ignores: Option<&[&str]>) -> io::Result<()> {
        std::fs::create_dir_all(dst)?;
        for entry in sorted_entries(src)? {
            let name = entry.file_name().unwrap_or_default();
            if is_ignored_name(name) {
                continue;
            }
            if let Some(ignores) = root_ignores {
                if ignores.contains(&name.to_string_lossy().as_ref()) {
                    continue;
                }
            }
            let target = dst.join(name);
            if entry.is_dir() {
                walk(&entry, &target, None)?;
            } else {
                std::fs::copy(&entry, &target)?;
            }
        }
        Ok(())
    }
    walk(src, dst, Some(extra_root_ignores))
}

/// Every path a `copy_tree` would visit, directories before their files,
/// pruning the ignored directories.
pub fn walk_copied_entries(root: &Path) -> Vec<PathBuf> {
    fn walk(dir: &Path, out: &mut Vec<PathBuf>) {
        let Ok(entries) = sorted_entries(dir) else {
            return;
        };
        let (dirs, files): (Vec<_>, Vec<_>) = entries.into_iter().partition(|p| {
            std::fs::symlink_metadata(p)
                .map(|m| m.is_dir())
                .unwrap_or(false)
        });
        let dirs: Vec<_> = dirs.into_iter().filter(|p| !is_ignored_dir(p)).collect();
        out.extend(dirs.iter().cloned());
        out.extend(files);
        for dir in dirs {
            walk(&dir, out);
        }
    }
    fn is_ignored_dir(path: &Path) -> bool {
        path.file_name()
            .map(|n| COPY_IGNORED_DIRS.contains(&n.to_string_lossy().as_ref()))
            .unwrap_or(false)
    }
    let mut out = Vec::new();
    walk(root, &mut out);
    out
}

fn symlink_error(root: &Path, entry: &Path, label: &str) -> SiteError {
    let rel = entry.strip_prefix(root).unwrap_or(entry);
    SiteError::Value(format!("{label} must not contain symlinks: {}", posix(rel)))
}

/// Fail on the first symlink a copy of `root` would touch.
pub fn reject_symlinks(root: &Path, label: &str) -> crate::Result<()> {
    for entry in walk_copied_entries(root) {
        if entry.is_symlink() {
            return Err(symlink_error(root, &entry, label));
        }
    }
    Ok(())
}

/// The relative file paths a copy of `root` would produce, rejecting symlinks
/// in the same walk.
pub fn collect_copyable_files(root: &Path, label: &str) -> crate::Result<BTreeSet<PathBuf>> {
    let mut files = BTreeSet::new();
    for entry in walk_copied_entries(root) {
        if entry.is_symlink() {
            return Err(symlink_error(root, &entry, label));
        }
        if entry.is_file() {
            files.insert(entry.strip_prefix(root).unwrap_or(&entry).to_path_buf());
        }
    }
    Ok(files)
}

/// SHA-256 hex of a file's bytes; `""` when it is not a regular file.
pub fn hash_file(path: &Path) -> String {
    match std::fs::read(path) {
        Ok(bytes) if path.is_file() => hex(&Sha256::digest(&bytes)),
        _ => String::new(),
    }
}

/// SHA-256 over `rel\0bytes\0` of every regular file under `root`, sorted by
/// path, skipping `node_modules`, `.next`, `out`, `__pycache__`, `.git`.
pub fn hash_tree(root: &Path) -> String {
    const SKIP: [&str; 5] = ["node_modules", ".next", "out", "__pycache__", ".git"];
    fn walk(dir: &Path, out: &mut Vec<PathBuf>) {
        let Ok(entries) = sorted_entries(dir) else {
            return;
        };
        for entry in entries {
            if entry
                .file_name()
                .map(|n| SKIP.contains(&n.to_string_lossy().as_ref()))
                .unwrap_or(false)
            {
                continue;
            }
            if entry.is_dir() {
                walk(&entry, out);
            } else if entry.is_file() {
                out.push(entry);
            }
        }
    }
    let mut files = Vec::new();
    walk(root, &mut files);
    files.sort();
    let mut digest = Sha256::new();
    for path in files {
        let rel = path.strip_prefix(root).unwrap_or(&path);
        digest.update(posix(rel).as_bytes());
        digest.update(b"\0");
        digest.update(std::fs::read(&path).unwrap_or_default());
        digest.update(b"\0");
    }
    hex(&digest.finalize())
}

/// SHA-256 hex of `bytes`.
pub fn sha256_hex(bytes: &[u8]) -> String {
    hex(&Sha256::digest(bytes))
}

fn hex(bytes: &[u8]) -> String {
    bytes.iter().map(|b| format!("{b:02x}")).collect()
}

/// `/`-separated rendering of a path.
pub fn posix(path: &Path) -> String {
    path.components()
        .map(|c| c.as_os_str().to_string_lossy().into_owned())
        .collect::<Vec<_>>()
        .join("/")
}

/// `rmtree` that tolerates a missing target.
pub fn remove_dir_all_if_exists(path: &Path) -> io::Result<()> {
    match std::fs::remove_dir_all(path) {
        Err(e) if e.kind() == io::ErrorKind::NotFound => Ok(()),
        other => other,
    }
}

/// `unlink` that tolerates a missing target.
pub fn remove_file_if_exists(path: &Path) -> io::Result<()> {
    match std::fs::remove_file(path) {
        Err(e) if e.kind() == io::ErrorKind::NotFound => Ok(()),
        other => other,
    }
}

/// Every regular file under `root`, sorted by full path (Python `sorted(rglob)`).
pub fn files_under(root: &Path) -> Vec<PathBuf> {
    fn walk(dir: &Path, out: &mut Vec<PathBuf>) {
        let Ok(entries) = sorted_entries(dir) else {
            return;
        };
        for entry in entries {
            if entry.is_dir() {
                walk(&entry, out);
            } else if entry.is_file() {
                out.push(entry);
            }
        }
    }
    let mut out = Vec::new();
    walk(root, &mut out);
    out.sort();
    out
}

/// Plain recursive copy of `src` into `dst` (Python `shutil.copytree`).
pub fn copy_tree_all(src: &Path, dst: &Path) -> io::Result<()> {
    std::fs::create_dir_all(dst)?;
    for entry in sorted_entries(src)? {
        let target = dst.join(entry.file_name().unwrap_or_default());
        if entry.is_dir() {
            copy_tree_all(&entry, &target)?;
        } else {
            std::fs::copy(&entry, &target)?;
        }
    }
    Ok(())
}

#[cfg(test)]
#[path = "fs_tests.rs"]
mod tests;
