//! Shared helpers for the black-box runs of the binary: the runner over the
//! no-op frontend runtime, the example project copy and small file helpers.
#![allow(dead_code)]

pub mod env;

use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

/// One finished run of the binary.
pub struct Run {
    pub code: i32,
    pub stdout: String,
    pub stderr: String,
}

impl Run {
    /// Exit 0, or the whole output in the panic message.
    pub fn ok(&self) -> &Run {
        assert_eq!(
            self.code, 0,
            "stdout:\n{}\nstderr:\n{}",
            self.stdout, self.stderr
        );
        self
    }

    /// Stderr without the no-op runtime's own warning: what this command
    /// reported.
    pub fn diagnostics(&self) -> String {
        self.stderr
            .lines()
            .filter(|l| !l.contains("FOLIO_FRONTEND_RUNTIME=noop"))
            .map(|l| format!("{l}\n"))
            .collect()
    }

    /// The step rows (`✓ ...` and `! ...`) in order.
    pub fn rows(&self) -> Vec<&str> {
        self.stdout
            .lines()
            .filter(|l| l.starts_with("✓ ") || l.starts_with("! "))
            .collect()
    }
}

/// Run `folio args` in `cwd`: colours off, the no-op frontend runtime, the
/// machine's Folio variables cleared, then `env` applied on top.
pub fn folio(cwd: &Path, args: &[&str], env: &[(&str, &str)]) -> Run {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_folio"));
    env::scrub(cmd.current_dir(cwd).args(args));
    for (name, value) in env {
        cmd.env(name, value);
    }
    let output = cmd.output().expect("folio binary");
    Run {
        code: output.status.code().unwrap_or(-1),
        stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
        stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
    }
}

/// Recursive copy of a fixture tree.
pub fn copy_tree(src: &Path, dst: &Path) {
    fs::create_dir_all(dst).unwrap();
    for entry in fs::read_dir(src).unwrap() {
        let entry = entry.unwrap();
        let target = dst.join(entry.file_name());
        if entry.file_type().unwrap().is_dir() {
            copy_tree(&entry.path(), &target);
        } else {
            fs::copy(entry.path(), &target).unwrap();
        }
    }
}

/// The repository root.
pub fn repo() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .unwrap()
}

/// `docs/examples/generated-site` copied into a canonical temp
/// dir, so the paths the binary writes into the manifest match.
pub fn example_project() -> (tempfile::TempDir, PathBuf) {
    let dir = tempfile::tempdir().unwrap();
    let project = dir.path().canonicalize().unwrap().join("generated-site");
    copy_tree(&repo().join("docs/examples/generated-site"), &project);
    (dir, project)
}

/// The file's text, or a panic naming it.
pub fn read(path: &Path) -> String {
    fs::read_to_string(path).unwrap_or_else(|e| panic!("{}: {e}", path.display()))
}
