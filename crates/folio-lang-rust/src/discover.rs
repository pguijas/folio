//! Source discovery under the configured roots: every crate under a root, its
//! entry module (`src/lib.rs`, else `src/main.rs`) and the file modules it
//! declares, depth first in declaration order. A module nobody declares is not
//! part of the crate and is not documented.

use std::collections::HashSet;
use std::path::{Component, Path, PathBuf};

use folio_ir::excludes::is_excluded;

/// One discovered file: where it is, what module it publishes, which root it came from.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceFile {
    pub path: PathBuf,
    pub module_name: String,
    pub root: PathBuf,
}

/// Directories no crate of the project lives under.
const SKIPPED_DIRS: [&str; 2] = ["target", "node_modules"];

/// Every reachable module under the roots, in publication order. Missing roots
/// yield nothing; the caller reports them.
pub fn discover(roots: &[PathBuf], excludes: &[String]) -> Vec<SourceFile> {
    let mut files = Vec::new();
    let mut seen = HashSet::new();
    for root in roots {
        for (crate_root, crate_name) in crates_under(root) {
            if let Some(entry) = entry_of(&crate_root) {
                walk(
                    &entry,
                    &crate_root,
                    &crate_name,
                    root,
                    excludes,
                    &mut seen,
                    &mut files,
                );
            }
        }
    }
    files
}

/// The crate a file belongs to: the nearest ancestor directory whose
/// `Cargo.toml` names a package, and that name as a module path.
pub fn crate_of(path: &Path) -> Option<(PathBuf, String)> {
    enclosing_crate(path.parent()?)
}

/// The crate a directory sits in, the directory itself included.
fn enclosing_crate(dir: &Path) -> Option<(PathBuf, String)> {
    dir.ancestors()
        .find_map(|dir| package_name(dir).map(|name| (dir.to_path_buf(), name)))
}

/// A crate's entry module: `src/lib.rs`, else `src/main.rs`.
fn entry_of(crate_root: &Path) -> Option<PathBuf> {
    ["src/lib.rs", "src/main.rs"]
        .iter()
        .map(|name| crate_root.join(name))
        .find(|path| path.is_file())
}

/// The module a file publishes, `demo_crate::utils::helpers`. A file outside
/// any crate publishes under its own stem.
pub fn module_name(path: &Path) -> String {
    match crate_of(path) {
        Some((crate_root, crate_name)) => module_in_crate(path, &crate_root, &crate_name),
        None => path
            .file_stem()
            .unwrap_or_default()
            .to_string_lossy()
            .into(),
    }
}

/// `[package] name` with `-` as `_`, the name the crate is imported under.
fn package_name(dir: &Path) -> Option<String> {
    let manifest = std::fs::read_to_string(dir.join("Cargo.toml")).ok()?;
    let name = manifest
        .parse::<toml::Value>()
        .ok()?
        .get("package")?
        .get("name")?
        .as_str()?
        .replace('-', "_");
    Some(name)
}

/// Every crate under a root, the root itself included, in path order.
fn crates_under(root: &Path) -> Vec<(PathBuf, String)> {
    let mut crates = Vec::new();
    let mut stack = vec![root.to_path_buf()];
    while let Some(dir) = stack.pop() {
        if let Some(name) = package_name(&dir) {
            crates.push((dir.clone(), name));
        }
        let Ok(entries) = std::fs::read_dir(&dir) else {
            continue;
        };
        for entry in entries.flatten() {
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().to_string();
            if path.is_dir() && !name.starts_with('.') && !SKIPPED_DIRS.contains(&name.as_str()) {
                stack.push(path);
            }
        }
    }
    // A root inside a crate (`crates/core/src`) publishes that crate, as long
    // as the entry module it would parse is under the root.
    if crates.is_empty() {
        if let Some((crate_root, name)) = enclosing_crate(root) {
            if entry_of(&crate_root).is_some_and(|entry| entry.starts_with(root)) {
                crates.push((crate_root, name));
            }
        }
    }
    crates.sort();
    crates
}

/// The module path of a file under its crate: `lib.rs`, `main.rs` and `mod.rs`
/// name their directory, every other file its own stem.
fn module_in_crate(path: &Path, crate_root: &Path, crate_name: &str) -> String {
    let rel = path
        .strip_prefix(crate_root.join("src"))
        .unwrap_or_else(|_| path.strip_prefix(crate_root).unwrap_or(path));
    let mut parts: Vec<String> = rel
        .components()
        .filter_map(|c| match c {
            Component::Normal(s) => Some(s.to_string_lossy().to_string()),
            _ => None,
        })
        .collect();
    match parts.last().map(String::as_str) {
        Some("lib.rs") | Some("main.rs") | Some("mod.rs") => {
            parts.pop();
        }
        Some(last) => {
            let stem = last.trim_end_matches(".rs").to_string();
            *parts.last_mut().expect("a last part") = stem;
        }
        None => {}
    }
    std::iter::once(crate_name.to_string())
        .chain(parts)
        .collect::<Vec<_>>()
        .join("::")
}

/// The directory a file's `mod` declarations resolve against.
fn child_dir(file: &Path) -> PathBuf {
    let parent = file.parent().unwrap_or(Path::new(""));
    match file.file_stem().and_then(|s| s.to_str()) {
        Some("lib") | Some("main") | Some("mod") | None => parent.to_path_buf(),
        Some(stem) => parent.join(stem),
    }
}

/// The file a `mod name;` declaration publishes: `name.rs` or `name/mod.rs`.
fn module_file(dir: &Path, name: &str) -> Option<PathBuf> {
    [
        dir.join(format!("{name}.rs")),
        dir.join(name).join("mod.rs"),
    ]
    .into_iter()
    .find(|path| path.is_file())
}

/// The `mod name;` declarations of a source, plain `pub` ones only: a private,
/// `pub(crate)` or `#[doc(hidden)]` module is an implementation detail, as it
/// is for `rustdoc`.
fn declared_modules(source: &str) -> Vec<String> {
    let Ok(file) = syn::parse_file(source) else {
        return Vec::new();
    };
    file.items
        .iter()
        .filter_map(|item| match item {
            syn::Item::Mod(m)
                if m.content.is_none() && crate::parse::published(&m.vis, &m.attrs) =>
            {
                Some(m.ident.to_string())
            }
            _ => None,
        })
        .collect()
}

// ponytail: the tree is parsed twice, here for `mod` and again in `parse_file`;
// share one parse if discovery ever shows up in a profile.
fn walk(
    path: &Path,
    crate_root: &Path,
    crate_name: &str,
    root: &Path,
    excludes: &[String],
    seen: &mut HashSet<PathBuf>,
    files: &mut Vec<SourceFile>,
) {
    if is_excluded(path, excludes) || !seen.insert(path.to_path_buf()) {
        return;
    }
    let Ok(source) = std::fs::read_to_string(path) else {
        return;
    };
    files.push(SourceFile {
        path: path.to_path_buf(),
        module_name: module_in_crate(path, crate_root, crate_name),
        root: root.to_path_buf(),
    });
    let dir = child_dir(path);
    for name in declared_modules(&source) {
        if let Some(child) = module_file(&dir, &name) {
            walk(&child, crate_root, crate_name, root, excludes, seen, files);
        }
    }
}

#[cfg(test)]
#[path = "discover_tests.rs"]
mod tests;
