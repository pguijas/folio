//! Path resolution shared by every configurable directory: the output-dir
//! containment rule, the contained-dir guard, non-strict canonicalisation and
//! the pathlib-style join.

use std::path::{Component, Path, PathBuf};

use crate::error::ConfigError;
use crate::value::quoted;

/// `Path.resolve(strict=False)`: canonicalise the longest existing ancestor
/// through the OS (symlinks, `..`), then append the missing tail with `.` and
/// `..` collapsed lexically. A relative path is anchored on the current directory.
pub fn canonicalize_lenient(path: &Path) -> PathBuf {
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir().unwrap_or_default().join(path)
    };
    let components: Vec<Component> = absolute.components().collect();
    for split in (1..=components.len()).rev() {
        let prefix: PathBuf = components[..split].iter().collect();
        let Ok(mut resolved) = std::fs::canonicalize(&prefix) else {
            continue;
        };
        for component in &components[split..] {
            match component {
                Component::ParentDir => {
                    resolved.pop();
                }
                Component::Normal(name) => resolved.push(name),
                _ => {}
            }
        }
        return resolved;
    }
    absolute
}

/// `str(pathlib.Path(base) / p)`: an absolute `p` replaces `base`; `.`
/// components, repeated and trailing separators go; `..` stays.
pub fn join_lexical(base: &Path, p: &str) -> PathBuf {
    let joined: PathBuf = base
        .join(p)
        .components()
        .filter(|c| !matches!(c, Component::CurDir))
        .collect();
    if joined.as_os_str().is_empty() {
        PathBuf::from(".")
    } else {
        joined
    }
}

/// `join_lexical` rendered as the string the config stores.
pub(crate) fn join_string(base: &Path, p: &str) -> String {
    join_lexical(base, p).to_string_lossy().into_owned()
}

fn output_error(message: impl Into<String>) -> ConfigError {
    ConfigError::field("output", message)
}

/// Resolve `output:` against `base` and refuse anything the build would
/// destroy: the project itself, its `.git`, or a configured source root.
pub fn resolve_output_dir(
    base: &Path,
    output_dir: &str,
    source_paths: &[&str],
) -> Result<PathBuf, ConfigError> {
    if output_dir.trim().is_empty() {
        return Err(output_error(
            "Output directory must be a non-empty relative path",
        ));
    }
    if Path::new(output_dir).is_absolute() {
        return Err(output_error(
            "Output directory must be relative to the project directory",
        ));
    }
    let project_root = canonicalize_lenient(base);
    let resolved = canonicalize_lenient(&project_root.join(output_dir));
    if resolved == project_root || !resolved.starts_with(&project_root) {
        return Err(output_error(
            "Output directory must stay within the project directory",
        ));
    }
    let git_dir = canonicalize_lenient(&project_root.join(".git"));
    if git_dir.starts_with(&resolved) {
        return Err(output_error(format!(
            "Output directory {} must not contain the repository's .git directory; \
             the build removes the output directory before writing to it",
            quoted(output_dir)
        )));
    }
    if resolved.starts_with(&git_dir) {
        return Err(output_error(format!(
            "Output directory {} must not be inside the repository's .git directory; \
             the build removes the output directory before writing to it",
            quoted(output_dir)
        )));
    }
    for raw_source in source_paths {
        if raw_source.trim().is_empty() {
            continue;
        }
        let source = canonicalize_lenient(&project_root.join(raw_source));
        if source.starts_with(&resolved) {
            return Err(output_error(format!(
                "Output directory {} would delete the source directory {}; the build \
                 removes the output directory before writing to it. Choose an output \
                 path that is not a source directory and does not contain one",
                quoted(output_dir),
                quoted(raw_source)
            )));
        }
    }
    Ok(resolved)
}

/// Resolve a user-configurable directory (`theme.package`, `template.path`,
/// `template.overlay_path`) against the project root: it must stay inside the
/// project, outside `.build/` and outside the output directory.
pub fn resolve_contained_dir(
    raw: &Path,
    project_root: &Path,
    output_dir: &Path,
    label: &str,
    must_exist: bool,
) -> Result<PathBuf, ConfigError> {
    let root = canonicalize_lenient(project_root);
    let path = if raw.is_absolute() {
        raw.to_path_buf()
    } else {
        root.join(raw)
    };
    let resolved = canonicalize_lenient(&path);
    let refuse = |message: String| Err(ConfigError::field(label, message));
    if !resolved.starts_with(&root) {
        return refuse(format!("{label} must stay within the project directory"));
    }
    if resolved.starts_with(root.join(".build")) {
        return refuse(format!("{label} cannot point inside the .build directory"));
    }
    if resolved.starts_with(canonicalize_lenient(output_dir)) {
        return refuse(format!("{label} cannot point inside the output directory"));
    }
    if must_exist && !resolved.is_dir() {
        return refuse(format!("{label} does not exist: {}", resolved.display()));
    }
    Ok(resolved)
}

#[cfg(test)]
#[path = "paths_tests.rs"]
mod tests;
