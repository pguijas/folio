//! Every `.js`, `.mjs` and `.cjs` file under the configured roots, in path
//! order, with the module name its path publishes. `node_modules`, `dist`,
//! `build` and dot directories are never read below a root; JSX and
//! TypeScript are reported rather than parsed into an empty page.

use std::collections::HashMap;
use std::path::{Path, PathBuf};

use folio_ir::excludes::is_excluded;

/// One file to parse: where it is, what module it publishes and the root it
/// was discovered under.
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct SourceFile {
    pub path: PathBuf,
    pub module_name: String,
    pub root: PathBuf,
}

/// What a walk of the roots found, and what it refused to read.
#[derive(Debug, Default, Clone, PartialEq, Eq)]
pub struct Discovery {
    pub files: Vec<SourceFile>,
    pub warnings: Vec<String>,
}

/// The extensions the reader owns; `.jsx` is deliberately not one of them.
pub const EXTENSIONS: [&str; 3] = ["js", "mjs", "cjs"];

/// Directories below a root that hold installed or built JavaScript, never
/// the project's own source. A root named after one is still read.
pub const SKIPPED_DIRS: [&str; 3] = ["node_modules", "dist", "build"];

/// TypeScript suffixes: reported once per root, never parsed.
const TYPESCRIPT: [&str; 4] = ["ts", "tsx", "mts", "cts"];

/// The files of every root, in path order per root, plus a warning per JSX
/// file and one per root that holds TypeScript. Two files that publish the
/// same module (`index.cjs` beside `index.mjs`, `a.js` beside `a/index.js`)
/// would share one page: the first in path order is read, the other named in
/// a warning.
pub fn discover(roots: &[PathBuf], excludes: &[String]) -> Discovery {
    let mut found = Discovery::default();
    let mut published: HashMap<String, PathBuf> = HashMap::new();
    for root in roots {
        let mut paths = Vec::new();
        walk(root, &mut paths);
        paths.sort();
        let mut typescript: Vec<PathBuf> = Vec::new();
        for path in paths {
            if is_excluded(&path, excludes) {
                continue;
            }
            match extension(&path) {
                Some("jsx") => found.warnings.push(format!(
                    "JSX is not read in this release; skipping {}",
                    path.display()
                )),
                Some(ext) if TYPESCRIPT.contains(&ext) => typescript.push(path),
                Some(ext) if EXTENSIONS.contains(&ext) => {
                    let module_name = module_name(&path, root);
                    if let Some(first) = published.get(&module_name) {
                        found.warnings.push(format!(
                            "{} publishes the module `{module_name}` that {} already does; skipping it",
                            path.display(),
                            first.display()
                        ));
                        continue;
                    }
                    published.insert(module_name.clone(), path.clone());
                    found.files.push(SourceFile {
                        module_name,
                        path,
                        root: root.clone(),
                    });
                }
                _ => {}
            }
        }
        if let Some(first) = typescript.first() {
            found.warnings.push(format!(
                "TypeScript is not read in this release; skipping {} file{} under {} (first: {})",
                typescript.len(),
                if typescript.len() == 1 { "" } else { "s" },
                root.display(),
                first.display()
            ));
        }
    }
    found
}

/// The dotted module a file publishes, relative to its root. `index.js` names
/// its directory, and a root's own `index.js` names the root.
pub fn module_name(path: &Path, root: &Path) -> String {
    let relative = path.strip_prefix(root).unwrap_or(path);
    let mut parts: Vec<String> = relative
        .iter()
        .map(|part| part.to_string_lossy().to_string())
        .collect();
    let stem = Path::new(parts.last().map_or("", |last| last.as_str()))
        .file_stem()
        .map_or(String::new(), |stem| stem.to_string_lossy().to_string());
    if stem == "index" {
        parts.pop();
    } else if let Some(last) = parts.last_mut() {
        *last = stem;
    }
    if parts.is_empty() {
        return root
            .file_name()
            .map_or(String::from("index"), |name| name.to_string_lossy().into());
    }
    parts.join(".")
}

/// Every file under `dir`, depth first, with the skipped and dot
/// directories left alone.
fn walk(dir: &Path, found: &mut Vec<PathBuf>) {
    let Ok(entries) = std::fs::read_dir(dir) else {
        return;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        let name = entry.file_name().to_string_lossy().to_string();
        if path.is_dir() {
            if !SKIPPED_DIRS.contains(&name.as_str()) && !name.starts_with('.') {
                walk(&path, found);
            }
        } else {
            found.push(path);
        }
    }
}

fn extension(path: &Path) -> Option<&str> {
    path.extension().and_then(|ext| ext.to_str())
}

#[cfg(test)]
#[path = "discover_tests.rs"]
mod tests;
