//! Source discovery under the configured roots: the `src/` import-root rule, package
//! naming, Python `sorted(Path)` order, excludes per file.

use std::path::{Component, Path, PathBuf};

use folio_ir::excludes::{is_excluded, python_sort_key};

/// One discovered file: where it is, what module it publishes, which root it came from.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceFile {
    pub path: PathBuf,
    pub module_name: String,
    pub root: PathBuf,
}

/// A root whose last component is `src` with no `src/__init__.py` publishes its
/// children under their import names instead of a synthetic `src.*` package.
pub fn is_import_root(root: &Path) -> bool {
    root.file_name().is_some_and(|n| n == "src") && !root.join("__init__.py").is_file()
}

/// Python's `Path.name`: `..` for a root ending in `..`, `""` for `/`.
fn python_path_name(path: &Path) -> String {
    match path.file_name() {
        Some(name) => name.to_string_lossy().to_string(),
        None => match path.components().next_back() {
            Some(Component::ParentDir) => "..".to_string(),
            _ => String::new(),
        },
    }
}

/// The dotted parts of `path` relative to `root`: `__init__.py` names its directory.
fn module_parts(path: &Path, root: &Path) -> Vec<String> {
    let rel = path.strip_prefix(root).unwrap_or(path);
    let mut parts: Vec<String> = rel
        .components()
        .filter_map(|c| match c {
            Component::Normal(s) => Some(s.to_string_lossy().to_string()),
            _ => None,
        })
        .collect();
    if parts.last().is_some_and(|s| s == "__init__.py") {
        parts.pop();
    } else if let Some(last) = parts.last_mut() {
        if let Some(stem) = last.strip_suffix(".py") {
            *last = stem.to_string();
        }
    }
    parts
}

/// The module a file publishes under its root; the watcher and discovery share it.
pub fn module_name(path: &Path, root: &Path) -> String {
    let parts = module_parts(path, root);
    if is_import_root(root) {
        return parts.join(".");
    }
    let root_name = python_path_name(root);
    if parts.is_empty() {
        root_name
    } else {
        format!("{root_name}.{}", parts.join("."))
    }
}

/// Every `.py` file under the roots in publication order. Missing roots yield nothing;
/// the caller reports them.
pub fn discover(roots: &[PathBuf], excludes: &[String]) -> Vec<SourceFile> {
    let mut files = Vec::new();
    for root in roots {
        if !root.exists() {
            continue;
        }
        let discovered = if is_import_root(root) {
            discover_import_root(root, excludes)
        } else {
            discover_package(root, &python_path_name(root), excludes)
        };
        files.extend(
            discovered
                .into_iter()
                .map(|(path, module_name)| SourceFile {
                    path,
                    module_name,
                    root: root.clone(),
                }),
        );
    }
    files
}

/// `sorted(root.rglob("*.py"))`, excluded files removed, named under `package_name`.
fn discover_package(
    root: &Path,
    package_name: &str,
    excludes: &[String],
) -> Vec<(PathBuf, String)> {
    let mut py_files = Vec::new();
    collect_py_files(root, &mut py_files);
    py_files.sort_by_cached_key(|p| python_sort_key(p));
    py_files
        .into_iter()
        .filter(|p| !is_excluded(p, excludes))
        .map(|p| {
            let parts = module_parts(&p, root);
            let name = if parts.is_empty() {
                package_name.to_string()
            } else {
                format!("{package_name}.{}", parts.join("."))
            };
            (p, name)
        })
        .collect()
}

/// Top-level modules first (sorted, `__init__.py` skipped), then each directory that
/// holds at least one non-excluded `.py`, as a package named after the directory.
fn discover_import_root(root: &Path, excludes: &[String]) -> Vec<(PathBuf, String)> {
    let mut top_level = Vec::new();
    let mut subdirs = Vec::new();
    if let Ok(entries) = std::fs::read_dir(root) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_dir() {
                subdirs.push(p);
            } else if p.extension().is_some_and(|e| e == "py")
                && p.file_name().is_some_and(|n| n != "__init__.py")
                && !is_excluded(&p, excludes)
            {
                top_level.push(p);
            }
        }
    }
    top_level.sort_by_cached_key(|p| python_sort_key(p));
    subdirs.sort_by_cached_key(|p| python_sort_key(p));

    let mut result: Vec<(PathBuf, String)> = top_level
        .into_iter()
        .map(|p| {
            let stem = p
                .file_stem()
                .unwrap_or_default()
                .to_string_lossy()
                .to_string();
            (p, stem)
        })
        .collect();
    for subdir in subdirs {
        let mut inside = Vec::new();
        collect_py_files(&subdir, &mut inside);
        if !inside.iter().any(|f| !is_excluded(f, excludes)) {
            continue;
        }
        let package_name = python_path_name(&subdir);
        result.extend(discover_package(&subdir, &package_name, excludes));
    }
    result
}

/// `Path.rglob("*.py")`: real directories are descended, directory symlinks are not,
/// symlinked files are yielded.
fn collect_py_files(dir: &Path, out: &mut Vec<PathBuf>) {
    let Ok(entries) = std::fs::read_dir(dir) else {
        return;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        let Ok(meta) = path.symlink_metadata() else {
            continue;
        };
        if meta.is_dir() {
            collect_py_files(&path, out);
        } else if path.extension().is_some_and(|e| e == "py") {
            out.push(path);
        }
    }
}

#[cfg(test)]
#[path = "discover_tests.rs"]
mod tests;
