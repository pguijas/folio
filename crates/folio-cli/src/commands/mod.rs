//! Command dispatch and the helpers every command shares: project target
//! resolution, cwd-relative path display, the shell-quoted command suffix.

pub mod build;
pub mod clean;
pub mod coverage;
pub mod github_pages;
pub mod init;
pub mod roadmap;
pub mod serve;
pub mod update;
pub mod versions;

use std::env;
use std::path::{Component, Path, PathBuf};

use crate::cli::{Command, ProjectArgs};
use crate::error::CliError;
use crate::ui::Ui;
use crate::PluginFactory;

/// Dispatch one parsed command.
pub fn run(command: Command, ui: &Ui, plugins: &[PluginFactory]) -> Result<(), CliError> {
    match command {
        Command::Init(args) => init::run(ui, args),
        Command::Build(args) => build::run(ui, args, plugins),
        Command::Serve(args) => serve::run(ui, args, plugins),
        Command::Coverage(args) => coverage::run(ui, args, plugins),
        Command::Clean(args) => clean::run(ui, args),
        Command::Roadmap(args) => roadmap::run(ui, args, plugins),
        Command::BuildVersions(args) => versions::run(ui, args, plugins),
        Command::GithubPages(cmd) => github_pages::run(ui, cmd),
    }
}

/// `Path.resolve(strict=False)`: absolute, symlinks followed on the part
/// that exists, the missing tail kept as written.
pub fn resolve_path(path: &Path) -> PathBuf {
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        env::current_dir()
            .map(|cwd| cwd.join(path))
            .unwrap_or_else(|_| path.to_path_buf())
    };
    // Component by component, like realpath: symlinks are followed on what
    // exists, `..` pops what was resolved so far, the missing tail is kept.
    let mut out = PathBuf::new();
    for component in absolute.components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                out.pop();
            }
            Component::Normal(_) => {
                out.push(component);
                if let Ok(canonical) = out.canonicalize() {
                    out = canonical;
                }
            }
            root => out.push(root),
        }
    }
    out
}

impl ProjectArgs {
    /// The project directory from `[DIRECTORY]` or `--project-dir`; both
    /// may be given only when they name the same place.
    pub fn resolve(&self) -> Result<PathBuf, CliError> {
        if let (Some(directory), Some(project_dir)) = (&self.directory, &self.project_dir) {
            if resolve_path(directory) != resolve_path(project_dir) {
                return Err(CliError::message(
                    "Pass the project directory either as an argument or --project-dir, not both.",
                ));
            }
        }
        let target = self
            .project_dir
            .clone()
            .or_else(|| self.directory.clone())
            .unwrap_or_else(|| env::current_dir().unwrap_or_else(|_| PathBuf::from(".")));
        Ok(resolve_path(&target))
    }
}

fn cwd() -> PathBuf {
    resolve_path(&env::current_dir().unwrap_or_else(|_| PathBuf::from(".")))
}

/// `os.path.relpath`: `target` relative to `base`, both absolute.
fn relpath(target: &Path, base: &Path) -> PathBuf {
    let target: Vec<Component> = target.components().collect();
    let base: Vec<Component> = base.components().collect();
    let common = target.iter().zip(&base).take_while(|(a, b)| a == b).count();
    let mut out = PathBuf::new();
    for _ in common..base.len() {
        out.push("..");
    }
    for part in &target[common..] {
        out.push(part);
    }
    out
}

/// `target` as the user would type it from the current directory, POSIX
/// separators, `.` for the current directory itself.
pub fn format_cli_path(target: &Path) -> String {
    let relative = relpath(&resolve_path(target), &cwd());
    let text: Vec<String> = relative
        .components()
        .map(|c| c.as_os_str().to_string_lossy().into_owned())
        .collect();
    if text.is_empty() {
        ".".to_string()
    } else {
        text.join("/")
    }
}

/// `shlex.quote`: unchanged when safe, else single-quoted.
fn shlex_quote(text: &str) -> String {
    let safe = !text.is_empty()
        && text
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || "@%+=:,./_-".contains(c));
    if safe {
        text.to_string()
    } else {
        format!("'{}'", text.replace('\'', "'\"'\"'"))
    }
}

/// `" <path>"` to append to `folio serve` etc., empty for the cwd.
pub fn command_target_suffix(target: &Path) -> String {
    if resolve_path(target) == cwd() {
        String::new()
    } else {
        format!(" {}", shlex_quote(&format_cli_path(target)))
    }
}

#[cfg(test)]
mod tests;
