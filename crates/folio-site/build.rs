//! Embeds every file of `template/` into the binary as a static
//! table of `(relative posix path, bytes)` plus `TEMPLATE_HASH`, the SHA-256
//! over that table; `node_modules`, `.next` and `out` are development residue
//! and never shipped, and neither are local files no checkout tracks
//! (`*.tsbuildinfo`, `.DS_Store`, `.env*`).

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

use sha2::{Digest, Sha256};

const SKIPPED_DIRS: [&str; 3] = ["node_modules", ".next", "out"];

/// Local files the walk finds but the template never ships.
fn skipped_file(name: &str) -> bool {
    name.ends_with(".tsbuildinfo") || name == ".DS_Store" || name.starts_with(".env")
}

fn collect(dir: &Path, out: &mut Vec<PathBuf>) {
    println!("cargo:rerun-if-changed={}", dir.display());
    let mut entries: Vec<_> = fs::read_dir(dir)
        .unwrap_or_else(|e| panic!("read {}: {e}", dir.display()))
        .map(|entry| entry.expect("dir entry").path())
        .collect();
    entries.sort();
    for path in entries {
        let name = path.file_name().unwrap().to_string_lossy();
        if path.is_dir() {
            if !SKIPPED_DIRS.contains(&name.as_ref()) {
                collect(&path, out);
            }
        } else if path.is_file() && !skipped_file(&name) {
            out.push(path);
        }
    }
}

fn main() {
    let manifest_dir = PathBuf::from(std::env::var("CARGO_MANIFEST_DIR").unwrap());
    let template_root = manifest_dir
        .join("../../template")
        .canonicalize()
        .expect("template exists");
    let mut files = Vec::new();
    collect(&template_root, &mut files);

    let mut entries: Vec<(String, PathBuf)> = files
        .into_iter()
        .map(|path| {
            let rel = path
                .strip_prefix(&template_root)
                .unwrap()
                .components()
                .map(|c| c.as_os_str().to_string_lossy().into_owned())
                .collect::<Vec<_>>()
                .join("/");
            (rel, path)
        })
        .collect();
    entries.sort();
    let table: Vec<String> = entries
        .iter()
        .map(|(rel, path)| {
            format!(
                "    ({rel:?}, include_bytes!({:?})),\n",
                path.display().to_string()
            )
        })
        .collect();
    let mut digest = Sha256::new();
    for (rel, path) in &entries {
        digest.update(rel.as_bytes());
        digest.update(b"\0");
        digest.update(fs::read(path).expect("template file readable"));
        digest.update(b"\0");
    }
    let hash: String = digest
        .finalize()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect();
    let out_dir = PathBuf::from(std::env::var("OUT_DIR").unwrap());
    let mut file = fs::File::create(out_dir.join("template_files.rs")).unwrap();
    writeln!(
        file,
        "/// The bundled template, one entry per file, sorted by path.\n\
         pub static TEMPLATE_FILES: &[(&str, &[u8])] = &[\n{}];\n\
         /// SHA-256 over the embedded `(path, bytes)` table.\n\
         pub const TEMPLATE_HASH: &str = {hash:?};",
        table.concat()
    )
    .unwrap();
}
