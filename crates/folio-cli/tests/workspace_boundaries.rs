//! Every crate the `folio` binary is built from lives in this workspace: a
//! dependency is a sibling crate or a registry crate, never a path outside
//! `crates/` or a git checkout.

use std::fs;
use std::path::{Path, PathBuf};

fn repo() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn manifest(path: &Path) -> toml::Value {
    fs::read_to_string(path)
        .expect("manifest exists")
        .parse()
        .expect("valid Cargo manifest")
}

#[test]
fn every_dependency_is_a_sibling_crate_or_a_registry_crate() {
    let crates = repo().join("crates");
    for name in [
        "folio-cli",
        "folio-config",
        "folio-mdx",
        "folio-plugins",
        "folio-site",
        "folio-watch",
        "folio-docs",
        "folio-ir",
        "folio-lang-python",
        "folio-lang-javascript",
        "folio-lang-rust",
    ] {
        let path = crates.join(name).join("Cargo.toml");
        assert!(path.is_file(), "the workspace must own {name}");
        let cargo = manifest(&path);
        for section in ["dependencies", "build-dependencies", "dev-dependencies"] {
            let Some(deps) = cargo.get(section).and_then(toml::Value::as_table) else {
                continue;
            };
            for (dep, spec) in deps {
                assert!(spec.get("git").is_none(), "{name} takes {dep} from git");
                if let Some(dep_path) = spec.get("path").and_then(toml::Value::as_str) {
                    let sibling = crates.join(name).join(dep_path);
                    assert_eq!(
                        sibling.parent().map(fs::canonicalize).and_then(Result::ok),
                        fs::canonicalize(&crates).ok(),
                        "{name} takes {dep} from outside crates/"
                    );
                }
            }
        }
    }
}
